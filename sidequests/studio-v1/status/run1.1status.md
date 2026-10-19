# Run 1.1: Artifact schemas and schema IO — status

**Quest:** studio-v1 (feature)  **Date:** 2026-10-19  **Status:** COMPLETE
**Spec trace:**
- `sidequests/studio-v1/studio-v1-rollout.md:265` (Run 1.1), `:45` (Input Gaps, early beats schema)
- `docs/project-definition.md:58` (§Scope, audio-ready), `:204` (style.yaml example), `:218` (style_bible.json), `:220` (shots.yaml example), `:328` (narration lead/follow, left open)
- `docs/coding-standards.md:9` (STD-001), `:29` (STD-006)
- `docs/glossary.md:11` (Beat), `:14` (Style bible)
- `docs/adr/README.md:5` (schema changes after M1 need an ADR)
- `schemas/manifest.schema.json` `properties.production_id` (the pattern `_defs` copies)

Decisions 1a–9a from the Phase 1 plan were approved by the user, along with the contract reconciled with Run 1.2 (parent message).

## Acceptance Criteria Checklist
- [x] The project definition's `style.yaml` and `shots.yaml` examples validate.
  - Evidence: `test_valid_fixture_loads[style/project_definition_example]` and `[shots/project_definition_example]`.
  - The fixtures are the sketches plus their envelope fields (see the proposed change below).
- [x] Each negative fixture fails, and its error names the path:
  - bad hex: `$.palette[1]`
  - missing `schema_version`, ×4 schemas: `$`
  - negative duration: `$.shots[0].duration_s` and `$.beats[0].duration_s`
  - 24 invalid fixtures in all, mapped to their paths in `EXPECTED_FAILURES`.
  - Evidence: `test_invalid_fixture_fails_naming_the_path[*]`. `test_every_invalid_fixture_has_an_expected_failure` holds that table and the fixture files equal.
- [x] `write_artifact` refuses an invalid object and writes nothing.
  - Evidence: `test_write_refuses_an_invalid_object_and_writes_nothing` (a new path stays missing and no temp file is left).
  - Also `test_write_refusal_leaves_an_existing_file_untouched` (the bytes are unchanged) and `test_write_refuses_a_non_finite_number_in_json_and_writes_nothing`.
- [x] `scripts/run_tests.sh` passes, run bare. Output is under Test Counts.

## What Changed
- `schemas/_defs.schema.json`: new. Shared `$defs`:
  - envelope: `schema_version`, `production_id`
  - values: `hex_color` (lowercase), `seconds`, `positive_seconds`
  - style identity: `dimension`, `style_id`, `style_ref`, `module_id`
  - ids: `beat_id`, `shot_id`
  - audio: `narration`, `sound_cues`
- `schemas/style.schema.json`: new.
  - Envelope: `schema_version`, `style_id`, `version`, `status`, `modules`.
  - Parameters sit at top level.
  - Visual parameters are strict: `palette` (required), `shading`, `line`, `lighting`, `forbidden`. Other dimensions stay open.
- `schemas/style_bible.schema.json`: new.
  - All five dimension keys are required. Each is a style_ref pinned to its own dimension, or null.
  - `overrides` is keyed by dimension.
- `schemas/shots.schema.json`: new. Every field from the sketch, all required, with `narration` and `sound_cues` nullable or empty.
- `schemas/beats.schema.json`: new. Fields: `id`, `start_s`, `duration_s`, `change`, `narration`, `sound_cues`.
- `studio/__init__.py`: new package (ADR-0002 layout).
- `studio/artifacts.py`: new.
  - `validate_artifact`, `load_artifact`, `write_artifact` (atomic: temp file plus `os.replace`), `ArtifactValidationError(source, errors)`.
  - Loaders: a safe YAML loader and a JSON loader, both rejecting duplicate keys.
  - Style helpers: `STYLE_ENVELOPE_KEYS` (taken from the schema's top-level `properties`), `style_params`, `merge_overrides`.
- `tests/test_schemas.py`: new, 59 tests.
- `tests/fixtures/schemas/<schema>/{valid,invalid}/`: new. 9 valid and 24 invalid fixtures.
- `pyproject.toml`, `uv.lock`: `referencing>=0.37` added as a direct dependency and relocked (parent-approved).

## How to Test
`scripts/run_tests.sh`. To run only this run's tests while iterating: `uv run --locked pytest tests/test_schemas.py`.

## Architecture Decisions
**Contract for Run 1.2 and every later stage.**
- **Schema names and loading:**
  - A schema is named by its file stem: `load_artifact(path, "style_bible")`.
  - `_defs` and unknown names are refused.
  - `$ref`s resolve through one `referencing.Registry`, built from every `schemas/*.schema.json` and keyed by `$id`.
- **Style params and overrides** (the reconciled contract):
  - `params = merge_overrides(style_params(style), bible["overrides"].get(dimension, {}))`.
  - Objects merge recursively; arrays and scalars replace.
  - The caller then re-validates `{**envelope, **params}` against `"style"`. `test_a_merged_style_that_breaks_the_schema_is_caught_by_revalidation` shows that this catches a bad override.
  - I provided `STYLE_ENVELOPE_KEYS`, `style_params` and `merge_overrides` as the parent allowed, so Run 1.2 should call them rather than write its own merge.
- **The visual definition repeats the envelope.** `unevaluatedProperties` inside a `$ref` cannot see the root's `properties`, so `$defs.visual` lists the envelope keys again as `true`. `test_visual_params_admit_exactly_the_style_envelope` holds the two lists equal.
- **Dimension names repeat across schemas.** They appear in the `_defs` enum, the `style_id`/`style_ref` patterns and the bible's keys. `test_dimension_names_agree_across_defs_and_style_bible` holds them equal.
- **The production_id pattern is copied, not referenced.** It is held equal to the manifest's by `test_production_id_pattern_equals_the_manifest_schemas` until the manifest `$ref`s `_defs`.

**Not ADR candidates now**: these come before M1 closes. After M1, any change to these schemas needs an ADR.

**Proposed change to `docs/project-definition.md`, for `/sidequest` close or the M1 close** (decisions 1a and 5a). I have not edited the file. *(2026-10-19: applied by the parent after the user confirmed the shown diff, together with a §Artifact schemas wording change: every artifact carries `schema_version`, every stage artifact also `production_id` — a style is a library asset.)*
- §Artifact schemas, `style.yaml` example: add `schema_version: 1`.
- §Artifact schemas, `shots.yaml` example: add `schema_version: 1` and `production_id: p-0001`. As written, the sketches do not validate under STD-006.
- §Scope (line 58), "optional narration-line and sound-cue fields": change to "narration-line and sound-cue fields (`narration: null`, `sound_cues: []` when unused)". Both fields are now required but may be null or empty, so nothing is silently left out.

## Open Issues
- not a defect: YAML writing still accepts non-finite numbers (`.inf`/`.nan`). JSON writing refuses them with `allow_nan=False`. A `minimum` does not reject NaN in jsonschema. Candidate fix: a finite-number check in `validate_artifact` if a stage ever computes times.
- not a defect: unique ids, contiguous timing and whether a referenced beat exists are outside what JSON Schema can check. They belong to validators (1.5 for shots), as stated in the schemas' descriptions.
- not a defect: the parameters of the non-visual dimensions are open by design (decision 8a). 1.5 should tighten camera before M1 closes.

## Carry-forward
None appended by this run; the parent applies them (see below).

## Shared-file edits for the parent to apply
1. **Rollout:** in `sidequests/studio-v1/studio-v1-rollout.md` Run 1.1, tick the three acceptance-criteria boxes (`- [ ]` → `- [x]`).
2. **`sidequests/studio-v1/status/carry-forward.md`**: append these lines:
```
- [1.1] -> quest | contract | Artifacts go through studio/artifacts.py: load_artifact(path, stem)/write_artifact(obj, path, stem)/validate_artifact(obj, stem) -> ArtifactValidationError(source, errors=[(json_path, msg)]); .yaml/.yml/.json by suffix, duplicate keys refused, host-side only (no yaml/jsonschema in Blender's Python).
- [1.1] -> quest | contract | Shared $defs live in schemas/_defs.schema.json (production_id, hex_color lowercase, seconds, positive_seconds, dimension, style_id, style_ref, module_id, beat_id, shot_id, narration, sound_cues); new schemas $ref them by "_defs.schema.json#/$defs/<name>".
- [1.1] -> 1.2,1.3,1.4,1.8 | contract | style params = merge_overrides(style_params(style), bible.overrides.get(dim, {})) then re-validate the merged style as "style"; style_ref <dim>/<name>@<v> -> styles/<dim>/<name>/style.yaml; bible requires all 5 dimension keys (ref or null).
- [1.1] -> 1.5,1.6,1.9 | deferred | Schemas don't check shot/beat id uniqueness, contiguous timing, beat existence or camera vocabulary — validators own these; 1.5 tightens camera style params in style.schema.json (open for non-visual dims) before M1 close.
- [1.1] -> 1.10 | deferred | manifest.schema.json should $ref _defs (production_id, style_ref) and validate_manifest use studio.artifacts; until then equality tests in tests/test_schemas.py (and 1.2's) hold the copies equal.
```

## Test Counts
`scripts/run_tests.sh`, run bare. All lanes passed:

```
=== lane: static — ok          (ruff check, ruff format --check: 49 files; mypy: 27 source files)
tests/test_schemas.py .................................................. [ 80%]
.........                                                                [ 86%]
====================== 143 passed, 16 deselected in 0.76s ======================
=== lane: unit — ok
===================== 16 passed, 143 deselected in 44.17s ======================
=== lane: blender — ok
=== run_tests.sh: all lanes ok (environment locks static unit blender)
```
This run adds 59 tests, all in `tests/test_schemas.py`. The totals include Run 1.2's in-progress tests, which were in the tree at the time and passed.

## Confidence Report
A. **Assumptions:**
- `t-<slug>` production ids are valid for every artifact, as in the manifest.
- `shading.model` and the `forbidden` entries are free strings until 1.3 and 1.4 settle a vocabulary.
- `line.weight_px` and `ramp_steps` are optional within their groups; only `palette` is required for a visual style.

B. **Deviations:** the fixtures are the sketches plus their envelope fields (decision 1a).

C. **Thin context:** what camera, motion and storytelling parameters look like. That is deferred to their first authors.

D. **Conflicts:**
- The AC's "examples validate" conflicted with STD-006. Resolved by decision 1a.
- §Scope's word "optional" conflicted with decision 5a. Resolved by the proposed change above.

E. **Complexity:** `style.schema.json` uses `if`/`then` with `unevaluatedProperties`, which is the least obvious construct here. The comment in `test_visual_params_admit_exactly_the_style_envelope` explains it, and that test holds it.

## Next Unblocked Run
- 1.5 and 1.6 (they need 1.1 only).
- 1.8 (it needs 1.1).
- 1.3 and 1.4, once 1.2 closes.
