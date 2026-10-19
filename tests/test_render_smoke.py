"""Render smoke: the harness CLI renders the plain scene at the preview profile, writing 48
frames, a contact sheet and a schema-valid manifest (docs/project-definition.md §M0 Tasks item 7).

It runs `render.py` as a script, the way CLAUDE.md §Blender invokes it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from blender.harness import contact_sheet, manifest, profiles

_ROOT = Path(__file__).resolve().parents[1]
_RENDER_PY = _ROOT / "blender" / "harness" / "render.py"
_PLAIN_SCENE = _ROOT / "tests" / "scenes" / "plain_scene.py"
_MODEL_ID = "fixture/test_render_smoke"
# §M0 Acceptance: "the smoke test passes on both Macs in a few minutes" (Run 0.7 decision: 120 s
# for this render's Blender process; the M5 Max Laptop takes about 7 s).
SMOKE_BUDGET_S = 120


@pytest.fixture(scope="module")
def smoke(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    out = tmp_path_factory.mktemp("smoke") / "out"
    completed = subprocess.run(
        [
            sys.executable,
            str(_RENDER_PY),
            "--scene",
            str(_PLAIN_SCENE),
            "--profile",
            "preview",
            "--out",
            str(out),
            "--seed",
            "0",
            "--model-id",
            _MODEL_ID,
        ],
        env={k: v for k, v in os.environ.items() if k != "AIAL_MODEL_ID"},
        check=False,
    )
    assert completed.returncode == 0
    doc: dict[str, Any] = json.loads((out / manifest.MANIFEST_NAME).read_text())
    return out, doc


@pytest.mark.blender
def test_preview_smoke_writes_48_frames(smoke: tuple[Path, dict[str, Any]]) -> None:
    out, doc = smoke
    names = sorted(p.name for p in (out / "frames").iterdir())
    assert names == [f"frame_{i:04d}.png" for i in range(1, 49)]
    assert [f["index"] for f in doc["frames"]] == list(range(1, 49))


@pytest.mark.blender
def test_preview_smoke_manifest_is_valid_and_records_m0_fields(
    smoke: tuple[Path, dict[str, Any]],
) -> None:
    _, doc = smoke
    manifest.validate_manifest(doc)
    assert doc["model_id"] == _MODEL_ID
    assert doc["blender_version"].startswith("5.2.2")
    assert doc["machine"]["label"] in manifest.MACHINE_LABELS.values()
    assert len(doc["git_commit"]) == 40
    assert doc["seeds"] == {"scene": 0}
    assert 0 < doc["timings"]["render_s"] < doc["timings"]["wall_s"]
    assert (doc["profile"], doc["engine"]) == ("preview", profiles.PROFILES["preview"].engine)
    assert doc["scene"] == "tests/scenes/plain_scene.py"


@pytest.mark.blender
def test_preview_smoke_contact_sheet_tiles_every_nth_frame(
    smoke: tuple[Path, dict[str, Any]],
) -> None:
    out, doc = smoke
    sheet = out / contact_sheet.FILE_NAME
    assert doc["contact_sheet"] == {
        "path": contact_sheet.FILE_NAME,
        "sha256": manifest.file_sha256(sheet),
    }
    width, height = profiles.PROFILES["preview"].resolution
    tiles = len(range(0, 48, contact_sheet.EVERY_N))
    rows = -(-tiles // contact_sheet.COLUMNS)
    with Image.open(sheet) as image:
        assert image.size == (contact_sheet.COLUMNS * width, rows * height)


@pytest.mark.blender
def test_preview_smoke_renders_within_the_budget(smoke: tuple[Path, dict[str, Any]]) -> None:
    _, doc = smoke
    assert doc["timings"]["wall_s"] < SMOKE_BUDGET_S
