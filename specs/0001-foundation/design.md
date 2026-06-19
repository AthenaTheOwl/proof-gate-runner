# Spec 0001 — Design (ProofGateRunner)

## Pipeline shape

```
checkout ─► install CLI ─► proof-gates run --all --path .
                                   │
                                   ├─► voice_lint
                                   ├─► spec_check
                                   ├─► encoding_sweep
                                   ├─► bom_sweep
                                   └─► traceability
                                          │
                                          └─► exit code + JSON report
```

The Action is a composite action; no Docker, no JS runtime. Install
the Python CLI, run it, collect the report. Each gate is independent
and addressable.

## Module map

```
action.yml                            # composite action definition
cli/
  main.py                             # click group with `run`
src/
  gates/
    base.py                           # Gate protocol + result shape
    voice_lint.py
    spec_check.py
    encoding_sweep.py
    bom_sweep.py
    traceability.py
catalogue/
  bug_classes_2026.md                 # the launch corpus
  voice_lint.md                       # rules + examples per gate
  spec_check.md
  encoding_sweep.md
  bom_sweep.md
  traceability.md
config/
  proof-gates.yaml                    # optional per-repo overrides
schemas/
  config.schema.json
examples/
  wired_repos/
    python-min/
    js-min/
    narrative-cards-min/
```

## Gate result shape

```python
@dataclass(frozen=True)
class GateResult:
    gate: str
    passed: bool
    findings: list[Finding]
    duration_ms: int

@dataclass(frozen=True)
class Finding:
    severity: Literal["fail", "warn"]
    path: str
    line: int | None
    rule_id: str
    message: str
```

`proof-gates run` aggregates `GateResult` objects, prints a Markdown
summary, optionally writes a JSON report, and exits non-zero if any
`severity == "fail"` finding exists.

## Catalogue discipline

Every catalogue entry has the same shape:

```markdown
## BUG-2026-W22-bom-in-readme

- Gate: bom_sweep
- Severity: fail
- PR: https://github.com/AthenaTheOwl/<repo>/pull/<n>
- Rule: bom_sweep::no_utf8_bom_in_text
- What happened: A UTF-8 BOM crept into README.md after an AI-generated edit
- What the gate did: Flagged the BOM on the first line of the file
- Repro:
  printf '\xef\xbb\xbfHello\n' > scratch.md
  uv run proof-gates run --gate bom_sweep --path scratch.md
```

A script enforces every entry links to a real PR.

## Action versioning

- `v0` (alpha, the first tagged release after spec 0002)
- Composite-action ref points at a tag, not a branch
- The repo runs the Action against itself in CI; if a PR breaks that
  CI, it does not merge

## Test discipline

- One unit test per `R-PGR-*` requirement
- One integration test per gate against `tests/fixtures/<gate>/{good,bad}/`
- One end-to-end test that invokes `proof-gates run --all` against
  `examples/wired_repos/python-min/` and asserts a clean pass
- All tests run offline
