"""The render harness's host CLI: the only way the studio renders (CLAUDE.md §Blender, STD-003).

    uv run python blender/harness/render.py --scene <script> --profile preview|final \
        --out <dir> --seed <int> --model-id <id>

It launches Blender headless on `blender/harness/_inblender.py`, which builds the scene script,
applies the profile from `blender/harness/profiles.py` and writes frames to `<out>/frames/`. Then
`run_render` tiles `<out>/contact_sheet.png` and writes `<out>/manifest.json` (CLAUDE.md §Blender:
every render writes a manifest), and returns the `RunResult` the manifest records.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path

if __package__ in (None, ""):
    # Run as a script, sys.path[0] is blender/harness/; the repo root makes `blender.` importable.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from blender.harness import contact_sheet, manifest, profiles
from blender.harness.run_result import FrameRecord, RenderDevice, RunResult, Timings

# CLAUDE.md §Blender names this binary; the BLENDER_BIN environment variable overrides it.
DEFAULT_BLENDER_BIN = "/Applications/Blender.app/Contents/MacOS/Blender"
MODEL_ID_ENV = "AIAL_MODEL_ID"

_INBLENDER = Path(__file__).resolve().with_name("_inblender.py")
_MANIFEST_SCHEMA = Path(__file__).resolve().parents[2] / "schemas" / "manifest.schema.json"


class HarnessError(Exception):
    """The harness refused to render, or Blender failed; the message says why."""


class BlenderFailed(HarnessError):
    def __init__(self, returncode: int) -> None:
        super().__init__(f"Blender exited with code {returncode}")
        self.returncode = returncode


def blender_bin() -> Path:
    return Path(os.environ.get("BLENDER_BIN", DEFAULT_BLENDER_BIN))


def production_id_for(scene: Path) -> str:
    """`t-<scene file stem>`, lower-cased with characters outside [a-z0-9_-] replaced by `-`."""
    production_id = "t-" + re.sub(r"[^a-z0-9_-]", "-", scene.stem.lower())
    # The manifest schema owns the production_id pattern (STD-001).
    schema = json.loads(_MANIFEST_SCHEMA.read_text(encoding="utf-8"))
    pattern = schema["properties"]["production_id"]["pattern"]
    if not re.fullmatch(pattern, production_id):
        raise HarnessError(
            f"scene file name {scene.name!r} gives production_id {production_id!r}, which does "
            f"not match {pattern} in {_MANIFEST_SCHEMA.name}; rename the scene script"
        )
    return production_id


def run_render(
    scene: Path, profile: str, out: Path, seed: int, model_id: str, binary: Path
) -> RunResult:
    """Render every frame of `scene` into `out/frames/`, then write its contact sheet and manifest.

    Refuses a non-empty `out/frames/` (Run 0.4 decision 5), so frames from another run are never
    mixed in or silently overwritten. Raises BlenderFailed when Blender exits non-zero, and
    manifest.UnknownMachineError on a machine with no label.
    """
    if profile not in profiles.PROFILES:
        raise HarnessError(f"unknown profile {profile!r}; choose from {sorted(profiles.PROFILES)}")
    if not model_id:
        raise HarnessError("model ID is empty")
    scene = scene.resolve()
    out = out.resolve()
    production_id = production_id_for(scene)
    frames_dir = out / "frames"
    if frames_dir.exists() and any(frames_dir.iterdir()):
        raise HarnessError(f"{frames_dir} is not empty; render into a fresh --out directory")
    frames_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="aial-render-") as tmp:
        result_path = Path(tmp) / "inblender_result.json"
        command = [
            str(binary),
            "-b",
            "--factory-startup",
            "-noaudio",
            "--python-exit-code",
            "1",
            "--python",
            str(_INBLENDER),
            "--",
            "--scene",
            str(scene),
            "--profile",
            profile,
            "--out",
            str(out),
            "--seed",
            str(seed),
            "--result",
            str(result_path),
        ]
        start = time.perf_counter()
        completed = subprocess.run(command, check=False)
        wall_s = time.perf_counter() - start
        if completed.returncode != 0:
            raise BlenderFailed(completed.returncode)
        facts = json.loads(result_path.read_text(encoding="utf-8"))

    device = facts["device"]
    result = RunResult(
        production_id=production_id,
        scene=scene,
        profile=profile,
        engine=facts["engine"],
        device=RenderDevice(
            engine_device=device["engine_device"],
            gpu_backend=device["gpu_backend"],
            cycles_compute_device_type=device["cycles_compute_device_type"],
            cycles_devices=tuple(device["cycles_devices"]),
        ),
        seed=seed,
        model_id=model_id,
        blender_version=facts["blender_version"],
        blender_build_hash=facts["blender_build_hash"],
        blender_bin=binary,
        resolution=(facts["resolution"][0], facts["resolution"][1]),
        samples=facts["samples"],
        frame_count=facts["frame_count"],
        frames=tuple(FrameRecord(index=f["index"], path=Path(f["path"])) for f in facts["frames"]),
        out_dir=out,
        timings=Timings(wall_s=wall_s, render_s=facts["render_s"]),
    )
    sheet = contact_sheet.build_contact_sheet(
        [frame.path for frame in result.frames],
        contact_sheet.EVERY_N,
        contact_sheet.COLUMNS,
        out / contact_sheet.FILE_NAME,
    )
    manifest.write_manifest(result, out, contact_sheet=sheet)
    return result


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="render.py", description="Render a scene script headless through the harness."
    )
    parser.add_argument("--scene", type=Path, required=True, help="scene script (ADR-0002)")
    parser.add_argument("--profile", choices=sorted(profiles.PROFILES), required=True)
    parser.add_argument("--out", type=Path, required=True, help="output dir; frames go in frames/")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument(
        "--model-id", help=f"model that generated the scene; falls back to ${MODEL_ID_ENV}"
    )
    args = parser.parse_args(argv)
    # No silent default: the harness cannot detect the model (rollout Input Gaps).
    args.model_id = args.model_id or os.environ.get(MODEL_ID_ENV)
    if not args.model_id:
        parser.error(f"a model ID is required: pass --model-id or set {MODEL_ID_ENV}")
    if not args.scene.is_file():
        parser.error(f"--scene {args.scene} is not a file")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        result = run_render(
            args.scene, args.profile, args.out, args.seed, args.model_id, blender_bin()
        )
    except BlenderFailed as exc:
        print(f"render.py: {exc}", file=sys.stderr)
        return exc.returncode
    except (HarnessError, manifest.UnknownMachineError) as exc:
        print(f"render.py: {exc}", file=sys.stderr)
        return 1
    print(
        f"render.py: {len(result.frames)} frames in {result.out_dir / 'frames'} "
        f"({result.engine}, {result.timings.wall_s:.1f}s); "
        f"manifest {result.out_dir / manifest.MANIFEST_NAME}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
