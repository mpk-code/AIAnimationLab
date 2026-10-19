"""Frame comparison policy (ADR-0001): exact pixel hash for EEVEE, 1/255 per channel for Cycles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from blender.harness import compare, manifest

SIZE = (4, 3)
BASE = (120, 60, 30, 255)


def _render_dir(
    out: Path,
    pixels: list[tuple[int, int, int, int]],
    *,
    engine: str = "BLENDER_EEVEE",
    seed: int = 0,
    size: tuple[int, int] = SIZE,
    note: str = "",
    styles: dict[str, str] | None = None,
    style_bible: dict[str, str] | None = None,
) -> Path:
    """A fake render: one PNG per entry of `pixels` (pixel (0, 0) set to it, the rest BASE) and a
    manifest holding the fields compare.py reads."""
    frames_dir = out / "frames"
    frames_dir.mkdir(parents=True)
    frames = []
    for i, pixel in enumerate(pixels, start=1):
        image = Image.new("RGBA", size, BASE)
        image.putpixel((0, 0), pixel)
        info = PngInfo()
        info.add_text("RenderTime", note)  # varies like Blender's metadata (ADR-0001)
        path = frames_dir / f"frame_{i:04d}.png"
        image.save(path, pnginfo=info)
        frames.append(
            {"index": i, "path": f"frames/{path.name}", "pixel_sha256": manifest.pixel_sha256(path)}
        )
    doc: dict[str, Any] = {
        "scene": "tests/scenes/plain_scene.py",
        "profile": "preview" if engine == "BLENDER_EEVEE" else "final",
        "engine": engine,
        "seeds": {"scene": seed},
        "resolution": list(size),
        "samples": 16,
        "frame_count": len(pixels),
        "frames": frames,
        "git_commit": "0" * 40,
        "git_dirty": False,
        "machine": {"label": "M5 Max Laptop"},
        "timings": {"wall_s": 1.0, "render_s": 0.5},
        "styles": styles or {},
        "style_bible": style_bible,
    }
    (out / manifest.MANIFEST_NAME).write_text(json.dumps(doc))
    return out


def _off_by(levels: int) -> tuple[int, int, int, int]:
    return (BASE[0] + levels, BASE[1], BASE[2], BASE[3])


def test_identical_pixels_match_although_png_metadata_differs(tmp_path: Path) -> None:
    a = _render_dir(tmp_path / "a", [BASE, BASE], note="00:00.33")
    b = _render_dir(tmp_path / "b", [BASE, BASE], note="00:00.24")
    result = compare.compare_runs(a, b)
    assert result.matches
    assert [f.pixel_equal for f in result.frames] == [True, True]


@pytest.mark.parametrize(
    ("engine", "levels", "matches"),
    [
        ("BLENDER_EEVEE", 1, False),
        ("CYCLES", 1, True),
        ("CYCLES", 2, False),
    ],
    ids=["eevee-off-by-1-fails", "cycles-off-by-1-passes", "cycles-off-by-2-fails"],
)
def test_one_channel_off_by_n_levels(
    tmp_path: Path, engine: str, levels: int, matches: bool
) -> None:
    a = _render_dir(tmp_path / "a", [BASE, BASE], engine=engine)
    b = _render_dir(tmp_path / "b", [BASE, _off_by(levels)], engine=engine)
    result = compare.compare_runs(a, b)
    assert result.matches is matches
    second = result.frames[1]
    assert (second.pixel_equal, second.max_abs_diff, second.differing_pixels) == (False, levels, 1)


def test_cli_prints_a_summary_and_exits_by_verdict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    a = _render_dir(tmp_path / "a", [BASE], engine="CYCLES")
    b = _render_dir(tmp_path / "b", [_off_by(1)], engine="CYCLES")
    c = _render_dir(tmp_path / "c", [_off_by(2)], engine="CYCLES")
    assert compare.main([str(a), str(b)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert (report["matches"], report["max_abs_diff"], report["frame_count"]) == (True, 1, 1)
    assert report["runs"][0]["manifest"] == str((a / manifest.MANIFEST_NAME).resolve())
    assert compare.main([str(a), str(c)]) == 1


@pytest.mark.parametrize(
    ("b_kwargs", "message"),
    [
        ({"seed": 1}, "seeds"),
        ({"engine": "CYCLES"}, "profile"),
        ({"size": (5, 3)}, "resolution"),
        ({"styles": {"visual": "visual/fixture-a@2"}}, "styles"),
        ({"style_bible": {"path": "b.json", "sha256": "b" * 64}}, "style_bible.sha256"),
    ],
    ids=["seed", "engine", "resolution", "styles", "style-bible-content"],
)
def test_renders_with_different_settings_are_refused(
    tmp_path: Path, b_kwargs: dict[str, Any], message: str
) -> None:
    a = _render_dir(tmp_path / "a", [BASE])
    b = _render_dir(tmp_path / "b", [BASE], **b_kwargs)
    with pytest.raises(compare.ComparisonError, match=message):
        compare.compare_runs(a, b)


def test_one_style_bible_at_two_paths_is_comparable(tmp_path: Path) -> None:
    styles = {"visual": "visual/fixture-a@2"}
    a = _render_dir(
        tmp_path / "a", [BASE], styles=styles, style_bible={"path": "a.json", "sha256": "a" * 64}
    )
    b = _render_dir(
        tmp_path / "b", [BASE], styles=styles, style_bible={"path": "b.json", "sha256": "a" * 64}
    )
    assert compare.compare_runs(a, b).matches


def test_an_engine_without_a_policy_is_refused(tmp_path: Path) -> None:
    a = _render_dir(tmp_path / "a", [BASE], engine="BLENDER_WORKBENCH")
    b = _render_dir(tmp_path / "b", [BASE], engine="BLENDER_WORKBENCH")
    with pytest.raises(compare.ComparisonError, match="no comparison policy"):
        compare.compare_runs(a, b)


def test_a_frame_of_another_size_is_refused(tmp_path: Path) -> None:
    a = _render_dir(tmp_path / "a", [BASE], engine="CYCLES")
    b = _render_dir(tmp_path / "b", [_off_by(1)], engine="CYCLES", size=(5, 3))
    # The manifests disagree on resolution too; make them agree so the decoded shapes are checked.
    doc = json.loads((b / manifest.MANIFEST_NAME).read_text())
    doc["resolution"] = list(SIZE)
    (b / manifest.MANIFEST_NAME).write_text(json.dumps(doc))
    with pytest.raises(compare.ComparisonError, match=r"\(3, 4, 4\)"):
        compare.compare_runs(a, b)


def test_a_missing_manifest_is_refused(tmp_path: Path) -> None:
    a = _render_dir(tmp_path / "a", [BASE])
    with pytest.raises(compare.ComparisonError, match=r"render .* through the harness"):
        compare.compare_runs(a, tmp_path / "empty")
