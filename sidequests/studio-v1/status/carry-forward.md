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

- [0.4] -> surface | gotcha | Scenes build into bpy.context.scene after the harness strips factory objects; the factory World is kept and sets the background unless build() replaces scene.world.
- [0.4] -> quest | deferred | fps (24) and aspect (16:9 resolutions) live in blender/harness/profiles.py until production.yaml exists; then move them there, profiles keep quality only.
- [0.5] -> surface | gotcha | git_dirty counts untracked files: render output inside the repo must sit under a gitignored path or every manifest reads dirty.
- [0.6] -> surface | gotcha | Blender 5.2 has no Action.fcurves; read keys via bpy_extras.anim_utils.action_get_channelbag_for_slot(action, slot).fcurves.
- [0.7] -> surface | gotcha | EEVEE pixels are machine-specific: same scene+seed differ between M5 Max Laptop and M1 Laptop; compare runs from one machine only (ADR-0001).
- [0.1] -> 5.1 | gotcha | Blender pin moves with .python-version (must equal Blender's bundled Python; doctor FAILs otherwise), Makefile BLENDER_EXPECTED and fake-bpy-module-5.2==20260730.
- [1.1] -> quest | contract | Artifacts go through studio/artifacts.py: load_artifact(path, stem)/write_artifact(obj, path, stem)/validate_artifact(obj, stem) -> ArtifactValidationError(source, errors=[(json_path, msg)]); .yaml/.yml/.json by suffix, duplicate keys refused, host-side only (no yaml/jsonschema in Blender's Python).
- [1.1] -> quest | contract | Shared $defs live in schemas/_defs.schema.json (production_id, hex_color lowercase, seconds, positive_seconds, dimension, style_id, style_ref, module_id, beat_id, shot_id, narration, sound_cues); new schemas $ref them by "_defs.schema.json#/$defs/<name>".
- [1.1] -> 1.3,1.4,1.8 | contract | style params = merge_overrides(style_params(style), bible.overrides.get(dim, {})) then re-validate the merged style as "style"; style_ref <dim>/<name>@<v> -> styles/<dim>/<name>/style.yaml; bible requires all 5 dimension keys (ref or null).
- [1.1] -> 1.5,1.6,1.9 | deferred | Schemas don't check shot/beat id uniqueness, contiguous timing, beat existence or camera vocabulary — validators own these; 1.5 tightens camera style params in style.schema.json (open for non-visual dims) before M1 close.
- [1.1] -> 1.10 | deferred | manifest.schema.json should $ref _defs (production_id, style_ref) and validate_manifest use studio.artifacts; until then equality tests in tests/test_schemas.py (and 1.2's) hold the copies equal.
- [1.2] -> 1.3,1.4,1.7 | contract | Style module = apply(params, scene) in blender/lib/<group>/<name>.py, registered in blender/lib/registry.py MODULES as id -> "module:attr"; params = style minus envelope + bible overrides.
- [1.2] -> 1.9,1.10 | contract | render.py --style-bible <style_bible.json> / run_render(..., style_bible=Path|None) (keyword, no default); manifest records styles {dim: ref} + style_bible {path, sha256}.
- [1.2] -> 1.3,1.4 | gotcha | Style modules run after build() and BEFORE the profile; setting render settings (e.g. Freestyle use_freestyle) is STD-003-banned and may be overwritten — prefer GP v3 line art.
- [1.2] -> 1.9,1.10 | deferred | Bible production_id is not reconciled with the manifest's scene-derived t-<stem> production_id; first production-rendering run decides.

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
~ M1 probe: deferred 0.3, landed 0.7 — ADR-0001 Accepted with both Macs' evidence
~ run_render writes <out>/contact_sheet.png + manifest.json itself — blender/harness/render.py, held by tests/test_render_smoke.py (est. 0.7)
~ reproducibility = blender/harness/compare.py compare_runs / CLI; refuses differing scene/profile/engine/seeds/resolution/samples/styles (est. 0.7, styles added 1.2)
~ Cycles final on Metal is not bit-identical (≤1/255) — never assert Cycles by hash; enforced by compare.py's tolerance policy and recorded in ADR-0001 (est. 0.7)
~ only the 1-frame Cycles determinism check asserts on final-profile pixels in the default lane — docs/test-strategy.md (decided 0.7)
~ the [1.1] params contract line was also routed to 1.2, which consumed it (landed 1.2)
