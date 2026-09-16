#!/usr/bin/env bash
# generate-changelog — bash entry point (bounty claude-builders-bounty#1)
#
#   bash changelog.sh                 # CHANGELOG.md from the last tag to HEAD
#   bash changelog.sh --stdout        # print instead of writing
#   bash changelog.sh --from-tag v1.2.0 --version 1.3.0
#
# Portable: no bashisms beyond POSIX-ish constructs, no third-party tools.
# Requires: git + python3 (3.8+). Both are checked with actionable messages.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PY_SCRIPT="$SCRIPT_DIR/changelog.py"

say() { printf '%s\n' "$*" >&2; }

# ── dependency checks (each failure names the fix, not just the problem) ──────
if ! command -v git >/dev/null 2>&1; then
  say "changelog.sh: git is required but was not found on PATH."
  say "  install it (e.g. 'apt install git', 'brew install git') and re-run."
  exit 127
fi

PY_BIN=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
      PY_BIN="$candidate"
      break
    fi
  fi
done

if [ -z "$PY_BIN" ]; then
  say "changelog.sh: python3 (>= 3.8) is required but was not found on PATH."
  say "  install it (e.g. 'apt install python3') and re-run."
  exit 127
fi

if [ ! -f "$PY_SCRIPT" ]; then
  say "changelog.sh: companion script not found at $PY_SCRIPT"
  say "  keep changelog.sh next to changelog.py (as shipped in this folder)."
  exit 2
fi

# Run from the caller's repository, not from this script's directory:
# the user runs the tool *inside* the project whose changelog they want.
exec "$PY_BIN" "$PY_SCRIPT" "$@"
