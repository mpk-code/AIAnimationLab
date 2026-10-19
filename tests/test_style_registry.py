"""Style-module registry and the harness's style application (Run 1.2).

Unit tests resolve style bibles on the host with Blender patched out; the blender test renders the
plain scene with a bible whose visual style names the test-only `testing/noop` module
(tests/style_modules/noop.py), monkeypatched into the registry.
"""

from __future__ import annotations

import importlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from blender.harness import manifest, render
from blender.lib import registry
from studio import artifacts

_ROOT = Path(__file__).resolve().parents[1]
_PLAIN_SCENE = _ROOT / "tests" / "scenes" / "plain_scene.py"
_DEFS = json.loads((_ROOT / "schemas" / "_defs.schema.json").read_text())
_NOOP_ID = "testing/noop"
_NOOP_TARGET = "tests.style_modules.noop:apply"
# Imported by name, as the harness imports it: a static import makes mypy see the file under two
# module names, because tests/ is not a package.
_NOOP_LOG_ENV: str = importlib.import_module(_NOOP_TARGET.partition(":")[0]).NOOP_LOG_ENV
_STYLE_ID = "visual/fixture-noop"
# Fixture inputs: a schema-valid visual style, not a style choice.
_STYLE: dict[str, Any] = {
    "schema_version": 1,
    "style_id": _STYLE_ID,
    "version": 2,
    "status": "candidate",
    "palette": ["#203040", "#d0c0b0"],
    "line": {"enabled": True, "weight_px": 1.5},
    "modules": [_NOOP_ID],
}


def _bible(tmp_path: Path, styles: dict[str, str | None], overrides: Any = None) -> Path:
    doc = {
        "schema_version": 1,
        "production_id": "t-style_registry",
        "styles": {
            "visual": None,
            "camera": None,
            "storytelling": None,
            "characterization": None,
            "motion": None,
            **styles,
        },
        "overrides": overrides or {},
    }
    path = tmp_path / "style_bible.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


@pytest.fixture
def styles_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A styles library holding _STYLE, with testing/noop registered."""
    root = tmp_path / "styles"
    (root / _STYLE_ID).mkdir(parents=True)
    (root / _STYLE_ID / "style.yaml").write_text(yaml.safe_dump(_STYLE), encoding="utf-8")
    monkeypatch.setattr(render, "STYLES_ROOT", root)
    monkeypatch.setitem(registry.MODULES, _NOOP_ID, _NOOP_TARGET)
    return root


@pytest.fixture
def no_blender(monkeypatch: pytest.MonkeyPatch) -> None:
    def launched(*args: object, **kwargs: object) -> None:
        raise AssertionError("Blender was launched despite an invalid style bible")

    monkeypatch.setattr(subprocess, "run", launched)


def test_the_shipping_registry_names_no_test_module() -> None:
    assert not any(module_id.startswith("testing/") for module_id in registry.MODULES)
    assert not any(target.startswith("tests.") for target in registry.MODULES.values())


def test_every_registered_id_matches_the_module_id_pattern() -> None:
    for module_id in registry.MODULES:
        registry.target_for(module_id)


def test_the_registry_reads_its_pattern_from_defs() -> None:
    assert registry.module_id_pattern() == _DEFS["$defs"]["module_id"]["pattern"]


def test_target_for_returns_the_registered_target(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(registry.MODULES, _NOOP_ID, _NOOP_TARGET)
    assert registry.target_for(_NOOP_ID) == _NOOP_TARGET


@pytest.mark.parametrize(
    ("module_id", "message"),
    [("shaders/not_registered", "unknown style module"), ("Shaders/Toon", "does not match")],
    ids=["unregistered", "malformed"],
)
def test_target_for_rejects_unknown_and_malformed_ids(module_id: str, message: str) -> None:
    with pytest.raises(registry.UnknownStyleModule, match=message):
        registry.target_for(module_id)


def test_the_plan_gives_each_module_the_style_params(styles_root: Path, tmp_path: Path) -> None:
    styles, plan = render.resolve_style_plan(_bible(tmp_path, {"visual": f"{_STYLE_ID}@2"}))
    assert styles == {"visual": f"{_STYLE_ID}@2"}
    assert plan == [
        {
            "dimension": "visual",
            "style": f"{_STYLE_ID}@2",
            "module": _NOOP_ID,
            "target": _NOOP_TARGET,
            "params": artifacts.style_params(_STYLE),
        }
    ]
    assert "modules" not in plan[0]["params"]


def test_overrides_deep_merge_into_the_params(styles_root: Path, tmp_path: Path) -> None:
    bible = _bible(tmp_path, {"visual": f"{_STYLE_ID}@2"}, {"visual": {"line": {"weight_px": 3.0}}})
    _, plan = render.resolve_style_plan(bible)
    assert plan[0]["params"]["line"] == {"enabled": True, "weight_px": 3.0}
    assert plan[0]["params"]["palette"] == _STYLE["palette"]


def test_an_override_that_breaks_the_style_is_refused(styles_root: Path, tmp_path: Path) -> None:
    bible = _bible(tmp_path, {"visual": f"{_STYLE_ID}@2"}, {"visual": {"line": {"weight_px": -1}}})
    with pytest.raises(artifacts.ArtifactValidationError, match="weight_px"):
        render.resolve_style_plan(bible)


def test_overrides_for_a_null_dimension_are_refused(styles_root: Path, tmp_path: Path) -> None:
    bible = _bible(tmp_path, {"visual": f"{_STYLE_ID}@2"}, {"motion": {"ease": "x"}})
    with pytest.raises(render.HarnessError, match="motion"):
        render.resolve_style_plan(bible)


@pytest.mark.parametrize(
    ("style_ref", "message"),
    [(f"{_STYLE_ID}@3", "is visual/fixture-noop@2"), ("visual/missing@1", "does not exist")],
    ids=["version-mismatch", "missing-style"],
)
def test_a_ref_that_does_not_resolve_is_refused(
    styles_root: Path, tmp_path: Path, style_ref: str, message: str
) -> None:
    with pytest.raises(render.HarnessError, match=message):
        render.resolve_style_plan(_bible(tmp_path, {"visual": style_ref}))


@pytest.mark.usefixtures("no_blender")
def test_an_unknown_module_id_fails_before_blender_or_any_frame(
    styles_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delitem(registry.MODULES, _NOOP_ID)
    out = tmp_path / "out"
    with pytest.raises(render.HarnessError, match=f"unknown style module '{_NOOP_ID}'"):
        render.run_render(
            _PLAIN_SCENE,
            "preview",
            out,
            0,
            "fixture/test_style_registry",
            Path("/nonexistent/Blender"),
            style_bible=_bible(tmp_path, {"visual": f"{_STYLE_ID}@2"}),
        )
    assert not (out / "frames").exists()


@pytest.mark.usefixtures("no_blender")
def test_the_cli_reports_an_unknown_module_id(
    styles_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delitem(registry.MODULES, _NOOP_ID)
    bible = _bible(tmp_path, {"visual": f"{_STYLE_ID}@2"})
    argv = ["--scene", str(_PLAIN_SCENE), "--profile", "preview", "--out", str(tmp_path / "o")]
    argv += ["--seed", "0", "--model-id", "fixture/test_style_registry"]
    assert render.main([*argv, "--style-bible", str(bible)]) == 1
    assert "unknown style module" in capsys.readouterr().err


def test_manifest_styles_schema_matches_defs() -> None:
    styles = json.loads(manifest.SCHEMA_PATH.read_text())["properties"]["styles"]
    assert styles["propertyNames"]["enum"] == _DEFS["$defs"]["dimension"]["enum"]
    assert styles["additionalProperties"]["pattern"] == _DEFS["$defs"]["style_ref"]["pattern"]


@pytest.mark.blender
def test_plain_scene_with_noop_bible_records_styles_and_calls_module_once(
    styles_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, blender_bin: Path
) -> None:
    log = tmp_path / "noop.log"
    monkeypatch.setenv(_NOOP_LOG_ENV, str(log))
    bible = _bible(tmp_path, {"visual": f"{_STYLE_ID}@2"})
    out = tmp_path / "out"
    result = render.run_render(
        _PLAIN_SCENE,
        "preview",
        out,
        0,
        "fixture/test_style_registry",
        blender_bin,
        style_bible=bible,
    )
    doc = json.loads((out / manifest.MANIFEST_NAME).read_text())
    assert doc["styles"] == {"visual": f"{_STYLE_ID}@2"}
    assert doc["style_bible"]["sha256"] == manifest.file_sha256(bible)
    assert result.styles == doc["styles"]
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert calls == [{"scene": "Scene", "params": artifacts.style_params(_STYLE)}]
    assert len(result.frames) == 48
