# AIAnimationLab bootstrap. `make` ONLY bootstraps the pinned toolchain; `just` runs repeatable
# tasks (./justfile). Ported, slimmed, from docketScore's Makefile.
REPO_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
UV_HOME   := $(REPO_ROOT)/.toolchain/uv
JUST_HOME := $(REPO_ROOT)/.toolchain/just

# Toolchain pins, each one exact version. scripts/install_tool.sh and scripts/doctor.sh read them
# from here. uv.toml's required-version copies UV_VERSION. Host Python (.python-version) equals
# Blender's bundled Python, so it moves when Blender does.
UV_VERSION   := 0.12.24
JUST_VERSION := 1.53.0
# The Blender doctor expects. Warn-only, not a pin, until ADR-0004 pins Blender (rollout Run 5.1).
BLENDER_EXPECTED := 5.2.2

# The one statement of the tool search order: this worktree's uv, then its just, then the caller's.
TOOL_PATH := PATH="$(UV_HOME)/bin:$(JUST_HOME)/bin:$$PATH"

.DEFAULT_GOAL := help
.PHONY: help tooling-bootstrap worktree-init setup doctor

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' Makefile \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# `uv python install --no-bin` puts uv's own build in its per-machine store with no python3.N on
# PATH; uv.toml's python-preference = "only-managed" keeps a machine Python from being picked.
tooling-bootstrap: ## Install pinned uv and just into .toolchain/ and uv's build of the .python-version Python
	@bash scripts/install_tool.sh uv
	@bash scripts/install_tool.sh just
	@$(TOOL_PATH) uv python install --no-bin "$$(tr -d '[:space:]' < .python-version)"
	@bash scripts/check_tool_version.sh "$(UV_HOME)/bin/uv" $(UV_VERSION) "make tooling-bootstrap"
	@bash scripts/check_tool_version.sh "$(JUST_HOME)/bin/just" $(JUST_VERSION) "make tooling-bootstrap"

worktree-init: tooling-bootstrap ## Bring up this worktree: toolchain, then uv sync once a pyproject.toml exists
	@if [ -f pyproject.toml ]; then $(TOOL_PATH) uv sync --locked; else echo "==> no pyproject.toml yet; skipping uv sync"; fi

setup: ## New machine: brew bundle (Brewfile), worktree-init, then doctor
	brew bundle --file="$(REPO_ROOT)/Brewfile"
	@$(MAKE) worktree-init
	@$(MAKE) doctor

doctor: ## Read-only report of every prerequisite and pin; exits 1 when anything needs action
	@bash scripts/doctor.sh
