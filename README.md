# ProofGateRunner — Public Gate-Rule Corpus and GitHub Action

A drop-in GitHub Action that runs a small set of typed proof gates on
every pull request: `voice_lint`, `spec_check`, `encoding_sweep`,
`bom_sweep`, and `traceability`. The Action ships alongside a public
catalogue of the bug classes the gates catch, with real PR references
from the author's own portfolio as launch corpus.

## What this is

AI-PR volume scaled past human-review capacity at every serious shop
in 2026. The 2026-W22 codex voice review caught BOM artifacts and
Latin-1 mojibake — exactly the bug class a typed proof gate catches in
half a second and a human reviewer misses on the fifth PR of the day.

ProofGateRunner is the gate chain extracted from the author's working
portfolio, packaged as a single GitHub Action so any repo can drop it
in. The five gates:

| Gate | What it catches |
|---|---|
| `voice_lint` | Marketing words, antithetical reversals, structural AI tells |
| `spec_check` | Requirements IDs in `specs/*/requirements.md` without an implementation or test |
| `encoding_sweep` | Latin-1 mojibake, mixed-encoding files, smart-quote drift |
| `bom_sweep` | UTF-8 BOM and other zero-width invisibles in text files |
| `traceability` | Decision records that reference a spec ID that doesn't exist |

Each gate has a one-page rule reference in `catalogue/` and a real PR
in the bug-classes corpus showing what it would have caught.

## Status

v0 scaffold. No implementation yet — only the spec ledger and the file
layout below. First runnable Action lands in spec 0002.

- [x] Repo scaffold + LICENSE + AGENTS.md
- [x] Spec 0001 (foundation) — requirements, design, tasks, acceptance
- [x] First-PR plan in `docs/first-pr.md`
- [ ] `action.yml` and five gate scripts
- [ ] Self-CI: the Action runs on this repo's own PRs
- [ ] Catalogue with at least 10 real bug-class entries from portfolio
- [ ] Drop-in instructions for external repos

## How to run

Placeholder. The runnable Action lands in spec 0002. Intended shape:

```yaml
# .github/workflows/proof-gates.yml in your repo
name: proof-gates
on: [pull_request]
jobs:
  gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: AthenaTheOwl/proof-gate-runner@v0
        with:
          gates: voice_lint,spec_check,encoding_sweep,bom_sweep,traceability
```

Locally:

```bash
uv sync
uv run proof-gates run --gate voice_lint --path .
uv run proof-gates run --all --path .
```

Until spec 0002 lands, the only thing that runs is
`python -c "print('scaffold')"`.

## Layout

```
proof-gate-runner/
  README.md
  LICENSE
  AGENTS.md
  .gitignore
  specs/
    0001-foundation/
      requirements.md
      design.md
      tasks.md
      acceptance.md
  docs/
    first-pr.md
```

Planned but not yet present:

```
  action.yml
  cli/
    main.py
  src/
    gates/
      voice_lint.py
      spec_check.py
      encoding_sweep.py
      bom_sweep.py
      traceability.py
  catalogue/
    bug_classes_2026.md
    voice_lint.md
    spec_check.md
    encoding_sweep.md
    bom_sweep.md
    traceability.md
  examples/
    wired_repos/
  tests/
    fixtures/
  pyproject.toml
```

## Who this is for

- Open-source maintainers drowning in drive-by AI-generated PRs
- Individual builders running the same kind of typed-artifact
  discipline the rest of this portfolio runs on
- Eventually, engineering platform teams once the catalogue is large
  enough to be cited as a reference

## What this is not

- Not a hosted SaaS. There is no proof-gates.io. The repo is one
  GitHub Action plus a CLI plus a catalogue.
- Not a code-review service. It runs deterministic checks, not LLM
  judgment.
- Not a security scanner. There are good ones; the niche here is
  voice, spec, and encoding hygiene under AI-PR velocity.

## License

MIT. See `LICENSE`.
