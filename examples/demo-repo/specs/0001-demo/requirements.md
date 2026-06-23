# demo requirements

## R-DEMO-001 -- entry point exists
the cli has an entry point. this id is referenced in src/main.py.

## R-DEMO-002 -- config loader
load config from disk. this id is referenced in src/main.py.

## R-DEMO-003 -- retry policy
retry transient failures. this id is declared here but never referenced
anywhere under the source dirs, so spec_check flags it.

## R-DEMO-004 -- audit log
write an audit log. also declared here and never referenced, so
spec_check flags it too.
