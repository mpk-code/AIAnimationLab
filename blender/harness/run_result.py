"""What one harness render produced: the hand-off from `render.py` to the manifest writer.

`render.py` (Run 0.4) builds a `RunResult`; `manifest.write_manifest` (Run 0.5) records it. Pure
Python with no `bpy`, so host code and tests import it without Blender.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FrameRecord:
    index: int  # Blender frame number, 1..frame_count
    path: Path  # absolute


@dataclass(frozen=True)
class Timings:
    wall_s: float  # the host's Blender subprocess, start to exit
    render_s: float  # the in-Blender render call only


@dataclass(frozen=True)
class RenderDevice:
    engine_device: str
    gpu_backend: str
    cycles_compute_device_type: str | None
    cycles_devices: tuple[str, ...]


@dataclass(frozen=True)
class RunResult:
    production_id: str
    scene: Path
    profile: str
    engine: str
    device: RenderDevice
    seed: int
    model_id: str
    blender_version: str
    blender_build_hash: str
    blender_bin: Path
    resolution: tuple[int, int]
    samples: int
    frame_count: int
    frames: tuple[FrameRecord, ...]
    out_dir: Path
    timings: Timings
    # dimension -> style_ref ("visual/cut-paper@3") for each non-null entry of the style bible;
    # empty when the render had no bible.
    styles: dict[str, str]
    style_bible: Path | None
