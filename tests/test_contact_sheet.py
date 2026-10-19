"""Contact sheet: every Nth frame tiled onto one PNG (docs/project-definition.md §M0 Tasks)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from blender.harness.contact_sheet import build_contact_sheet

TILE = (8, 6)


def _colour(i: int) -> tuple[int, int, int, int]:
    return (i * 5, 255 - i * 5, 100, 255)


def _frames(directory: Path, count: int) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(count):
        path = directory / f"{i + 1:04d}.png"
        Image.new("RGBA", TILE, _colour(i)).save(path)
        paths.append(path)
    return paths


def test_48_frames_every_6th_gives_one_sheet_of_8_tiles(tmp_path: Path) -> None:
    frames = _frames(tmp_path / "frames", 48)
    out = build_contact_sheet(frames, every_n=6, columns=4, out_path=tmp_path / "sheet.png")

    assert out == tmp_path / "sheet.png"
    with Image.open(out) as sheet:
        assert sheet.size == (4 * TILE[0], 2 * TILE[1])
        tiles = [
            sheet.getpixel((col * TILE[0] + TILE[0] // 2, row * TILE[1] + TILE[1] // 2))
            for row in range(2)
            for col in range(4)
        ]
    assert tiles == [_colour(i) for i in range(0, 48, 6)]


def test_partial_last_row_leaves_cells_empty(tmp_path: Path) -> None:
    frames = _frames(tmp_path / "frames", 5)
    out = build_contact_sheet(frames, every_n=1, columns=3, out_path=tmp_path / "sheet.png")
    with Image.open(out) as sheet:
        assert sheet.size == (3 * TILE[0], 2 * TILE[1])
        assert sheet.getpixel((2 * TILE[0] + 1, TILE[1] + 1)) == (0, 0, 0, 0)


def test_mismatched_frame_sizes_are_rejected(tmp_path: Path) -> None:
    frames = _frames(tmp_path / "frames", 2)
    Image.new("RGBA", (4, 4), _colour(0)).save(frames[1])
    with pytest.raises(ValueError, match="size"):
        build_contact_sheet(frames, every_n=1, columns=2, out_path=tmp_path / "sheet.png")


@pytest.mark.parametrize(("every_n", "columns"), [(0, 4), (6, 0)])
def test_non_positive_arguments_are_rejected(tmp_path: Path, every_n: int, columns: int) -> None:
    frames = _frames(tmp_path / "frames", 2)
    with pytest.raises(ValueError):
        build_contact_sheet(frames, every_n=every_n, columns=columns, out_path=tmp_path / "s.png")


def test_no_frames_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no frames"):
        build_contact_sheet([], every_n=1, columns=1, out_path=tmp_path / "s.png")
