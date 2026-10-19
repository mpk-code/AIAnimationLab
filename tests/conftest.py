"""Shared fixtures. Tests marked ``blender`` run against ``BLENDER_BIN`` and are skipped, with the
path in the reason, when it is not an executable file — never silently dropped."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# scripts/run_tests.sh's blender lane repeats this path for its banner.
from blender.harness.render import DEFAULT_BLENDER_BIN as _DEFAULT_BLENDER_BIN


def _blender_bin() -> Path:
    return Path(os.environ.get("BLENDER_BIN", _DEFAULT_BLENDER_BIN))


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    binary = _blender_bin()
    if binary.is_file() and os.access(binary, os.X_OK):
        return
    skip = pytest.mark.skip(reason=f"BLENDER_BIN is not executable: {binary}")
    for item in items:
        if "blender" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def blender_bin() -> Path:
    return _blender_bin()
