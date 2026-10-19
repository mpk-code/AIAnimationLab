#!/usr/bin/env bash
# doctor.sh [REPO_ROOT]
# Read-only report of every prerequisite and pin: one ok / warn / FAIL line each, with the fix.
# Exit 1 when any line is FAIL, else 0. Changes nothing. Pins are read from the Makefile and
# .python-version, never restated here (STD-001).
set -uo pipefail

root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
blender_app="/Applications/Blender.app"
failed=0
ok() { echo "  ok    $*"; }
warn() { echo "  warn  $*"; }
fail() { echo "  FAIL  $*"; failed=1; }
make_pin() { sed -n "s/^$1[[:space:]]*:=[[:space:]]*\([^[:space:]#]*\).*/\1/p" "${root}/Makefile"; }

echo "==> pinned toolchain (.toolchain/)"
for spec in "uv:$(make_pin UV_VERSION)" "just:$(make_pin JUST_VERSION)"; do
  tool="${spec%%:*}" pin="${spec#*:}"
  if msg="$(bash "${root}/scripts/check_tool_version.sh" "${root}/.toolchain/${tool}/bin/${tool}" "${pin}" \
    "make worktree-init" 2>&1)"; then
    ok "${tool} ${pin}"
  else
    fail "${msg//$'\n'/ }"
  fi
done

py_pin="$(tr -d '[:space:]' < "${root}/.python-version" 2> /dev/null)"
uv="${root}/.toolchain/uv/bin/uv"
found="$(cd "${root}" && VIRTUAL_ENV='' "${uv}" python find --managed-python --no-project "${py_pin}" 2> /dev/null)"
managed="$(cd "${root}" && "${uv}" python dir 2> /dev/null)"
have="$("${found:-/nonexistent}" -c 'import platform; print(platform.python_version())' 2> /dev/null)"
if [[ -n "${managed}" && "${found}" == "${managed}"/* && "${have}" == "${py_pin}" ]]; then
  ok "Python ${py_pin} (uv-managed: ${found})"
else
  fail "no uv-managed Python ${py_pin} (.python-version) found. Fix: make worktree-init, which installs exactly .python-version; if the Blender bundled-Python check below also FAILs, correct .python-version first."
fi

echo "==> Blender (${blender_app})"
blender_pin="$(make_pin BLENDER_EXPECTED)"
blender="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "${blender_app}/Contents/Info.plist" 2> /dev/null)"
if [[ -z "${blender}" ]]; then
  fail "Blender not found at ${blender_app}. Fix: install Blender ${blender_pin} there."
elif [[ "${blender}" == "${blender_pin}" ]]; then
  ok "Blender ${blender}"
else
  # Warn only until ADR-0004 pins Blender (rollout Run 5.1); then this becomes fail.
  warn "Blender ${blender}, but the Makefile expects ${blender_pin} (BLENDER_EXPECTED)."
fi
bundled="$(find "${blender_app}/Contents/Resources" -path '*/python/bin/python3.*' -type f ! -name '*-config' 2> /dev/null | head -n 1)"
bundled_v="$("${bundled:-/nonexistent}" --version 2> /dev/null | awk '{ print $2 }')"
if [[ -z "${bundled_v}" ]]; then
  fail "could not run Blender's bundled Python under ${blender_app}/Contents/Resources."
elif [[ "${bundled_v}" == "${py_pin}" ]]; then
  ok "Blender's bundled Python ${bundled_v} = .python-version"
else
  fail "Blender's bundled Python is ${bundled_v}, but .python-version is ${py_pin}. Host Python must equal it. Fix: set .python-version to ${bundled_v} and run make worktree-init (Python and Blender pins move together)."
fi

echo "==> outside tools (Brewfile)"
for cmd in ffmpeg shellcheck; do
  if path="$(command -v "${cmd}")"; then
    ok "${cmd}: $("${path}" -version 2> /dev/null | head -n 1 || true)$("${path}" --version 2> /dev/null | sed -n 's/^version: //p')"
  else
    fail "${cmd} not on PATH. Fix: make setup (brew bundle)"
  fi
done

(( failed )) && { echo "doctor: something needs action (FAIL lines above)."; exit 1; }
echo "doctor: all checks pass."
