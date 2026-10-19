"""Schema IO: the one way a stage reads or writes an artifact (STD-006).

Every artifact is validated against `schemas/<name>.schema.json` on read and on write; the
schemas `$ref` shared definitions in `schemas/_defs.schema.json`, resolved by `$id` through one
registry of every file in `schemas/`. YAML and JSON are chosen by file suffix. Both loaders refuse
duplicate keys, which PyYAML and `json` otherwise resolve silently to the last value.
"""

from __future__ import annotations

import copy
import json
import os
import tempfile
from collections.abc import Hashable, Mapping
from functools import cache
from pathlib import Path
from typing import Any

import jsonschema
import yaml
from referencing import Registry, Resource
from yaml.nodes import MappingNode

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = REPO_ROOT / "schemas"
_SCHEMA_SUFFIX = ".schema.json"
_YAML_SUFFIXES = frozenset({".yaml", ".yml"})


class ArtifactValidationError(ValueError):
    """An artifact does not match its schema. `errors` holds every (json_path, message) pair."""

    def __init__(self, source: Path | None, errors: list[tuple[str, str]]) -> None:
        self.source = source
        self.errors = errors
        where = f"{source}: " if source is not None else ""
        detail = "; ".join(f"{path}: {message}" for path, message in errors)
        super().__init__(f"{where}{len(errors)} schema error(s): {detail}")


def _schema_paths() -> dict[str, Path]:
    return {
        p.name.removesuffix(_SCHEMA_SUFFIX): p
        for p in sorted(SCHEMAS_DIR.glob(f"*{_SCHEMA_SUFFIX}"))
    }


@cache
def _registry() -> Registry[Any]:
    resources = []
    for path in _schema_paths().values():
        contents = json.loads(path.read_text())
        resources.append((contents["$id"], Resource.from_contents(contents)))
    return Registry().with_resources(resources)


@cache
def _validator(schema: str) -> jsonschema.Draft202012Validator:
    paths = _schema_paths()
    # _defs holds shared definitions, not an artifact shape; validating against it accepts anything.
    if schema.startswith("_") or schema not in paths:
        names = ", ".join(n for n in paths if not n.startswith("_"))
        raise ValueError(f"unknown artifact schema {schema!r}; known: {names}")
    contents = json.loads(paths[schema].read_text())
    return jsonschema.Draft202012Validator(contents, registry=_registry())


def validate_artifact(obj: Mapping[str, Any], schema: str, *, source: Path | None = None) -> None:
    """Raise `ArtifactValidationError` listing every error unless `obj` matches `schema`.

    `schema` is a file stem in `schemas/`, e.g. "shots" for `schemas/shots.schema.json`.
    """
    errors = sorted(
        (error.json_path, error.message) for error in _validator(schema).iter_errors(obj)
    )
    if errors:
        raise ArtifactValidationError(source, errors)


class _StrictSafeLoader(yaml.SafeLoader):
    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Hashable, Any]:
        seen: set[Hashable] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in seen:
                raise yaml.constructor.ConstructorError(
                    None, None, f"duplicate key {key!r}", key_node.start_mark
                )
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def _refuse_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key!r}")
        result[key] = value
    return result


def _format(path: Path) -> str:
    if path.suffix in _YAML_SUFFIXES:
        return "yaml"
    if path.suffix == ".json":
        return "json"
    raise ValueError(f"{path}: artifact files are .yaml, .yml or .json, not {path.suffix!r}")


def load_artifact(path: Path, schema: str) -> dict[str, Any]:
    """Parse `path` and return it once it validates against `schema`.

    Raises `ArtifactValidationError` on a schema mismatch, and `ValueError` (YAML or JSON parse
    errors included) on a bad suffix, a parse error or a duplicate key.
    """
    text = path.read_text()
    if _format(path) == "yaml":
        try:
            doc: Any = yaml.load(text, Loader=_StrictSafeLoader)
        except yaml.YAMLError as exc:
            raise ValueError(f"{path}: {exc}") from exc
    else:
        doc = json.loads(text, object_pairs_hook=_refuse_duplicate_json_keys)
    validate_artifact(doc, schema, source=path)
    # validate_artifact passed, and every artifact schema has "type": "object".
    return dict(doc)


def write_artifact(obj: Mapping[str, Any], path: Path, schema: str) -> None:
    """Validate `obj` against `schema`, then write it to `path` atomically.

    On any failure — schema, serialization, I/O — nothing is written and an existing file at
    `path` is left untouched.
    """
    validate_artifact(obj, schema, source=path)
    if _format(path) == "yaml":
        text = yaml.safe_dump(dict(obj), sort_keys=False, allow_unicode=True)
    else:
        text = json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


# The style envelope is whatever style.schema.json declares at its top level; every other key is a
# style parameter that modules receive (`style_params`).
STYLE_ENVELOPE_KEYS: frozenset[str] = frozenset(
    json.loads((SCHEMAS_DIR / f"style{_SCHEMA_SUFFIX}").read_text())["properties"]
)


def style_params(style: Mapping[str, Any]) -> dict[str, Any]:
    """The style's parameters: a deep copy of everything outside `STYLE_ENVELOPE_KEYS`."""
    return {k: copy.deepcopy(v) for k, v in style.items() if k not in STYLE_ENVELOPE_KEYS}


def merge_overrides(base: Mapping[str, Any], patch: Mapping[str, Any]) -> dict[str, Any]:
    """Deep-merge a style bible's `overrides[dimension]` patch over a style's parameters.

    Objects merge key by key, recursively; arrays and scalars in `patch` replace. Neither input is
    modified. The result is not validated: re-validate the merged style against "style".
    """
    merged = copy.deepcopy(dict(base))
    for key, value in patch.items():
        current = merged.get(key)
        if isinstance(current, Mapping) and isinstance(value, Mapping):
            merged[key] = merge_overrides(current, value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged
