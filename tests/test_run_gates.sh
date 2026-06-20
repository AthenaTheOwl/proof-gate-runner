#!/usr/bin/env bash
# tests/test_run_gates.sh -- offline harness for run_gates.sh and the
# two v0 gates. Exercises real code paths against synthetic fixtures
# (R-PGR-V1-010, R-PGR-V1-012). Runs on Linux CI and on Git Bash.

set -u

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
script="$repo_root/scripts/run_gates.sh"

if [ ! -f "$script" ]; then
  echo "test_run_gates.sh: cannot find $script" >&2
  exit 1
fi

work="$(mktemp -d 2>/dev/null || mktemp -d -t pgr-test)"
trap 'rm -rf "$work"' EXIT

pass=0
fail=0

emit() { printf '%s\n' "$*"; }

check() {
  local name="$1"
  local expected="$2"
  local actual="$3"
  if [ "$expected" = "$actual" ]; then
    emit "  ok   - $name (got $actual)"
    pass=$((pass + 1))
  else
    emit "  FAIL - $name (expected $expected, got $actual)"
    fail=$((fail + 1))
  fi
}

check_grep() {
  local name="$1"
  local needle="$2"
  local file="$3"
  if [ -f "$file" ] && grep -q -- "$needle" "$file"; then
    emit "  ok   - $name (found '$needle' in $(basename "$file"))"
    pass=$((pass + 1))
  else
    emit "  FAIL - $name (missing '$needle' in $file)"
    fail=$((fail + 1))
  fi
}

check_not_grep() {
  local name="$1"
  local needle="$2"
  local file="$3"
  if [ -f "$file" ] && grep -q -- "$needle" "$file"; then
    emit "  FAIL - $name ('$needle' should not appear in $file)"
    fail=$((fail + 1))
  else
    emit "  ok   - $name (no '$needle' in $(basename "$file"))"
    pass=$((pass + 1))
  fi
}

run_gates() {
  # usage: run_gates GATES PATH REPORT_FILE -> echoes exit code
  local gates="$1"
  local target="$2"
  local report="$3"
  bash "$script" --gates "$gates" --path "$target" --report "$report" >/dev/null 2>&1
  echo $?
}

# ---------------------------------------------------------------------------
# 1. voice_lint -- good fixture passes
# ---------------------------------------------------------------------------
emit "case: voice_lint clean fixture"
vl_good="$work/voice_lint_good"
mkdir -p "$vl_good"
cat > "$vl_good/README.md" <<'MD'
# clean fixture

plain prose with no banned words and no reversal patterns. just a
short paragraph that should pass the gate cleanly.
MD
report="$work/r1.md"
rc=$(run_gates voice_lint "$vl_good" "$report")
check "exit code 0 on clean tree" 0 "$rc"
check_grep "report has voice_lint pass row" '| voice_lint | pass |' "$report"

# ---------------------------------------------------------------------------
# 2. voice_lint -- bad fixture fails with banlist rule id
# ---------------------------------------------------------------------------
emit "case: voice_lint banlist fixture"
vl_bad="$work/voice_lint_bad"
mkdir -p "$vl_bad"
cat > "$vl_bad/notes.md" <<'MD'
# notes

this fixture uses a marketing word on purpose: leverage the whole
thing for testing.
MD
report="$work/r2.md"
rc=$(run_gates voice_lint "$vl_bad" "$report")
check "exit code 1 on banlist hit" 1 "$rc"
check_grep "report has voice_lint fail row" '| voice_lint | fail |' "$report"
check_grep "report names the failing banlist rule" 'voice_lint::banlist::leverage' "$report"

# ---------------------------------------------------------------------------
# 3. voice_lint -- reversal pattern fails
# ---------------------------------------------------------------------------
emit "case: voice_lint reversal fixture"
vl_rev="$work/voice_lint_reversal"
mkdir -p "$vl_rev"
cat > "$vl_rev/doc.md" <<'MD'
# doc

this is not a list but a paragraph for testing the reversal pattern.
MD
report="$work/r3.md"
rc=$(run_gates voice_lint "$vl_rev" "$report")
check "exit code 1 on reversal pattern" 1 "$rc"
check_grep "report names reversal rule" 'voice_lint::reversal' "$report"

# ---------------------------------------------------------------------------
# 4. spec_check -- good fixture (ID referenced) passes
# ---------------------------------------------------------------------------
emit "case: spec_check referenced id"
sc_good="$work/spec_check_good"
mkdir -p "$sc_good/specs/0001-x" "$sc_good/src"
cat > "$sc_good/specs/0001-x/requirements.md" <<'MD'
# requirements

## R-FOO-001 -- entry point exists
the cli has an entry point.
MD
cat > "$sc_good/src/main.py" <<'PY'
# R-FOO-001 -- referenced here so spec_check passes
def main():
    return 0
PY
report="$work/r4.md"
rc=$(run_gates spec_check "$sc_good" "$report")
check "exit code 0 when every id is referenced" 0 "$rc"
check_grep "report has spec_check pass row" '| spec_check | pass |' "$report"

# ---------------------------------------------------------------------------
# 5. spec_check -- bad fixture (ID never referenced) fails
# ---------------------------------------------------------------------------
emit "case: spec_check unreferenced id"
sc_bad="$work/spec_check_bad"
mkdir -p "$sc_bad/specs/0001-x" "$sc_bad/src"
cat > "$sc_bad/specs/0001-x/requirements.md" <<'MD'
# requirements

## R-BAR-002 -- never referenced anywhere
this id has no implementation.
MD
cat > "$sc_bad/src/main.py" <<'PY'
def main():
    return 0
PY
report="$work/r5.md"
rc=$(run_gates spec_check "$sc_bad" "$report")
check "exit code 1 when id is unreferenced" 1 "$rc"
check_grep "report names the unreferenced rule" 'spec_check::unreferenced' "$report"

# ---------------------------------------------------------------------------
# 6. unknown gate name -> exit 2, no run
# ---------------------------------------------------------------------------
emit "case: unknown gate name"
report="$work/r6.md"
rc=$(run_gates not_a_gate "$vl_good" "$report")
check "exit code 2 on unknown gate" 2 "$rc"
# the dispatcher must not have written a report when no gate ran
if [ ! -f "$report" ]; then
  emit "  ok   - no report file written for unknown gate"
  pass=$((pass + 1))
else
  emit "  FAIL - report file should not exist for unknown gate"
  fail=$((fail + 1))
fi

# ---------------------------------------------------------------------------
# 7. isolation: a failing gate does not stop the second gate (R-PGR-V1-012)
# ---------------------------------------------------------------------------
emit "case: gate isolation"
iso="$work/iso"
mkdir -p "$iso/specs/0001-x" "$iso/src"
cat > "$iso/specs/0001-x/requirements.md" <<'MD'
# requirements

## R-ISO-007 -- referenced below
MD
cat > "$iso/src/main.py" <<'PY'
# R-ISO-007 keeps spec_check happy in the isolation case
PY
# add a banlist hit so voice_lint fails
cat > "$iso/README.md" <<'MD'
# iso

synergy across the board.
MD
report="$work/r7.md"
rc=$(run_gates voice_lint,spec_check "$iso" "$report")
check "exit code 1 (voice_lint failed)" 1 "$rc"
check_grep "voice_lint row present and failing" '| voice_lint | fail |' "$report"
check_grep "spec_check row present and passing" '| spec_check | pass |' "$report"

# ---------------------------------------------------------------------------
# 8. missing path -> exit 3
# ---------------------------------------------------------------------------
emit "case: missing --path"
report="$work/r8.md"
rc=$(run_gates voice_lint "$work/does_not_exist" "$report")
check "exit code 3 when path missing" 3 "$rc"

# ---------------------------------------------------------------------------
# 9. report has the marker comment
# ---------------------------------------------------------------------------
emit "case: report marker"
report="$work/r9.md"
rc=$(run_gates voice_lint "$vl_good" "$report")
check "clean run still exit 0" 0 "$rc"
check_grep "report contains marker" '<!-- proof-gate-runner:summary -->' "$report"
check_not_grep "report does not contain banlist literal in a heading" 'failing rules:' "$report"

# ---------------------------------------------------------------------------
# 10. mixed known + unknown gate -> exit 2 before any gate runs
# ---------------------------------------------------------------------------
emit "case: mixed known + unknown gate"
report="$work/r10.md"
rc=$(run_gates voice_lint,not_a_gate "$vl_good" "$report")
check "exit code 2 when one of several gates is unknown" 2 "$rc"
if [ ! -f "$report" ]; then
  emit "  ok   - no report file written for mixed unknown gate"
  pass=$((pass + 1))
else
  emit "  FAIL - report file should not exist for mixed unknown gate"
  fail=$((fail + 1))
fi

# ---------------------------------------------------------------------------
# 11. spec_check uses word-boundary matching (R-FOO-001 does not satisfy R-FOO-0011)
# ---------------------------------------------------------------------------
emit "case: spec_check word-boundary"
wb="$work/word_boundary"
mkdir -p "$wb/specs/0001-x" "$wb/src"
cat > "$wb/specs/0001-x/requirements.md" <<'MD'
# requirements

## R-FOO-0011 -- long suffix; must not be satisfied by R-FOO-001
MD
cat > "$wb/src/main.py" <<'PY'
# This file references R-FOO-001, NOT R-FOO-0011.
# A substring match would spuriously pass; word-bounded must fail.
PY
report="$work/r11.md"
rc=$(run_gates spec_check "$wb" "$report")
check "exit code 1 when only a substring of the id is present" 1 "$rc"
check_grep "report names the unreferenced rule" 'spec_check::unreferenced' "$report"

emit ""
emit "summary: $pass passed, $fail failed"

if [ "$fail" -gt 0 ]; then
  exit 1
fi
exit 0
