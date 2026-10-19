# Run 0.3: Blender API probe spike → ADR-0001 — status

**Quest:** studio-v1 (feature)  **Date:** 2026-10-19  **Status:** COMPLETE

**Spec trace:**
- `sidequests/studio-v1/studio-v1-rollout.md:138`: the Run 0.3 spec; acceptance criteria at `:147`.
- `docs/project-definition.md:311`: §M0 Tasks item 3.
- `docs/project-definition.md:319`: §M0 Acceptance, reproducibility.
- `docs/project-definition.md:275`: §Risks, Blender API drift.
- `CLAUDE.md:22-23`: §Blender, `bpy.data` and render only through the harness.
- `docs/coding-standards.md:13`: STD-002. `:17`: STD-003. `:21`: STD-004.
- `docs/test-strategy.md:12`: Reproducibility layer.
- `docs/adr/0000-template.md`: ADR structure.

**User decisions, 2026-10-19 (at plan approval):**
1. (a) One isolated render call, as a recorded spike exception.
2. (a) 256², Cycles 16 samples, denoise off, seed 0, PNG RGBA8; hash both the pixels and the file.
3. Meet Run 0.2's ruff/mypy config.
4. Keep the probe as a re-runnable tool.

## Acceptance Criteria Checklist
- [x] Probe JSON from this machine is quoted in ADR-0001 with the machine named. Evidence:
  - `docs/adr/0001-blender-api-baseline.md` §Evidence quotes run 1's report verbatim.
  - The machine is Apple M5 Max, arm64, macOS 27.0.1, commit 86aad30.
  - Status is `Provisional`, review trigger "the M1 Mac is probed", expiry the M0 exit gate (Run 0.7).
- [x] ADR-0001's Decision names the exact-hash engine (`BLENDER_EEVEE`, decoded-pixel sha256) and the Cycles tolerance (GPU/Metal, max abs diff ≤ 1/255 per 8-bit channel), with the hashes from the two renders as evidence (table and JSON in §Evidence).
- [x] Contradictions with `CLAUDE.md` / §M0 Acceptance are listed below as proposed changes, not applied (see Confidence Report D).
- [x] `scripts/run_tests.sh` passes — run bare by the parent on the combined Run 0.2 + 0.3 tree, 2026-10-19: exit 0, all lanes ok (environment, locks, static — mypy 3 source files incl. `blender/probe/api_probe.py`, unit 4 passed, blender 1 passed). At the time of this run it was pending 0.2; Run 0.2's lint and type checks were run on the probe instead (below).

### Evidence

The probe ran twice as separate processes. The output went to the scratchpad only:

```
$ S=/private/tmp/claude-501/-Users-mpkirby-projects-AIAnimationLab/b8f02529-7e31-4167-a7be-13d2b15adcba/scratchpad/probe/final
$ for i in 1 2; do /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -noaudio --python-exit-code 1 --python blender/probe/api_probe.py -- --out "$S/run$i" --report "$S/probe-m5max-run$i.json" > "$S/run$i.log" 2>&1; echo "run$i exit=$?"; done
run1 exit=0
run2 exit=0
```

Determinism, from `probe-m5max-run1.json`. Run 2 is identical except for the file hashes and the timings.

```
BLENDER_EEVEE  pixel_sha256 d7e06ed6a6d39b4f6de4326ad1fe053f928e561fedc56564dc1f0156b6d3d892 (×2)  max_abs_diff_255 0  differing_pixels 0
CYCLES (GPU)   pixel_sha256 f07c44023ffd1119aa8d5cbdb85f5a9a602b098716052b60f6e2f4ab1a86deba (×2)  max_abs_diff_255 0  differing_pixels 0
```

Cross-process comparison, `diff probe-m5max-run1.json probe-m5max-run2.json`. Only `file_sha256` and `wall_seconds` lines change:

```
~  42  "file_sha256": "a0b9a7ca…a21c" → "3713e45a…ed00"
~  44  "wall_seconds": 0.386 → 0.387
~  48  "file_sha256": "bb5f1450…4c7c" → "a3042ccf…3a2b"
~  50  "wall_seconds": 0.25 → 0.217
~  72  "file_sha256": "b635d6de…9734" → "16f8b85e…6e6d"
~  74  "wall_seconds": 2.547 → 1.717
~  78  "file_sha256": "60686b64…a2da" → "2a65ebcf…d551"
~  80  "wall_seconds": 0.487 → 0.852
```

An earlier exploratory run, before the engine-list fix, produced the same two pixel hashes as well.

Why the PNG file hashes differ: the PNG `tEXt` chunks of `run1/blender_eevee_{1,2}.png`, parsed with a struct walk:

```
blender_eevee_1.png [... b'Date\x002026/10/19 12:54:57', ..., b'RenderTime\x0000:00.33', b'Memory\x000M']
blender_eevee_2.png [... b'Date\x002026/10/19 12:54:57', ..., b'RenderTime\x0000:00.24', b'Memory\x000M']
```

Factory-startup Cycles defaults, from a read-only query script run in the scratchpad:

```
DEFAULTS compute_device_type='METAL' scene.cycles.device='CPU' engine='BLENDER_EEVEE'
```

Lint and type checks under Run 0.2's `pyproject.toml`/`uv.lock` (present but uncommitted at the time):

```
$ .toolchain/uv/bin/uv run --locked ruff check blender/probe
All checks passed!
$ .toolchain/uv/bin/uv run --locked ruff format --check blender/probe
1 file already formatted
$ .toolchain/uv/bin/uv run --locked mypy blender/probe
Success: no issues found in 1 source file
```

## What Changed
- `blender/probe/api_probe.py` (new, 338 lines): headless probe. It builds the scene with `bpy.data` only and writes a JSON report covering:
  - machine and Blender info;
  - the runtime engine IDs;
  - Cycles/Metal devices;
  - the GPU backend;
  - per-engine renders done twice, with pixel and file hashes and the max abs diff.

  Its only operator call is in `_render_still`, the recorded spike exception.
- `docs/adr/0001-blender-api-baseline.md` (new): Provisional ADR. It records the API baseline and the determinism policy, with the probe JSON quoted.
- `sidequests/studio-v1/status/run0.3status.md` (new): this report.
- Applied by the parent after user approval (2026-10-19), from Confidence Report D: `docs/project-definition.md` §M0 Acceptance and `docs/test-strategy.md` Reproducibility row now say "exact hashes of the decoded frame pixels"; ADR-0001's quoted report relabels the hostname as "M5 Max Laptop".

## How to Test
```
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -noaudio --python-exit-code 1 \
  --python blender/probe/api_probe.py -- --out <scratch>/run1 --report <scratch>/probe.json
# run twice; compare determinism.*.runs[].pixel_sha256 within and across reports
.toolchain/uv/bin/uv run --locked ruff check blender/probe && .toolchain/uv/bin/uv run --locked mypy blender/probe
scripts/run_tests.sh   # once Run 0.2 lands
```

## Architecture Decisions
- **Determinism policy (ADR-0001):**
  - EEVEE uses an exact sha256 of the decoded RGBA pixels.
  - Cycles GPU/Metal uses max abs diff ≤ 1/255, with denoise off, seed fixed and the animated seed off.
  - Cycles was bit-identical here, but the tolerance stays, per §M0, because the evidence is one frame on one machine.
- **Spike exception to STD-002/STD-003 (user decision 1a):** recorded in ADR-0001 Consequences. The scope is re-running this probe. It does not cover new render calls under `blender/probe/` once the harness exists. CLAUDE.md is unchanged.
- **Engine list read from the TypeError on an invalid assignment:** the static RNA `enum_items` lists only `BLENDER_EEVEE`, and no public API exposes the dynamic enum. This is fragile if Blender rewords the message. The probe raises a `RuntimeError` rather than guessing.

## Open Issues
- not a defect: the gate was pending Run 0.2 during this run; it has since passed on the combined tree (see the checklist).
- not a defect: OIDN denoise determinism is not measured. It is a Run 0.4 profile question. ADR-0001 keeps denoise out of the reproducibility test.
- not a defect: `docs/adr/0002-python-toolchain-and-layout.md:24` (Run 0.2's file, not edited) lists the `blender/` subdirectories without `blender/probe/`. The parent may want to add "`blender/probe/` holds the in-Blender API probe (ADR-0001)" when 0.2 lands.
- not a defect: the probe report includes `hostname`. User decision 2026-10-19: committed records name machines by label, not hostname — this one is the **M5 Max Laptop** (the user also has an M5 Max Mac Studio, so "M5 Max" alone is ambiguous). ADR-0001's quoted report was relabelled; a machine-label mechanism is routed to Run 0.5's manifest.

## Shared-file edits for the parent to apply

**`docs/adr/README.md`:** replace the placeholder row `| — | — | — |` (or append below 0002's row, keeping numeric order):
```
| [0001](0001-blender-api-baseline.md) | Blender 5.2.2 API baseline and render determinism policy | Provisional |
```

**`sidequests/studio-v1/studio-v1-rollout.md`:**
- Header `:138` becomes `### Run 0.3: Blender API probe spike → ADR-0001 — COMPLETE`. Match whatever marker Run 0.1 used.
- Tick the first three acceptance criteria under `:147` (`- [ ]` → `- [x]`).
- Leave `` `scripts/run_tests.sh` passes `` as `- [ ]` with the suffix ` — pending 0.2`, or tick it once 0.2's runner passes.

**`sidequests/studio-v1/status/carry-forward.md`:** append:
```
- [0.3] -> 0.4,0.7 | contract | Engine IDs (5.2.2): BLENDER_EEVEE, BLENDER_WORKBENCH, CYCLES. Cycles GPU = prefs compute_device_type="METAL" + scene.cycles.device="GPU" (ADR-0001).
- [0.3] -> 0.4 | gotcha | Factory-startup scene.cycles.device is 'CPU' even with METAL prefs: Cycles silently renders on CPU unless the harness sets GPU and records it.
- [0.3] -> 0.4,0.7 | gotcha | PNG bytes differ every render (tEXt Date/RenderTime metadata): compare sha256 of decoded pixels (Image.pixels), never file bytes.
- [0.3] -> 0.7 | decision | EEVEE exact pixel sha256; Cycles Metal max abs diff <= 1/255, denoise off, fixed seed, no animated seed. Measured diff 0 on M5 Max (ADR-0001).
- [0.3] -> 0.7 | deferred | Rerun blender/probe/api_probe.py on the M1 Mac; quote its JSON in ADR-0001 and lift it from Provisional (expiry: M0 exit).
```

## Test Counts
No pytest suite in this run (gate pending 0.2 at the time). Parent's bare `scripts/run_tests.sh` on the combined tree: exit 0 — unit 4 passed / 1 deselected, blender 1 passed / 4 deselected.

| Check | Result |
| --- | --- |
| Probe runs | 2 of 2 exit 0, about 5 s wall each |
| Probe renders | 8 frames total (2 engines × 2 renders × 2 runs) |
| Pixel hashes | identical per engine |
| ruff check | pass |
| ruff format --check | pass |
| mypy (strict, with fake-bpy-module-5.2 stubs) | pass |

## Confidence Report
**A. Assumptions made**
- One 256² frame of a trivial scene stands in for "reproducible". Run 0.7 must confirm it on the 48-frame plain scene.
- The factory-startup Cycles preference `METAL` is assumed to also hold on the M1.

**B. Deviations from existing patterns**
- ADR-0001 adds an `## Evidence` section that `0000-template.md` lacks. It holds the quoted JSON the acceptance criterion requires.
- Rendering in the probe deviates from STD-002/STD-003, by user decision (recorded spike exception).

**C. Thin context**
- No spec defines "frame hash". §M0 and the test strategy say "exact frame hashes" without saying file or pixels.

**D. Conflicts found (proposed changes; the wording change below was applied after user approval on 2026-10-19)**
- §M0 Acceptance (`docs/project-definition.md:319`) and `docs/test-strategy.md:12` say "exact frame hashes" for EEVEE. File hashes never match because of the PNG metadata. Proposed wording: "exact hashes of the decoded frame pixels". ADR-0001 already refines this, and a later ADR wins.
- §M0's claim that Cycles on GPU is "not guaranteed bit-identical" was not contradicted, since 0 diff was measured on one frame. No change is proposed.
- `CLAUDE.md:23` ("Never call render operators ad hoc"): the probe is a recorded exception in ADR-0001. No CLAUDE.md change is proposed, per user decision 1a.

**E. Complexity concentrations**
- `render_engines()` parses Blender's TypeError message: the one fragile spot.
- `_compare()` walks Python lists over 262k floats. That is fine at 256², but too slow for full-resolution frames. Run 0.7 should use numpy inside Blender if it reuses this.

## Next Unblocked Run
0.4 (once 0.2 lands; consumes the 0.3 engine IDs). 0.7 is still blocked on 0.4–0.6.
