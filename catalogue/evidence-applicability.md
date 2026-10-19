# A green gate belongs to one set of inputs

`voice_lint` establishes that the scanned text triggered none of its configured
rules. `spec_check` establishes reference coverage for declared requirement IDs.
Neither establishes that a feature works, a requirement is well chosen, or a
linked source supports a product claim. Keep those statements explicit when a
specialist reviewer prepares a release recommendation.

A reusable proof receipt should carry the command and arguments, exit status,
source revision or content digest, rule version, environment, and raw output
location. This runner emits reports for its current gates; the full receipt
envelope is an integration responsibility. Do not label a receipt as applying to
a later revision solely because its command string is unchanged.

Use three states in a change review. A passing historical receipt remains a pass
for its recorded inputs. A changed file or rule may make its current applicability
unknown. A rerun supplies a new observation, including a new failure. Keeping these
separate prevents an agent from quietly converting yesterday's success into
today's verification.

The smallest review exercise uses a clean fixture, a changed fixture containing a
known violation, and the same gate command. Preserve both reports. Ask the reviewer
to identify which report covers the proposed change before showing the author's
claim. A sound review rejects the stale receipt even when the earlier run passed.

A browser or implementation check can supply different evidence when needed.
This catalogue entry changes no gate rule, installs no workflow, and makes no
claim that a manual receipt protocol is enforced by the runner.
