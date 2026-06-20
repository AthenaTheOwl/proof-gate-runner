# Spec 0002 — Acceptance (ProofGateRunner v0.1)

> v0 narrowing: `decisions/DEC-001-gate-rule-corpus-v0.md` cuts this
> spec down to the two stdlib gates (`voice_lint`, `spec_check`), a
> composite action that calls `scripts/run_gates.sh` directly, and the
> `self-ci` workflow. The `uv sync` / `proof-gates run` / `pytest`
> commands below are the spec-0003 target, not the v0 surface. For the
> v0 local verification path, see the README "how to run" section and
> `tests/test_run_gates.sh`.

v0.1 is done when a fresh clone of this repo can run every command in
the "local verification" block, and the self-CI workflow runs the
composite Action on a real PR and posts the summary table as a PR
comment.

## Local verification (fresh clone)

```bash
git clone <repo> proof-gate-runner && cd proof-gate-runner
uv sync

# CLI smoke
uv run proof-gates --help
uv run proof-gates run --help

# every gate runs and the repo passes its own gates
uv run proof-gates run --gates voice_lint,spec_check,ruff,pytest --path .

# each gate addressable on its own
uv run proof-gates run --gates voice_lint --path .
uv run proof-gates run --gates spec_check --path .
uv run proof-gates run --gates ruff       --path .
uv run proof-gates run --gates pytest     --path .

# unknown gate name → exit 2 before any gate runs
uv run proof-gates run --gates not_a_gate --path . ; echo $?   # 2

# isolation: a deliberate failing gate does not skip later gates
# (the report table has one row per requested gate, every time)
uv run proof-gates run \
  --gates voice_lint,ruff \
  --path tests/fixtures/voice_lint/bad \
  --report /tmp/report.md ; echo $?   # 1
grep -c '| voice_lint ' /tmp/report.md   # 1
grep -c '| ruff '       /tmp/report.md   # 1

# tests
uv run pytest -q

# action lint (optional, requires actionlint on PATH)
actionlint action.yml
```

## CI verification (must hold on every PR to `main`)

- `.github/workflows/self-ci.yml` triggers on `pull_request` to `main`.
- The job uses `uses: ./` (local action reference) so the workflow
  tests the in-progress code.
- The job step writes a four-row table to the step summary
  (`voice_lint`, `spec_check`, `ruff`, `pytest`).
- On a PR, the Action posts (or updates) one comment beginning with
  `<!-- proof-gate-runner:summary -->`. Re-running the workflow edits
  the same comment in place; it does not stack.
- A PR that introduces a banlist word in `README.md` fails the
  `voice_lint` gate, and the failure is visible both in the step
  summary and the PR comment.

## Out of scope for v0.1 acceptance

The following are spec 0001 acceptance items deliberately not gated in
v0.1 — they ship in spec 0003 or later:

- `encoding_sweep`, `bom_sweep`, `traceability` gates
- `catalogue/bug_classes_2026.md` and `scripts/catalogue_has_pr_ref.py`
- `examples/wired_repos/*` worked examples
- `config/proof-gates.yaml` + JSON schema
- A `v0` git tag and `CHANGELOG.md`
