"""Style-module registry: the one map from a style's `modules:` ids to Blender-side code.

A style module is a Python module under `blender/lib/<category>/<name>.py` that defines
`apply(params, scene)` (the `StyleModule` contract below). `render.py` looks every id up here on the
host, before Blender launches, so an unknown id fails with no frame written. Targets are
`"package.module:attr"` strings, not callables, because style modules import `bpy` and the host
cannot. `_inblender.py` imports them. No `bpy` import here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    import bpy

_DEFS_SCHEMA = Path(__file__).resolve().parents[2] / "schemas" / "_defs.schema.json"

# module id -> "importable.module:attr". Runs 1.3/1.4 add a row per module they ship.
MODULES: dict[str, str] = {}


class StyleModule(Protocol):
    """`params` is the resolved style: its parameters minus the envelope keys, with the style
    bible's overrides merged in (render.py). The module builds through `bpy.data` (STD-002) and
    sets no render settings (STD-003): the harness applies the profile after every module."""

    def __call__(self, params: dict[str, Any], scene: bpy.types.Scene) -> None: ...


class UnknownStyleModule(ValueError):
    """A style names a module id that is malformed or has no row in MODULES."""


def module_id_pattern() -> str:
    """The module-id pattern, read from its owner `schemas/_defs.schema.json` (STD-001)."""
    defs = json.loads(_DEFS_SCHEMA.read_text(encoding="utf-8"))
    pattern: str = defs["$defs"]["module_id"]["pattern"]
    return pattern


def target_for(module_id: str) -> str:
    """The import target registered for `module_id`; raises UnknownStyleModule."""
    pattern = module_id_pattern()
    if not re.fullmatch(pattern, module_id):
        raise UnknownStyleModule(f"style module id {module_id!r} does not match {pattern}")
    try:
        return MODULES[module_id]
    except KeyError:
        raise UnknownStyleModule(
            f"unknown style module {module_id!r}; registered: {sorted(MODULES) or 'none'} "
            "(blender/lib/registry.py MODULES)"
        ) from None
