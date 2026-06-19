# AGENTS.md — proof-gate-runner

Operating contract for AI agents (Claude, Codex, Cursor) working in this
repo. Conventions match the rest of the AthenaTheOwl portfolio so an
agent already trained on athena-site or supplier-risk-rag-agent
recognizes the shape.

## What this repo is

A drop-in GitHub Action plus CLI that runs five typed proof gates on a
codebase: `voice_lint`, `spec_check`, `encoding_sweep`, `bom_sweep`,
`traceability`. Each gate has a one-page rule reference in
`catalogue/` and a real PR in the portfolio bug-classes corpus.

## Roles you may see in tasks

| Role | What they do |
|---|---|
| `gate-author` | Implements a single gate under `src/gates/`, with rules referenced from `catalogue/` |
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

## Gates (will land in spec 0002)

The repo runs its own gates on its own PRs in CI. If a `voice_lint`
fix is shipped that regresses the gate against this repo, CI fails.

- `voice_lint` on every catalogue page and README
- `spec_check` on every `R-PGR-*` ID
- `validate_action.py` runs `actionlint` against `action.yml`
- `catalogue_has_pr_ref.py` — every entry in `catalogue/bug_classes_2026.md`
  links to a real PR in the portfolio

## Out of scope

- LLM-judged review. The gates are deterministic by design.
- Security scanning. There are good security tools; the niche here is
  voice, spec, and encoding hygiene under AI-PR velocity.
- Hosted runner. The Action runs on GitHub-hosted runners; the CLI
  runs locally; there is no SaaS.
- Cross-org telemetry. Each repo runs its own gates against its own
  rules. The catalogue is the shared artifact, not a scoreboard.
