#!/usr/bin/env bash
# collect_machine_evidence.sh [OUT_DIR]
# Collects a machine's reproducibility evidence into one tarball to send back: doctor, the gate
# twice (cold and warm, timed), the Blender API probe twice (ADR-0001), and an EEVEE and a Cycles
# render pair checked by blender/harness/compare.py. Re-run it on a new machine, after a Blender
# bump, or after a harness or profile change. Needs a set-up clone (`make setup`), a clean tree and
# a MACHINE_LABELS row for this Mac. Writes only under OUT_DIR (default: outside the repo).
set -uo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${root}" || exit 1
uv="${root}/.toolchain/uv/bin/uv"
blender_bin="/Applications/Blender.app/Contents/MacOS/Blender"
stop() { printf '\nSTOP: %s\n' "$*" >&2; exit 1; }
step() { printf '\n==> %s\n' "$*"; }

[[ -x "${uv}" ]] || stop "no pinned uv in .toolchain/. Fix: make setup"
[[ -z "$(git status --porcelain)" ]] || stop "the working tree is not clean, so manifests would read git_dirty. Commit or stash first."
# The label, never the OS hostname, names the machine in every record (MACHINE_LABELS).
label="$("${uv}" run --locked python -c \
  'from blender.harness.manifest import collect_machine; print(collect_machine()["label"])')" \
  || stop "this Mac has no machine label (message above). Add its hw.model row first."
slug="$(printf '%s' "${label}" | tr '[:upper:] ' '[:lower:]-')"
stamp="$(date +%Y%m%d-%H%M%S)"
out="${1:-${HOME}/aial-evidence-${slug}-${stamp}}"
mkdir -p "${out}" || exit 1
exits="${out}/exits.txt"
record() { echo "$1 exit $2" | tee -a "${exits}"; }

step "Machine: ${label}"
{
  echo "date: $(date)"
  echo "label: ${label}"
  echo "hw.model: $(sysctl -n hw.model)"
  echo "chip: $(sysctl -n machdep.cpu.brand_string)"
  echo "macOS: $(sw_vers -productVersion)"
  echo "blender: $("${blender_bin}" --factory-startup --version 2> /dev/null | head -n 1)"
  echo "HEAD: $(git rev-parse HEAD)"
} | tee "${out}/machine.txt"

step "make doctor"
make doctor > "${out}/doctor.log" 2>&1
rc=$?
cat "${out}/doctor.log"
record doctor "${rc}"
[[ "${rc}" -eq 0 ]] || stop "make doctor failed; fix what it names, then re-run."

# The first gate run includes Cycles' one-time Metal kernel compile; the second is warm.
for n in 1 2; do
  step "Gate run ${n}"
  /usr/bin/time -p scripts/run_tests.sh > "${out}/run_tests-${n}.log" 2>&1
  rc=$?
  tail -n 4 "${out}/run_tests-${n}.log"
  record "gate-${n}" "${rc}"
done

for n in 1 2; do
  step "Probe run ${n}"
  "${blender_bin}" -b --factory-startup -noaudio --python-exit-code 1 \
    --python blender/probe/api_probe.py -- \
    --out "${out}/probe-run${n}" --report "${out}/probe-run${n}.raw.json" > "${out}/probe-run${n}.log" 2>&1
  record "probe-${n}" "$?"
  if [[ -f "${out}/probe-run${n}.raw.json" ]]; then
    sed -E "s/(\"hostname\": *)\"[^\"]*\"/\\1\"${label}\"/" "${out}/probe-run${n}.raw.json" > "${out}/probe-run${n}.json"
    rm -f "${out}/probe-run${n}.raw.json"
  fi
  rm -rf "${out}/probe-run${n}"
done

step "Render pairs"
ev="${out}/renders"
mkdir -p "${ev}"
# One frame at the final profile: the same Cycles check as tests/test_render_determinism.py.
cat > "${ev}/plain_scene_frame1.py" << EOF
import importlib.util
_spec = importlib.util.spec_from_file_location("_plain_scene", "${root}/tests/scenes/plain_scene.py")
_plain = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_plain)
FRAME_COUNT = 1
build = _plain.build
EOF
export AIAL_MODEL_ID=fixture/machine-evidence
for r in a b; do
  "${uv}" run --locked python blender/harness/render.py --scene tests/scenes/plain_scene.py \
    --profile preview --out "${ev}/eevee-${r}" --seed 0 > "${ev}/eevee-${r}.log" 2>&1
  record "eevee-${r}" "$?"
  "${uv}" run --locked python blender/harness/render.py --scene "${ev}/plain_scene_frame1.py" \
    --profile final --out "${ev}/cycles-${r}" --seed 0 > "${ev}/cycles-${r}.log" 2>&1
  record "cycles-${r}" "$?"
done
for engine in eevee cycles; do
  "${uv}" run --locked python blender/harness/compare.py "${ev}/${engine}-a" "${ev}/${engine}-b" \
    > "${ev}/compare-${engine}.json"
  record "compare-${engine}" "$?"
done

step "Packaging (manifests, compare JSON, logs; no frames)"
# __pycache__: Blender byte-compiles the frame-1 wrapper beside it (its Python ignores PYTHONDONTWRITEBYTECODE).
rm -rf "${ev}"/*/frames "${ev}"/*/contact_sheet.png "${ev}/__pycache__"
tarball="${out}.tar.gz"
tar -czf "${tarball}" -C "$(dirname "${out}")" "$(basename "${out}")"
echo
cat "${exits}"
echo
echo "Send back: ${tarball}"
