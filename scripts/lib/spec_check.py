"""spec_check gate (R-PGR-V1-004).

Parses every ``specs/*/requirements.md`` under --path for requirement
identifiers of the form ``R-<PROJECT>-<TAIL>`` (where TAIL accepts
optional version infixes such as ``V1`` and a numeric or alpha-numeric
suffix). For each ID, asserts that the same literal string appears in
at least one file under one of the SOURCE_DIRS below. An ID with no
occurrence outside its own requirements.md is reported as a fail
finding.

decisions/ is included in SOURCE_DIRS so that a deferred or carried-over
requirement may be discharged by an explicit decision record rather
than by code.
"""
from __future__ import annotations

import re
from pathlib import Path

from gates import Finding

ID_PATTERN = re.compile(r"\bR-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+){1,3}\b")

SOURCE_DIRS: tuple[str, ...] = (
    "src",
    "cli",
    "scripts",
    "tests",
    "decisions",
    ".github",
    "action.yml",
    "README.md",
    "AGENTS.md",
)

_SKIP_DIRS: frozenset[str] = frozenset({
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
})


def _iter_source_files(root: Path):
    seen: set[Path] = set()
    for entry in SOURCE_DIRS:
        target = root / entry
        if not target.exists():
            continue
        if target.is_file():
            if target not in seen:
                seen.add(target)
                yield target
            continue
        for path in target.rglob("*"):
            if not path.is_file():
                continue
            try:
                rel_parts = path.relative_to(root).parts
            except ValueError:
                rel_parts = path.parts
            if any(p in _SKIP_DIRS for p in rel_parts):
                continue
            if path in seen:
                continue
            seen.add(path)
            yield path


def _collect_requirement_ids(specs_root: Path) -> dict[str, tuple[str, int]]:
    """Return id -> (first spec file, lineno) so each ID is reported once."""
    ids: dict[str, tuple[str, int]] = {}
    if not specs_root.is_dir():
        return ids
    for req_file in sorted(specs_root.glob("*/requirements.md")):
        try:
            text = req_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in ID_PATTERN.findall(line):
                ids.setdefault(match, (str(req_file).replace("\\", "/"), lineno))
    return ids


def _read_source_blob(root: Path) -> str:
    chunks: list[str] = []
    for path in _iter_source_files(root):
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    return "\n".join(chunks)


def _relpath_from(root: Path, raw: str) -> str:
    try:
        return str(Path(raw).resolve().relative_to(root)).replace("\\", "/")
    except (ValueError, OSError):
        return raw


def _is_referenced(rid: str, blob: str) -> bool:
    # word-boundary match so R-PGR-001 does not spuriously satisfy R-PGR-0011
    return re.search(rf"(?<![A-Za-z0-9_-]){re.escape(rid)}(?![A-Za-z0-9_-])", blob) is not None


def run(path: Path) -> list[Finding]:
    root = path.resolve()
    specs_root = root / "specs"
    ids = _collect_requirement_ids(specs_root)
    if not ids:
        return []
    blob = _read_source_blob(root)
    findings: list[Finding] = []
    for rid in sorted(ids):
        if _is_referenced(rid, blob):
            continue
        spec_file, lineno = ids[rid]
        findings.append(Finding(
            severity="fail",
            path=_relpath_from(root, spec_file),
            line=lineno,
            rule_id="spec_check::unreferenced",
            message=(
                f"requirement {rid} declared in specs/ has no reference "
                f"under {'/'.join(SOURCE_DIRS)}"
            ),
        ))
    return findings
