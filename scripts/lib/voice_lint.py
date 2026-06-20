"""voice_lint gate (R-PGR-V1-003).

Walks a tree of .md / .txt / .rst files and reports two classes of
finding:

  * banlist words (marketing vocabulary the portfolio rejects)
  * antithetical-reversal sentence shapes ("not X but Y",
    "it's not X; it's Y")

The banlist and reversal patterns live here as the single canonical
source. v0 does not skip code fences -- see design.md "failure modes".

Rule directories that exist to *document* the rules themselves
(``specs/``, ``decisions/``, ``catalogue/``) are skipped by default so
the gate can be pointed at a repo root without flagging the rule
catalog. The host can override by pointing --path directly at one of
those directories.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from gates import Finding

BANLIST: tuple[str, ...] = (
    "leverage",
    "synergy",
    "robust",
    "demonstrates",
    "comprehensive",
    "best-in-class",
    "unleash",
)

SCAN_EXTENSIONS: frozenset[str] = frozenset({".md", ".txt", ".rst"})

SKIP_DIR_NAMES: frozenset[str] = frozenset({
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "specs",
    "decisions",
    "catalogue",
    ".pytest_cache",
})

_BANLIST_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (word, re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE))
    for word in BANLIST
)

_REVERSAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bnot\s+[\w'\"-]+(?:\s+[\w'\"-]+){0,6}\s+but\s+[\w'\"-]+", re.IGNORECASE),
    re.compile(r"\bit'?s\s+not\s+[\w'\"-]+(?:\s+[\w'\"-]+){0,6}\s*[;:]\s*it'?s\s+[\w'\"-]+", re.IGNORECASE),
)


def _iter_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        if root.suffix.lower() in SCAN_EXTENSIONS:
            yield root
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SCAN_EXTENSIONS:
            continue
        try:
            rel_parts = path.relative_to(root).parts
        except ValueError:
            rel_parts = path.parts
        if any(part in SKIP_DIR_NAMES for part in rel_parts[:-1]):
            continue
        yield path


def _relpath(fp: Path, root: Path) -> str:
    try:
        rel = fp.relative_to(root)
    except ValueError:
        rel = fp
    return str(rel).replace("\\", "/")


def run(path: Path) -> list[Finding]:
    root = path.resolve()
    findings: list[Finding] = []
    for fp in _iter_files(root):
        try:
            text = fp.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = _relpath(fp, root)
        for lineno, line in enumerate(text.splitlines(), start=1):
            for word, pattern in _BANLIST_PATTERNS:
                if pattern.search(line):
                    findings.append(Finding(
                        severity="fail",
                        path=rel,
                        line=lineno,
                        rule_id=f"voice_lint::banlist::{word}",
                        message=f"banlist word: {word}",
                    ))
            for pattern in _REVERSAL_PATTERNS:
                if pattern.search(line):
                    findings.append(Finding(
                        severity="fail",
                        path=rel,
                        line=lineno,
                        rule_id="voice_lint::reversal",
                        message="antithetical reversal sentence shape",
                    ))
                    break
    return findings
