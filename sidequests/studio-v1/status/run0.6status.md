# Run 0.6: Plain test scene — status

**Quest:** studio-v1 (feature)  **Date:** 2026-10-19  **Status:** COMPLETE

**Spec trace:**
- `sidequests/studio-v1/studio-v1-rollout.md`, `### Run 0.6: Plain test scene` (spec and acceptance criteria).
- `docs/project-definition.md` §M0 Tasks item 5 ("a deliberately plain test scene").
- `docs/adr/0002-python-toolchain-and-layout.md`, "Scene-script contract".
- STD-002, STD-003, STD-004, STD-005 (fixture exemption), STD-007.

**User decisions, 2026-10-19 (at plan approval):**
1. `build(seed)` targets `bpy.context.scene` and assumes it is empty. The harness (Run 0.4) empties the factory scene through `bpy.data`, calls `build`, then sets `frame_start=1` / `frame_end=FRAME_COUNT` and every render setting. It fails if `scene.camera` is unset after build. The factory World is kept.
2. Setting `scene.camera`, keyframing the camera's location and adding the TRACK_TO constraint count as scene content.
3. The three boxes get a seeded xy jitter from `random.Random(seed)`. The amplitude is a named constant with a comment saying why it has that size.

## Acceptance Criteria Checklist

- [x] `grep -n "bpy.ops" tests/scenes/plain_scene.py` returns nothing (exit 1, no output).
- [x] The Blender integration test passes in background mode (`tests/test_plain_scene.py`, 3 tests).
- [x] `scripts/run_tests.sh` passes (all lanes, exit 0).

### Evidence

```
$ grep -n "bpy.ops" tests/scenes/plain_scene.py; echo "grep exit=$?"
grep exit=1
$ scripts/run_tests.sh   # tail; exit 0
=== lane: environment — ok
=== lane: locks
Resolved 25 packages in 5ms
=== lane: locks — ok
=== lane: static
All checks passed!
27 files already formatted
Success: no issues found in 9 source files
=== lane: static — ok
=== lane: unit
collected 8 items / 4 deselected / 4 selected
tests/test_toolchain_pins.py ....                                        [100%]
======================= 4 passed, 4 deselected in 0.02s ========================
=== lane: unit — ok
=== lane: blender
collected 8 items / 4 deselected / 4 selected
tests/test_plain_scene.py ...                                            [ 75%]
tests/test_toolchain_pins.py .                                           [100%]
======================= 4 passed, 4 deselected in 5.32s ========================
=== lane: blender — ok
=== run_tests.sh: all lanes ok (environment locks static unit blender)
```

## What Changed

- `tests/scenes/plain_scene.py` (new): `FRAME_COUNT = 48` and `build(seed)`. Uses `bpy.data` only and builds a floor, three `from_pydata` boxes, one SUN light, and a camera that is set as `scene.camera`. The camera has location keys at frames 1 and 48 and a TRACK_TO constraint aimed at the centre box. The module docstring records the STD-005 fixture exemption.
- `tests/test_plain_scene.py` (new, `@pytest.mark.blender`): starts `blender -b --factory-startup` with a `--python-expr` driver that empties the factory scene, loads the scene file by path and calls `build`, then prints one `PLAIN_SCENE=<json>` line. Asserts:
  - the object types, `FRAME_COUNT == 48`, and that location keys on all 3 axes are at exactly {1, 48};
  - that the render settings and frame range are unchanged by `build`;
  - that the same seed gives identical box locations and a different seed gives different ones.

## How to Test

`scripts/run_tests.sh` (blender lane). No renders in this run.

## Architecture Decisions

The user decisions above. None needs an ADR beyond ADR-0002: decision 1 states what the existing scene-script contract means for the target scene.

## Open Issues

- Blender 5.2 has no `Action.fcurves` (layered actions). The test reads keys through `bpy_extras.anim_utils.action_get_channelbag_for_slot`.
- The camera framing has not been looked at in a frame yet. Run 0.7's contact sheet is the first visual check.

## Shared-file edits for the parent to apply

- **Rollout:** tick Run 0.6's three acceptance criteria in `sidequests/studio-v1/studio-v1-rollout.md`.
- **Carry-forward** (append to the live band):
  - `- [0.6] -> 0.4,0.7 | contract | Scene scripts build into bpy.context.scene, which is empty on entry; the harness sets frame_start=1, frame_end=FRAME_COUNT and all render settings after build.`
  - `- [0.6] -> 0.7 | contract | tests/scenes/plain_scene.py: 6 objects, scene.camera set, location keys at 1 and 48; seed jitters box xy, so a different seed must give different frames.`
  - `- [0.6] -> surface | gotcha | Blender 5.2 has no Action.fcurves; read keys via bpy_extras.anim_utils.action_get_channelbag_for_slot(action, slot).fcurves.`
- **Fold:** the `[0.2] -> 0.4,0.5,0.6` scene-script contract line can lose its `0.6` target, or fold once 0.4 lands.

## Test Counts

Blender lane: 4 passed (3 new). Unit lane: 4 passed (unchanged).

## Confidence Report

- MEASURED: the gate passes and the grep returns nothing (commands and output above).
- INFERRED: the 0.3 m jitter keeps every box in view at any seed. This follows from the geometry; no frame has been rendered to confirm it (Run 0.7).

## Next Unblocked Run

Run 0.7, once 0.4 and 0.5 are done.
