#!/usr/bin/env bash
# check_tool_version.sh TOOL PIN FIX
# Exit 0 only when TOOL (a path or a command on PATH) reports exactly version PIN in its
# `--version` output; 1 when it reports another version; 2 when that cannot be measured. Prints why
# on failure, with FIX, the command that brings the tool to its pin. Ported from docketScore.
set -uo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: check_tool_version.sh TOOL PIN FIX" >&2
  exit 2
fi
tool="$1" pin="$2" fix="$3"

found_bin="$(command -v "${tool}" || true)"
if [[ -z "${found_bin}" ]]; then
  echo "error: no ${tool} found; this repository pins ${pin}." >&2
  echo "  Fix: ${fix}" >&2
  exit 2
fi
output="$(cd / && "${found_bin}" --version 2> /dev/null || true)"
if [[ ! "${output}" =~ ([0-9]+\.[0-9]+\.[0-9]+) ]]; then
  echo "error: could not read a version from ${found_bin} --version (got '${output}')." >&2
  exit 2
fi
[[ "${BASH_REMATCH[1]}" == "${pin}" ]] && exit 0
echo "error: ${found_bin} is ${BASH_REMATCH[1]}, but this repository pins ${pin}." >&2
echo "  Fix: ${fix}" >&2
exit 1
