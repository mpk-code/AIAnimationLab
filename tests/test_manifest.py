"""Manifest schema and writer (project-definition §M0 Acceptance item 2; ADR-0001 hashes)."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any

import jsonschema
import numpy as np
import pytest
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from blender.harness import manifest
from blender.harness.profiles import PROFILES
from blender.harness.run_result import FrameRecord, RenderDevice, RunResult, Timings

FRAME_SIZE = (4, 3)


def _write_png(path: Path, colour: tuple[int, ...], mode: str = "RGBA", note: str = "") -> Path:
    # A tEXt chunk that varies like Blender's Date/RenderTime, so file bytes differ while the
    # pixels do not (ADR-0001).
    info = PngInfo()
    info.add_text("RenderTime", note)
    Image.new(mode, FRAME_SIZE, colour).save(path, pnginfo=info)
    return path


def _run_result(out_dir: Path, frame_count: int = 3, **overrides: Any) -> RunResult:
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    frames = tuple(
        FrameRecord(
            index=i,
            path=_write_png(frames_dir / f"{i:04d}.png", (i * 40, 10, 200, 255), note=f"0{i}"),
        )
        for i in range(1, frame_count + 1)
    )
    fields: dict[str, Any] = {
        "production_id": "t-synthetic",
        "scene": manifest.REPO_ROOT / "tests" / "scenes" / "plain_scene.py",
        "profile": "preview",
        "engine": "BLENDER_EEVEE",
        "device": RenderDevice(
            engine_device="GPU",
            gpu_backend="METAL",
            cycles_compute_device_type=None,
            cycles_devices=(),
        ),
        "seed": 4127,
        "model_id": "fixture/test_manifest",
        "blender_version": "5.2.2 LTS",
        "blender_build_hash": "d13f752e3b9c",
        "blender_bin": Path("/Applications/Blender.app/Contents/MacOS/Blender"),
        "resolution": FRAME_SIZE,
        "samples": 16,
        "frame_count": frame_count,
        "frames": frames,
        "out_dir": out_dir,
        "timings": Timings(wall_s=3.5, render_s=2.25),
    }
    fields.update(overrides)
    return RunResult(**fields)


@pytest.fixture
def written(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    path = manifest.write_manifest(_run_result(tmp_path), tmp_path, contact_sheet=None)
    doc: dict[str, Any] = json.loads(path.read_text())
    return path, doc


def _schema() -> dict[str, Any]:
    schema: dict[str, Any] = json.loads(manifest.SCHEMA_PATH.read_text())
    return schema


def test_written_manifest_validates_and_records_m0_fields(
    tmp_path: Path, written: tuple[Path, dict[str, Any]]
) -> None:
    path, doc = written
    assert path == tmp_path / "manifest.json"
    jsonschema.Draft202012Validator(_schema()).validate(doc)

    # §M0 Acceptance item 2: model ID, Blender version, machine, git commit, seeds, timings.
    m0_fields = ["model_id", "blender_version", "machine", "git_commit", "seeds", "timings"]
    assert set(m0_fields) <= set(_schema()["required"])
    assert doc["model_id"] == "fixture/test_manifest"
    assert doc["blender_version"] == "5.2.2 LTS"
    assert doc["machine"]["label"] in manifest.MACHINE_LABELS.values()
    assert "hostname" not in doc["machine"]
    assert doc["git_commit"] == manifest.collect_git(manifest.REPO_ROOT).commit
    assert doc["seeds"] == {"scene": 4127}
    assert doc["timings"] == {"wall_s": 3.5, "render_s": 2.25}


def test_run_result_fields_are_recorded(written: tuple[Path, dict[str, Any]]) -> None:
    _, doc = written
    assert doc["production_id"] == "t-synthetic"
    assert doc["scene"] == "tests/scenes/plain_scene.py"
    assert doc["device"] == {
        "engine_device": "GPU",
        "gpu_backend": "METAL",
        "cycles_compute_device_type": None,
        "cycles_devices": [],
    }
    assert doc["resolution"] == list(FRAME_SIZE)
    assert (doc["samples"], doc["frame_count"]) == (16, 3)
    assert [f["index"] for f in doc["frames"]] == [1, 2, 3]
    assert [f["path"] for f in doc["frames"]] == [f"frames/{i:04d}.png" for i in (1, 2, 3)]
    assert doc["contact_sheet"] is None


def test_frame_file_sha256_matches_shasum(
    tmp_path: Path, written: tuple[Path, dict[str, Any]]
) -> None:
    _, doc = written
    for frame in doc["frames"]:
        out = subprocess.run(
            ["shasum", "-a", "256", str(tmp_path / frame["path"])],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert frame["file_sha256"] == out.split()[0]


def test_frame_pixel_sha256_matches_an_independent_decode(
    tmp_path: Path, written: tuple[Path, dict[str, Any]]
) -> None:
    _, doc = written
    for frame in doc["frames"]:
        with Image.open(tmp_path / frame["path"]) as image:
            pixels = np.asarray(image, dtype=np.uint8)
        assert pixels.shape == (FRAME_SIZE[1], FRAME_SIZE[0], 4)
        assert frame["pixel_sha256"] == hashlib.sha256(pixels.tobytes()).hexdigest()


def test_pixel_hash_ignores_png_metadata_but_file_hash_does_not(tmp_path: Path) -> None:
    a = _write_png(tmp_path / "a.png", (1, 2, 3, 255), note="00:00.33")
    b = _write_png(tmp_path / "b.png", (1, 2, 3, 255), note="00:00.24")
    assert manifest.file_sha256(a) != manifest.file_sha256(b)
    assert manifest.pixel_sha256(a) == manifest.pixel_sha256(b)


def test_pixel_hash_changes_with_one_pixel(tmp_path: Path) -> None:
    a = _write_png(tmp_path / "a.png", (1, 2, 3, 255))
    with Image.open(a) as image:
        changed = image.copy()
    changed.putpixel((0, 0), (1, 2, 4, 255))
    changed.save(tmp_path / "b.png")
    assert manifest.pixel_sha256(a) != manifest.pixel_sha256(tmp_path / "b.png")


def test_pixel_hash_treats_rgb_as_opaque_rgba(tmp_path: Path) -> None:
    rgb = _write_png(tmp_path / "rgb.png", (9, 8, 7), mode="RGB")
    rgba = _write_png(tmp_path / "rgba.png", (9, 8, 7, 255))
    assert manifest.pixel_sha256(rgb) == manifest.pixel_sha256(rgba)


@pytest.mark.parametrize("mode", ["P", "L", "I;16"])
def test_pixel_hash_rejects_modes_it_would_convert_lossily(tmp_path: Path, mode: str) -> None:
    path = tmp_path / "frame.png"
    Image.new(mode, FRAME_SIZE).save(path)
    with pytest.raises(ValueError, match="mode"):
        manifest.pixel_sha256(path)


def test_schema_rejects_a_manifest_missing_model_id(
    written: tuple[Path, dict[str, Any]],
) -> None:
    _, doc = written
    broken = copy.deepcopy(doc)
    del broken["model_id"]
    with pytest.raises(jsonschema.ValidationError, match="model_id"):
        manifest.validate_manifest(broken)


def test_invalid_manifest_is_not_written(tmp_path: Path) -> None:
    with pytest.raises(jsonschema.ValidationError):
        manifest.write_manifest(_run_result(tmp_path, model_id=""), tmp_path, contact_sheet=None)
    assert not (tmp_path / "manifest.json").exists()


@pytest.mark.parametrize("production_id", ["p-0001", "t-plain_scene"])
def test_production_id_accepts_production_and_test_forms(
    tmp_path: Path, production_id: str
) -> None:
    path = manifest.write_manifest(
        _run_result(tmp_path, production_id=production_id), tmp_path, contact_sheet=None
    )
    assert json.loads(path.read_text())["production_id"] == production_id


@pytest.mark.parametrize("production_id", ["plain_scene", "p-1", "t-", "T-Plain"])
def test_production_id_rejects_other_forms(tmp_path: Path, production_id: str) -> None:
    with pytest.raises(jsonschema.ValidationError):
        manifest.write_manifest(
            _run_result(tmp_path, production_id=production_id), tmp_path, contact_sheet=None
        )


def test_frame_count_must_match_frames(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="frame_count"):
        manifest.write_manifest(
            replace(_run_result(tmp_path, frame_count=3), frame_count=4),
            tmp_path,
            contact_sheet=None,
        )


def test_frames_outside_out_dir_are_rejected(tmp_path: Path) -> None:
    result = _run_result(tmp_path / "a")
    with pytest.raises(ValueError):
        manifest.write_manifest(result, tmp_path / "b", contact_sheet=None)


def test_contact_sheet_is_recorded_relative_with_its_hash(tmp_path: Path) -> None:
    sheet = _write_png(tmp_path / "contact_sheet.png", (5, 5, 5, 255))
    path = manifest.write_manifest(_run_result(tmp_path), tmp_path, contact_sheet=sheet)
    assert json.loads(path.read_text())["contact_sheet"] == {
        "path": "contact_sheet.png",
        "sha256": manifest.file_sha256(sheet),
    }


def test_machine_label_comes_from_the_hardware_model() -> None:
    assert manifest.machine_label("Mac17,6") == "M5 Max Laptop"
    assert manifest.machine_label("Mac17,14") == "M5 Max Mac Studio"
    assert manifest.machine_label("MacBookPro18,2") == "M1 Laptop"


def test_unknown_hardware_model_fails_loudly() -> None:
    with pytest.raises(manifest.UnknownMachineError, match="add a row"):
        manifest.machine_label("Mac99,1")


def test_schema_label_enum_matches_the_machine_map() -> None:
    enum = _schema()["properties"]["machine"]["properties"]["label"]["enum"]
    assert sorted(enum) == sorted(manifest.MACHINE_LABELS.values())


def test_schema_profile_enum_matches_the_profile_table() -> None:
    assert sorted(_schema()["properties"]["profile"]["enum"]) == sorted(PROFILES)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        check=True,
        capture_output=True,
    )


def test_collect_git_flags_a_dirty_tree(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    (tmp_path / "scene.py").write_text("FRAME_COUNT = 1\n")
    _git(tmp_path, "add", "scene.py")
    _git(tmp_path, "commit", "-q", "-m", "init")

    clean = manifest.collect_git(tmp_path)
    assert clean.dirty is False
    assert len(clean.commit) == 40

    (tmp_path / "scene.py").write_text("FRAME_COUNT = 2\n")
    assert manifest.collect_git(tmp_path).dirty is True


def test_collect_git_counts_untracked_files_as_dirty(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "commit", "-q", "--allow-empty", "-m", "init")
    (tmp_path / "new_scene.py").write_text("FRAME_COUNT = 1\n")
    assert manifest.collect_git(tmp_path).dirty is True
