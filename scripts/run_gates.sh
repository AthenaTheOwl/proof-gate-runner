#!/usr/bin/env bash
# proof-gate-runner shell entry point (R-PGR-V1-001, R-PGR-V1-002).
#
# Invoked by action.yml and by the local self-test. Reads inputs from
# either CLI flags or the PGR_* environment variables, then dispatches
# to scripts/lib/gates.py.
#
# Inputs (env or flag):
#   PGR_GATES / --gates    comma-separated gate names (required)
#   PGR_PATH  / --path     path to scan (default: .)
#   PGR_REPORT / --report  markdown report path (default: temp file)
#
# Exit codes are passed through from gates.py:
#   0 pass, 1 gate failure, 2 unknown gate, 3 internal error.

set -u

usage() {
  cat >&2 <<'EOF'
usage: run_gates.sh [--gates LIST] [--path PATH] [--report FILE]
       (or set PGR_GATES / PGR_PATH / PGR_REPORT in the environment)
EOF
}

gates="${PGR_GATES:-}"
target_path="${PGR_PATH:-.}"
report_path="${PGR_REPORT:-}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
lib_dir="$script_dir/lib"

# pick a python that actually runs (not just one on PATH): the Windows
# Store shim resolves on `command -v` but exits nonzero, so probe each
# candidate with --version before committing to it.
python_bin=""
for cand in "${PYTHON:-}" python3 python; do
  [ -n "$cand" ] || continue
  if command -v "$cand" >/dev/null 2>&1 && "$cand" --version >/dev/null 2>&1; then
    python_bin="$cand"
    break
  fi
done
if [ -z "$python_bin" ]; then
  echo "run_gates.sh: no working python interpreter on PATH" >&2
  exit 3
fi

# `demo` is a no-arg readable run against the committed examples/demo-repo
# fixture. Everything after `demo` is passed straight through to the
# python entry point (e.g. --path to point it elsewhere).
if [ "${1:-}" = "demo" ]; then
  shift
  exec "$python_bin" "$lib_dir/gates.py" demo "$@"
fi

while [ $# -gt 0 ]; do
  case "$1" in
    --gates)
      gates="${2:-}"
      shift 2
      ;;
    --gates=*)
      gates="${1#--gates=}"
      shift
      ;;
    --path)
      target_path="${2:-}"
      shift 2
      ;;
    --path=*)
      target_path="${1#--path=}"
      shift
      ;;
    --report)
      report_path="${2:-}"
      shift 2
      ;;
    --report=*)
      report_path="${1#--report=}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "run_gates.sh: unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [ -z "$gates" ]; then
  echo "run_gates.sh: --gates is empty (set PGR_GATES or pass --gates)" >&2
  exit 2
fi

if [ -z "$report_path" ]; then
  tmp_root="${RUNNER_TEMP:-${TMPDIR:-/tmp}}"
  mkdir -p "$tmp_root"
  report_path="$tmp_root/proof-gate-runner-report.md"
fi

"$python_bin" "$lib_dir/gates.py" \
  --gates "$gates" \
  --path "$target_path" \
  --report "$report_path"
status=$?

if [ -n "${GITHUB_STEP_SUMMARY:-}" ] && [ -f "$report_path" ]; then
  cat "$report_path" >> "$GITHUB_STEP_SUMMARY"
fi

if [ -n "${GITHUB_OUTPUT:-}" ]; then
  {
    echo "report=$report_path"
    echo "status=$status"
  } >> "$GITHUB_OUTPUT"
fi

exit $status
