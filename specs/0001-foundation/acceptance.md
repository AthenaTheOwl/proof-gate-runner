# Spec 0001 — Acceptance (ProofGateRunner)

v0 (this scaffold PR) is done when:

- `README.md`, `LICENSE`, `AGENTS.md`, `.gitignore` exist
- `specs/0001-foundation/{requirements,design,tasks,acceptance}.md` exist
- `docs/first-pr.md` describes the second PR
- README status checkboxes show the scaffold rows checked
- No code beyond what spec 0001 names lives in this repo

Spec 0002 (the next PR) is done when:

```bash
uv sync
uv run pytest                                            # all green
uv run proof-gates run --all --path .                    # repo passes its own gates
uv run proof-gates run --gate voice_lint --path .
uv run proof-gates run --gate spec_check --path .
uv run proof-gates run --gate encoding_sweep --path .
uv run proof-gates run --gate bom_sweep --path .
uv run proof-gates run --gate traceability --path .
uv run python scripts/catalogue_has_pr_ref.py
actionlint action.yml
```

And:

- The Action runs successfully on this repo's own PRs through
  `.github/workflows/self-ci.yml`
- Every catalogue entry in `catalogue/bug_classes_2026.md` links to a
  real PR in the portfolio (enforced by `catalogue_has_pr_ref.py`)
- Each gate has a `tests/fixtures/<gate>/{good,bad}/` pair and a
  matching integration test
- All tests run offline

Gates that gate this repo's own PRs: `voice_lint`, `spec_check`,
`encoding_sweep`, `bom_sweep`, `traceability`,
`catalogue_has_pr_ref`. A PR that fails any gate is not merged.
