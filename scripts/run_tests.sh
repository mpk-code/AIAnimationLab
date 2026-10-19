#!/usr/bin/env bash
# run_tests.sh [LANE]
# The studio's one gate. With no argument it runs every lane in order and stops at the first
# failure; the order is part of ADR-0002's contract:
#   environment  scripts/doctor.sh
#   locks        uv lock --check, before any `uv run`, which would rewrite a stale lock
#   static       ruff check, ruff format --check, mypy
#   unit         pytest -m "not blender"
#   blender      pytest -m blender
# With LANE it runs that one lane, or `ruff` / `mypy`, the two halves of static (the justfile's
# per-edit recipes). `just ci` runs it bare.
set -uo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${root}" || exit 1
# Same search order as the Makefile's TOOL_PATH: this worktree's uv, then its just.
export PATH="${root}/.toolchain/uv/bin:${root}/.toolchain/just/bin:${PATH}"
# Use this checkout's .venv, not an activated one from elsewhere.
unset VIRTUAL_ENV

lanes=(environment locks static unit blender)
if (($# > 1)); then
  echo "usage: scripts/run_tests.sh [${lanes[*]} ruff mypy]" >&2
  exit 2
fi
if (($# == 1)); then
  [[ " ${lanes[*]} ruff mypy " == *" $1 "* ]] || {
    echo "unknown lane '$1'; lanes: ${lanes[*]} ruff mypy" >&2
    exit 2
  }
  lanes=("$1")
fi

lane_environment() { bash scripts/doctor.sh; }
lane_locks() { uv lock --check; }
lane_ruff() { uv run --locked ruff check . && uv run --locked ruff format --check .; }
lane_mypy() { uv run --locked mypy; }
lane_static() { lane_ruff && lane_mypy; }
lane_unit() { uv run --locked pytest -m "not blender"; }
lane_blender() {
  # Mirrors tests/conftest.py's default; pytest itself skips each blender test with the reason.
  local bin="${BLENDER_BIN:-/Applications/Blender.app/Contents/MacOS/Blender}"
  if [[ ! -x "${bin}" ]]; then
    echo "!!! SKIPPED: blender lane — BLENDER_BIN is not executable: ${bin}"
    echo "!!! Blender-dependent tests did NOT run; this gate says nothing about them."
  fi
  uv run --locked pytest -m blender
}

for lane in "${lanes[@]}"; do
  echo "=== lane: ${lane}"
  if "lane_${lane}"; then
    echo "=== lane: ${lane} — ok"
  else
    echo "=== lane: ${lane} — FAILED; later lanes not run"
    exit 1
  fi
done
echo "=== run_tests.sh: all lanes ok (${lanes[*]})"
