#!/usr/bin/env bash
# install_tool.sh uv|just [REPO_ROOT]
# Puts the release build of the uv or just that REPO_ROOT/Makefile pins (UV_VERSION, JUST_VERSION)
# at REPO_ROOT/.toolchain/<tool>/bin/, downloading only when the copy there does not already report
# the pin. Exit 0 when it is in place, 1 when it could not be done, 2 on bad usage or an unreadable
# pin. Never touches a machine-wide uv or just. Ported from docketScore's install_uv.sh and
# install_just.sh, merged, and without their per-machine cache (Run 0.1 decision).
#
# The download is accepted only when three SHA-256 values agree: the one committed in
# REPO_ROOT/.<tool>.sha256, the one the release publishes, and the file's own. The committed value
# means changed bytes need a reviewed commit, not only a change at the origin.
set -uo pipefail

tool="${1:-}"
root="${2:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
die() { echo "error: $*" >&2; exit 1; }

case "${tool}" in
  uv) var=UV_VERSION; release="https://github.com/astral-sh/uv/releases/download"; sums=sha256.sum ;;
  just) var=JUST_VERSION; release="https://github.com/casey/just/releases/download"; sums=SHA256SUMS ;;
  *) echo "usage: install_tool.sh uv|just [REPO_ROOT]" >&2; exit 2 ;;
esac
pin="$(sed -n "s/^${var}[[:space:]]*:=[[:space:]]*\([^[:space:]#]*\).*/\1/p" "${root}/Makefile" 2> /dev/null)"
if [[ ! "${pin}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "error: ${root}/Makefile's ${var} is '${pin}', not one exact version such as 1.2.3." >&2
  exit 2
fi

[[ "$(uname -s)" == Darwin ]] || die "this repository fetches ${tool} for macOS only, not $(uname -s)."
case "$(uname -m)" in
  arm64) triple=aarch64-apple-darwin ;;
  x86_64) triple=x86_64-apple-darwin ;;
  *) die "no ${tool} build is pinned for $(uname -m)." ;;
esac
if [[ "${tool}" == uv ]]; then asset="uv-${triple}.tar.gz"; else asset="just-${pin}-${triple}.tar.gz"; fi
dest="${root}/.toolchain/${tool}"

# Run from / so no project's configuration (uv.toml's required-version) is read on the way.
version_of() { (cd / && "$1" --version 2> /dev/null) | awk -v t="${tool}" '$1 == t { print $2; exit }'; }
listed() { awk -v f="${asset}" '$2 == f || $2 == "*" f { print $1 }' "$1" 2> /dev/null; }

[[ "$(version_of "${dest}/bin/${tool}")" == "${pin}" ]] && exit 0

committed="$(listed "${root}/.${tool}.sha256")"
[[ "${committed}" =~ ^[0-9a-f]{64}$ ]] \
  || die ".${tool}.sha256 holds no single SHA-256 for ${asset}. Add its line from ${release}/${pin}/${sums}."

mkdir -p "${root}/.toolchain" || die "could not create ${root}/.toolchain."
staging="$(mktemp -d "${root}/.toolchain/.staging.XXXXXX")" || die "could not create a staging directory."
trap 'rm -rf "${staging}"' EXIT
# A stalled transfer ends with curl's error, not a hung bootstrap.
fetch() {
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
    --connect-timeout 30 --speed-limit 1024 --speed-time 60 -o "$2" "$1"
}
echo "==> ${tool}: fetching ${asset} from ${release}/${pin}/"
fetch "${release}/${pin}/${sums}" "${staging}/${sums}" || die "could not download ${sums}. Nothing was installed."
fetch "${release}/${pin}/${asset}" "${staging}/${asset}" || die "could not download ${asset}. Nothing was installed."
published="$(listed "${staging}/${sums}")"
[[ "${published}" == "${committed}" ]] \
  || die "the release's ${sums} lists '${published}' for ${asset}, not ${committed} (.${tool}.sha256). Nothing was installed."
actual="$(shasum -a 256 "${staging}/${asset}" | awk '{ print $1 }')"
[[ "${actual}" == "${committed}" ]] \
  || die "the downloaded ${asset} has SHA-256 ${actual}, not ${committed}. Nothing was installed."

# uv's archive holds uv-<triple>/{uv,uvx}; just's holds just at its top level.
{ mkdir -p "${staging}/x" "${staging}/out/bin" && tar -xzf "${staging}/${asset}" -C "${staging}/x"; } \
  || die "could not extract ${asset}. Nothing was installed."
if [[ "${tool}" == uv ]]; then
  mv "${staging}/x/uv-${triple}/uv" "${staging}/x/uv-${triple}/uvx" "${staging}/out/bin/"
else
  mv "${staging}/x/just" "${staging}/out/bin/"
fi || die "could not find ${tool} in ${asset}. Nothing was installed."
[[ "$(version_of "${staging}/out/bin/${tool}")" == "${pin}" ]] \
  || die "the extracted ${tool} does not report version ${pin}. Nothing was installed."
{ rm -rf "${dest}" && mv "${staging}/out" "${dest}"; } || die "could not move ${tool} into ${dest}."
echo "==> ${tool}: ${pin} at ${dest}/bin"
