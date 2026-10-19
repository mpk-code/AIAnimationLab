"""The harness CLI refuses bad input before launching Blender, and renders a scene by profile.

Unit tests drive `render.main` in-process; the blender-marked tests run `render.py` as a script, the
way CLAUDE.md §Blender invokes it.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from blender.harness import profiles, render

_ROOT = Path(__file__).resolve().parents[1]
_RENDER_PY = _ROOT / "blender" / "harness" / "render.py"

# Test fixture: a 2-frame scene (one plane, one camera) built into bpy.context.scene per the
# scene-script contract (ADR-0002). Its literals are fixture inputs, not style choices.
_TWO_FRAME_SCENE = """
import bpy

FRAME_COUNT = 2


def build(seed: int) -> None:
    scene = bpy.context.scene
    mesh = bpy.data.meshes.new("fixture_plane")
    mesh.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)])
    plane = bpy.data.objects.new("fixture_plane", mesh)
    plane.location.x = seed * 0.01
    scene.collection.objects.link(plane)
    camera = bpy.data.objects.new("fixture_camera", bpy.data.cameras.new("fixture_camera"))
    camera.location = (0.0, 0.0, 5.0)
    scene.collection.objects.link(camera)
    scene.camera = camera
"""


@pytest.fixture
def scene_script(tmp_path: Path) -> Path:
    path = tmp_path / "two_frame_scene.py"
    path.write_text(_TWO_FRAME_SCENE, encoding="utf-8")
    return path


def _argv(scene: Path, out: Path, /, **overrides: str | None) -> list[str]:
    flags: dict[str, str | None] = {
        "--scene": str(scene),
        "--profile": "preview",
        "--out": str(out),
        "--seed": "0",
        "--model-id": "fixture/test_harness_cli",
    }
    flags.update({f"--{k.replace('_', '-')}": v for k, v in overrides.items()})
    argv: list[str] = []
    for flag, value in flags.items():
        if value is not None:
            argv += [flag, value]
    return argv


@pytest.fixture
def no_blender(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail the test if the CLI gets as far as launching Blender."""

    def launched(*args: object, **kwargs: object) -> None:
        raise AssertionError("Blender was launched despite invalid arguments")

    monkeypatch.setattr(subprocess, "run", launched)
    monkeypatch.delenv(render.MODEL_ID_ENV, raising=False)


@pytest.mark.usefixtures("no_blender")
@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"profile": "draft"}, "invalid choice: 'draft'"),
        ({"scene": None}, "--scene"),
        ({"model_id": None}, "a model ID is required"),
        ({"seed": None}, "--seed"),
        ({"seed": "abc"}, "invalid int value"),
    ],
    ids=["unknown-profile", "missing-scene", "missing-model-id", "missing-seed", "bad-seed"],
)
def test_invalid_arguments_exit_non_zero_with_a_message(
    scene_script: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    overrides: dict[str, str | None],
    message: str,
) -> None:
    with pytest.raises(SystemExit) as exc:
        render.main(_argv(scene_script, tmp_path / "out", **overrides))
    assert exc.value.code != 0
    assert message in capsys.readouterr().err


@pytest.mark.usefixtures("no_blender")
def test_a_scene_path_that_is_not_a_file_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exc:
        render.main(_argv(tmp_path / "missing.py", tmp_path / "out"))
    assert exc.value.code != 0
    assert "is not a file" in capsys.readouterr().err


@pytest.mark.usefixtures("no_blender")
def test_a_non_empty_frames_dir_is_refused(
    scene_script: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "out"
    (out / "frames").mkdir(parents=True)
    (out / "frames" / "frame_0001.png").write_bytes(b"stale")
    assert render.main(_argv(scene_script, out)) == 1
    assert "is not empty" in capsys.readouterr().err


def test_the_model_id_falls_back_to_the_environment(
    scene_script: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(render.MODEL_ID_ENV, "fixture/from-env")
    args = render._parse_args(_argv(scene_script, tmp_path, model_id=None))
    assert args.model_id == "fixture/from-env"


@pytest.mark.parametrize(
    ("stem", "expected"),
    [("plain_scene", "t-plain_scene"), ("Two Frame.v2", "t-two-frame-v2")],
)
def test_production_id_is_t_plus_the_normalised_scene_stem(stem: str, expected: str) -> None:
    assert render.production_id_for(Path(f"{stem}.py")) == expected


def test_a_stem_that_cannot_be_normalised_is_refused() -> None:
    with pytest.raises(render.HarnessError, match="rename the scene script"):
        render.production_id_for(Path("_hidden.py"))


def test_the_cli_profile_choices_are_the_profile_table() -> None:
    assert set(profiles.PROFILES) == {"preview", "final"}
    for name, profile in profiles.PROFILES.items():
        assert profile.name == name


def test_preview_is_eevee_and_final_is_cycles_on_the_gpu() -> None:
    assert profiles.PROFILES["preview"].engine == "BLENDER_EEVEE"
    final = profiles.PROFILES["final"]
    assert (final.engine, final.cycles_device) == ("CYCLES", "GPU")
    # ADR-0001's Cycles tolerance was measured with denoise off.
    assert final.cycles_denoise is False


def _render(scene: Path, out: Path, profile: str, blender_bin: Path, test_name: str) -> None:
    command = [sys.executable, str(_RENDER_PY), *_argv(scene, out, profile=profile)]
    command[command.index("--model-id") + 1] = f"fixture/{test_name}"
    completed = subprocess.run(
        command, env={**os.environ, "BLENDER_BIN": str(blender_bin)}, check=False
    )
    assert completed.returncode == 0


@pytest.mark.blender
def test_preview_renders_a_two_frame_scene_to_frames_dir(
    scene_script: Path, tmp_path: Path, blender_bin: Path
) -> None:
    out = tmp_path / "out"
    _render(scene_script, out, "preview", blender_bin, "test_preview_renders_a_two_frame_scene")
    assert sorted(p.name for p in (out / "frames").iterdir()) == [
        "frame_0001.png",
        "frame_0002.png",
    ]


@pytest.mark.blender
def test_preview_run_result_records_engine_device_and_blender(
    scene_script: Path, tmp_path: Path, blender_bin: Path
) -> None:
    result = render.run_render(
        scene_script,
        "preview",
        tmp_path / "out",
        7,
        "fixture/test_preview_run_result",
        blender_bin,
        style_bible=None,
    )
    assert result.production_id == "t-two_frame_scene"
    assert (result.engine, result.device.engine_device) == ("BLENDER_EEVEE", "GPU")
    assert result.device.gpu_backend == "METAL"
    assert result.device.cycles_compute_device_type is None
    assert result.blender_version.startswith("5.2.2")
    assert len(result.blender_build_hash) > 0
    assert (result.seed, result.resolution, result.frame_count) == (7, (640, 360), 2)
    assert [f.index for f in result.frames] == [1, 2]
    assert all(f.path.is_file() for f in result.frames)
    assert 0 < result.timings.render_s < result.timings.wall_s
    assert (result.styles, result.style_bible) == ({}, None)


@pytest.mark.blender
def test_final_renders_on_cycles_with_the_metal_gpu(tmp_path: Path, blender_bin: Path) -> None:
    scene = tmp_path / "one_frame_scene.py"
    scene.write_text(_TWO_FRAME_SCENE.replace("FRAME_COUNT = 2", "FRAME_COUNT = 1"), "utf-8")
    result = render.run_render(
        scene,
        "final",
        tmp_path / "out",
        0,
        "fixture/test_final_renders_on_cycles",
        blender_bin,
        style_bible=None,
    )
    assert result.engine == "CYCLES"
    assert result.device.engine_device == "GPU"
    assert result.device.cycles_compute_device_type == "METAL"
    assert result.device.cycles_devices
    assert [f.path.name for f in result.frames] == ["frame_0001.png"]
