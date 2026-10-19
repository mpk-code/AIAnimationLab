"""Same-seed harness renders reproduce (docs/project-definition.md §M0 Acceptance item 1, ADR-0001).

EEVEE renders the 48-frame plain scene at the preview profile and must match by exact pixel hash.
Cycles renders one frame of the same scene at the final profile, its only profile, and must match
within ADR-0001's per-pixel tolerance; docs/test-strategy.md allows this one final-profile render.
There is no skip when Metal is missing: the harness refuses a CPU fallback, so the test fails.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from blender.harness import compare, manifest, render

_PLAIN_SCENE = Path(__file__).resolve().parent / "scenes" / "plain_scene.py"

# Test fixture: the plain scene cut to its first frame, so the Cycles check renders one
# final-profile frame instead of 48 (Run 0.7 decision 1).
_ONE_FRAME_PLAIN_SCENE = f"""
import importlib.util

_spec = importlib.util.spec_from_file_location("_plain_scene", {str(_PLAIN_SCENE)!r})
_plain = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_plain)

FRAME_COUNT = 1
build = _plain.build
"""


def _render(scene: Path, profile: str, out: Path, seed: int, blender_bin: Path) -> Path:
    render.run_render(
        scene, profile, out, seed, "fixture/test_render_determinism", blender_bin, style_bible=None
    )
    return out


def _manifest(out: Path) -> dict[str, Any]:
    doc: dict[str, Any] = json.loads((out / manifest.MANIFEST_NAME).read_text())
    return doc


@pytest.fixture(scope="module")
def eevee_runs(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Three preview renders of the plain scene: two with seed 0, one with seed 1."""
    root = tmp_path_factory.mktemp("eevee")
    # Module scope cannot take the function-scoped blender_bin fixture; both read BLENDER_BIN.
    binary = render.blender_bin()
    return {
        name: _render(_PLAIN_SCENE, "preview", root / name, seed, binary)
        for name, seed in (("seed0_a", 0), ("seed0_b", 0), ("seed1", 1))
    }


@pytest.mark.blender
def test_eevee_same_seed_preview_runs_match_exactly(eevee_runs: dict[str, Path]) -> None:
    result = compare.compare_runs(eevee_runs["seed0_a"], eevee_runs["seed0_b"])
    assert (result.engine, result.tolerance) == ("BLENDER_EEVEE", 0)
    assert len(result.frames) == 48
    assert all(frame.pixel_equal for frame in result.frames)
    assert result.matches


@pytest.mark.blender
def test_eevee_a_different_seed_changes_the_frames(eevee_runs: dict[str, Path]) -> None:
    """The negative control: the hash check can fail, so its passing above means something."""
    seed0 = [f["pixel_sha256"] for f in _manifest(eevee_runs["seed0_a"])["frames"]]
    seed1 = [f["pixel_sha256"] for f in _manifest(eevee_runs["seed1"])["frames"]]
    assert len(seed0) == len(seed1) == 48
    assert all(a != b for a, b in zip(seed0, seed1, strict=True))


@pytest.mark.blender
def test_runs_with_different_seeds_are_refused(eevee_runs: dict[str, Path]) -> None:
    with pytest.raises(compare.ComparisonError, match="seeds"):
        compare.compare_runs(eevee_runs["seed0_a"], eevee_runs["seed1"])


@pytest.mark.blender
def test_cycles_same_seed_final_frame_matches_within_tolerance(
    tmp_path: Path, blender_bin: Path
) -> None:
    scene = tmp_path / "plain_scene_frame1.py"
    scene.write_text(_ONE_FRAME_PLAIN_SCENE, encoding="utf-8")
    runs = [_render(scene, "final", tmp_path / name, 0, blender_bin) for name in ("a", "b")]
    result = compare.compare_runs(*runs)
    assert (result.engine, result.tolerance) == ("CYCLES", compare.CYCLES_MAX_ABS_DIFF)
    assert len(result.frames) == 1
    assert result.frames[0].max_abs_diff <= compare.CYCLES_MAX_ABS_DIFF
    assert result.matches
