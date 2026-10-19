"""Blender API probe: reports the installed Blender's API surface as one JSON file (ADR-0001).

Re-run it on every machine and on every Blender version change; ADR-0001 quotes its output.
Run headless only:

    Blender -b --factory-startup -noaudio --python-exit-code 1 \
        --python blender/probe/api_probe.py -- --out <scratch dir> --report <file.json>

The determinism pre-check renders through `_render_still`, a time-boxed spike exception to
STD-003 recorded in ADR-0001: it writes to `--out` only, never to a production path, and writes
no manifest. Production renders go through `blender/harness/`.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import platform
import subprocess
import sys
import time
from array import array
from pathlib import Path
from typing import Any

import bpy
import gpu

# Probe render settings, fixed by the Run 0.3 plan (ADR-0001 records them with the results).
RESOLUTION = 256
CYCLES_SAMPLES = 16
CYCLES_SEED = 0
RUNS_PER_ENGINE = 2


def _sysctl(name: str) -> str:
    result = subprocess.run(["sysctl", "-n", name], capture_output=True, text=True, check=False)
    return result.stdout.strip()


def _git_commit() -> str:
    repo = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip()


def machine_info() -> dict[str, Any]:
    return {
        "arch": platform.machine(),
        "cpu": _sysctl("machdep.cpu.brand_string"),
        "memory_bytes": int(_sysctl("hw.memsize") or 0),
        "macos": platform.mac_ver()[0],
        "hostname": platform.node(),
        "git_commit": _git_commit(),
    }


def blender_info() -> dict[str, Any]:
    return {
        "version_string": bpy.app.version_string,
        "version": list(bpy.app.version),
        "build_hash": bpy.app.build_hash.decode(),
        "build_branch": bpy.app.build_branch.decode(),
        "build_date": bpy.app.build_date.decode(),
        "python": sys.version,
        "background": bpy.app.background,
    }


def _set_engine(scene: bpy.types.Scene, engine: str) -> None:
    # The stubs type RenderSettings.engine as the static enum (BLENDER_EEVEE only); at runtime
    # it accepts every registered engine, so assign through an untyped reference.
    render: Any = scene.render
    render.engine = engine


def render_engines(scene: bpy.types.Scene) -> list[str]:
    """Return the engine identifiers `scene.render.engine` accepts at runtime.

    The RNA enum's static `enum_items` lists only BLENDER_EEVEE: Workbench and add-on engines
    (CYCLES) are added by a dynamic item callback that no public API exposes. Assigning an
    invalid identifier makes Blender list the accepted set in the TypeError, so read it there.
    """
    try:
        _set_engine(scene, "API_PROBE_INVALID_ENGINE")
    except TypeError as exc:
        accepted = str(exc).rsplit(" not found in ", 1)[-1]
        engines = ast.literal_eval(accepted)
        if isinstance(engines, tuple) and all(isinstance(e, str) for e in engines):
            return list(engines)
        raise RuntimeError(f"cannot parse engine list from {exc!s}") from exc
    raise RuntimeError("an invalid render engine identifier was accepted")


def gpu_info() -> dict[str, Any]:
    # In background mode gpu.platform raises SystemError until a render has initialised the
    # GPU module, so call this after the EEVEE render. An error is a finding, not a failure.
    try:
        return {
            "backend": gpu.platform.backend_type_get(),
            "device_type": gpu.platform.device_type_get(),
            "renderer": gpu.platform.renderer_get(),
            "vendor": gpu.platform.vendor_get(),
            "version": gpu.platform.version_get(),
        }
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def _cycles_preferences() -> Any:
    # The Cycles add-on's preferences class is registered at runtime and is not in the bpy
    # stubs, so its attributes (compute_device_type, devices, refresh_devices) are untyped.
    preferences = bpy.context.preferences
    if preferences is None:
        raise RuntimeError("bpy.context.preferences is None; cannot configure Cycles devices")
    return preferences.addons["cycles"].preferences


def configure_cycles_metal() -> dict[str, Any]:
    prefs = _cycles_preferences()
    # compute_device_type is a dynamic enum too; get_device_types is the add-on's own lister.
    available = [item[0] for item in prefs.get_device_types(bpy.context)]
    prefs.compute_device_type = "METAL"
    prefs.refresh_devices()
    devices = []
    for device in prefs.devices:
        device.use = device.type == "METAL"
        devices.append({"name": device.name, "type": device.type, "use": device.use})
    return {
        "compute_device_types": available,
        "compute_device_type": prefs.compute_device_type,
        "devices": devices,
    }


def build_scene() -> bpy.types.Scene:
    """Build a small scene through bpy.data only (STD-002): two meshes, a light, a camera."""
    scene = bpy.data.scenes.new("api_probe")
    world = bpy.data.worlds.new("api_probe_world")
    world.color = (0.05, 0.05, 0.05)
    scene.world = world

    cube = bpy.data.meshes.new("probe_cube")
    verts = [(x, y, z) for x in (-1.0, 1.0) for y in (-1.0, 1.0) for z in (0.0, 2.0)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    cube.from_pydata(verts, [], faces)
    cube.update()
    floor = bpy.data.meshes.new("probe_floor")
    floor.from_pydata([(-6, -6, 0), (6, -6, 0), (6, 6, 0), (-6, 6, 0)], [], [(0, 1, 2, 3)])
    floor.update()

    light_data = bpy.data.lights.new("probe_light", type="SUN")
    assert isinstance(light_data, bpy.types.SunLight)
    light_data.energy = 3.0
    camera_data = bpy.data.cameras.new("probe_camera")

    # Probe-only placements: a readable composition, not a style choice (STD-005 is for
    # style and scene code).
    placements: list[tuple[str, bpy.types.ID, tuple[float, float, float], tuple[float, ...]]] = [
        ("probe_cube", cube, (0.4, 0.2, 0.0), (0.0, 0.0, 0.35)),
        ("probe_floor", floor, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ("probe_light", light_data, (3.0, -2.0, 6.0), (0.6, 0.2, 0.9)),
        ("probe_camera", camera_data, (6.5, -5.5, 4.2), (1.13, 0.0, 0.87)),
    ]
    for name, data, location, rotation in placements:
        obj = bpy.data.objects.new(name, data)
        obj.location = location
        obj.rotation_euler = rotation
        scene.collection.objects.link(obj)
        if name == "probe_camera":
            scene.camera = obj

    render = scene.render
    render.resolution_x = RESOLUTION
    render.resolution_y = RESOLUTION
    render.resolution_percentage = 100
    render.image_settings.file_format = "PNG"
    render.image_settings.color_mode = "RGBA"
    render.image_settings.color_depth = "8"
    return scene


def scene_summary(scene: bpy.types.Scene) -> dict[str, Any]:
    objects = list(scene.collection.objects)
    return {
        "ok": True,
        "built_with": "bpy.data only",
        "objects": len(objects),
        "meshes": sum(1 for o in objects if o.type == "MESH"),
        "lights": sum(1 for o in objects if o.type == "LIGHT"),
        "cameras": sum(1 for o in objects if o.type == "CAMERA"),
    }


def _render_still(scene: bpy.types.Scene, path: Path) -> float:
    """Render one still to `path`; returns wall seconds.

    STD-002/STD-003 exception (ADR-0001): rendering has no bpy.data equivalent, so this calls
    bpy.ops.render.render. It is the only operator call in the probe and the only render call
    outside blender/harness/; output goes to the probe's --out directory only.
    """
    scene.render.filepath = str(path)
    start = time.perf_counter()
    result = bpy.ops.render.render(write_still=True, scene=scene.name)
    elapsed = time.perf_counter() - start
    if "FINISHED" not in result:
        raise RuntimeError(f"render of {path.name} returned {result}")
    return elapsed


def _decoded_pixels(path: Path) -> array[float]:
    image = bpy.data.images.load(str(path), check_existing=False)
    try:
        # The stubs' bpy_prop_array declares neither __len__ nor __getitem__ (stub gap);
        # Image.size is (width, height) at runtime.
        size: Any = image.size
        pixels = array("f", [0.0]) * (int(size[0]) * int(size[1]) * image.channels)
        image.pixels.foreach_get(pixels)
        return pixels
    finally:
        bpy.data.images.remove(image)


def _compare(first: array[float], second: array[float]) -> dict[str, Any]:
    if len(first) != len(second):
        return {"pixel_hash_equal": False, "error": "decoded pixel buffers differ in size"}
    diffs = [round(abs(a - b) * 255) for a, b in zip(first, second, strict=True)]
    channels = 4
    differing_pixels = sum(
        1 for i in range(0, len(diffs), channels) if any(diffs[i : i + channels])
    )
    return {
        "pixel_hash_equal": first.tobytes() == second.tobytes(),
        "max_abs_diff_255": max(diffs),
        "differing_pixels": differing_pixels,
    }


def _configure_engine(scene: bpy.types.Scene, engine: str) -> dict[str, Any]:
    _set_engine(scene, engine)
    view_settings = scene.view_settings
    if view_settings is None:
        raise RuntimeError("scene.view_settings is None")
    settings: dict[str, Any] = {
        "engine": engine,
        "resolution": [RESOLUTION, RESOLUTION],
        "file_format": "PNG RGBA 8-bit",
        "view_transform": view_settings.view_transform,
        "film_transparent": scene.render.film_transparent,
    }
    if engine == "CYCLES":
        # scene.cycles is the Cycles add-on's property group, not in the bpy stubs.
        untyped_scene: Any = scene
        cycles = untyped_scene.cycles
        cycles.device = "GPU"
        cycles.samples = CYCLES_SAMPLES
        cycles.use_denoising = False
        cycles.seed = CYCLES_SEED
        cycles.use_animated_seed = False
        settings.update(
            device=cycles.device,
            samples=cycles.samples,
            use_adaptive_sampling=cycles.use_adaptive_sampling,
            use_denoising=cycles.use_denoising,
            seed=cycles.seed,
            use_animated_seed=cycles.use_animated_seed,
        )
    else:
        eevee = scene.eevee
        if eevee is None:
            raise RuntimeError("scene.eevee is None")
        settings["taa_render_samples"] = eevee.taa_render_samples
    return settings


def determinism_check(scene: bpy.types.Scene, engine: str, out: Path) -> dict[str, Any]:
    settings = _configure_engine(scene, engine)
    runs = []
    buffers = []
    for index in range(1, RUNS_PER_ENGINE + 1):
        path = out / f"{engine.lower()}_{index}.png"
        seconds = _render_still(scene, path)
        pixels = _decoded_pixels(path)
        buffers.append(pixels)
        runs.append(
            {
                "file": path.name,
                "pixel_sha256": hashlib.sha256(pixels.tobytes()).hexdigest(),
                "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "wall_seconds": round(seconds, 3),
            }
        )
    return {"settings": settings, "runs": runs, **_compare(buffers[0], buffers[1])}


def _eevee_engine_id(engines: list[str]) -> str:
    ids = [e for e in engines if e.startswith("BLENDER_EEVEE")]
    if len(ids) != 1:
        raise RuntimeError(f"expected exactly one EEVEE engine identifier, found {ids}")
    return ids[0]


def _parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(prog="api_probe.py")
    parser.add_argument("--out", type=Path, required=True, help="scratch dir for probe frames")
    parser.add_argument("--report", type=Path, required=True, help="JSON report path")
    return parser.parse_args(argv)


def main() -> None:
    args = _parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    scene = build_scene()
    engines = render_engines(scene)
    report: dict[str, Any] = {
        "probe": "blender/probe/api_probe.py",
        "machine": machine_info(),
        "blender": blender_info(),
        "render_engines": engines,
        "cycles": configure_cycles_metal(),
        "scene_build": scene_summary(scene),
    }
    report["determinism"] = {
        engine: determinism_check(scene, engine, args.out)
        for engine in (_eevee_engine_id(engines), "CYCLES")
    }
    report["gpu"] = gpu_info()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
