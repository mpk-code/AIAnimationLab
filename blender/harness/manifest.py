"""Manifest writer: records one harness render in `<out>/manifest.json` (CLAUDE.md §Blender).

Host-side; no Blender. `render.py` hands over a `RunResult`; this module adds the facts the host
knows (git state, machine), hashes every frame, validates against `schemas/manifest.schema.json`
(STD-006) and only then writes.

Frames carry two hashes. `file_sha256` checks the PNG on disk. `pixel_sha256` is the frame's
identity for reproducibility: Blender writes Date/RenderTime into PNG metadata, so file bytes
differ on every render even when the pixels match (ADR-0001).
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
from PIL import Image

from blender.harness.run_result import RunResult

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "manifest.schema.json"
MANIFEST_NAME = "manifest.json"

# Manifests name a machine by a stable label, never its OS hostname (user decision, 2026-10-19).
# Keyed by `sysctl -n hw.model`, which differs between the two M5 Max machines although their
# chips are identical. The schema's label enum must equal these values (tests hold it).
MACHINE_LABELS: dict[str, str] = {
    "Mac17,6": "M5 Max Laptop",
    "Mac17,14": "M5 Max Mac Studio",
    "MacBookPro18,2": "M1 Laptop",
}

# Modes that become 8-bit RGBA without changing any value. Anything else (palette, greyscale,
# 16-bit) would be converted lossily, so two different frames could hash or compare alike.
_HASHABLE_MODES = ("RGBA", "RGB")


class UnknownMachineError(RuntimeError):
    """This machine's hardware model has no label in MACHINE_LABELS."""


@dataclass(frozen=True)
class GitState:
    commit: str
    dirty: bool


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_rgba(path: Path) -> Image.Image:
    """Decode a frame as 8-bit RGBA: the pixels both `pixel_sha256` and `compare.py` read.

    RGB images gain opaque alpha. Other modes raise ValueError rather than convert lossily.
    """
    with Image.open(path) as image:
        if image.mode not in _HASHABLE_MODES:
            raise ValueError(f"{path}: mode {image.mode} is not one of {_HASHABLE_MODES}")
        return image.convert("RGBA")


def pixel_sha256(path: Path) -> str:
    """sha256 of the image's decoded pixels as 8-bit RGBA, row-major: the frame identity.

    PNG metadata does not affect it. RGB images hash as RGBA with opaque alpha.
    """
    return hashlib.sha256(load_rgba(path).tobytes()).hexdigest()


def collect_git(repo: Path) -> GitState:
    """HEAD and whether the tree differs from it. Untracked files count as dirty: an uncommitted
    scene script means the commit alone cannot reproduce the render."""

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
        ).stdout

    return GitState(
        commit=git("rev-parse", "HEAD").strip(), dirty=bool(git("status", "--porcelain").strip())
    )


def machine_label(hardware_model: str) -> str:
    try:
        return MACHINE_LABELS[hardware_model]
    except KeyError:
        raise UnknownMachineError(
            f"hardware model {hardware_model!r} has no machine label: add a row to "
            "MACHINE_LABELS in blender/harness/manifest.py and the label to the schema's enum"
        ) from None


def _sysctl(name: str) -> str:
    return subprocess.run(
        ["sysctl", "-n", name], capture_output=True, text=True, check=True
    ).stdout.strip()


def collect_machine() -> dict[str, str]:
    hardware_model = _sysctl("hw.model")
    return {
        "label": machine_label(hardware_model),
        "hardware_model": hardware_model,
        "chip": _sysctl("machdep.cpu.brand_string"),
        "os": f"macOS {platform.mac_ver()[0]}",
        "arch": platform.machine(),
    }


def validate_manifest(doc: dict[str, Any]) -> None:
    """Raise jsonschema.ValidationError unless `doc` matches the manifest schema."""
    schema = json.loads(SCHEMA_PATH.read_text())
    jsonschema.Draft202012Validator(schema).validate(doc)


def _repo_relative(path: Path) -> str:
    resolved = path.resolve()
    if resolved.is_relative_to(REPO_ROOT):
        return resolved.relative_to(REPO_ROOT).as_posix()
    return str(resolved)


def write_manifest(run_result: RunResult, out_dir: Path, *, contact_sheet: Path | None) -> Path:
    """Validate and write `<out_dir>/manifest.json`; returns its path.

    Frame and contact-sheet paths are recorded relative to `out_dir` and must lie inside it.
    Nothing is written when validation fails.
    """
    if len(run_result.frames) != run_result.frame_count:
        raise ValueError(
            f"frame_count is {run_result.frame_count} but {len(run_result.frames)} frames given"
        )
    root = out_dir.resolve()

    def relative(path: Path) -> str:
        return path.resolve().relative_to(root).as_posix()

    git = collect_git(REPO_ROOT)
    device = run_result.device
    doc: dict[str, Any] = {
        "schema_version": 1,
        "production_id": run_result.production_id,
        "git_commit": git.commit,
        "git_dirty": git.dirty,
        "model_id": run_result.model_id,
        "blender_version": run_result.blender_version,
        "blender_build_hash": run_result.blender_build_hash,
        "blender_bin": str(run_result.blender_bin),
        "machine": collect_machine(),
        "scene": _repo_relative(run_result.scene),
        "seeds": {"scene": run_result.seed},
        "timings": {
            "wall_s": run_result.timings.wall_s,
            "render_s": run_result.timings.render_s,
        },
        "profile": run_result.profile,
        "engine": run_result.engine,
        "device": {
            "engine_device": device.engine_device,
            "gpu_backend": device.gpu_backend,
            "cycles_compute_device_type": device.cycles_compute_device_type,
            "cycles_devices": list(device.cycles_devices),
        },
        "resolution": list(run_result.resolution),
        "samples": run_result.samples,
        "frame_count": run_result.frame_count,
        "frames": [
            {
                "index": frame.index,
                "path": relative(frame.path),
                "file_sha256": file_sha256(frame.path),
                "pixel_sha256": pixel_sha256(frame.path),
            }
            for frame in run_result.frames
        ],
        "contact_sheet": None
        if contact_sheet is None
        else {"path": relative(contact_sheet), "sha256": file_sha256(contact_sheet)},
    }
    validate_manifest(doc)
    path = out_dir / MANIFEST_NAME
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    return path
