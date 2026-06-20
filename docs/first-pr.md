# First PR after the scaffold

This file describes the actual first runnable PR after the v0 scaffold.
The full spec-0002 design listed four gates, a `pyproject.toml`, and a
PR-comment upsert step. v0 narrows that to two gates and a step-summary
write per `decisions/DEC-001-gate-rule-corpus-v0.md`. The deferred work
moves to spec 0003.

## goal

A working composite GitHub Action plus a single shell entry point that
runs the two v0 gates on a repo and exits non-zero on any fail finding.
The Action runs on this repo's own PRs as proof-of-discipline.

## files added by the first runnable PR

- `action.yml` -- composite action
- `scripts/run_gates.sh` -- shell entry point
- `scripts/lib/gates.py` -- dispatcher, `Finding`, `GateResult`,
  registry, markdown report
- `scripts/lib/voice_lint.py` -- banlist + reversal-pattern scan
- `scripts/lib/spec_check.py` -- R-ID parse + cross-reference
- `catalogue/voice_lint.md` -- public rendering of the voice_lint rules
- `decisions/DEC-001-gate-rule-corpus-v0.md` -- the scope-cut record
- `.github/workflows/self-ci.yml` -- runs the Action on this repo's PRs
- `tests/test_run_gates.sh` -- offline shell harness with synthetic
  fixtures for each gate

## files updated by the first runnable PR

- `README.md` -- replace placeholder "How to run" with the real command
- `AGENTS.md` -- align Gates section with the v0 gate set
- `specs/0002-design/tasks.md` -- check off rows landed in v0

## verification

```bash
bash tests/test_run_gates.sh
bash scripts/run_gates.sh --gates voice_lint,spec_check --path .
# optional, if actionlint is on PATH:
actionlint action.yml
```

Plus: push the PR, observe `self-ci.yml` runs the Action against the
HEAD of the branch, the unit job runs the shell harness, and the
dogfood job runs the composite action against this repo.

## out of scope for this PR (moves to spec 0003)

- `ruff` and `pytest` gates (R-PGR-V1-005, R-PGR-V1-006)
- `pyproject.toml`, `click`, `pydantic` (R-PGR-V1-011)
- PR-comment upsert via `actions/github-script@v7` (the upsert half of
  R-PGR-V1-007; the step-summary half ships in v0)
- `encoding_sweep`, `bom_sweep`, `traceability` gates
- the full 10+ entry corpus
- worked external-repo examples
- a `v0` tagged release
