"""The plain test scene: the fixture that render smoke and reproducibility tests render (M0).

It is a test fixture, not a style, and is exempt from STD-005: plainness is its purpose, so its
placements, primitive boxes and stock BEZIER easing are deliberate. It follows the scene-script
contract (ADR-0002): build into `bpy.context.scene`, which must be empty; the harness owns the
frame range and every render setting.
"""

from __future__ import annotations

import random

import bpy

FRAME_COUNT = 48

# Fixture placements chosen for a readable composition, not a style choice (STD-005 exemption).
_FLOOR_HALF_SIZE = 6.0
# (name, centre xy, (width, depth, height)) for each box standing on the floor.
_BOXES: list[tuple[str, tuple[float, float], tuple[float, float, float]]] = [
    ("plain_box_centre", (0.4, 0.2), (2.0, 2.0, 2.0)),
    ("plain_box_tall", (-2.3, 1.6), (1.0, 1.2, 3.1)),
    ("plain_box_low", (2.1, -2.4), (1.6, 0.9, 0.7)),
]
# Small enough that no box leaves the camera's view or touches another box at any seed; large
# enough that two seeds give visibly different frames.
_JITTER_M = 0.3
_LIGHT_LOCATION = (3.0, -2.0, 6.0)
_LIGHT_ROTATION = (0.6, 0.2, 0.9)
# The camera dollies along an arc between these two keyed locations, tracking the centre box.
_CAMERA_START = (7.0, -6.0, 4.0)
_CAMERA_END = (4.0, -7.5, 3.0)


def _box_mesh(name: str, size: tuple[float, float, float]) -> bpy.types.Mesh:
    w, d, h = size
    verts = [(x, y, z) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2) for z in (0.0, h)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


def _floor_mesh() -> bpy.types.Mesh:
    s = _FLOOR_HALF_SIZE
    mesh = bpy.data.meshes.new("plain_floor")
    mesh.from_pydata([(-s, -s, 0.0), (s, -s, 0.0), (s, s, 0.0), (-s, s, 0.0)], [], [(0, 1, 2, 3)])
    mesh.update()
    return mesh


def build(seed: int) -> None:
    scene = bpy.context.scene
    if scene is None:
        raise RuntimeError("bpy.context.scene is None; cannot build the plain scene")
    rng = random.Random(seed)
    link = scene.collection.objects.link

    link(bpy.data.objects.new("plain_floor", _floor_mesh()))

    centre: bpy.types.Object | None = None
    for name, (x, y), size in _BOXES:
        box = bpy.data.objects.new(name, _box_mesh(name, size))
        box.location = (
            x + rng.uniform(-_JITTER_M, _JITTER_M),
            y + rng.uniform(-_JITTER_M, _JITTER_M),
            0.0,
        )
        link(box)
        centre = centre or box

    light_data = bpy.data.lights.new("plain_light", type="SUN")
    assert isinstance(light_data, bpy.types.SunLight)
    light_data.energy = 3.0
    light = bpy.data.objects.new("plain_light", light_data)
    light.location = _LIGHT_LOCATION
    light.rotation_euler = _LIGHT_ROTATION
    link(light)

    camera = bpy.data.objects.new("plain_camera", bpy.data.cameras.new("plain_camera"))
    link(camera)
    scene.camera = camera
    track = camera.constraints.new(type="TRACK_TO")
    assert isinstance(track, bpy.types.TrackToConstraint)
    track.target = centre
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    for frame, location in ((1, _CAMERA_START), (FRAME_COUNT, _CAMERA_END)):
        camera.location = location
        camera.keyframe_insert("location", frame=frame)
