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
- [0.3] -> 0.7 | deferred | Rerun blender/probe/api_probe.py on the M1 Laptop; quote its JSON in ADR-0001 and lift it from Provisional (expiry: M0 exit).
- [0.4] -> surface | gotcha | Scenes build into bpy.context.scene after the harness strips factory objects; the factory World is kept and sets the background unless build() replaces scene.world.
- [0.4] -> quest | deferred | fps (24) and aspect (16:9 resolutions) live in blender/harness/profiles.py until production.yaml exists; then move them there, profiles keep quality only.
- [0.5] -> surface | gotcha | git_dirty counts untracked files: render output inside the repo must sit under a gitignored path or every manifest reads dirty.
- [0.6] -> surface | gotcha | Blender 5.2 has no Action.fcurves; read keys via bpy_extras.anim_utils.action_get_channelbag_for_slot(action, slot).fcurves.
- [0.7] -> quest | contract | render.run_render itself writes <out>/contact_sheet.png and <out>/manifest.json; callers never call write_manifest/build_contact_sheet directly.
- [0.7] -> quest | contract | Reproducibility = blender/harness/compare.py compare_runs(out_a, out_b) or its CLI (JSON, exit 0 = match); refuses runs differing in scene/profile/engine/seeds/resolution/samples.
- [0.7] -> surface | gotcha | Cycles final on Metal is not bit-identical: a same-seed 1080p frame differed by 1/255 in 73 px (M5 Max). Never assert Cycles by hash; use compare.py.
- [0.7] -> quest | decision | Only the 1-frame Cycles determinism check asserts on final-profile pixels in the default lane (docs/test-strategy.md); other pixel assertions use preview.

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
~ Blender tests: @pytest.mark.blender + blender_bin fixture (tests/conftest.py), run by run_tests.sh's blender lane — no new lane (est. 0.2, used 0.4–0.7)
~ EEVEE exact pixel hash, Cycles Metal <= 1/255 (denoise off, fixed seed): compare.py _TOLERANCE_BY_ENGINE (decided 0.3 ADR-0001, landed 0.7)
~ run_render(scene, profile, out, seed, model_id, binary) -> RunResult lives in blender/harness/render.py (est. 0.4, consumed 0.7)
~ render.py refuses a non-empty <out>/frames/ (exit 1): every render needs its own --out — held by test_harness_cli::test_a_non_empty_frames_dir_is_refused (est. 0.4)
~ write_manifest / build_contact_sheet wired inside run_render (est. 0.5, landed 0.7)
~ frame identity = manifest.pixel_sha256 over manifest.load_rgba (8-bit RGBA, Pillow); compare.py decodes with the same load_rgba; values differ from ADR-0001's float-buffer hashes (est. 0.5, landed 0.7)
~ plain_scene: 48 frames, seed jitters boxes so another seed changes every frame — held by test_render_determinism::test_eevee_a_different_seed_changes_the_frames (est. 0.6, used 0.7)
