# AIAnimationLab

A Claude Code production system that turns a seed idea into a short Blender-rendered animation through staged, human-steerable decisions, built to test whether that output is measurably less generic than one-shot prompting.

- **Start here:** `docs/project-definition.md` (purpose, pipeline, milestones), then `CLAUDE.md` (studio doctrine).
- **Language:** `docs/glossary.md`. **Decisions:** `docs/adr/`.
- **Work in progress:** `sidequests/` (one folder per quest; quests are independent, with no release or main rollout above them).

## New machine

`make setup` brings up everything once the repo is on the machine. Before that, once per Mac:

1. Xcode command-line tools: `xcode-select --install` (provides `git` and `make`).
2. Homebrew from <https://brew.sh> (`make setup` runs `brew bundle`).
3. Blender at the version `make doctor` expects (`BLENDER_EXPECTED` in the `Makefile`), in `/Applications`. It is not installed through Homebrew, whose cask can't be pinned.
4. `git clone https://github.com/mpk-code/AIAnimationLab.git`, then `make setup` in the clone. Its last step, `make doctor`, must pass.
5. Add the Mac's `sysctl -n hw.model` to `MACHINE_LABELS` in `blender/harness/manifest.py` (and the schema's label enum) if it isn't there; renders refuse an unlabelled machine.

After that, `git pull` plus `make worktree-init` keeps a clone current. To collect a machine's reproducibility evidence (new machine, Blender bump, harness or profile change), run `scripts/collect_machine_evidence.sh` on a clean tree and send back the tarball it prints.

## Development workflow

Dev-process skills in `.claude/skills/` (ported from docketScore):

| Flow | Skills |
| --- | --- |
| Plan | `/grill` → `/sidequest` open → `/generate-rollout` |
| Build | `/run-process` (one run per session), `/commit` |
| Fix | `/bug-fix`, `/defect-filing` |
| Review | `/code-review`, `/complexity-review`, `/unit-test-review`, `/arch-review`, `/doc-review` |
| Long sessions | `/state-loop`, `/overseer` |
| Other | `/optimize`, `/sequence-diagram`, `/skill-creator`, `sw_engineer` |

Film pipeline stage skills live separately in `skills/<stage>/`.
