# proof-gate-runner

A typed gate reads `notes.txt:3`, finds a banlist word, and fails the pull request in half a second. The reviewer on their fifth AI-authored PR of the day would have read past it. The gate doesn't get tired.

## What it does

AI-PR volume scaled past human-review capacity in 2026. The W22 voice review on this portfolio caught BOM artifacts and Latin-1 mojibake by hand — exactly the bug class a deterministic check catches the same way every time, and a person stops catching somewhere around the fifth PR.

proof-gate-runner is a drop-in GitHub Action that runs typed proof gates on every pull request. v0 ships two: `voice_lint` (banlist words and antithetical-reversal sentence shapes in `.md`/`.txt`/`.rst`) and `spec_check` (`R-*` requirement IDs declared in `specs/*/requirements.md` but referenced nowhere in the tree). The Action is one composite action plus a stdlib-only python entry point. No `pip install`, no third-party runtime, no Docker. Three more gates — `encoding_sweep`, `bom_sweep`, `traceability` — are scoped to spec 0003; the cut is recorded in `decisions/DEC-001-gate-rule-corpus-v0.md`.

The rules render to a catalogue rather than a scoreboard. Each repo runs its own gates against its own rules. The shared artifact is the rule, not the verdict.

## Try it

One command, no arguments, no install. It runs both v0 gates against the committed `examples/demo-repo` fixture — planted on purpose with the bug classes the gates catch — and prints a ranked summary:

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

You see in one screen which bug classes a tree trips and how often, so a reviewer drowning in AI-generated PRs knows where to look first. Add `--path <dir>` to point the same run at any other tree.

## Live demo

`streamlit_app.py` (repo root) wraps the same `demo` verb as an interactive page: it runs the v0 gates against the committed `examples/demo-repo` fixture, renders the ranked result, a per-finding table filterable by gate, and a paste-box to voice_lint your own text. It reads the committed gate code and fixture directly — no network, no secrets.

<!-- live url: https://<app>.streamlit.app -->

run locally:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

deploy on Streamlit Community Cloud: New app -> repo `AthenaTheOwl/proof-gate-runner`, branch `main`, main file `streamlit_app.py`.

## How to run

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

Locally (no install step required, python 3 is the only runtime dependency):

```bash
bash scripts/run_gates.sh --gates voice_lint --path .
bash scripts/run_gates.sh --gates voice_lint,spec_check --path . --report report.md
```

Or invoke the python entry point directly:

```bash
python3 scripts/lib/gates.py --gates voice_lint --path .
```

Exit codes: `0` all gates passed, `1` at least one fail finding, `2` unknown gate name, `3` internal error (e.g. `--path` does not exist).

The repo runs its own gates on its own PRs in CI via `.github/workflows/self-ci.yml`. Ship a `voice_lint` change that regresses the gate against this repo and CI fails. The tool that lints prose is held to its own banlist.

## Test harness

```bash
bash tests/test_run_gates.sh
```

The harness creates synthetic good/bad fixtures under a temp directory for each gate, runs `scripts/run_gates.sh` against them, and checks the exit code and the report contents. It runs offline, in seconds, on Linux CI and on Git Bash.

## How it connects

The gate logic started as one-off scripts copied between repos. This is where it lives as a single Action:

- [athena-site](https://github.com/AthenaTheOwl/athena-site) — runs `voice_lint` as an advisory PR gate; the portfolio's meta/control-plane repo.
- [supplier-risk-rag-agent](https://github.com/AthenaTheOwl/supplier-risk-rag-agent) — shares the `R-*` requirement-ID convention that `spec_check` enforces.

`voice_lint.py` and `spec_check.py` were the shared discipline before they were one repo. Each consumer kept its own copy and its own banlist; the catalogue is what they hold in common.

## Layout

```
proof-gate-runner/
  README.md  LICENSE  AGENTS.md  action.yml
  scripts/
    run_gates.sh
    lib/
      gates.py        # dispatcher + Finding/GateResult + markdown report
      voice_lint.py
      spec_check.py
  catalogue/voice_lint.md
  examples/demo-repo/         # planted fixture scanned by `run_gates.sh demo`
  decisions/DEC-001-gate-rule-corpus-v0.md
  specs/0001-foundation/  specs/0002-design/
  .github/workflows/self-ci.yml
  tests/test_run_gates.sh
  docs/first-pr.md
```

## Scope

It runs deterministic checks, not LLM judgment, and it is not a security scanner — there are good ones. The niche is voice, spec, and encoding hygiene under AI-PR velocity. There is no hosted runner and no proof-gates.io: one GitHub Action, a small python entry point, and a catalogue.

## License

MIT. See `LICENSE`.
