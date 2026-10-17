# AIAnimationLab

A Claude Code production system that turns a seed idea into a short Blender-rendered animation through staged, human-steerable decisions, built to test whether that output is measurably less generic than one-shot prompting.

- **Start here:** `docs/project-definition.md` (purpose, pipeline, milestones), then `CLAUDE.md` (studio doctrine).
- **Language:** `docs/glossary.md`. **Decisions:** `docs/adr/`.
- **Work in progress:** `sidequests/` (one folder per quest; quests are independent, with no release or main rollout above them).

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
