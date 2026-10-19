"""Compare two harness renders frame by frame: the reproducibility check (ADR-0001).

    uv run python blender/harness/compare.py <out_a> <out_b>

Each argument is a render's `--out` directory. Its `manifest.json` names the engine, and the engine
picks the policy ADR-0001 decided. EEVEE frames match only when their `pixel_sha256` values are
equal. Cycles GPU frames match when no 8-bit channel differs by more than CYCLES_MAX_ABS_DIFF. The
CLI prints a JSON summary and exits 0 when every frame matches, 1 otherwise. Host-side; no Blender.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

if __package__ in (None, ""):
    # Run as a script, sys.path[0] is blender/harness/; the repo root makes `blender.` importable.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from blender.harness.manifest import MANIFEST_NAME, load_rgba

# ADR-0001 Decision: Cycles GPU frames may differ by at most 1/255 per 8-bit channel.
CYCLES_MAX_ABS_DIFF = 1
# Allowed per-channel difference, in 8-bit levels, for each engine ADR-0001 gives a policy for.
_TOLERANCE_BY_ENGINE: dict[str, int] = {"BLENDER_EEVEE": 0, "CYCLES": CYCLES_MAX_ABS_DIFF}
# Manifest fields two renders must share for their frames to be comparable.
_SAME_RENDER_FIELDS = (
    "scene",
    "profile",
    "engine",
    "seeds",
    "resolution",
    "samples",
    "frame_count",
)


class ComparisonError(ValueError):
    """The two renders cannot be compared: different settings, engine or frames."""


@dataclass(frozen=True)
class FrameDiff:
    index: int
    pixel_sha256_a: str
    pixel_sha256_b: str
    pixel_equal: bool
    max_abs_diff: int  # largest per-channel difference, 8-bit levels
    differing_pixels: int  # pixels with any channel different


@dataclass(frozen=True)
class Comparison:
    engine: str
    tolerance: int  # 0 means the pixel hashes must be equal
    frames: tuple[FrameDiff, ...]

    @property
    def matches(self) -> bool:
        if self.tolerance == 0:
            return all(frame.pixel_equal for frame in self.frames)
        return all(frame.max_abs_diff <= self.tolerance for frame in self.frames)


def _read_manifest(out: Path) -> dict[str, Any]:
    path = out / MANIFEST_NAME
    if not path.is_file():
        raise ComparisonError(f"{path} does not exist; render {out} through the harness first")
    doc: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return doc


def _diff_pixels(path_a: Path, path_b: Path) -> tuple[int, int]:
    # int16 so the subtraction of two uint8 values cannot wrap.
    a = np.asarray(load_rgba(path_a), dtype=np.int16)
    b = np.asarray(load_rgba(path_b), dtype=np.int16)
    if a.shape != b.shape:
        raise ComparisonError(f"{path_a} is {a.shape} but {path_b} is {b.shape}")
    diff = np.abs(a - b)
    return int(diff.max()), int(np.count_nonzero(diff.max(axis=-1)))


def compare_runs(out_a: Path, out_b: Path) -> Comparison:
    """Compare every frame of two renders of the same scene, profile and seed."""
    doc_a, doc_b = _read_manifest(out_a), _read_manifest(out_b)
    for field in _SAME_RENDER_FIELDS:
        if doc_a[field] != doc_b[field]:
            raise ComparisonError(
                f"the renders differ in {field}: {doc_a[field]!r} vs {doc_b[field]!r}"
            )
    engine = doc_a["engine"]
    if engine not in _TOLERANCE_BY_ENGINE:
        raise ComparisonError(f"ADR-0001 sets no comparison policy for engine {engine!r}")
    tolerance = _TOLERANCE_BY_ENGINE[engine]

    frames = []
    for frame_a, frame_b in zip(doc_a["frames"], doc_b["frames"], strict=True):
        if frame_a["index"] != frame_b["index"]:
            raise ComparisonError(f"frame {frame_a['index']} pairs with frame {frame_b['index']}")
        equal = frame_a["pixel_sha256"] == frame_b["pixel_sha256"]
        max_abs, differing = (
            (0, 0) if equal else _diff_pixels(out_a / frame_a["path"], out_b / frame_b["path"])
        )
        frames.append(
            FrameDiff(
                index=frame_a["index"],
                pixel_sha256_a=frame_a["pixel_sha256"],
                pixel_sha256_b=frame_b["pixel_sha256"],
                pixel_equal=equal,
                max_abs_diff=max_abs,
                differing_pixels=differing,
            )
        )
    return Comparison(engine=engine, tolerance=tolerance, frames=tuple(frames))


def summary(comparison: Comparison, out_a: Path, out_b: Path) -> dict[str, Any]:
    """The CLI's JSON report: verdict, policy, both manifests' provenance and every frame."""
    runs = []
    for out in (out_a, out_b):
        doc = _read_manifest(out)
        runs.append(
            {
                "manifest": str((out / MANIFEST_NAME).resolve()),
                "git_commit": doc["git_commit"],
                "git_dirty": doc["git_dirty"],
                "machine": doc["machine"]["label"],
                "wall_s": doc["timings"]["wall_s"],
            }
        )
    return {
        "matches": comparison.matches,
        "engine": comparison.engine,
        "tolerance": comparison.tolerance,
        "frames_equal_by_hash": sum(frame.pixel_equal for frame in comparison.frames),
        "frame_count": len(comparison.frames),
        "max_abs_diff": max((frame.max_abs_diff for frame in comparison.frames), default=0),
        "runs": runs,
        "frames": [asdict(frame) for frame in comparison.frames],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="compare.py", description="Compare two harness renders frame by frame (ADR-0001)."
    )
    parser.add_argument("out_a", type=Path, help="first render's --out directory")
    parser.add_argument("out_b", type=Path, help="second render's --out directory")
    args = parser.parse_args(argv)
    try:
        comparison = compare_runs(args.out_a, args.out_b)
    except ComparisonError as exc:
        print(f"compare.py: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary(comparison, args.out_a, args.out_b), indent=2))
    return 0 if comparison.matches else 1


if __name__ == "__main__":
    sys.exit(main())
