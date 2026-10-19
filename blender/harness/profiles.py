"""Render profiles: the one table of render settings (STD-001, STD-003).

Pure Python with no bpy import, so the host CLI validates `--profile` against the same table the
in-Blender entry applies. Nothing else sets engine, resolution, samples or output format.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class Profile:
    name: str
    engine: str  # a runtime `scene.render.engine` identifier (ADR-0001)
    resolution: tuple[int, int]
    # EEVEE: taa_render_samples; Cycles: samples.
    samples: int
    # The three cycles_* fields apply only when engine is CYCLES; the EEVEE profile ignores them.
    # cycles_device is None for EEVEE, which always renders on the GPU backend.
    cycles_device: str | None
    cycles_adaptive_sampling: bool
    cycles_denoise: bool
    # fps belongs to production.yaml (docs/project-definition.md §Artifact schemas); the profile
    # holds it until that artifact exists. Run 0.4 decision 3.
    fps: int
    view_transform: str
    film_transparent: bool


# Values: Run 0.4 decision 3 (user, 2026-10-19). Final keeps denoise off so ADR-0001's Cycles
# tolerance policy applies to it as measured.
PROFILES: dict[str, Profile] = {
    "preview": Profile(
        name="preview",
        engine="BLENDER_EEVEE",
        resolution=(640, 360),
        samples=16,
        cycles_device=None,
        cycles_adaptive_sampling=False,
        cycles_denoise=False,
        fps=24,
        view_transform="AgX",
        film_transparent=False,
    ),
    "final": Profile(
        name="final",
        engine="CYCLES",
        resolution=(1920, 1080),
        samples=256,
        cycles_device="GPU",
        cycles_adaptive_sampling=True,
        cycles_denoise=False,
        fps=24,
        view_transform="AgX",
        film_transparent=False,
    ),
}

# Every frame is written as 8-bit RGBA PNG under both profiles.
FILE_FORMAT: Final = "PNG"
COLOR_MODE: Final = "RGBA"
COLOR_DEPTH: Final = "8"
