# Spec 0002 — Tasks (ProofGateRunner v0.1)

Ordered for the next two PRs. PR-A lands the runnable CLI plus the
composite action; PR-B wires the self-CI workflow and the PR-comment
step. Each task carries one or more `R-PGR-V1-*` IDs.

## PR-A — CLI, four gates, action.yml

- [ ] R-PGR-V1-011 `pyproject.toml` with Python 3.11, `click`,
      `pydantic`, dev deps `pytest`, `ruff`; entry point
      `proof-gates = "cli.main:cli"`.
- [ ] R-PGR-V1-008 `src/gates/base.py` — `Gate` protocol, `GateResult`,
      `Finding` dataclasses.
- [ ] R-PGR-V1-002 R-PGR-V1-008 R-PGR-V1-012 `cli/main.py` — `click`
      group with `run`, gate registry dict, dispatch loop, exit-code
      mapping per spec.
- [ ] R-PGR-V1-002 `cli/report.py` — aggregate `GateResult` list into
      the Markdown table from design.md.
- [ ] R-PGR-V1-003 `src/gates/voice_lint.py` + banlist constant +
      reversal-pattern regexes.
- [ ] R-PGR-V1-004 `src/gates/spec_check.py` — parse
      `specs/*/requirements.md` for `R-*-[A-Z0-9]+` IDs, grep
      `src/`/`cli/`/`tests/` for each.
- [ ] R-PGR-V1-005 `src/gates/ruff.py` — subprocess wrapper around
      `ruff check --output-format json`; not-installed handling.
- [ ] R-PGR-V1-006 `src/gates/pytest_gate.py` — subprocess wrapper
      around `pytest -q`; not-installed and no-tests handling.
- [ ] R-PGR-V1-010 Fixture pairs under `tests/fixtures/<gate>/{good,bad}/`
      for the four gates.
- [ ] R-PGR-V1-010 `tests/test_gate_voice_lint.py`,
      `test_gate_spec_check.py`, `test_gate_ruff.py`,
      `test_gate_pytest.py` — one integration test per gate.
- [ ] R-PGR-V1-002 R-PGR-V1-012 `tests/test_cli.py` — exit code 0/1/2,
      unknown-gate path, isolation (failing gate does not skip later
      gates).
- [ ] R-PGR-V1-001 `action.yml` — composite action with `gates` and
      `path` inputs, `setup-python@v5`, `pip install -e .`,
      `proof-gates run`, write to `$GITHUB_STEP_SUMMARY`.

## PR-B — self-CI workflow and PR-comment upsert

- [ ] R-PGR-V1-007 PR-comment upsert step in `action.yml` using
      `actions/github-script@v7`, keyed on the
      `<!-- proof-gate-runner:summary -->` marker.
- [ ] R-PGR-V1-009 `.github/workflows/self-ci.yml` — invokes `./` on
      every PR to `main` with the four-gate list.
- [ ] R-PGR-V1-007 `tests/test_report.py` — Markdown table golden
      output for the upsert flow.
