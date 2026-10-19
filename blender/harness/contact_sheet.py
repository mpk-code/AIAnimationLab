"""Contact sheet: every Nth rendered frame tiled onto one PNG, for reviewing a render at a glance.

Host-side Pillow code; no Blender. Tiles keep each frame's native size, in row-major order.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from pathlib import Path

from PIL import Image

# The harness's sheet for every render (Run 0.7 decision 2, user, 2026-10-19): 48 frames give 8
# tiles in 4 columns by 2 rows. Long productions and final-profile frames need these scaled or the
# tiles downscaled; revisit when production.yaml exists (docs/plans/followups.md).
EVERY_N = 6
COLUMNS = 4
FILE_NAME = "contact_sheet.png"


def build_contact_sheet(frames: Sequence[Path], every_n: int, columns: int, out_path: Path) -> Path:
    """Tile frames[0], frames[every_n], ... into `columns` columns and write a PNG to `out_path`.

    Cells left over in the last row stay transparent. All picked frames must share one size.
    """
    if every_n < 1 or columns < 1:
        raise ValueError(f"every_n and columns must be >= 1, got {every_n} and {columns}")
    picked = list(frames)[::every_n]
    if not picked:
        raise ValueError("no frames to tile")

    tiles = []
    for path in picked:
        with Image.open(path) as image:
            tiles.append(image.convert("RGBA"))
    width, height = tiles[0].size
    for path, tile in zip(picked, tiles, strict=True):
        if tile.size != (width, height):
            raise ValueError(f"frame size {tile.size} of {path} differs from {(width, height)}")

    rows = math.ceil(len(tiles) / columns)
    sheet = Image.new("RGBA", (columns * width, rows * height), (0, 0, 0, 0))
    for i, tile in enumerate(tiles):
        sheet.paste(tile, ((i % columns) * width, (i // columns) * height))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, format="PNG")
    return out_path
