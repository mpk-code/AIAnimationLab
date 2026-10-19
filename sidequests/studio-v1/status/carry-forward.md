# Carry-forward ledger — studio-v1

> Cumulative, machine-loaded channel for routed cross-run handoffs. `/run-process` pre-flight
> prints the entries routed to the run being started; post-flight appends a run's handoffs.
> Format — one routed conclusion per line, ≤5 per run:
>
>     - [<from-run>] -> <targets> | <class> | <one-line conclusion>
>
> <targets>: comma-separated run IDs (no spaces), and/or `surface` (any run, any quest, on this
> surface) / `quest` (any later run here). <class>: contract | gotcha | deferred | decision.
> ROUTING RULE: an entry exists ONLY if addressed to a future audience — un-routed noise stays
> in the status report's Open Issues. See the run-process "Carry-forward ledger" section.

- [0.1] -> 5.1 | gotcha | .python-version must equal Blender's bundled Python (doctor FAILs otherwise): bump Blender pin, .python-version and Makefile BLENDER_EXPECTED together.
- [0.2] -> 5.1 | gotcha | fake-bpy-module-5.2==20260730 (pyproject dev group) moves with the Blender pin, alongside .python-version and BLENDER_EXPECTED.
- [0.2] -> 0.7 | contract | Blender tests take @pytest.mark.blender + the blender_bin fixture (tests/conftest.py); run_tests.sh's blender lane runs them — add no new lane.
- [0.3] -> 0.7 | decision | EEVEE exact pixel sha256; Cycles Metal max abs diff <= 1/255, denoise off, fixed seed, no animated seed. Measured diff 0 on the M5 Max Laptop (ADR-0001).
- [0.3] -> 0.7 | deferred | Rerun blender/probe/api_probe.py on the M1 Laptop; quote its JSON in ADR-0001 and lift it from Provisional (expiry: M0 exit).
- [0.4] -> 0.7 | contract | render.run_render(scene, profile, out, seed, model_id, binary) -> RunResult (blender/harness/run_result.py); CLI needs --scene --profile --out --seed --model-id|AIAL_MODEL_ID.
- [0.4] -> 0.7 | gotcha | render.py refuses a non-empty <out>/frames/ (exit 1): each determinism run needs its own --out dir.
- [0.4] -> surface | gotcha | Scenes build into bpy.context.scene after the harness strips factory objects; the factory World is kept and sets the background unless build() replaces scene.world.
- [0.4] -> quest | deferred | fps (24) and aspect (16:9 resolutions) live in blender/harness/profiles.py until production.yaml exists; then move them there, profiles keep quality only.
- [0.5] -> 0.7,quest | contract | write_manifest(run_result, out_dir, *, contact_sheet) and build_contact_sheet(frames, every_n, columns, out_path) in blender/harness/; RunResult lives in run_result.py.
- [0.5] -> 0.7 | contract | Frame identity = blender.harness.manifest.pixel_sha256 (8-bit RGBA via Pillow); compare.py imports it — its values differ from ADR-0001's float-buffer hashes.
- [0.5] -> 0.7 | gotcha | git_dirty counts untracked files: render output inside the repo must sit under a gitignored path or every manifest reads dirty.
- [0.6] -> 0.7 | contract | tests/scenes/plain_scene.py: 6 objects, scene.camera set, location keys at 1 and 48; seed jitters box xy, so a different seed must give different frames.
- [0.6] -> surface | gotcha | Blender 5.2 has no Action.fcurves; read keys via bpy_extras.anim_utils.action_get_channelbag_for_slot(action, slot).fcurves.

<!-- folded: consumed/resolved residues; pre-flight does not read past here -->
~ uv/Python pins: uv.toml required-version == Makefile UV_VERSION; pyproject requires-python admits .python-version — held by tests/test_toolchain_pins.py (est. 0.1, enforced 0.2)
~ uv ignores [tool.uv] in a pyproject next to uv.toml: uv settings live only in uv.toml — guarded by tests/test_toolchain_pins.py (est. 0.2)
~ scene-script contract build(seed) + FRAME_COUNT, bpy.data only, into bpy.context.scene — ADR-0002; implemented by blender/harness/_inblender.py and tests/scenes/plain_scene.py (est. 0.2, landed 0.4/0.6)
~ engine IDs BLENDER_EEVEE / BLENDER_WORKBENCH / CYCLES and Cycles GPU via METAL live in blender/harness/profiles.py and _inblender.py (est. 0.3, landed 0.4)
~ Cycles GPU/METAL set and asserted by blender/harness/_inblender.py _enable_metal_devices; test_final_renders_on_cycles_with_the_metal_gpu (est. 0.3, enforced 0.4)
~ Cycles-only background render leaves gpu uninitialised (gpu.platform raises SystemError until gpu.init()) — handled in blender/harness/_inblender.py _gpu_backend (est. 0.4)
~ PNG bytes differ every render (tEXt Date/RenderTime): frame identity is the decoded-pixel hash — manifest.pixel_sha256, held by tests/test_manifest.py (est. 0.3, enforced 0.5)
~ machine label: hw.model -> label map MACHINE_LABELS in blender/harness/manifest.py + schema enum, held equal by tests/test_manifest.py (decided 0.3, landed 0.5)
~ production_id p-NNNN | t-<slug>, set by the harness in RunResult; model_id required via --model-id/AIAL_MODEL_ID, fixtures pass fixture/<test-name> (decided 0.5)
