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
