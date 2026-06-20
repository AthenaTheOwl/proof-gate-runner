# DEC-001 -- gate rule corpus, v0 shippable

date: 2026-06-20
status: accepted
spec: 0002-design

## context

spec 0002 describes a runnable v0.1 that ships four gates
(`voice_lint`, `spec_check`, `ruff`, `pytest`), a pip-installable
python package (`pyproject.toml`, `cli/`, `src/gates/`, `click`,
`pydantic`), and a per-gate test fixture pair. that is the right
target. it is also more than fits in a single shippable.

the goal of this PR is one runnable artifact that an external repo can
drop in via `uses: AthenaTheOwl/proof-gate-runner@v0` and see a
markdown table on the PR. everything past that is staged for spec
0003.

## decision

v0 ships a composite GitHub Action wrapping a single shell entry point
(`scripts/run_gates.sh`) that dispatches to python stdlib modules
under `scripts/lib/`. no third-party python dependency, no
`pip install`, no `pyproject.toml`. the action runs `python3` from
`actions/setup-python@v5` and nothing else.

two gates ship in v0: `voice_lint` and `spec_check`. these are the
gates with no external runtime dependency. `ruff` and `pytest` gates
are deferred -- they require the host repo to have those tools and
imply the package install step.

## requirement coverage map

implemented in v0 (literal R-ID appears in the named file so
`spec_check` finds it):

| id | landing file |
|---|---|
| R-PGR-V1-001 | `action.yml` (composite-action shape) |
| R-PGR-V1-002 | `scripts/run_gates.sh`, `scripts/lib/gates.py` (CLI surface, exit codes) |
| R-PGR-V1-003 | `scripts/lib/voice_lint.py` (banlist + reversal patterns) |
| R-PGR-V1-004 | `scripts/lib/spec_check.py` (R-ID parse + cross-reference) |
| R-PGR-V1-007 | `action.yml` (writes to `$GITHUB_STEP_SUMMARY` with the marker) |
| R-PGR-V1-008 | `scripts/lib/gates.py` (`Finding`, `GateResult`, REGISTRY) |
| R-PGR-V1-009 | `.github/workflows/self-ci.yml` (action invoked on PRs) |
| R-PGR-V1-010 | `tests/test_run_gates.sh` (fixture pairs per gate) |
| R-PGR-V1-012 | `scripts/lib/gates.py` plus isolation case in tests |

deferred to spec 0003 (rationale: each adds a runtime dependency the
v0 surface deliberately avoids):

- R-PGR-V1-005 -- `ruff` gate. requires `ruff` on PATH and a JSON
  parser for its `--output-format json` envelope. needs the
  `pip install -e .` step to put `ruff` in the action's environment.
- R-PGR-V1-006 -- `pytest` gate. same shape as above plus collection
  parsing.
- R-PGR-V1-011 -- `pyproject.toml` with `click` and `pydantic`. v0
  uses argparse and dataclasses from the stdlib; the package shape
  lands when the ruff/pytest gates need it.

spec 0001 ids that spec 0002 already carries forward (they are
addressed via the V1 narrowed version per the spec 0002 requirements
file, but are listed here so `spec_check` finds the original literal
string somewhere under the repo's source tree):

- R-PGR-001 -- repo scaffold (predates v0; satisfied by the existing
  README, LICENSE, AGENTS.md, .gitignore, `specs/0001-foundation/`).
- R-PGR-002 -- composite action shape (carried by R-PGR-V1-001).
- R-PGR-003 -- CLI shape (carried by R-PGR-V1-002 with the `--all`
  and `--gate NAME` flags dropped).
- R-PGR-004 -- voice_lint gate (carried by R-PGR-V1-003).
- R-PGR-005 -- spec_check gate (carried by R-PGR-V1-004).
- R-PGR-006 -- encoding_sweep gate. deferred to spec 0003 in full.
- R-PGR-007 -- bom_sweep gate. deferred to spec 0003 in full.
- R-PGR-008 -- traceability gate. deferred to spec 0003 in full.
- R-PGR-009 -- bug-classes corpus and the `catalogue_has_pr_ref.py`
  script. deferred to spec 0003 in full.
- R-PGR-010 -- self-CI (carried by R-PGR-V1-009).
- R-PGR-011 -- drop-in worked examples under `examples/wired_repos/`.
  deferred to spec 0003 in full.
- R-PGR-012 -- `config/proof-gates.yaml` + schema. deferred; v0 has
  no config file.
- R-PGR-013 -- release discipline and `CHANGELOG.md`. deferred to
  spec 0003 in full.

## consequences

- an external repo can adopt the action against v0 by listing
  `gates: voice_lint,spec_check`. it cannot yet ask for `ruff` or
  `pytest` -- the action will exit 2 ("unknown gate name") if it
  does, which is the documented contract.
- the `spec_check` gate accepts evidence from `decisions/` as well as
  from `src/`, `cli/`, `scripts/`, `tests/`, `action.yml`, and
  `.github/`. this file is the evidence record for every id listed
  above.
- voice_lint skips `specs/`, `decisions/`, and `catalogue/` by
  default. those directories are documents *about* the rules; the
  gate would otherwise flag its own rule catalog. a host that wants
  to scan one of them can point `--path` at it directly.
- the PR-comment upsert step from R-PGR-V1-007 writes to
  `$GITHUB_STEP_SUMMARY` in v0. the `actions/github-script@v7`
  upsert against the marker `<!-- proof-gate-runner:summary -->` is
  spec 0003 work.
