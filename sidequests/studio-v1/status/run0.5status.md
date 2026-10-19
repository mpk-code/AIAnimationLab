# Run 0.5: Manifest schema, writer and contact sheet — status

**Quest:** studio-v1 (feature)  **Date:** 2026-10-19  **Status:** COMPLETE

**Spec trace:**
- `sidequests/studio-v1/studio-v1-rollout.md:178`: the Run 0.5 spec. Input Gaps model-ID bullet at `:42`.
- `docs/project-definition.md:236`: §Artifact schemas, `manifest.json`. `:314`: §M0 Tasks item 6. `:320`: §M0 Acceptance item 2.
- `docs/adr/0001-blender-api-baseline.md`: frame identity is the decoded-pixel sha256; the harness records the Cycles device.
- `docs/adr/0002-python-toolchain-and-layout.md`: layout under `blender/harness/`; gate lanes.
- `docs/coding-standards.md` STD-001, STD-004, STD-006.

**User decisions, 2026-10-19 (at plan approval):**
1. Machine label: a committed map from `sysctl -n hw.model` to a label in `blender/harness/manifest.py`. `Mac17,6` → "M5 Max Laptop", `Mac17,14` → "M5 Max Mac Studio", `MacBookPro18,2` → "M1 Laptop". An unknown model fails with "add a row". There is no hostname field.
2. Hashes: record both `file_sha256` and `pixel_sha256` for each frame. Reproducibility compares `pixel_sha256`. `pixel_sha256()` is public, so 0.7's `compare.py` can import it.
3. production_id: the schema accepts `p-NNNN` or `t-<slug>`. The harness sets it in `RunResult`; `write_manifest` never works it out.
4. Model ID: `--model-id` is required, with env `AIAL_MODEL_ID` as a fallback; the render fails if neither is set. Fixture renders pass `fixture/<test-name>`.

**Parent reconciliation:** the run-result contract is `blender/harness/run_result.py`, with exactly the four dataclasses the parent specified. I created it first so Run 0.4 could import it.

## Acceptance Criteria Checklist
- [x] **A manifest written from a synthetic run result validates against the schema and contains every §M0 Acceptance item 2 field.** Covered by `tests/test_manifest.py::test_written_manifest_validates_and_records_m0_fields`. It validates with `Draft202012Validator` and asserts that `model_id`, `blender_version`, `machine`, `git_commit`, `seeds` and `timings` are in the schema's `required` list and hold the expected values. `test_run_result_fields_are_recorded` covers the other fields.
- [x] **Frame hashes (criterion reworded per decision 2; the new wording is under Shared-file edits).**
  - `test_frame_file_sha256_matches_shasum` runs `shasum -a 256` on each frame.
  - `test_frame_pixel_sha256_matches_an_independent_decode` hashes a numpy uint8 decode.
  - `test_pixel_hash_ignores_png_metadata_but_file_hash_does_not` uses the same pixels with different `tEXt RenderTime` chunks: `file_sha256` differs and `pixel_sha256` is equal.
- [x] **A 48-frame synthetic set with `every_n=6` yields one PNG with 8 tiles.** Covered by `tests/test_contact_sheet.py::test_48_frames_every_6th_gives_one_sheet_of_8_tiles`. The sheet is 4 columns × 2 rows, and the tile colours are frames 0, 6, …, 42 in order.
- [x] **The schema rejects a manifest missing `model_id`, and a dirty tree is flagged** (from Files/Modules). Covered by `test_schema_rejects_a_manifest_missing_model_id`, `test_invalid_manifest_is_not_written`, `test_collect_git_flags_a_dirty_tree` and `test_collect_git_counts_untracked_files_as_dirty`.
- [x] **`scripts/run_tests.sh` passes** — run bare by the parent on the combined Run 0.4 + 0.5 + 0.6 tree, 2026-10-19: exit 0, all lanes ok (static 16 source files; unit 50 passed; blender 7 passed). At the time of this run it exited 1: environment, locks and static passed, and the unit lane failed only on Run 0.4's in-progress `tests/test_harness_cli.py::test_invalid_arguments_exit_non_zero_with_a_message[missing-scene]` (`TypeError: _argv() got multiple values for argument 'scene'`). I did not edit it, per the parallel-run rules. All 33 of this run's tests pass. **The parent re-runs the gate bare once 0.4 lands.**

### Evidence
`scripts/run_tests.sh` (bare, 2026-10-19). The lane lines plus the exit code, filtered from the full log:
```
=== lane: environment
=== lane: environment — ok
=== lane: locks
=== lane: locks — ok
=== lane: static
=== lane: static — ok
=== lane: unit
=== lane: unit — FAILED; later lanes not run
exit=1
```
The tail of the unit lane (`scripts/run_tests.sh unit`):
```
>           render.main(_argv(scene_script, tmp_path / "out", **overrides))
E           TypeError: _argv() got multiple values for argument 'scene'
tests/test_harness_cli.py:97: TypeError
================== 1 failed, 49 passed, 7 deselected in 1.46s ==================
=== lane: unit — FAILED; later lanes not run
```
`uv run --locked pytest -q tests/test_manifest.py tests/test_contact_sheet.py`:
```
.................................                                        [100%]
33 passed in 1.13s
```
An earlier bare run failed static on the 0.4 files `_inblender.py` (mypy Literal assignments) and `render.py`/`test_harness_cli.py` (attr-defined, E501). Those were all gone on the second run.

## What Changed
- `blender/harness/run_result.py` (new): the frozen dataclasses `FrameRecord`, `Timings`, `RenderDevice` and `RunResult`, as the parent's contract specified. Pure Python, no `bpy`.
- `schemas/manifest.schema.json` (new): Draft 2020-12, `additionalProperties: false` throughout, `schema_version` const 1. The fields are `production_id`, `git_commit`, `git_dirty`, `model_id`, `blender_version`, `blender_build_hash`, `blender_bin`, `machine{label, hardware_model, chip, os, arch}`, `scene`, `seeds{scene}`, `timings{wall_s, render_s}`, `profile`, `engine`, `device{engine_device, gpu_backend, cycles_compute_device_type, cycles_devices}`, `resolution`, `samples`, `frame_count`, `frames[]{index, path, file_sha256, pixel_sha256}`, and `contact_sheet{path, sha256}|null`.
- `blender/harness/manifest.py` (new):
  - `write_manifest(run_result, out_dir, *, contact_sheet) -> Path` validates before it writes.
  - Public helpers: `pixel_sha256`, `file_sha256`, `collect_git`, `collect_machine`, `machine_label`, `validate_manifest`, `MACHINE_LABELS` and `UnknownMachineError`.
  - Frame and contact-sheet paths are recorded relative to `out_dir`; a path outside it raises `ValueError`.
  - `scene` is recorded relative to the repo root when it is inside the repo.
- `blender/harness/contact_sheet.py` (new): `build_contact_sheet(frames, every_n, columns, out_path) -> Path`.
  - Uses Pillow, with tiles at native size in row-major order.
  - Leftover cells in the last row are transparent.
  - Mismatched frame sizes, or `every_n`/`columns` below 1, raise `ValueError`.
- `tests/test_manifest.py` (new, 28 tests) and `tests/test_contact_sheet.py` (new, 5 tests).
- `blender/__init__.py` and `blender/harness/__init__.py`: empty, and identical to 0.4's. Without them, ruff's import sorting treats `blender` as third-party.

Reuse checked: I adapted `blender/probe/api_probe.py:_sysctl`/`_git_commit` (lines 37–47) rather than importing them. ADR-0001 forbids importing the probe, and it imports `bpy` at load time. I did not copy its `platform.node()` hostname. The schema's profile enum test imports `blender.harness.profiles.PROFILES` (0.4's file, already present), so it is not skipped.

## Open Issues
- **The pixel hash's values differ from ADR-0001's quoted numbers.** The probe hashed Blender's float `Image.pixels` buffer; `pixel_sha256` hashes Pillow's 8-bit RGBA bytes. Frames are identified the same way (8-bit → float is a one-to-one mapping), but the hex values are not comparable across the two. 0.7 must compare with `manifest.pixel_sha256` on both sides.
- **`git_dirty` counts untracked files.** Harness output inside the repo must be under a gitignored path (e.g. `productions/*/frames/`), or every manifest will read dirty.
- `pixel_sha256` accepts only RGB/RGBA PNGs. A profile that switches to 16-bit or BW output would raise, by design.
- The schema leaves out skill and style versions, per-stage token use and gate decisions (project-definition §Artifact schemas). They are not needed for M0. Adding them after M1 needs an ADR.
- Something outside this run rewrote `tests/test_contact_sheet.py`'s import order (probably a `ruff --fix` before the `__init__.py` files existed), and modified `tests/conftest.py`. I re-fixed my own file and left `conftest.py` alone. It is not mine; probably 0.4 or 0.6.

## Shared-file edits for the parent to apply
1. **Rollout `:178` Run 0.5:** tick all four criteria once the bare gate passes. Replace criterion 2 with:
   `- [ ] Each frame records file_sha256 (matches \`shasum -a 256\` of the file) and pixel_sha256 (matches an independent decode of the 8-bit RGBA pixels); reproducibility compares pixel_sha256 (ADR-0001).`
   In Files/Modules, `machine {hostname, …}` becomes `machine {label, hardware_model, chip, os, arch}` (no hostname, user decision 2026-10-19).
2. **Rollout Input Gaps `:42`, model-ID bullet:** append `Resolved 2026-10-19 (Run 0.5): confirmed — required \`--model-id\`, fallback env \`AIAL_MODEL_ID\`, fail if neither; fixture renders pass \`fixture/<test-name>\`.`
3. **Carry-forward lines to append:**
```
- [0.5] -> 0.7,quest | contract | write_manifest(run_result, out_dir, *, contact_sheet) and build_contact_sheet(frames, every_n, columns, out_path) in blender/harness/; RunResult lives in run_result.py.
- [0.5] -> 0.7 | contract | Frame identity = blender.harness.manifest.pixel_sha256 (8-bit RGBA via Pillow); compare.py imports it — its values differ from ADR-0001's float-buffer hashes.
- [0.5] -> surface | contract | Machine label comes from MACHINE_LABELS (hw.model -> label) in manifest.py + schema enum; a new Mac fails loudly until both get a row.
- [0.5] -> quest | decision | production_id is p-NNNN or t-<slug>, set by the harness in RunResult; model_id required via --model-id/AIAL_MODEL_ID; fixtures pass fixture/<test-name>.
- [0.5] -> 0.7 | gotcha | git_dirty counts untracked files: render output inside the repo must sit under a gitignored path or every manifest reads dirty.
```
4. **Fold:** the `[0.3] -> 0.5 | decision` machine-label line is consumed. Residue: `~ machine label: hw.model -> label map in blender/harness/manifest.py (decided 0.3, landed 0.5)`.
