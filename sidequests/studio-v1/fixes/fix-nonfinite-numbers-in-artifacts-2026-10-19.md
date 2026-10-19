# Fix: Non-finite numbers (NaN, +inf) pass artifact validation and get written
**Date:** 2026-10-19
**Issue:** unmanaged
**Lane:** code
**Source review:** none — freestanding (found in Run 1.1, `sidequests/studio-v1/status/run1.1status.md` Open Issues)
**Requirements trace:** STD-006 "validated against `schemas/` on write and on read. Times are seconds (float)" (`docs/coding-standards.md:31`); §Artifact schemas "Times are in seconds" (`docs/project-definition.md:186`); Run 1.1 acceptance "each negative fixture … fails with a named path" (`sidequests/studio-v1/studio-v1-rollout.md`, Run 1.1)
**Architecture trace:** none — a code guard in `studio/artifacts.py` and one serializer flag in `blender/harness/manifest.py`; no schema, harness CLI, manifest field or doctrine change (ADR-0002 layout, `docs/adr/0002-python-toolchain-and-layout.md`, unchanged)
**Reuse checked:** `studio/artifacts.py:140` already writes JSON with `allow_nan=False` (the JSON half of write was guarded, the validator was not); `ArtifactValidationError` (`studio/artifacts.py:31`) carries `(json_path, message)` pairs in the form the guard reports; no existing finiteness helper in the repo (`git grep -n -E 'isfinite|allow_nan' -- '*.py'`)
**Root Cause:** `jsonschema` (4.26.0) treats NaN and ±inf as valid `number` instances, and every comparison with NaN is false, so `minimum`/`exclusiveMinimum` never fire for NaN and are satisfied by +inf. `validate_artifact` relies only on the schema, YAML's safe loader resolves `.nan`/`.inf`, and `json.loads` accepts the non-standard `NaN`/`Infinity` tokens, so a non-finite value passes load, validate and YAML write.
**Status:** COMPLETE  **Completed:** 2026-10-19

## Hypotheses
No initial hypothesis (unmanaged defect). Root cause confirmed by reproduction:
- `Draft202012Validator({"type":"number","exclusiveMinimum":0})` reports no error for `nan` or `inf`; `nan > 0` and `nan <= 0` are both False (jsonschema 4.26.0).
- A `beats` fixture with `duration_s` set to nan / +inf passes `validate_artifact`; `write_artifact` to `.yaml` writes `duration_s: .nan` / `.inf`; `.json` refuses (allow_nan=False); -inf is rejected by the minimum. Loading YAML `.nan` returns nan; `json.loads` accepts a `NaN` token.

## Scope of Change
- Files to modify: `studio/artifacts.py` (finiteness check inside `validate_artifact`, so load, write and every caller's re-validation — `blender/harness/render.py` style resolution — get it); `blender/harness/manifest.py` (`json.dumps(..., allow_nan=False)` in `write_manifest`).
- Schemas / artifact formats / harness interface to update: none.
- Specs to rewrite or annotate: none (STD-006 already requires the behaviour).
- Tests to write (TDD — first): in `tests/test_schemas.py` and `tests/test_manifest.py`.

## Test-Driven Approach
*(Planned names; the tests as written are listed under Test Results.)*
1. A beats doc with `duration_s` non-finite (nan, inf, -inf) raises `ArtifactValidationError` naming `$.beats[0].duration_s`.
2. A style with an open (non-visual) param holding nan is rejected (the guard is schema-independent).
3. `.nan` in YAML and a `NaN` token in JSON both fail to load, naming the path.
4. A YAML write of a nan doc raises and leaves an existing file byte-identical, with no new file.
5. `write_manifest` refuses a non-finite timing and writes no `manifest.json`.

## Fix Steps
1. Write the failing tests above; run them and confirm they fail for the right reason (accepted / file written).
2. Add a private walker in `studio/artifacts.py` that yields `(json_path, message)` for every float that is not `math.isfinite`, in the same `$.a[0].b` path form jsonschema uses; merge its errors into `validate_artifact`'s sorted list.
3. Add `allow_nan=False` to `write_manifest`'s `json.dumps`.
4. Confirm the new tests pass; run `scripts/run_tests.sh` bare.

## Regression Test Plan
- `scripts/run_tests.sh` (all lanes): schema fixtures, style resolution (`tests/test_style_registry.py`), manifest, smoke and determinism renders — real renders produce finite timings and params, so nothing should change.

## Interface Changes
`validate_artifact`/`load_artifact`/`write_artifact` now also reject non-finite numbers (error message "`<value>` is not a finite number"). `write_manifest` raises `ValueError` on a non-finite value instead of writing an invalid-JSON manifest.

## Render Changes (if applicable)
None.

## Risks
- A legitimate use of infinity (e.g. "no limit") would now be refused. None exists; such a value should be `null` with a schema saying so.

## Deferred Work
- not a defect: `validate_manifest` still uses its own validator rather than `studio.artifacts` (already routed: ledger `[1.1] -> 1.10 | deferred`); the `allow_nan=False` here covers the non-finite case for the manifest until then.

## Refactoring recommendation (Step 5b)
**Option B(a) — no refactor needed.** The guard is one private function plus a merge in an existing function; the manifest change is one keyword. `validate_manifest`'s separate validator is already tracked for Run 1.10.

## Completion Summary
### Changes Made
- `studio/artifacts.py`: new `_non_json_values` walker merged into `validate_artifact`'s sorted errors — flags every float that is not `math.isfinite` and (after review finding 1) every non-`str` mapping key; `_json_path` + `_PLAIN_KEY` format its paths with jsonschema's own `json_path` rule (after review finding 2). `ArtifactValidationError`'s message now says "validation error(s)", since not every error is a schema error.
- `blender/harness/manifest.py`: `write_manifest` serializes with `allow_nan=False`.
- `tests/test_schemas.py`: 11 new test cases; `tests/test_manifest.py`: 1 new test.

### Landed verification
`git grep --untracked -n -E 'def _non_json_values|is not a finite number"|allow_nan=False\) \+' -- studio blender tests`:
- `studio/artifacts.py:87` `def _non_json_values(...)`; `studio/artifacts.py:93` the "is not a finite number" message
- `blender/harness/manifest.py:199` `json.dumps(doc, indent=2, sort_keys=True, allow_nan=False)`
- `tests/test_schemas.py:204, :212, :221, :222, :245, :256` assertions on the guard's message

### Root Cause (confirmed)
As stated in the header: jsonschema 4.26.0 accepts NaN and ±inf as `number`, and NaN defeats every comparison keyword; nothing else in `studio/artifacts.py` checked finiteness. The review added a second gap with the same cause (JSON Schema cannot express it): YAML mapping keys that are not strings (`.nan: 1`, `1: x`, `true: x`) passed in open style params and would be coerced, and could collide, in `json.dumps`.

### Test Results
- Red first: 7 of 9 initial cases failed with "DID NOT RAISE" before the fix; the 2 that passed were `-inf` (already caught by `exclusiveMinimum`) and the pre-existing JSON-write test.
- New tests (green after the fix): `test_validate_rejects_a_non_finite_number_naming_its_path[nan|inf|-inf]` (asserting the guard's own message, so `-inf` can only pass through the guard), `test_a_non_finite_number_in_an_open_style_param_is_rejected`, `test_guard_paths_use_jsonschemas_form_for_non_identifier_keys`, `test_a_non_string_yaml_key_is_rejected[.nan|1|true]`, `test_load_rejects_non_finite_numbers[.yaml|.json]`, `test_write_refuses_a_non_finite_number_in_yaml_and_leaves_files_alone`, `tests/test_manifest.py::test_a_non_finite_timing_is_refused_and_not_written`.
- Final `scripts/run_tests.sh` (bare, exit 0): environment, locks, static ok (mypy 27 source files); unit `155 passed, 16 deselected`; blender `16 passed, 155 deselected in 44.40s`. No render output changed.

### Adversarial review outcome
Separate subagent; its own bare gate run exit 0.
- 🔴 HIGH: none.
- 🟡 MEDIUM 1 — non-finite / non-string mapping keys still passed in open params and would be coerced by `json.dumps` in `render.py`'s style plan: **resolved** (walker rejects non-`str` keys; `test_a_non_string_yaml_key_is_rejected`).
- 🟡 MEDIUM 2 — comment and plan claimed jsonschema's `json_path` form, false for non-identifier keys (STD-007 G1): **resolved** (paths built with jsonschema's rule; `test_guard_paths_use_jsonschemas_form_for_non_identifier_keys`).
- 🟢 3 — a NaN timing from Blender makes `write_manifest` raise an uncaught `ValueError` after frames exist (same as an existing `jsonschema.ValidationError` there): not a defect: `perf_counter` timings are finite; `render.main`'s exception handling is pre-existing and unchanged; noted.
- 🟢 4 — tests asserted only the path, so `-inf` passed without the fix: **resolved** (assert the guard's message).
- 🟢 5 — JSON load input built by brittle text replacement: **resolved** (mutate the dict, then `json.dumps`/`yaml.safe_dump`, which emit `NaN`/`.nan` by default).
- 🟢 6 — `match=` tied to CPython's full message: **resolved** (`match="not JSON compliant"`).
- 🟢 7 — test comment repeated the guard's rationale: **resolved** (replaced by a one-line note on why the message is asserted).
- 🟢 8 — `np.float32`, `Decimal`, sets not walked: not a defect: no loader produces them; `write_artifact`'s serializers refuse them.
- 🟢 9 — "schema error(s)" wording: **resolved** ("validation error(s)").
- 🟢 10 — plan status/test names; keep the NaN hunk apart from Run 1.2's in the commit: **resolved** (this summary); commit grouping noted for `/commit`.

### Refactoring Decision
- Option B(a): No refactor — one private walker and path helper plus one serializer flag; `validate_manifest`'s separate validator is already routed to Run 1.10.

### Risks Realized
None. ("Infinity as no-limit" does not occur in any schema or fixture.)

### Future Work Deferred
- not a defect: `validate_manifest` still uses its own validator (routed: ledger `[1.1] -> 1.10 | deferred`).
- not a defect: `render.main` does not catch `ValueError`/`jsonschema.ValidationError` from `write_manifest` (pre-existing; a finite-timing render cannot reach it).

### Mode
- freestanding
