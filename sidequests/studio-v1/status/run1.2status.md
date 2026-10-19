# Run 1.2: Style-module contract and harness style application — status

**Quest:** studio-v1 (feature)  **Date:** 2026-10-19  **Status:** COMPLETE (uncommitted; ran in parallel with Run 1.1 in the same tree).
**Spec trace:** `sidequests/studio-v1/studio-v1-rollout.md:283-299` (Run 1.2), `:238-246` (M1 header); `docs/project-definition.md` §Style library, §Artifact schemas; `docs/glossary.md` "Style", "Style module", "Style bible"; ADR-0002 (scene-script contract, `sys.path`, layout); STD-001, STD-002, STD-003, STD-006, STD-007.

## Acceptance Criteria Checklist
- [x] **Rendering the plain scene with a style bible naming a test module records `styles` in the manifest and calls the module once.** `tests/test_style_registry.py::test_plain_scene_with_noop_bible_records_styles_and_calls_module_once` (blender lane) renders `tests/scenes/plain_scene.py` at the preview profile with a bible whose visual style lists `testing/noop`. It asserts:
  - manifest `styles == {"visual": "visual/fixture-noop@2"}`;
  - `style_bible.sha256` is the bible's hash;
  - the noop log holds exactly one call, whose params are the style minus its envelope;
  - 48 frames were rendered.
- [x] **An unknown module id fails the render before any frame is written.** `test_an_unknown_module_id_fails_before_blender_or_any_frame` (unit): `run_render` raises `HarnessError` naming the id, with `subprocess.run` patched to fail if called and a nonexistent Blender binary, and `<out>/frames` is never created. `test_the_cli_reports_an_unknown_module_id` checks the CLI's exit 1 and stderr message.
- [x] **`scripts/run_tests.sh` passes.** Run bare, exit 0 (output under Test Counts).

## What Changed
- `blender/lib/__init__.py` (new, empty) and `blender/lib/registry.py` (new, no `bpy` import):
  - `MODULES: dict[str, str]` maps module id → lazy `"package.module:attr"` target. It ships empty; 1.3 and 1.4 add rows.
  - `target_for(id)` raises `UnknownStyleModule(ValueError)` for an unregistered id, or for an id that doesn't match the `module_id` pattern it reads from `schemas/_defs.schema.json`.
  - `StyleModule` Protocol: `apply(params: dict[str, Any], scene: bpy.types.Scene) -> None`.
- `blender/harness/render.py`:
  - `--style-bible <path>` (optional; absent means unstyled) and the module constant `STYLES_ROOT`.
  - `resolve_style_plan(bible) -> (styles, plan)` uses Run 1.1's `load_artifact`, `style_params`, `merge_overrides` and `validate_artifact`. It skips null dimensions, refuses overrides for null dimensions, refuses a version or style_id mismatch, and re-validates the merged style.
  - `run_render(..., *, style_bible: Path | None)` is keyword-only with no default. It resolves before `frames/` is created and converts any `ValueError` into `HarnessError`.
  - It writes `style_plan.json` into the temp dir and passes `--style-plan` to Blender.
- `blender/harness/_inblender.py`:
  - `--style-plan` is required (`[]` means unstyled).
  - Every target is imported and checked callable before `build()`.
  - Each `apply(params, scene)` runs once, in plan order, after `build()` and before `_apply_profile`.
- `blender/harness/run_result.py`: `styles: dict[str, str]`, `style_bible: Path | None`.
- `blender/harness/manifest.py` and `schemas/manifest.schema.json`: two new required fields.
  - `styles`: `{dimension: style_ref}`, `{}` without a bible. Its key enum and value pattern are copied from `_defs`, and a test holds them equal.
  - `style_bible`: `{path, sha256} | null`.
- `blender/harness/compare.py`:
  - `styles` was added to the same-render fields.
  - The style bible is compared by `sha256` only, so one bible copied to two paths still compares.
- `tests/style_modules/noop.py` (new, test-only): it appends one JSON line per call to `$AIAL_TEST_NOOP_LOG`. It is never in the shipping `MODULES`; a test holds that.
- `tests/test_style_registry.py` (new: 15 unit tests, 1 blender test).
- Existing tests updated:
  - `tests/test_manifest.py`: fixture fields, plus 3 new tests (no-bible fields, recorded styles and hash, malformed refs).
  - `tests/test_compare.py`: fixture fields, plus refusal cases for styles and bible content, and the same bible at two paths.
  - `tests/test_harness_cli.py`, `tests/test_render_determinism.py`: explicit `style_bible=None`.

## How to Test
- `scripts/run_tests.sh`.
- By hand: `uv run python blender/harness/render.py --scene tests/scenes/plain_scene.py --profile preview --out <tmp> --seed 0 --model-id fixture/manual --style-bible <bible.json>`. The bible must name a style under `styles/` whose modules are registered. None ship yet, so until Run 1.3 only a bible with no modules, or all-null styles, renders this way.

## Architecture Decisions
All were approved by the user from the plan's recommendations:
1. Registry entries are lazy `"module:attr"` strings, so the host rejects unknown ids without Blender.
2. `params` is the whole style minus its envelope keys.
3. Overrides are deep-merged per dimension (objects merge, arrays and scalars replace), then the merged style is re-validated.
4. The manifest gets `styles` plus `style_bible {path, sha256} | null`.
5. `compare.py` refuses runs whose styles or bible content differ.

Implementation choices:
- I reused 1.1's `merge_overrides` and `STYLE_ENVELOPE_KEYS` rather than writing a second copy.
- The test module lives under `tests/`, and the test registers it by monkeypatching `registry.MODULES` and `render.STYLES_ROOT`. The test imports `NOOP_LOG_ENV` through `importlib` because `tests/` is not a package: a static import made mypy see the file under two module names.

## Test Counts
`scripts/run_tests.sh` (bare, exit 0); the full output is in the scratchpad `gate.txt`. Excerpt:
```
=== lane: environment — ok
=== lane: locks — ok
All checks passed!
Success: no issues found in 27 source files
=== lane: static — ok
tests/test_style_registry.py ...............                             [ 97%]
====================== 143 passed, 16 deselected in 1.11s ======================
=== lane: unit — ok
tests/test_style_registry.py .                                           [ 93%]
===================== 16 passed, 143 deselected in 55.95s ======================
=== lane: blender — ok
=== run_tests.sh: all lanes ok (environment locks static unit blender)
```
These counts include Run 1.1's in-progress `tests/test_schemas.py`, which was green at the time.

## Open Issues
- **Freestyle risk for Run 1.3.** A Freestyle line treatment needs `scene.render.use_freestyle` and line-set settings. Those are render settings: STD-003 reserves them to the harness, and `_apply_profile` runs after the style modules. Grease Pencil v3 line art builds as datablocks and avoids this. If 1.3 picks Freestyle, it needs an ADR, or a profile-owned switch the style requests.
- The style bible's `production_id` is not cross-checked against the manifest's scene-derived `production_id`, which is `t-<scene stem>`. The first consumer that renders a production (1.9/1.10) should decide which one wins.
- A style's `status` is not checked: a `retired` or `candidate` style renders. Retired styles live under `styles/retired/`, so a bible ref can't reach them by path.
- `MODULES` is empty until 1.3 and 1.4 register modules.

## Shared-file edits for the parent to apply
**Rollout** (`sidequests/studio-v1/studio-v1-rollout.md`, Run 1.2): tick all three acceptance criteria and mark the run done/COMPLETE in the same form as earlier runs.

**Carry-forward** (`sidequests/studio-v1/status/carry-forward.md`), append to the live band:
```
- [1.2] -> 1.3,1.4,1.7 | contract | Style module = apply(params, scene) in blender/lib/<group>/<name>.py, registered in blender/lib/registry.py MODULES as id -> "module:attr"; params = style minus envelope + bible overrides.
- [1.2] -> 1.9,1.10 | contract | render.py --style-bible <style_bible.json> / run_render(..., style_bible=Path|None) (keyword, no default); manifest records styles {dim: ref} + style_bible {path, sha256}.
- [1.2] -> 1.3,1.4 | gotcha | Style modules run after build() and BEFORE the profile; setting render settings (e.g. Freestyle use_freestyle) is STD-003-banned and may be overwritten — prefer GP v3 line art.
- [1.2] -> 1.9,1.10 | deferred | Bible production_id is not reconciled with the manifest's scene-derived t-<stem> production_id; first production-rendering run decides.
```
