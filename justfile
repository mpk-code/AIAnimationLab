# AIAnimationLab task runner. `just` runs repeatable tasks; the Makefile ONLY bootstraps the
# pinned toolchain (`make worktree-init`). Never move bootstrap into a recipe.
# Same search order as the Makefile's TOOL_PATH: this worktree's uv, then its just.
export PATH := justfile_directory() / ".toolchain/uv/bin" + ":" + justfile_directory() / ".toolchain/just/bin" + ":" + env_var("PATH")

# List the recipes
default:
    @just --list

# Read-only report of every prerequisite and pin
doctor:
    @bash scripts/doctor.sh

# The gate: every lane of scripts/run_tests.sh, in order (ADR-0002). An alias, not a second gate.
ci:
    @bash scripts/run_tests.sh

# Unit lane only (no Blender), for the per-edit loop
test:
    @bash scripts/run_tests.sh unit

# ruff check and ruff format --check (the static lane's first half)
lint:
    @bash scripts/run_tests.sh ruff

# mypy (the static lane's second half)
typecheck:
    @bash scripts/run_tests.sh mypy
