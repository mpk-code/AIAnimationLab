"""Test-only style module: changes nothing in the scene and logs each call.

Never registered in `blender/lib/registry.py`; tests/test_style_registry.py monkeypatches it in as
`testing/noop`. Each call appends the params it received, as one JSON line, to the file named by
the NOOP_LOG_ENV environment variable, which reaches Blender because the harness passes its
environment through.
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # Type-only, so host-side tests can import NOOP_LOG_ENV without Blender.
    import bpy

NOOP_LOG_ENV = "AIAL_TEST_NOOP_LOG"


def apply(params: dict[str, Any], scene: bpy.types.Scene) -> None:
    with open(os.environ[NOOP_LOG_ENV], "a", encoding="utf-8") as log:
        log.write(json.dumps({"scene": scene.name, "params": params}, sort_keys=True) + "\n")
