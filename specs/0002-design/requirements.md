# Spec 0002 — Requirements (ProofGateRunner v0.1)

v0.1 narrows spec 0001 to the smallest end-to-end shape that lets an
external repo drop the Action into its CI and see a per-gate pass/fail
summary on the PR. Five gates from spec 0001 collapse to four for v0.1:
two are carried over (`voice_lint`, `spec_check`), two are new and
delegate to existing tools (`ruff`, `pytest`), and three are deferred
to spec 0003 (`encoding_sweep`, `bom_sweep`, `traceability`).

Each requirement below carries a refinement note pointing back to spec
0001 where applicable.

## R-PGR-V1-001 — composite action with `gates` input
`action.yml` is a composite GitHub Action. It accepts one required
input `gates` (comma-separated list of gate names) and one optional
input `path` (default `.`). It checks out the repo (assumes the caller
has already done so), installs the CLI from this repo, runs the
requested gates, and writes a Markdown report to `$GITHUB_STEP_SUMMARY`.
Carries `R-PGR-002` from spec 0001; narrows from "default runs all
five" to "no default — caller must list gates explicitly."

## R-PGR-V1-002 — CLI `proof-gates run` entry point
`proof-gates run` accepts `--gates voice_lint,spec_check,ruff,pytest`,
`--path PATH`, and `--report PATH` (Markdown output file). Exit code 0
when every gate passes, 1 when any gate fails, 2 when an unknown gate
name appears. Carries `R-PGR-003`; drops `--gate NAME` singular and
`--all` (one flag, comma-separated, no special-case `--all`); drops
`--config` (deferred to spec 0003).

## R-PGR-V1-003 — `voice_lint` gate
`src/gates/voice_lint.py` scans `.md`, `.txt`, and `.rst` files for a
banlist (`leverage`, `synergy`, `robust`, `demonstrates`,
`comprehensive`, `best-in-class`, `unleash`) and antithetical-reversal
patterns (`not X but Y`, `it's not X; it's Y`). Rules and the banlist
live in `catalogue/voice_lint.md` and are imported from a single
canonical Python constant. Carries `R-PGR-004` from spec 0001 unchanged
in scope.

## R-PGR-V1-004 — `spec_check` gate
`src/gates/spec_check.py` parses every `specs/*/requirements.md` for
`R-*-[A-Z0-9]+` IDs and asserts each ID appears in at least one file
under `src/`, `cli/`, or `tests/`. Missing IDs fail the gate. Carries
`R-PGR-005`; refines the regex to allow the `V1` infix used here.

## R-PGR-V1-005 — `ruff` gate
`src/gates/ruff.py` shells out to `ruff check --output-format json
<path>` and converts the JSON output into the `Finding` shape from
`src/gates/base.py`. Any `E*` or `F*` rule produces a `fail` finding;
`W*` and `D*` produce `warn`. If `ruff` is not on `PATH`, the gate
returns one `fail` finding with `rule_id = "ruff::not_installed"`.

## R-PGR-V1-006 — `pytest` gate
`src/gates/pytest_gate.py` shells out to `pytest -q --tb=no
--no-header -o cache_dir=/tmp/.pytest_cache <path>/tests` and parses
the trailing summary line. Any failed or errored test produces a `fail`
finding per test. If no test files exist, the gate returns one `warn`
finding with `rule_id = "pytest::no_tests_found"`. If `pytest` is not
on `PATH`, one `fail` finding with `rule_id = "pytest::not_installed"`.

## R-PGR-V1-007 — PR comment summary
The composite Action emits a Markdown table to
`$GITHUB_STEP_SUMMARY` (one row per gate: name, pass/fail, finding
count, duration). When `GITHUB_EVENT_NAME == pull_request` and a
`GITHUB_TOKEN` is available, the Action posts the same table as a PR
comment using `actions/github-script@v7`. The comment is keyed by a
hidden marker (`<!-- proof-gate-runner:summary -->`) so re-runs update
the existing comment instead of stacking. The comment never reproduces
finding messages — the step summary holds those.

## R-PGR-V1-008 — gate registry and dispatch
`src/gates/base.py` defines `Gate` (protocol), `GateResult`, and
`Finding` per spec 0001's design. `cli/main.py` holds a single
dict `GATES = {"voice_lint": ..., "spec_check": ..., "ruff": ...,
"pytest": ...}` and dispatches in the order the caller listed. Unknown
names exit 2 before any gate runs. Carries the result-shape part of
`R-PGR-003`.

## R-PGR-V1-009 — self-CI on this repo's own PRs
`.github/workflows/self-ci.yml` runs the composite Action against this
repo on every pull request to `main`, with
`gates: voice_lint,spec_check,ruff,pytest`. The workflow uses
`uses: ./` (local action reference) so the workflow tests the
in-progress version, not a tag. Carries `R-PGR-010`; narrows the gate
list to the four v0.1 gates.

## R-PGR-V1-010 — per-gate fixture pair plus integration test
`tests/fixtures/<gate>/good/` and `tests/fixtures/<gate>/bad/` exist
for each of the four gates. `tests/test_gate_<gate>.py` calls the
gate against both fixtures and asserts a clean pass on `good/` and at
least one `fail` finding with a known `rule_id` on `bad/`. The four
integration tests run offline and finish in under five seconds total.

## R-PGR-V1-011 — `pyproject.toml` with pinned dev tools
`pyproject.toml` declares Python 3.11, runtime deps (`click`,
`pydantic`), and dev deps (`pytest`, `ruff`) with upper bounds on
major versions. `uv sync` produces a working environment.
`uv run proof-gates run --gates voice_lint --path .` succeeds on a
clean clone. No transitive runtime dep is unpinned.

## R-PGR-V1-012 — gate isolation (no early exit)
The CLI runs every requested gate even if an earlier gate fails.
Aggregate exit code is non-zero if any gate failed, but `pytest`
failing does not prevent `voice_lint` from running. The step summary
shows every gate's row regardless of which ones failed. This is the
behavior the PR comment depends on — the table must be complete.
