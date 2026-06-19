# Spec 0001 — Foundation (ProofGateRunner)

## R-PGR-001 — repo scaffold
Repo lives at `e:/claude_code/random-apps/proof-gate-runner`. MIT
license, copyright Vignesh Gopalakrishnan. README, AGENTS.md,
.gitignore, and `specs/0001-foundation/` exist before any runnable
code lands.

## R-PGR-002 — GitHub Action shape
`action.yml` defines a composite GitHub Action with one input,
`gates`, accepting a comma-separated list of gate names. The Action
checks out the repo, installs the CLI, and runs the requested gates.
Default value runs all five.

## R-PGR-003 — CLI shape
`proof-gates run` is the single entry point. Subflags: `--gate NAME`,
`--all`, `--path PATH`, `--config PATH`. Exit code 0 on pass, non-zero
on fail. JSON output mode for CI consumption.

## R-PGR-004 — voice_lint gate
`src/gates/voice_lint.py` checks every text file in the repo against a
banlist plus structural anti-patterns (antithetical reversals, "not X
but Y" shape). Rules live in `catalogue/voice_lint.md` and are imported
from a single canonical source.

## R-PGR-005 — spec_check gate
`src/gates/spec_check.py` parses every `specs/*/requirements.md` for
`R-*-NNN` IDs and asserts each ID appears in either source code or a
test file. Missing IDs fail the gate. Rules in `catalogue/spec_check.md`.

## R-PGR-006 — encoding_sweep gate
`src/gates/encoding_sweep.py` walks the repo and flags files with
mixed encodings, Latin-1 mojibake markers (e.g. `â€™`, `Ã©`), and
smart-quote drift in source files. Rules in
`catalogue/encoding_sweep.md`.

## R-PGR-007 — bom_sweep gate
`src/gates/bom_sweep.py` flags UTF-8 BOMs and other zero-width
invisibles in text files. Rules in `catalogue/bom_sweep.md`.

## R-PGR-008 — traceability gate
`src/gates/traceability.py` parses every `decisions/DEC-*.md` for spec
references (`R-*-NNN`) and asserts each referenced ID exists in
`specs/*/requirements.md`. Rules in `catalogue/traceability.md`.

## R-PGR-009 — bug-classes corpus
`catalogue/bug_classes_2026.md` is the launch corpus. Every entry
links to a real PR in the author's portfolio that demonstrates the
gate catching that bug class. A script
`scripts/catalogue_has_pr_ref.py` enforces this.

## R-PGR-010 — self-CI
The Action runs on this repo's own PRs through `.github/workflows/`.
A PR that breaks the Action against this repo fails its own CI.

## R-PGR-011 — drop-in instructions
`examples/wired_repos/` contains at least three worked examples
showing how to add the Action to a Python repo, a JS repo, and a
narrative-card repo.

## R-PGR-012 — config schema
`config/proof-gates.yaml` is an optional per-repo configuration with a
schema in `schemas/config.schema.json`. Without the config, sane
defaults apply.

## R-PGR-013 — release discipline
Tagged releases use semver. Breaking changes require a major bump and
a migration note in `CHANGELOG.md`.
