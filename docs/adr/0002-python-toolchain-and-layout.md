---
id: 0002
title: Python toolchain, test gate, host-side package layout and scene-script contract
status: Proposed
date: 2026-10-19
supersedes: N/A
superseded-by: N/A
---

# 0002: Python toolchain, test gate, host-side package layout and scene-script contract

## Status

Proposed. Raised by quest `studio-v1` Run 0.2 (`sidequests/studio-v1/studio-v1-rollout.md`, Run 0.2). Includes a `CLAUDE.md` amendment that the user confirmed on 2026-10-19 and that was applied in the same run.

## Context

M0 needs one test gate before the harness, the manifest and the test scene are built (`docs/project-definition.md` §Milestones, M0). Pure-Python harness code runs both on the host and inside Blender, so the host interpreter has to be Blender's. §Repository structure has no home for host-side orchestration code (draws, gates, schema IO, the stage runner). That gap is listed in the rollout's Input Gaps. Runs 0.4–0.6 each need the same scene-script interface.

## Decision

- **Toolchain:** `make` only bootstraps the pinned uv, just and Python (`make setup` / `make worktree-init` / `make doctor`) and `just` runs tasks. Host Python is exactly Blender's bundled Python (`.python-version`). `uv.toml` is the only uv configuration, so `pyproject.toml` has no `[tool.uv]` table. Dependencies are locked in `uv.lock`, and `bpy` is typed against the exact-pinned `fake-bpy-module-<Blender minor>` stubs.
- **Gate:** `scripts/run_tests.sh` is the one canonical gate. It runs these lanes in this order and stops at the first failure: environment (`scripts/doctor.sh`) → locks (`uv lock --check`) → static (ruff check, ruff format --check, mypy strict over the repo minus `.claude/`) → unit (`pytest -m "not blender"`) → blender (`pytest -m blender`). It reports the blender lane as skipped, loudly, when `BLENDER_BIN` does not resolve. `just ci` is its alias, and `just test` / `lint` / `typecheck` run single lanes of it.
- **Layout:** host-side orchestration lives in a top-level `studio/` package, `validators/` and `eval/` are their own packages, `blender/lib/` holds Blender-side style modules, `blender/harness/` holds the host-side harness CLI and its in-Blender entry, and `blender/probe/` holds the in-Blender API probe (ADR-0001). Each directory is created by the first run that puts code in it.
- **Scene-script contract:** a scene script is a Python module that defines `build(seed: int) -> None` and a module-level `FRAME_COUNT: int`. It builds the scene only through `bpy.data` (STD-002) and sets no render settings or output paths (STD-003). The harness's in-Blender entry inserts the repository root at the front of `sys.path` before importing it, so scene scripts and style modules import repo packages by their full name (`blender.lib.…`, `studio.…`).

### `CLAUDE.md` amendment (applied in Run 0.2)

```diff
 ## Blender
 
+- Bootstrap a machine with `make setup`, a worktree with `make worktree-init`; check it with `make doctor`. `make` only bootstraps; `just` runs tasks.
 - Blender **5.2.2 LTS** (`/Applications/Blender.app/Contents/MacOS/Blender`). Not yet pinned; record the version in every manifest. Pin before E1.
@@
 ## Tests
 
-`scripts/run_tests.sh` is the canonical runner (pytest + ruff + mypy; created in M0). Don't construct ad-hoc pytest command lines for gate decisions. Render smoke tests run the preview profile through the harness.
+`scripts/run_tests.sh` is the canonical runner (lanes in order: doctor → `uv lock --check` → ruff/mypy → unit → blender); `just ci` is its alias, never a second gate. Don't construct ad-hoc pytest command lines for gate decisions. Render smoke tests run the preview profile through the harness.
```

## Alternatives considered

| Alternative | Why not chosen |
| --- | --- |
| uv settings in `pyproject.toml` `[tool.uv]`, with `uv.toml` deleted | Equivalent for the root project, but `uv.toml` also covers uv commands run outside the project, and Run 0.1 already made it the pin's copy. Keeping both files is not possible: uv 0.12.24 ignores `[tool.uv]` next to a `uv.toml` and only warns (seen in Run 0.2). |
| `ignore_missing_imports` for `bpy` / `mathutils` instead of stubs | Every `bpy` call becomes `Any`. mypy would catch no Blender API misuse, which works against §Risks "Blender API drift". |
| just recipes that restate the lane commands | That would be a second definition of the gate, which can drift from `scripts/run_tests.sh`. |
| shellcheck in the static lane | Not in the rollout's lane list. Deferred to `docs/plans/followups.md`. |
| Host-side code under `blender/` | It mixes code that runs on the host with code that must import inside Blender. |
| Scene scripts that set render settings | Breaks STD-003: render profiles must be the harness's alone. |

## Consequences

- Every later run builds against one gate and one scene interface. Runs 0.4–0.6 import `build` / `FRAME_COUNT` rather than inventing their own.
- `tests/test_toolchain_pins.py` holds `uv.toml` `required-version` equal to the Makefile's `UV_VERSION`, holds `pyproject.toml` free of `[tool.uv]`, holds `requires-python` to the pinned minor, and checks that the running interpreter and Blender's bundled Python equal `.python-version`.
- The `fake-bpy-module-5.2` pin moves with the Blender pin (ADR-0004, Run 5.1), together with `.python-version` and the Makefile's `BLENDER_EXPECTED`.
- The environment lane needs `/Applications/Blender.app`, because doctor FAILs without it. On a machine without Blender the gate therefore cannot pass. Only a `BLENDER_BIN` override reaches the loud-skip path.
- ruff and mypy exclude `.claude/`. The dev-process skills' scripts are ported tooling, not studio code.
