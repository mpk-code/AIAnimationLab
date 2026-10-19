# Run 0.4: Harness runner — status

**Quest:** studio-v1 (feature)  **Date:** 2026-10-19  **Status:** COMPLETE
**Spec trace:** `sidequests/studio-v1/studio-v1-rollout.md` §"Run 0.4: Harness runner" and Input Gaps (model ID); `docs/adr/0001-blender-api-baseline.md` §Decision, §Evidence "Other findings", §Consequences (harness sets GPU + METAL and records both; probe not importable); `docs/adr/0002-python-toolchain-and-layout.md` §Decision "Scene-script contract"; `docs/coding-standards.md` STD-001–STD-004; `docs/project-definition.md` §Artifact schemas (`production.yaml` `fps: 24`); `CLAUDE.md` §Blender.

## Acceptance Criteria Checklist
- [x] Rendering a 2-frame scene with `--profile preview` writes 2 PNGs to `<out>/frames/` and exits 0 — `tests/test_harness_cli.py::test_preview_renders_a_two_frame_scene_to_frames_dir` (runs `render.py` as a script). Also: the 48-frame plain scene (Run 0.6) rendered through the harness into the scratchpad, `render.py: 48 frames in …/scratchpad/r04/plain/frames (BLENDER_EEVEE, 9.9s)`, exit 0.
- [x] `--profile` outside `preview|final`, a missing `--scene`, or a missing model ID exits non-zero with a message — `test_invalid_arguments_exit_non_zero_with_a_message[unknown-profile|missing-scene|missing-model-id|missing-seed|bad-seed]`, plus a manual check (exit codes 2, 2, 2): `invalid choice: 'draft'`, `the following arguments are required: --scene`, `a model ID is required: pass --model-id or set AIAL_MODEL_ID`. A test fixture makes these tests fail if Blender would have been launched.
- [x] `grep -rn "render.render\|filepath" blender/ --include='*.py'` — hits only in `blender/harness/_inblender.py` (lines 119, 155, 161) and `blender/probe/api_probe.py` (203, 206, 208).
- [x] `scripts/run_tests.sh` passes — all lanes ok, exit 0, 19.0 s total.

## What Changed
- `blender/harness/profiles.py` — new: `Profile` dataclass, `PROFILES` table (`preview`, `final`), PNG/RGBA/8-bit constants.
- `blender/harness/render.py` — new: host CLI plus `run_render(...) -> RunResult`, `production_id_for`, `DEFAULT_BLENDER_BIN`, `MODEL_ID_ENV`, `HarnessError` / `BlenderFailed`.
- `blender/harness/_inblender.py` — new: in-Blender entry. Empties the factory scene, calls `build(seed)`, requires a camera, applies the profile and the Cycles Metal setup, makes the single `bpy.ops.render.render(animation=True)` call, and writes the in-Blender facts as JSON.
- `tests/test_harness_cli.py` — new: 13 unit tests and 3 blender tests (preview 2-frame CLI, preview run-result fields, final/Cycles 1-frame GPU/METAL).
- `tests/conftest.py` — the approved 2-line edit: imports `DEFAULT_BLENDER_BIN` from `render.py` instead of repeating it.
- `blender/harness/.gitkeep` — deleted; the directory now holds files, so it was an orphan.
- `blender/__init__.py`, `blender/harness/__init__.py` — empty; Run 0.5 created them first, and they are left identical.
- Imports `blender/harness/run_result.py` (Run 0.5's file, not edited).

## How to Test
```
scripts/run_tests.sh
uv run python blender/harness/render.py --scene tests/scenes/plain_scene.py --profile preview \
  --out <scratch>/plain --seed 0 --model-id fixture/manual     # 48 PNGs in <scratch>/plain/frames
```

## Architecture Decisions
These are user decisions from 2026-10-19 (Run 0.4 plan, decisions 1–6):
1. **Scene selection.** Scene scripts build into `bpy.context.scene`. The harness first removes the factory Cube/Light/Camera objects and their orphaned mesh/light/camera datablocks through `bpy.data`. The factory **World is kept**, so it sets the background (grey in the plain scene's frames). The orphaned factory "Material" datablock is also kept; it is unused. The run fails if `build()` leaves no `scene.camera`.
2. **`--seed` is required.** It drives `build(seed)` and the Cycles `seed`.
3. **Profiles:**
   - preview: EEVEE, 640×360, TAA 16
   - final: Cycles on GPU/METAL, 1920×1080, 256 samples, adaptive sampling on, denoise off, `use_animated_seed=False`
   - both: 24 fps, AgX, PNG RGBA 8-bit, opaque film. All values are set explicitly.
4. **Cycles coverage.** A Cycles 1-frame final test runs in the blender lane.
5. **Existing output.** A non-empty `<out>/frames/` is refused (exit 1).
6. **`BLENDER_BIN` default.** `render.py` owns `DEFAULT_BLENDER_BIN`.

Implementation decisions:
- **Device facts are read back from Blender, not echoed from the profile.** If Cycles has no enabled Metal device, or `scene.cycles.device` is not `GPU`, the harness raises rather than falling back to the CPU.
- **`gpu_backend`** is read after the render. A Cycles-only render does not initialise the `gpu` module in background mode (a new finding beyond ADR-0001), so the harness calls `gpu.init()` when `gpu.platform` raises.
- **`production_id`** is `t-<stem>`: lower-cased, with characters outside `[a-z0-9_-]` replaced by `-`. It is validated against the pattern read from `schemas/manifest.schema.json` (the single source, STD-001). A stem that cannot be normalised is refused.
- **The in-Blender result JSON** goes to a `TemporaryDirectory`, so `<out>` holds only `frames/` until Run 0.7 adds the manifest.

ADR candidate: none new. Decision 1 refines ADR-0002's scene-script contract ("builds into `bpy.context.scene`, emptied by the harness; the factory World stays"). Fold it into ADR-0002 when that ADR is accepted.

## Open Issues
- not a defect: while lint-fixing I ran `ruff check --fix .` and `ruff format .` repo-wide **once**. Those commands may have applied lint/format-only fixes to Run 0.5's in-progress files: `blender/harness/manifest.py`, `blender/harness/contact_sheet.py`, `tests/test_manifest.py`, `tests/test_contact_sheet.py` (all mtime 13:25:37). They are untracked, so there is no diff. Run 0.5 should re-read them before editing. Later ruff runs were limited to this run's files.
- not a defect: `samples` in the run result is the profile value the harness assigned. It is not read back from Blender.
- not a defect: `tests/conftest.py` `_blender_bin()` repeats `render.blender_bin()`. This was left as-is, because only the 2-line edit was approved.

## Carry-forward
None appended. The proposed lines are in the section below, for the parent to apply.

## Shared-file edits for the parent to apply
**Rollout** (`sidequests/studio-v1/studio-v1-rollout.md`, `### Run 0.4`):
- add `- **Status:** COMPLETE 2026-10-19 — \`sidequests/studio-v1/status/run0.4status.md\`` under the heading;
- tick all four acceptance-criteria boxes.

**Carry-forward ledger** (`sidequests/studio-v1/status/carry-forward.md`, live band):
```
- [0.4] -> 0.7 | contract | render.run_render(scene, profile, out, seed, model_id, binary) -> RunResult (blender/harness/run_result.py); CLI needs --scene --profile --out --seed --model-id|AIAL_MODEL_ID.
- [0.4] -> 0.7 | gotcha | render.py refuses a non-empty <out>/frames/ (exit 1): each determinism run needs its own --out dir.
- [0.4] -> surface | gotcha | Scenes build into bpy.context.scene after the harness strips factory objects; the factory World is kept and sets the background unless build() replaces scene.world.
- [0.4] -> surface | gotcha | A Cycles-only background render leaves the gpu module uninitialised: gpu.platform raises SystemError until gpu.init() (harness _gpu_backend handles it).
- [0.4] -> quest | deferred | fps (24) and aspect (16:9 resolutions) live in blender/harness/profiles.py until production.yaml exists; then move them there, profiles keep quality only.
```
Fold: the `[0.2] -> 0.4,0.5,0.6` scene-contract line and the `[0.3] -> 0.4` Cycles-CPU gotcha were consumed here. The gotcha now has an enforcement mechanism (the harness raises without a Metal device, and `test_final_renders_on_cycles_with_the_metal_gpu` asserts METAL). Suggested residue: `~ Cycles GPU/METAL set and asserted by blender/harness/_inblender.py _enable_metal_devices; test_final_renders_on_cycles_with_the_metal_gpu (est. 0.3, enforced 0.4)`.

**Integration note:** Run 0.7 is the integration consumer of `RunResult`. It wires `write_manifest(run_result, out_dir)` and `build_contact_sheet` into `render.main` after `run_render`.

## Test Counts
`scripts/run_tests.sh` (full output: `/private/tmp/claude-501/-Users-mpkirby-projects-AIAnimationLab/b8f02529-7e31-4167-a7be-13d2b15adcba/scratchpad/r04-gate.txt`):
```
=== lane: environment — ok
=== lane: locks — ok
=== lane: static — ok          (ruff: All checks passed!; mypy clean)
======================= 50 passed, 7 deselected in 1.10s =======================   (unit)
====================== 7 passed, 50 deselected in 15.96s =======================   (blender)
=== run_tests.sh: all lanes ok (environment locks static unit blender)
scripts/run_tests.sh  6.53s user 3.29s system 51% cpu 19.035 total
```
Of these, this run's file holds 16 tests: 13 unit and 3 blender. The totals also include Run 0.5 and Run 0.6 tests that are in the tree.

## Confidence Report
A. **Assumptions:**
- A missing `--seed` gets the same argparse error as the other required flags.
- `engine_device` is `"GPU"` for EEVEE, because EEVEE always renders on the GPU backend.

B. **Deviations:**
- Patterns from `api_probe.py` (engine assignment via `Any`, Cycles prefs, Metal device enable) are copied, not imported, because ADR-0001 forbids importing the probe.

C. **Thin context:**
- No glossary entry for "render profile", although STD-001 names render profiles as a glossary enum.

D. **Conflicts:** None.

E. **Complexity concentrations:**
- `_inblender._apply_profile` (engine branch).

## Next Unblocked Run
0.7, once 0.5 and 0.6 are complete.
