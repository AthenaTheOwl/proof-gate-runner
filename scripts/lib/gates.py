#!/usr/bin/env python3
"""proof-gate-runner dispatcher.

Stdlib-only entry point invoked by scripts/run_gates.sh. Loads the
requested gate modules from this directory, runs each gate against
--path, aggregates findings into a markdown report, and exits with a
code keyed to the result set.

Exit codes:
  0  every requested gate passed (no fail-severity finding)
  1  at least one gate produced a fail-severity finding
  2  unknown gate name in --gates; no gate ran
  3  internal error (e.g. --path does not exist)

Requirement coverage (see decisions/DEC-001-gate-rule-corpus-v0.md for
the rationale on which IDs land here vs. defer to spec 0003):

  spec 0002 implemented in v0:
    R-PGR-V1-001 R-PGR-V1-002 R-PGR-V1-003 R-PGR-V1-004
    R-PGR-V1-007 R-PGR-V1-008 R-PGR-V1-009 R-PGR-V1-010
    R-PGR-V1-012
"""
from __future__ import annotations

import argparse
import importlib
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

REGISTRY: dict[str, str] = {
    "voice_lint": "voice_lint:run",
    "spec_check": "spec_check:run",
}

MARKER = "<!-- proof-gate-runner:summary -->"


@dataclass(frozen=True)
class Finding:
    severity: str  # "fail" or "warn"
    path: str
    line: Optional[int]
    rule_id: str
    message: str


@dataclass
class GateResult:
    gate: str
    findings: list[Finding] = field(default_factory=list)
    duration_ms: int = 0

    @property
    def passed(self) -> bool:
        return not any(f.severity == "fail" for f in self.findings)


def _load(spec: str) -> Callable[[Path], list[Finding]]:
    mod_name, func_name = spec.split(":", 1)
    mod = importlib.import_module(mod_name)
    return getattr(mod, func_name)


def _run_one(name: str, path: Path) -> GateResult:
    start = time.monotonic()
    try:
        fn = _load(REGISTRY[name])
        findings = list(fn(path))
    except Exception as exc:  # boundary catch; the dispatcher must not crash mid-batch
        findings = [
            Finding(
                severity="fail",
                path="",
                line=None,
                rule_id=f"{name}::internal_error",
                message=f"{type(exc).__name__}: {exc}"[:240],
            )
        ]
    duration_ms = int((time.monotonic() - start) * 1000)
    return GateResult(gate=name, findings=findings, duration_ms=duration_ms)


def render_report(results: list[GateResult]) -> str:
    lines = [
        MARKER,
        "## proof-gate-runner",
        "",
        "| gate | result | findings | duration |",
        "|------|--------|----------|----------|",
    ]
    for r in results:
        verdict = "pass" if r.passed else "fail"
        lines.append(f"| {r.gate} | {verdict} | {len(r.findings)} | {r.duration_ms} ms |")
    lines.append("")
    failing_rules = sorted({
        f.rule_id for r in results for f in r.findings if f.severity == "fail"
    })
    if failing_rules:
        lines.append("failing rules: " + ", ".join(f"`{rid}`" for rid in failing_rules))
    else:
        lines.append("all requested gates passed.")
    lines.append("")
    return "\n".join(lines)


def render_summary(results: list[GateResult], target: Path) -> str:
    """A human-readable summary of a gate run: which gates failed, the
    rules ranked by how often they fired, and the single worst offender.

    This is what `demo` prints. It is not the markdown PR report (that is
    render_report); it is the at-a-glance result a person reads in the
    terminal.
    """
    total = sum(len(r.findings) for r in results)
    failed = [r for r in results if not r.passed]
    lines: list[str] = []
    lines.append(f"proof-gate-runner -- scanned {target}")
    lines.append(
        f"{len(results)} gate(s), {total} finding(s), "
        f"{len(failed)} gate(s) failing"
    )
    lines.append("")

    col = f"{'gate':<12} {'result':<6} {'findings':>8}  rules that fired"
    lines.append(col)
    lines.append("-" * max(len(col), 60))
    for r in results:
        verdict = "pass" if r.passed else "FAIL"
        rules = sorted({_short_rule(f.rule_id) for f in r.findings})
        rules_txt = ", ".join(rules) if rules else "-"
        lines.append(
            f"{r.gate:<12} {verdict:<6} {len(r.findings):>8}  {rules_txt}"
        )
    lines.append("")

    counts = Counter(
        _short_rule(f.rule_id) for r in results for f in r.findings
    )
    if counts:
        lines.append("findings ranked by rule:")
        for rule, n in counts.most_common():
            lines.append(f"  {n:>3}x  {rule}")
        lines.append("")
        worst_rule, worst_n = counts.most_common(1)[0]
        example = next(
            f for r in results for f in r.findings
            if _short_rule(f.rule_id) == worst_rule
        )
        loc = example.path or "(no path)"
        if example.line is not None:
            loc += f":{example.line}"
        # the headline names the rule + first location, not the raw match
        # text: this summary is meant to be readable in any doc, including
        # the repo's own voice_lint-gated README, so it never echoes a
        # matched banlist word back out.
        lines.append(
            f"top rule: {worst_rule} fired {worst_n}x (first at {loc})"
        )
    else:
        lines.append("no findings -- the scanned tree is clean.")
    return "\n".join(lines) + "\n"


def _short_rule(rule_id: str) -> str:
    # collapse voice_lint::banlist::leverage -> voice_lint::banlist so the
    # ranking groups the whole banlist class together rather than one row
    # per word.
    parts = rule_id.split("::")
    return "::".join(parts[:2]) if len(parts) > 2 else rule_id


def _emit_findings_to_stdout(results: list[GateResult]) -> None:
    # always written so the harness step log shows the findings even when
    # --report is set. callers invoking gates.py directly with --report=""
    # will see both this per-finding stream and the markdown report on
    # stdout; the action harness always sets --report so the dual write
    # does not trigger in CI.
    for r in results:
        if not r.findings:
            continue
        sys.stdout.write(f"\n[{r.gate}] {len(r.findings)} finding(s)\n")
        for f in r.findings:
            loc = f.path or "(no path)"
            if f.line is not None:
                loc += f":{f.line}"
            sys.stdout.write(f"  [{f.severity}] {f.rule_id} {loc}: {f.message}\n")


def _demo_fixture_dir() -> Path:
    # examples/demo-repo, resolved relative to this file so the demo works
    # from any cwd and offline.
    return (Path(__file__).resolve().parents[2] / "examples" / "demo-repo")


def run_demo(argv: Optional[list[str]] = None) -> int:
    """No-arg demo: run every v0 gate against the committed demo fixture
    and print a readable, ranked summary. Read-only and offline.

    Exit code mirrors a real run (1 because the fixture is planted with
    failures on purpose), but the demo is about the readable output, not
    the code. Pass --path to point it at any other tree.
    """
    parser = argparse.ArgumentParser(
        prog="proof-gates demo",
        description="run all v0 gates against the committed demo fixture and print a readable summary",
    )
    parser.add_argument(
        "--path",
        default=None,
        help="tree to scan; default is the committed examples/demo-repo fixture",
    )
    args = parser.parse_args(argv)

    target = Path(args.path) if args.path else _demo_fixture_dir()
    if not target.exists():
        sys.stderr.write(f"proof-gates demo: path does not exist: {target}\n")
        return 3

    results = [_run_one(name, target) for name in REGISTRY]
    sys.stdout.write(render_summary(results, target))
    return 0 if all(r.passed for r in results) else 1


def main(argv: Optional[list[str]] = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if raw and raw[0] == "demo":
        return run_demo(raw[1:])

    parser = argparse.ArgumentParser(
        prog="proof-gates",
        description="run one or more proof gates against a path (or `demo` for a no-arg readable run)",
    )
    parser.add_argument(
        "--gates",
        required=True,
        help="comma-separated gate names (e.g. voice_lint,spec_check)",
    )
    parser.add_argument(
        "--path",
        default=".",
        help="path to scan; default is the current directory",
    )
    parser.add_argument(
        "--report",
        default="",
        help="markdown report output file; if empty, the report goes to stdout",
    )
    args = parser.parse_args(argv)

    requested = [g.strip() for g in args.gates.split(",") if g.strip()]
    if not requested:
        sys.stderr.write("proof-gates: --gates is empty\n")
        return 2

    unknown = [g for g in requested if g not in REGISTRY]
    if unknown:
        sys.stderr.write(f"proof-gates: unknown gate(s): {', '.join(unknown)}\n")
        sys.stderr.write(f"proof-gates: known gates: {', '.join(sorted(REGISTRY))}\n")
        return 2

    target = Path(args.path)
    if not target.exists():
        sys.stderr.write(f"proof-gates: --path does not exist: {target}\n")
        return 3

    # R-PGR-V1-012: every requested gate runs even if an earlier one fails.
    results = [_run_one(name, target) for name in requested]

    _emit_findings_to_stdout(results)
    md = render_report(results)

    if args.report:
        report_path = Path(args.report)
        try:
            if report_path.parent and not report_path.parent.exists():
                report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(md, encoding="utf-8")
        except OSError as exc:
            sys.stderr.write(f"proof-gates: failed to write {report_path}: {exc}\n")
    else:
        sys.stdout.write(md)

    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
