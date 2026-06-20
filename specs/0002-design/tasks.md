# Spec 0002 — Tasks (ProofGateRunner v0.1)

v0 ships the narrower surface recorded in
`decisions/DEC-001-gate-rule-corpus-v0.md`: two gates, a stdlib-only
python entry point, a composite action, and the self-CI workflow. The
deferred rows (ruff, pytest, pyproject, github-script upsert) move to
spec 0003.

## PR-A — v0 entry point and two gates (landed)

- [x] R-PGR-V1-001 `action.yml` — composite action with `gates` and
      `path` inputs, `setup-python@v5`, single `run` step that invokes
      `scripts/run_gates.sh` and writes the report to
      `$GITHUB_STEP_SUMMARY`.
- [x] R-PGR-V1-002 `scripts/run_gates.sh` + `scripts/lib/gates.py` —
      shell wrapper plus python dispatcher with `--gates`, `--path`,
      `--report`, exit-code mapping per spec.
- [x] R-PGR-V1-003 `scripts/lib/voice_lint.py` — banlist constant +
      reversal-pattern regexes. Rule rendering in
      `catalogue/voice_lint.md`.
- [x] R-PGR-V1-004 `scripts/lib/spec_check.py` — parse
      `specs/*/requirements.md` for `R-*-[A-Z0-9]+` IDs (word-bounded),
      cross-reference under `src/`, `cli/`, `scripts/`, `tests/`,
      `decisions/`, `action.yml`, `.github/`, `README.md`, `AGENTS.md`.
- [x] R-PGR-V1-008 `scripts/lib/gates.py` — `Finding` + `GateResult`
      dataclasses and `REGISTRY` dispatch dict.
- [x] R-PGR-V1-010 `tests/test_run_gates.sh` — synthetic good/bad
      fixtures per gate, offline, runs in seconds on Git Bash and CI.
- [x] R-PGR-V1-012 dispatcher runs every requested gate even if an
      earlier gate fails; isolation case in the shell harness.

## PR-B — self-CI workflow and PR-comment (step-summary half)

R-PGR-V1-007 is split: the step-summary write lands here in PR-B; the
`actions/github-script@v7` upsert against the marker comment is
deferred to spec 0003 (listed below).

- [x] R-PGR-V1-007 (step-summary half) — `scripts/run_gates.sh`
      appends the markdown report to `$GITHUB_STEP_SUMMARY` when it
      runs in Actions. The marker `<!-- proof-gate-runner:summary -->`
      is written into the report by `gates.render_report`.
- [x] R-PGR-V1-009 `.github/workflows/self-ci.yml` — unit job runs the
      shell harness; dogfood job invokes `./` against this repo.

## Deferred to spec 0003 (per DEC-001)

- [ ] R-PGR-V1-005 `ruff` gate. Requires `ruff` on PATH and the
      pip-install step the v0 action avoids.
- [ ] R-PGR-V1-006 `pytest` gate. Same shape; collection-error parser
      lives with the spec 0003 work.
- [ ] R-PGR-V1-007 (upsert half) — `actions/github-script@v7` step
      that patches the marker comment on PR events. v0 only writes to
      the step summary.
- [ ] R-PGR-V1-011 `pyproject.toml` with `click` + `pydantic`. The v0
      entry point uses argparse and dataclasses from the stdlib; the
      package shape lands when the ruff/pytest gates need it.
