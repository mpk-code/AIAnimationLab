"""The toolchain pins agree with their one record each (ADR-0002, STD-001).

uv's pin is the Makefile's ``UV_VERSION``; ``uv.toml``'s ``required-version`` copies it. Python's
pin is ``.python-version``, which must equal Blender's bundled Python because harness code runs
both on the host and inside Blender. ``scripts/doctor.sh`` reports the installed tools; these tests
hold the files to each other.
"""

from __future__ import annotations

import platform
import re
import subprocess
import tomllib
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]


def _makefile_pin(name: str) -> str:
    # The same reading as scripts/doctor.sh's make_pin: `NAME := value`.
    text = (_ROOT / "Makefile").read_text(encoding="utf-8")
    match = re.search(rf"^{name}\s*:=\s*(\S+)", text, re.M)
    assert match, f"no `{name} :=` line in the Makefile"
    return match.group(1)


def _python_pin() -> str:
    return (_ROOT / ".python-version").read_text(encoding="utf-8").strip()


def _pyproject() -> dict[str, object]:
    return tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_uv_toml_required_version_is_the_makefile_uv_pin() -> None:
    uv_toml = tomllib.loads((_ROOT / "uv.toml").read_text(encoding="utf-8"))
    assert uv_toml.get("required-version") == f"=={_makefile_pin('UV_VERSION')}"


def test_pyproject_has_no_uv_table_for_uv_to_ignore() -> None:
    # uv ignores [tool.uv] in a pyproject.toml next to a uv.toml (with only a warning), so a pin
    # written there would look enforced and not be.
    tool = _pyproject().get("tool", {})
    assert isinstance(tool, dict)
    assert "uv" not in tool, "move [tool.uv] settings into uv.toml"


def test_requires_python_is_the_pinned_minor() -> None:
    major, minor, _patch = _python_pin().split(".")
    project = _pyproject()["project"]
    assert isinstance(project, dict)
    assert project["requires-python"] == f"=={major}.{minor}.*"


def test_the_running_interpreter_is_the_pin() -> None:
    assert platform.python_version() == _python_pin()


@pytest.mark.blender
def test_blenders_bundled_python_is_the_pin(blender_bin: Path) -> None:
    result = subprocess.run(
        [
            str(blender_bin),
            "--background",
            "--factory-startup",
            "--python-exit-code",
            "1",
            "--python-expr",
            "import platform; print('BUNDLED_PYTHON=' + platform.python_version())",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    found = re.search(r"^BUNDLED_PYTHON=(\S+)$", result.stdout, re.M)
    assert found, result.stdout
    assert found.group(1) == _python_pin()
