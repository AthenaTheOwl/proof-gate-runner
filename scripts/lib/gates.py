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


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="proof-gates",
        description="run one or more proof gates against a path",
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
