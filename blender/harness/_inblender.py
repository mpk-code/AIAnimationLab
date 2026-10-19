"""The harness's in-Blender entry: build a scene script, apply a render profile, render its frames.

Launched only by `blender/harness/render.py` (never run by hand), under
`Blender -b --factory-startup --python blender/harness/_inblender.py -- <args>`. It writes the
in-Blender half of the run result as JSON to `--result`; render.py adds the host-side facts.

Scene-script contract (ADR-0002, Run 0.4 decision 1): the script defines `build(seed: int) -> None`
and `FRAME_COUNT: int`, and builds into `bpy.context.scene`, which this entry has first emptied of
the factory objects. The factory World is kept, so it still sets the background.

Style application (Run 1.2): `--style-plan` is the JSON list render.py resolved and validated from
the style bible on the host (Blender's Python has no jsonschema or yaml). Each entry's target is
imported before build(); each `apply(params, scene)` runs once, in plan order, after build() and
before the profile, so no style module can change a render setting the profile owns (STD-003).
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import sys
import time
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
# ADR-0002: scene scripts and style modules import repo packages by full name.
sys.path.insert(0, str(_REPO_ROOT))

import bpy  # noqa: E402
import gpu  # noqa: E402

from blender.harness import profiles  # noqa: E402


def _parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(prog="_inblender.py")
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--profile", choices=sorted(profiles.PROFILES), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--style-plan", type=Path, required=True)
    return parser.parse_args(argv)


StyleApply = Callable[[dict[str, Any], bpy.types.Scene], None]


def _load_style_plan(path: Path) -> list[tuple[StyleApply, dict[str, Any]]]:
    """Import every planned style module's `apply`; returns (apply, params) in plan order."""
    plan = json.loads(path.read_text(encoding="utf-8"))
    loaded = []
    for entry in plan:
        module_name, _, attr = entry["target"].partition(":")
        apply = getattr(importlib.import_module(module_name), attr, None)
        if not callable(apply):
            raise RuntimeError(
                f"style module {entry['module']!r}: {entry['target']} is not a callable "
                "(blender/lib/registry.py)"
            )
        loaded.append((apply, entry["params"]))
    return loaded


def _load_scene_script(path: Path) -> tuple[ModuleType, int]:
    spec = importlib.util.spec_from_file_location(f"_aial_scene_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load scene script {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "build", None)):
        raise RuntimeError(f"{path}: scene script defines no build(seed) function (ADR-0002)")
    frame_count = getattr(module, "FRAME_COUNT", None)
    # bool is an int subclass; FRAME_COUNT = True is a mistake, not one frame.
    if type(frame_count) is not int or frame_count < 1:
        raise RuntimeError(f"{path}: FRAME_COUNT must be an int >= 1, got {frame_count!r}")
    return module, frame_count


def _empty_factory_scene(scene: bpy.types.Scene) -> None:
    """Remove the factory Cube, Light and Camera objects and the datablocks they leave unused."""
    for obj in list(scene.objects):
        data = obj.data
        bpy.data.objects.remove(obj)
        if data is None or data.users > 0:
            continue
        if isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)
        elif isinstance(data, bpy.types.Light):
            bpy.data.lights.remove(data)
        elif isinstance(data, bpy.types.Camera):
            bpy.data.cameras.remove(data)


def _cycles_preferences() -> Any:
    # The Cycles add-on's preferences are registered at runtime and are not in the bpy stubs.
    preferences = bpy.context.preferences
    if preferences is None:
        raise RuntimeError("bpy.context.preferences is None; cannot configure Cycles devices")
    return preferences.addons["cycles"].preferences


def _enable_metal_devices() -> tuple[str, ...]:
    """Select Metal for Cycles and enable only the Metal devices; fail if there are none.

    ADR-0001: a factory-startup scene renders Cycles on the CPU unless the harness selects the GPU,
    and a CPU fallback must not pass silently.
    """
    prefs = _cycles_preferences()
    prefs.compute_device_type = "METAL"
    prefs.refresh_devices()
    enabled = []
    for device in prefs.devices:
        device.use = device.type == "METAL"
        if device.use:
            enabled.append(str(device.name))
    if not enabled:
        raise RuntimeError("no Metal device available for Cycles; refusing to render on the CPU")
    return tuple(enabled)


def _apply_profile(
    scene: bpy.types.Scene, profile: profiles.Profile, seed: int, frame_count: int, out: Path
) -> dict[str, Any]:
    """Set every render setting from the profile; return the device facts it established."""
    render = scene.render
    # The stubs type engine as the static enum (BLENDER_EEVEE only); at runtime it accepts every
    # registered engine (ADR-0001).
    untyped_render: Any = render
    untyped_render.engine = profile.engine
    render.resolution_x, render.resolution_y = profile.resolution
    render.resolution_percentage = 100
    render.fps = profile.fps
    render.fps_base = 1.0
    render.film_transparent = profile.film_transparent
    render.image_settings.file_format = profiles.FILE_FORMAT
    render.image_settings.color_mode = profiles.COLOR_MODE
    render.image_settings.color_depth = profiles.COLOR_DEPTH
    render.use_file_extension = True
    render.filepath = str(out / "frames" / "frame_####")
    view_settings = scene.view_settings
    if view_settings is None:
        raise RuntimeError("scene.view_settings is None")
    # The stubs type view_transform as Literal['NONE']: its items come from the OCIO config at
    # runtime, so assign through an untyped reference.
    untyped_view: Any = view_settings
    untyped_view.view_transform = profile.view_transform
    scene.frame_start = 1
    scene.frame_end = frame_count

    if profile.engine == "CYCLES":
        devices = _enable_metal_devices()
        # scene.cycles is the Cycles add-on's property group, not in the bpy stubs.
        cycles = getattr(scene, "cycles")  # noqa: B009
        cycles.device = profile.cycles_device
        cycles.samples = profile.samples
        cycles.use_adaptive_sampling = profile.cycles_adaptive_sampling
        cycles.use_denoising = profile.cycles_denoise
        cycles.seed = seed
        cycles.use_animated_seed = False
        if cycles.device != "GPU":
            raise RuntimeError(f"scene.cycles.device is {cycles.device!r}, expected 'GPU'")
        return {
            "engine_device": str(cycles.device),
            "cycles_compute_device_type": str(_cycles_preferences().compute_device_type),
            "cycles_devices": list(devices),
        }
    eevee = scene.eevee
    if eevee is None:
        raise RuntimeError("scene.eevee is None")
    eevee.taa_render_samples = profile.samples
    return {"engine_device": "GPU", "cycles_compute_device_type": None, "cycles_devices": []}


def _render_animation(scene: bpy.types.Scene) -> float:
    """Render frame_start..frame_end to render.filepath; returns wall seconds.

    STD-002/STD-003: rendering has no bpy.data equivalent, so this is the harness's one operator
    call and the only render call outside blender/probe/.
    """
    start = time.perf_counter()
    result = bpy.ops.render.render(animation=True, scene=scene.name)
    elapsed = time.perf_counter() - start
    if "FINISHED" not in result:
        raise RuntimeError(f"render returned {result}")
    return elapsed


def _gpu_backend() -> str:
    """Blender's GPU backend (e.g. METAL), as gpu.platform reports it after the render."""
    try:
        return str(gpu.platform.backend_type_get())
    except SystemError:
        # In background mode an EEVEE render initialises the gpu module (ADR-0001) but a Cycles
        # render does not, and gpu.platform raises until gpu.init() runs.
        gpu.init()
        return str(gpu.platform.backend_type_get())


def main() -> None:
    args = _parse_args()
    profile = profiles.PROFILES[args.profile]
    module, frame_count = _load_scene_script(args.scene)
    style_plan = _load_style_plan(args.style_plan)
    scene = bpy.context.scene
    if scene is None:
        raise RuntimeError("bpy.context.scene is None")
    _empty_factory_scene(scene)
    module.build(args.seed)
    for apply, params in style_plan:
        apply(params, scene)
    if scene.camera is None:
        raise RuntimeError(f"{args.scene}: build() left bpy.context.scene without a camera")
    device = _apply_profile(scene, profile, args.seed, frame_count, args.out)
    render_s = _render_animation(scene)

    frames = []
    for index in range(scene.frame_start, scene.frame_end + 1):
        path = Path(scene.render.frame_path(frame=index))
        if not path.is_file():
            raise RuntimeError(f"frame {index} was not written to {path}")
        frames.append({"index": index, "path": str(path)})
    result = {
        "engine": str(scene.render.engine),
        "device": {**device, "gpu_backend": _gpu_backend()},
        "blender_version": bpy.app.version_string,
        "blender_build_hash": bpy.app.build_hash.decode(),
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "samples": profile.samples,
        "frame_count": frame_count,
        "frames": frames,
        "render_s": render_s,
    }
    args.result.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
