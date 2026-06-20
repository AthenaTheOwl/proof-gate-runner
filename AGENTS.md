# AGENTS.md — proof-gate-runner

Operating contract for AI agents (Claude, Codex, Cursor) working in this
repo. Conventions match the rest of the AthenaTheOwl portfolio so an
agent already trained on athena-site or supplier-risk-rag-agent
recognizes the shape.

## What this repo is

A drop-in GitHub Action plus a stdlib-only python entry point that runs
typed proof gates on a codebase. v0 ships two gates: `voice_lint` and
`spec_check`. Three more (`encoding_sweep`, `bom_sweep`, `traceability`)
are scoped to spec 0003. The scope cut is recorded in
`decisions/DEC-001-gate-rule-corpus-v0.md`.

## Roles you may see in tasks

| Role | What they do |
|---|---|
| `gate-author` | Implements a single gate under `scripts/lib/`, with rules rendered into `catalogue/` |
| `catalogue-curator` | Maintains `catalogue/*.md` and the `bug_classes_2026.md` index |
| `action-author` | Maintains `action.yml` and the composite-action shape |
| `dogfood-runner` | Wires the Action into the portfolio repos as launch corpus |
| `release-author` | Publishes tagged versions; maintains backward compatibility |

These roles exist in the spec ledger; v0 does not implement them.

## Voice constraints

- No marketing words. The banlist is literally enforced by one of the
  gates this repo ships, so the README must pass its own gate.
- No antithetical reversals as a structural device.
- Plain assertions. Rules are deterministic; catalogue entries are
  references, not pitches.

## Gates (v0, landed in spec 0002)

The repo runs its own gates on its own PRs in CI via
`.github/workflows/self-ci.yml`. If a `voice_lint` change is shipped
that regresses the gate against this repo, CI fails.

- `voice_lint` on every README, AGENTS.md, and catalogue page
  (catalogue/, specs/, and decisions/ are skipped by default; the host
  can override by pointing `--path` at one of them directly)
- `spec_check` on every `R-PGR-*` ID declared under
  `specs/*/requirements.md`

Deferred to spec 0003: `ruff`, `pytest`, `encoding_sweep`, `bom_sweep`,
`traceability`, the bug-classes corpus, and the
`actions/github-script@v7` PR-comment upsert step.

## Out of scope

- LLM-judged review. The gates are deterministic by design.
- Security scanning. There are good security tools; the niche here is
  voice, spec, and encoding hygiene under AI-PR velocity.
- Hosted runner. The Action runs on GitHub-hosted runners; the CLI
  runs locally; there is no SaaS.
- Cross-org telemetry. Each repo runs its own gates against its own
  rules. The catalogue is the shared artifact, not a scoreboard.
