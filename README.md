# proof-gate-runner -- typed gates and a public rule corpus

A drop-in GitHub Action that runs typed proof gates on every pull
request. v0 ships two gates: `voice_lint` and `spec_check`. Three more
(`encoding_sweep`, `bom_sweep`, `traceability`) are scoped to spec 0003.
See `decisions/DEC-001-gate-rule-corpus-v0.md` for the scope cut.

## what this is

AI-PR volume scaled past human-review capacity at every serious shop in
2026. The 2026-W22 codex voice review caught BOM artifacts and Latin-1
mojibake -- exactly the bug class a typed proof gate catches in half a
second and a human reviewer misses on the fifth PR of the day.

The Action is one composite action plus a stdlib-only python entry
point. No `pip install`, no third-party runtime dependency, no Docker.

## gates in v0

| gate | what it catches | rule rendering |
|---|---|---|
| `voice_lint` | banlist words and antithetical-reversal sentence shapes in `.md`/`.txt`/`.rst` | `catalogue/voice_lint.md` |
| `spec_check` | `R-*` requirement IDs declared in `specs/*/requirements.md` that are not referenced anywhere under `src/`, `cli/`, `scripts/`, `tests/`, `decisions/`, `action.yml`, `.github/`, `README.md`, or `AGENTS.md` | (rules embedded in `scripts/lib/spec_check.py`) |

## status

- [x] repo scaffold + LICENSE + AGENTS.md
- [x] spec 0001 (foundation) -- requirements, design, tasks, acceptance
- [x] spec 0002 (design) -- requirements, design, tasks, acceptance
- [x] `action.yml` + `scripts/run_gates.sh` + `scripts/lib/{gates,voice_lint,spec_check}.py`
- [x] self-CI: the Action runs on this repo's own PRs (`.github/workflows/self-ci.yml`)
- [ ] `encoding_sweep`, `bom_sweep`, `traceability` gates (spec 0003)
- [ ] catalogue with at least 10 real bug-class entries from portfolio (spec 0003)
- [ ] worked drop-in examples for external repos (spec 0003)
- [ ] PR-comment upsert via `actions/github-script@v7` (spec 0003; v0 writes to `$GITHUB_STEP_SUMMARY` only)

## how to run

In a consumer repo:

```yaml
# .github/workflows/proof-gates.yml
name: proof-gates
on: [pull_request]
jobs:
  gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: AthenaTheOwl/proof-gate-runner@v0
        with:
          gates: voice_lint,spec_check
```

Locally (no install step required, python 3 is the only runtime
dependency):

```bash
bash scripts/run_gates.sh --gates voice_lint --path .
bash scripts/run_gates.sh --gates voice_lint,spec_check --path . --report report.md
```

Or invoke the python entry point directly:

```bash
python3 scripts/lib/gates.py --gates voice_lint --path .
```

Exit codes: `0` all gates passed, `1` at least one fail finding, `2`
unknown gate name, `3` internal error (e.g. `--path` does not exist).

## try it

One command, no arguments, no install. It runs both v0 gates against
the committed `examples/demo-repo` fixture (planted on purpose with the
bug classes the gates catch) and prints a ranked summary:

```bash
bash scripts/run_gates.sh demo
# or: python3 scripts/lib/gates.py demo
```

```
proof-gate-runner -- scanned .../examples/demo-repo
2 gate(s), 10 finding(s), 2 gate(s) failing

gate         result findings  rules that fired
------------------------------------------------------------
voice_lint   FAIL          8  voice_lint::banlist, voice_lint::reversal
spec_check   FAIL          2  spec_check::unreferenced

findings ranked by rule:
    6x  voice_lint::banlist
    2x  voice_lint::reversal
    2x  spec_check::unreferenced

top rule: voice_lint::banlist fired 6x (first at notes.txt:3)
```

The point: you see in one screen which bug classes a tree trips and how
often, so a reviewer drowning in AI-generated PRs knows where to look
first. Add `--path <dir>` to point the same run at any other tree.

## test harness

```bash
bash tests/test_run_gates.sh
```

The harness creates synthetic good/bad fixtures under a temp directory
for each gate, runs `scripts/run_gates.sh` against them, and checks the
exit code and the report contents. It runs offline, in seconds, on
Linux CI and on Git Bash.

## layout

```
proof-gate-runner/
  README.md
  LICENSE
  AGENTS.md
  action.yml
  scripts/
    run_gates.sh
    lib/
      gates.py        # dispatcher + Finding/GateResult + markdown report
      voice_lint.py
      spec_check.py
  catalogue/
    voice_lint.md
  examples/
    demo-repo/         # planted fixture scanned by `run_gates.sh demo`
  decisions/
    DEC-001-gate-rule-corpus-v0.md
  specs/
    0001-foundation/
    0002-design/
  .github/
    workflows/
      self-ci.yml
  tests/
    test_run_gates.sh
  docs/
    first-pr.md
```

## who this is for

- open-source maintainers handling drive-by AI-generated PRs
- individual builders running typed-artifact discipline across a
  portfolio of repos
- engineering platform teams once the catalogue is large enough to cite

## what this is not

- not a hosted SaaS. there is no proof-gates.io. the repo is one
  GitHub Action plus a small python entry point plus a catalogue.
- not a code-review service. it runs deterministic checks, not LLM
  judgment.
- not a security scanner. there are good ones; the niche here is
  voice, spec, and encoding hygiene under AI-PR velocity.

## license

MIT. See `LICENSE`.
