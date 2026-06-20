# Spec 0002 — Design (ProofGateRunner v0.1)

## Pipeline shape

```
GitHub Action (composite)
  step 1: setup-python 3.11
  step 2: pip install -e .            (installs proof-gates CLI)
  step 3: proof-gates run             (one CLI call, every gate)
            │
            ├─► voice_lint  ─► GateResult
            ├─► spec_check  ─► GateResult
            ├─► ruff        ─► GateResult
            └─► pytest      ─► GateResult
                                │
                                ▼
            cli/main.py aggregates → Markdown table
                                │
            step 4: write table to $GITHUB_STEP_SUMMARY
            step 5: if PR event, upsert PR comment via github-script
            step 6: exit 0 / 1 / 2 per R-PGR-V1-002
```

Composite-action only. No Docker, no JavaScript runtime. Every step is
a `run:` shell step or an `uses:` reference to an action already
maintained by `actions/`.

## Block decomposition

| Block | Path | Owns | Depends on |
|---|---|---|---|
| `action.yml` | repo root | Composite action wire-up, input parsing, PR-comment step | CLI module via `pip install -e .` |
| `cli` | `cli/main.py` | Argument parsing, gate dispatch, report aggregation, exit code | `src/gates/*`, `click` |
| `gates.base` | `src/gates/base.py` | `Gate` protocol, `GateResult`, `Finding` dataclasses | stdlib only |
| `gates.voice_lint` | `src/gates/voice_lint.py` | Banlist scan + reversal-pattern scan | `gates.base`, `catalogue/voice_lint.md` (rule list) |
| `gates.spec_check` | `src/gates/spec_check.py` | Parse R-IDs, grep for usage | `gates.base` |
| `gates.ruff` | `src/gates/ruff.py` | Subprocess wrapper around `ruff check --output-format json` | `gates.base`, `ruff` on PATH |
| `gates.pytest` | `src/gates/pytest_gate.py` | Subprocess wrapper around `pytest -q` plus summary parser | `gates.base`, `pytest` on PATH |
| `report` | `cli/report.py` | Aggregate `GateResult` list into Markdown table; write to file or stdout | `gates.base` |
| `tests` | `tests/` | Per-gate fixtures + integration tests + CLI smoke test | every block above |
| `workflow` | `.github/workflows/self-ci.yml` | Invoke `./` (local action) on PR events | `action.yml` |

Dependency direction is one-way: `workflow → action.yml → cli → gates.*
→ gates.base`. No back-edges. The catalogue Markdown files are read-only
references; the rule data lives in Python constants beside each gate
and the catalogue file is the published rendering of the same data.

## Interfaces

### CLI surface

```
proof-gates run \
  --gates voice_lint,spec_check,ruff,pytest \
  --path . \
  [--report report.md]
```

Exit codes:

| Code | Meaning |
|---|---|
| 0 | every requested gate passed |
| 1 | at least one gate had a `fail` finding |
| 2 | unknown gate name (no gates ran) |
| 3 | internal error (uncaught exception in CLI; gate exceptions surface as findings) |

### Gate protocol

```python
class Gate(Protocol):
    name: str  # matches the CLI key
    def run(self, path: Path) -> GateResult: ...

@dataclass(frozen=True)
class GateResult:
    gate: str
    passed: bool        # True iff no severity=="fail" findings
    findings: list[Finding]
    duration_ms: int

@dataclass(frozen=True)
class Finding:
    severity: Literal["fail", "warn"]
    path: str           # repo-relative
    line: int | None
    rule_id: str        # e.g. "voice_lint::banlist::leverage"
    message: str
```

### Markdown report shape

```markdown
<!-- proof-gate-runner:summary -->
## proof-gate-runner

| gate        | result | findings | duration |
|-------------|--------|----------|----------|
| voice_lint  | pass   | 0        | 142 ms   |
| spec_check  | pass   | 0        | 87 ms    |
| ruff        | fail   | 3        | 412 ms   |
| pytest      | pass   | 0        | 1840 ms  |

Failing rules in this run: `ruff::E501`, `ruff::F401`.
See the step summary for finding-level detail.
```

The hidden marker (`<!-- proof-gate-runner:summary -->`) is the key
the `actions/github-script@v7` step matches when deciding whether to
create a new comment or edit the existing one.

### PR-comment upsert (`action.yml` step 5)

The step runs only when `github.event_name == 'pull_request'` and a
token is available. It calls `octokit.issues.listComments`, finds the
first comment whose body starts with the marker, and either patches it
or posts a new one. The Markdown body is read from the report file
written in step 3.

## Failure modes per block

### `action.yml`
- **Missing `gates` input** → action fails at parse with a clear error.
  No partial run.
- **PR comment step fails** (token missing, rate limit, network) →
  step is `continue-on-error: true`. The step summary still gets the
  table. Action exit code is preserved.
- **CLI install fails** → action fails fast at step 2; no gates run.

### `cli`
- **Unknown gate name** → exit 2, print `unknown gate: <name>` to
  stderr, do not run any gate.
- **Gate raises uncaught exception** → caught at dispatch boundary,
  converted to a `GateResult` with `passed=False` and one `Finding`
  whose `rule_id` is `<gate>::internal_error`. Continue to next gate.
- **`--path` does not exist** → exit 3 with a stderr message before
  dispatch.

### `gates.voice_lint`
- **Binary file with a Markdown extension** → skip silently
  (`UnicodeDecodeError` → no finding).
- **Banlist matches inside a code fence** → still flagged in v0.1;
  fence-aware skipping is deferred (out of scope).

### `gates.spec_check`
- **No `specs/*/requirements.md` files** → pass with zero findings
  (no IDs to check).
- **Malformed R-ID line** → skip, do not crash.

### `gates.ruff`
- **`ruff` not on PATH** → one `fail` finding,
  `rule_id="ruff::not_installed"`.
- **`ruff check` exits non-zero with no JSON** (config error) → one
  `fail` finding, `rule_id="ruff::config_error"`, message is the first
  64 chars of stderr.

### `gates.pytest`
- **`pytest` not on PATH** → one `fail` finding,
  `rule_id="pytest::not_installed"`.
- **No tests collected** → one `warn` finding,
  `rule_id="pytest::no_tests_found"`. Gate still passes.
- **Collection error** → one `fail` finding per error,
  `rule_id="pytest::collection_error"`.

### `report`
- **Write target unwritable** → log to stderr and continue; report
  also goes to `$GITHUB_STEP_SUMMARY` so the data is not lost.

## External dependencies

| Dep | Where | Why | License | Failure plan |
|---|---|---|---|---|
| `click` | runtime | CLI parsing | BSD-3 | pin major; standard, low risk |
| `pydantic` | runtime | report serialization | MIT | pin major |
| `pytest` | dev + gate target | pytest gate runs the host repo's pytest | MIT | gate handles not-installed |
| `ruff` | dev + gate target | ruff gate runs the host repo's ruff | MIT | gate handles not-installed |
| `actions/checkout@v4` | action | check out caller's repo | MIT | pinned; widely used |
| `actions/setup-python@v5` | action | install Python 3.11 | MIT | pinned |
| `actions/github-script@v7` | action | PR-comment upsert | MIT | pinned; only runs when token present |

No new package fetched at action runtime beyond what `pip install -e .`
pulls. No network call from the CLI itself.

## Reuse from sibling repos

The `Gate` / `GateResult` / `Finding` shape lifts directly from spec
0001's design. No sibling-repo code is imported; the patterns
(composite-action + Python CLI + per-gate fixture pairs) are the same
shape used in the rest of the AthenaTheOwl portfolio.

## Out of scope for v0.1

The following are listed in spec 0001 and explicitly held back to spec
0003 or later:

- `encoding_sweep` gate (deferred to spec 0003)
- `bom_sweep` gate (deferred to spec 0003)
- `traceability` gate (deferred to spec 0003)
- `catalogue/bug_classes_2026.md` and the `catalogue_has_pr_ref.py`
  enforcement script (deferred to spec 0003)
- `examples/wired_repos/*` worked examples (deferred to spec 0003)
- `config/proof-gates.yaml` + JSON schema (deferred; v0.1 has no
  config file, gates take defaults)
- `v0` tagged release (deferred; v0.1 is consumed via `uses: ./` in
  this repo's own CI)
- Per-rule severity overrides
- Fence-aware Markdown skipping in `voice_lint`
- LLM-judged review of any kind
- Docker action variant
