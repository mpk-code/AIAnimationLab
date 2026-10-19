"""Artifact schemas in `schemas/` and their IO through `studio.artifacts` (Run 1.1, STD-006).

Fixtures live in `tests/fixtures/schemas/<schema>/{valid,invalid}/`; the directory name is the
schema stem each fixture is loaded against.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest
import yaml

from studio.artifacts import (
    SCHEMAS_DIR,
    STYLE_ENVELOPE_KEYS,
    ArtifactValidationError,
    load_artifact,
    merge_overrides,
    style_params,
    validate_artifact,
    write_artifact,
)

FIXTURES = Path(__file__).parent / "fixtures" / "schemas"
ARTIFACT_SCHEMAS = ("style", "style_bible", "shots", "beats")

# Each invalid fixture -> the json_path its error must name, and a fragment of the message.
EXPECTED_FAILURES: dict[str, tuple[str, str]] = {
    "style/bad_hex": ("$.palette[1]", "#E85D3"),
    "style/missing_schema_version": ("$", "'schema_version' is a required property"),
    "style/unknown_visual_param": ("$", "'grain' was unexpected"),
    "style/bad_module_id": ("$.modules[0]", "toon_ramp"),
    "style/duplicate_module": ("$.modules", "non-unique"),
    "style/bad_status": ("$.status", "draft"),
    "style/unknown_dimension": ("$.style_id", "sound/hum"),
    "style_bible/missing_schema_version": ("$", "'schema_version' is a required property"),
    "style_bible/ref_without_version": ("$.styles.visual", "visual/cut-paper"),
    "style_bible/ref_in_wrong_dimension": ("$.styles.visual", "camera/fixture-open@2"),
    "style_bible/missing_dimension": ("$.styles", "'motion' is a required property"),
    "style_bible/unknown_override_dimension": ("$.overrides", "lighting"),
    "style_bible/bad_production_id": ("$.production_id", "p-1"),
    "shots/missing_schema_version": ("$", "'schema_version' is a required property"),
    "shots/negative_duration": ("$.shots[0].duration_s", "-2.5"),
    "shots/zero_duration": ("$.shots[0].duration_s", "less than or equal to the minimum of 0"),
    "shots/missing_narration": ("$.shots[0]", "'narration' is a required property"),
    "shots/negative_cue_offset": ("$.shots[0].sound_cues[0].offset_s", "-0.1"),
    "shots/empty_shots": ("$.shots", "should be non-empty"),
    "beats/missing_schema_version": ("$", "'schema_version' is a required property"),
    "beats/negative_duration": ("$.beats[0].duration_s", "-1.0"),
    "beats/negative_start": ("$.beats[0].start_s", "-0.5"),
    "beats/bad_beat_id": ("$.beats[0].id", "beat1"),
    "beats/empty_change": ("$.beats[0].change", "non-empty"),
}


def _fixtures(kind: str) -> list[Path]:
    return sorted(p for p in FIXTURES.glob(f"*/{kind}/*") if p.suffix in {".yaml", ".json"})


def _key(path: Path) -> str:
    return f"{path.parent.parent.name}/{path.stem}"


def _schema(name: str) -> dict[str, Any]:
    result: dict[str, Any] = json.loads((SCHEMAS_DIR / f"{name}.schema.json").read_text())
    return result


def _valid_shots() -> dict[str, Any]:
    return load_artifact(FIXTURES / "shots" / "valid" / "with_audio_fields.yaml", "shots")


# --- the schemas themselves ---------------------------------------------------------------------


@pytest.mark.parametrize("path", sorted(SCHEMAS_DIR.glob("*.schema.json")), ids=lambda p: p.name)
def test_schema_is_valid_draft_2020_12_with_id_equal_to_its_filename(path: Path) -> None:
    schema = json.loads(path.read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    assert schema["$id"] == path.name


def test_production_id_pattern_equals_the_manifest_schemas() -> None:
    # Held by this test until manifest.schema.json $refs _defs (carry-forward, Run 1.1).
    defs = _schema("_defs")["$defs"]["production_id"]["pattern"]
    assert _schema("manifest")["properties"]["production_id"]["pattern"] == defs


def test_dimension_names_agree_across_defs_and_style_bible() -> None:
    defs = _schema("_defs")["$defs"]
    dimensions = defs["dimension"]["enum"]
    alternation = "(" + "|".join(dimensions) + ")/"
    assert defs["style_id"]["pattern"].startswith("^" + alternation)
    assert defs["style_ref"]["pattern"].startswith("^" + alternation)
    styles = _schema("style_bible")["properties"]["styles"]
    assert styles["required"] == dimensions
    assert list(styles["properties"]) == dimensions
    for dimension, slot in styles["properties"].items():
        assert slot["oneOf"][1]["pattern"] == f"^{dimension}/"


def test_visual_params_admit_exactly_the_style_envelope() -> None:
    # unevaluatedProperties inside a $ref cannot see the root's properties, so the visual
    # definition lists the envelope keys again; this holds the two lists equal.
    visual = _schema("style")["$defs"]["visual"]["properties"]
    admitted = {key for key, sub in visual.items() if sub is True}
    assert admitted == STYLE_ENVELOPE_KEYS
    assert set(_schema("style")["required"]) == STYLE_ENVELOPE_KEYS


# --- fixtures -----------------------------------------------------------------------------------


def test_every_artifact_schema_has_valid_and_invalid_fixtures() -> None:
    for kind in ("valid", "invalid"):
        assert {p.parent.parent.name for p in _fixtures(kind)} == set(ARTIFACT_SCHEMAS)


@pytest.mark.parametrize("path", _fixtures("valid"), ids=_key)
def test_valid_fixture_loads(path: Path) -> None:
    doc = load_artifact(path, path.parent.parent.name)
    assert doc["schema_version"] == 1


def test_every_invalid_fixture_has_an_expected_failure() -> None:
    assert {_key(p) for p in _fixtures("invalid")} == set(EXPECTED_FAILURES)


@pytest.mark.parametrize("path", _fixtures("invalid"), ids=_key)
def test_invalid_fixture_fails_naming_the_path(path: Path) -> None:
    json_path, fragment = EXPECTED_FAILURES[_key(path)]
    with pytest.raises(ArtifactValidationError) as caught:
        load_artifact(path, path.parent.parent.name)
    assert caught.value.source == path
    assert any(p == json_path and fragment in m for p, m in caught.value.errors), (
        caught.value.errors
    )
    assert json_path in str(caught.value)


# --- load_artifact / write_artifact -------------------------------------------------------------


@pytest.mark.parametrize("suffix", [".yaml", ".yml", ".json"])
def test_write_then_load_round_trips(tmp_path: Path, suffix: str) -> None:
    doc = _valid_shots()
    target = tmp_path / f"shots{suffix}"
    write_artifact(doc, target, "shots")
    assert load_artifact(target, "shots") == doc
    assert [p.name for p in tmp_path.iterdir()] == [target.name]


def test_write_refuses_an_invalid_object_and_writes_nothing(tmp_path: Path) -> None:
    doc = _valid_shots()
    doc["shots"][0]["duration_s"] = -1.0
    target = tmp_path / "shots.yaml"
    with pytest.raises(ArtifactValidationError) as caught:
        write_artifact(doc, target, "shots")
    assert ("$.shots[0].duration_s", "-1.0 is less than or equal to the minimum of 0") in (
        caught.value.errors
    )
    assert list(tmp_path.iterdir()) == []


def test_write_refusal_leaves_an_existing_file_untouched(tmp_path: Path) -> None:
    target = tmp_path / "shots.json"
    write_artifact(_valid_shots(), target, "shots")
    before = target.read_bytes()
    bad = _valid_shots()
    del bad["schema_version"]
    with pytest.raises(ArtifactValidationError):
        write_artifact(bad, target, "shots")
    assert target.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == [target.name]


def test_write_refuses_a_non_finite_number_in_json_and_writes_nothing(tmp_path: Path) -> None:
    doc = _valid_shots()
    doc["shots"][0]["lens_mm"] = float("inf")
    with pytest.raises(ValueError):
        write_artifact(doc, tmp_path / "shots.json", "shots")
    assert list(tmp_path.iterdir()) == []


def _beats() -> dict[str, Any]:
    return load_artifact(FIXTURES / "beats" / "valid" / "two_beats.yaml", "beats")


def _open_style() -> dict[str, Any]:
    return load_artifact(FIXTURES / "style" / "valid" / "camera_open_params.yaml", "style")


# The guard's own message, so each case can only pass because of it (`minimum` alone catches -inf).
@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")], ids=str)
def test_validate_rejects_a_non_finite_number_naming_its_path(value: float) -> None:
    doc = _beats()
    doc["beats"][0]["duration_s"] = value
    with pytest.raises(ArtifactValidationError) as caught:
        validate_artifact(doc, "beats")
    assert ("$.beats[0].duration_s", f"{value!r} is not a finite number") in caught.value.errors


def test_a_non_finite_number_in_an_open_style_param_is_rejected() -> None:
    style = _open_style()
    style["average_shot_length_s"] = float("nan")
    with pytest.raises(ArtifactValidationError) as caught:
        validate_artifact(style, "style")
    assert caught.value.errors == [("$.average_shot_length_s", "nan is not a finite number")]


def test_guard_paths_use_jsonschemas_form_for_non_identifier_keys() -> None:
    style = _open_style()
    style["shot rules"] = {"a.b": [1.0, float("inf")], "it's": float("nan")}
    with pytest.raises(ArtifactValidationError) as caught:
        validate_artifact(style, "style")
    assert caught.value.errors == [
        ("$['shot rules']['a.b'][1]", "inf is not a finite number"),
        ("$['shot rules']['it\\'s']", "nan is not a finite number"),
    ]


@pytest.mark.parametrize("key", [".nan", "1", "true"])
def test_a_non_string_yaml_key_is_rejected(tmp_path: Path, key: str) -> None:
    source = (FIXTURES / "style" / "valid" / "camera_open_params.yaml").read_text()
    target = tmp_path / "style.yaml"
    target.write_text(source + f"{key}: 1\n")
    with pytest.raises(ArtifactValidationError) as caught:
        load_artifact(target, "style")
    assert [path for path, message in caught.value.errors if "is not a string" in message] == ["$"]


@pytest.mark.parametrize("suffix", [".yaml", ".json"])
def test_load_rejects_non_finite_numbers(tmp_path: Path, suffix: str) -> None:
    doc = _beats()
    doc["beats"][0]["duration_s"] = float("nan")
    target = tmp_path / f"beats{suffix}"
    # Both serializers emit NaN by default (.nan / NaN), as a hand-edited file would.
    target.write_text(yaml.safe_dump(doc) if suffix == ".yaml" else json.dumps(doc))
    with pytest.raises(ArtifactValidationError) as caught:
        load_artifact(target, "beats")
    assert ("$.beats[0].duration_s", "nan is not a finite number") in caught.value.errors


def test_write_refuses_a_non_finite_number_in_yaml_and_leaves_files_alone(tmp_path: Path) -> None:
    target = tmp_path / "beats.yaml"
    write_artifact(_beats(), target, "beats")
    before = target.read_bytes()
    bad = _beats()
    bad["beats"][1]["sound_cues"][0]["offset_s"] = float("nan")
    with pytest.raises(ArtifactValidationError) as caught:
        write_artifact(bad, target, "beats")
    assert ("$.beats[1].sound_cues[0].offset_s", "nan is not a finite number") in (
        caught.value.errors
    )
    assert target.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == [target.name]


def test_an_unknown_suffix_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="toml"):
        write_artifact(_valid_shots(), tmp_path / "shots.toml", "shots")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("name", ["nope", "_defs"])
def test_an_unknown_or_non_artifact_schema_is_refused(name: str) -> None:
    with pytest.raises(ValueError, match="unknown artifact schema"):
        validate_artifact({}, name)


def test_validate_reports_every_error_not_just_the_first() -> None:
    doc = _valid_shots()
    doc["shots"][0]["duration_s"] = -1.0
    doc["shots"][1]["lens_mm"] = 0
    with pytest.raises(ArtifactValidationError) as caught:
        validate_artifact(doc, "shots")
    paths = [p for p, _ in caught.value.errors]
    assert paths == ["$.shots[0].duration_s", "$.shots[1].lens_mm"]
    assert caught.value.source is None


@pytest.mark.parametrize(
    ("name", "text"),
    [
        ("dup.yaml", "schema_version: 1\nschema_version: 1\n"),
        ("dup.json", '{"schema_version": 1, "schema_version": 1}'),
    ],
)
def test_a_duplicate_key_is_refused(tmp_path: Path, name: str, text: str) -> None:
    target = tmp_path / name
    target.write_text(text)
    with pytest.raises(ValueError, match="duplicate key 'schema_version'"):
        load_artifact(target, "beats")


def test_yaml_loading_refuses_python_object_tags(tmp_path: Path) -> None:
    target = tmp_path / "evil.yaml"
    target.write_text("schema_version: !!python/object/apply:os.getcwd []\n")
    with pytest.raises(ValueError, match="python/object"):
        load_artifact(target, "beats")


# --- style helpers ------------------------------------------------------------------------------


def test_style_params_drop_the_envelope() -> None:
    style = load_artifact(FIXTURES / "style" / "valid" / "project_definition_example.yaml", "style")
    params = style_params(style)
    assert set(params) == set(style) - STYLE_ENVELOPE_KEYS
    assert set(params) == {"palette", "shading", "line", "lighting", "forbidden"}


def test_merge_overrides_merges_objects_and_replaces_arrays_and_scalars() -> None:
    base = {"palette": ["#000000", "#111111"], "line": {"enabled": True, "weight_px": 2.5}}
    patch = {"palette": ["#222222"], "line": {"weight_px": 3.0}, "lighting": {"key_fill_ratio": 4}}
    merged = merge_overrides(base, patch)
    assert merged == {
        "palette": ["#222222"],
        "line": {"enabled": True, "weight_px": 3.0},
        "lighting": {"key_fill_ratio": 4},
    }
    assert base == {"palette": ["#000000", "#111111"], "line": {"enabled": True, "weight_px": 2.5}}
    merged["lighting"]["key_fill_ratio"] = 9
    assert patch["lighting"] == {"key_fill_ratio": 4}


def test_a_merged_style_that_breaks_the_schema_is_caught_by_revalidation() -> None:
    style = load_artifact(FIXTURES / "style" / "valid" / "project_definition_example.yaml", "style")
    envelope = {k: v for k, v in style.items() if k in STYLE_ENVELOPE_KEYS}
    merged = {**envelope, **merge_overrides(style_params(style), {"line": {"weight_px": -1}})}
    with pytest.raises(ArtifactValidationError) as caught:
        validate_artifact(merged, "style")
    assert [p for p, _ in caught.value.errors] == ["$.line.weight_px"]
