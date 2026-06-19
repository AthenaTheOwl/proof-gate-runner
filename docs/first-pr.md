# First PR after the scaffold

This file describes the literal next PR after the v0 scaffold lands.
Spec 0002 is the work plan; this file is the file-level changeset.

## Goal

A working `proof-gates` CLI plus a composite GitHub Action that runs
five gates on a repo and exits non-zero on any failing rule. The Action
runs on this repo's own PRs as proof-of-discipline. Three seed entries
in the bug-classes corpus reference real PRs from the portfolio.

## Files changed

New:

- `pyproject.toml` — Python 3.11, `uv`, `click`, `pydantic`,
  `jsonschema`, `pyyaml`
- `cli/main.py` — `click` group with `run`
- `src/__init__.py`
- `src/gates/__init__.py`
- `src/gates/base.py` — `Gate` protocol + `GateResult` + `Finding`
- `src/gates/voice_lint.py`
- `src/gates/spec_check.py`
- `src/gates/encoding_sweep.py`
- `src/gates/bom_sweep.py`
- `src/gates/traceability.py`
- `action.yml` — composite action
- `catalogue/bug_classes_2026.md`
- `catalogue/voice_lint.md`
- `catalogue/spec_check.md`
- `catalogue/encoding_sweep.md`
- `catalogue/bom_sweep.md`
- `catalogue/traceability.md`
- `schemas/config.schema.json`
- `config/proof-gates.yaml` — defaults file
- `tests/fixtures/voice_lint/{good,bad}/`
- `tests/fixtures/spec_check/{good,bad}/`
- `tests/fixtures/encoding_sweep/{good,bad}/`
- `tests/fixtures/bom_sweep/{good,bad}/`
- `tests/fixtures/traceability/{good,bad}/`
- `tests/test_cli.py`
- `tests/test_gate_voice_lint.py`
- `tests/test_gate_spec_check.py`
- `tests/test_gate_encoding_sweep.py`
- `tests/test_gate_bom_sweep.py`
- `tests/test_gate_traceability.py`
- `tests/test_end_to_end.py`
- `scripts/catalogue_has_pr_ref.py`
- `.github/workflows/self-ci.yml` — runs the Action on this repo

Modified:

- `README.md` — replace placeholder "How to run" with the real command
- `specs/0001-foundation/tasks.md` — check off spec-0002 rows
- `AGENTS.md` — point Gates section at real scripts

## Verification

```bash
uv sync
uv run pytest -v
uv run proof-gates run --all --path .
actionlint action.yml
uv run python scripts/catalogue_has_pr_ref.py
```

Plus: push the PR, observe `self-ci.yml` runs the Action against the
HEAD of the branch, and the Action passes (or fails for a real reason
the contributor needs to fix).

## Out of scope for this PR

- The full 10+ entry corpus (spec 0003)
- Worked external-repo examples (spec 0003)
- A `v0` tagged release (spec 0003)
- Per-rule configuration overrides beyond defaults
