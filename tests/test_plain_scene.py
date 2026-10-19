"""The plain test scene builds headless through the scene-script contract (ADR-0002, Run 0.6).

The render harness is not used here: the driver below stands in for its build step (empty the
factory scene, call ``build``) and reports the result as one JSON line, so these tests check the
scene's contents without rendering.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCENE = _ROOT / "tests" / "scenes" / "plain_scene.py"

# Runs inside Blender. Loads the scene by path, as the harness's --scene does.
_DRIVER = """
import importlib.util, json, sys
import bpy
from bpy_extras import anim_utils

root, scene_path, seed = sys.argv[sys.argv.index("--") + 1 :]
sys.path.insert(0, root)
scene = bpy.context.scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj)

def render_state():
    r = scene.render
    return [r.engine, r.resolution_x, r.resolution_y, r.resolution_percentage, r.filepath,
            r.image_settings.file_format, scene.frame_start, scene.frame_end]

before = render_state()
spec = importlib.util.spec_from_file_location("plain_scene", scene_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.build(int(seed))

objects = list(scene.collection.objects)
camera = scene.camera
keys = {}
if camera is not None and camera.animation_data and camera.animation_data.action:
    channelbag = anim_utils.action_get_channelbag_for_slot(
        camera.animation_data.action, camera.animation_data.action_slot)
    for fcurve in channelbag.fcurves:
        frames = [k.co[0] for k in fcurve.keyframe_points]
        keys[f"{fcurve.data_path}[{fcurve.array_index}]"] = frames
print("PLAIN_SCENE=" + json.dumps({
    "frame_count": module.FRAME_COUNT,
    "types": sorted(o.type for o in objects),
    "camera_type": camera.type if camera else None,
    "camera_keys": keys,
    "boxes": {o.name: list(o.location) for o in objects if o.name.startswith("plain_box")},
    "render_state_unchanged": render_state() == before,
}))
"""


def _build(blender_bin: Path, seed: int) -> dict[str, Any]:
    result = subprocess.run(
        [
            str(blender_bin),
            "--background",
            "--factory-startup",
            "-noaudio",
            "--python-exit-code",
            "1",
            "--python-expr",
            _DRIVER,
            "--",
            str(_ROOT),
            str(_SCENE),
            str(seed),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    found = re.search(r"^PLAIN_SCENE=(.+)$", result.stdout, re.M)
    assert found, result.stdout
    summary: dict[str, Any] = json.loads(found.group(1))
    return summary


@pytest.mark.blender
def test_plain_scene_contents(blender_bin: Path) -> None:
    summary = _build(blender_bin, seed=7)
    assert summary["frame_count"] == 48
    assert summary["types"] == ["CAMERA", "LIGHT", "MESH", "MESH", "MESH", "MESH"]
    assert summary["camera_type"] == "CAMERA"
    assert summary["camera_keys"] == {f"location[{i}]": [1.0, 48.0] for i in range(3)}


@pytest.mark.blender
def test_plain_scene_leaves_render_settings_and_frame_range_to_the_harness(
    blender_bin: Path,
) -> None:
    assert _build(blender_bin, seed=7)["render_state_unchanged"] is True


@pytest.mark.blender
def test_plain_scene_variation_comes_only_from_the_seed(blender_bin: Path) -> None:
    first, again, other = (_build(blender_bin, seed=s)["boxes"] for s in (7, 7, 8))
    assert len(first) == 3
    assert first == again
    assert first != other
