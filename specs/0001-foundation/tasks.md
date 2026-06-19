# Spec 0001 — Tasks (ProofGateRunner)

First PR (the scaffold — this commit):

- [x] R-PGR-001 scaffold: README + LICENSE + AGENTS.md + .gitignore
- [x] R-PGR-001 specs/0001-foundation/{requirements,design,tasks,acceptance}.md
- [x] R-PGR-001 docs/first-pr.md

Second PR (foundation runnable code):

- [ ] R-PGR-003 `cli/main.py` with `run` subcommand
- [ ] R-PGR-003 `src/gates/base.py` with `Gate` protocol + result shape
- [ ] R-PGR-004 `src/gates/voice_lint.py` + `catalogue/voice_lint.md`
- [ ] R-PGR-005 `src/gates/spec_check.py` + `catalogue/spec_check.md`
- [ ] R-PGR-006 `src/gates/encoding_sweep.py` + `catalogue/encoding_sweep.md`
- [ ] R-PGR-007 `src/gates/bom_sweep.py` + `catalogue/bom_sweep.md`
- [ ] R-PGR-008 `src/gates/traceability.py` + `catalogue/traceability.md`
- [ ] R-PGR-002 `action.yml` composite action
- [ ] R-PGR-012 `schemas/config.schema.json` + default config loader
- [ ] R-PGR-010 `.github/workflows/self-ci.yml` running the action on
      this repo
- [ ] R-PGR-009 `catalogue/bug_classes_2026.md` with 3 seed entries
- [ ] Tests: one per requirement; one integration test per gate
- [ ] `scripts/catalogue_has_pr_ref.py` enforcement script

Third PR (corpus expansion + drop-in examples):

- [ ] R-PGR-011 `examples/wired_repos/python-min/` worked example
- [ ] R-PGR-011 `examples/wired_repos/js-min/` worked example
- [ ] R-PGR-011 `examples/wired_repos/narrative-cards-min/` worked example
- [ ] R-PGR-009 expand corpus to 10+ entries from portfolio PRs
- [ ] R-PGR-013 tag `v0`, ship CHANGELOG.md, document migration policy
