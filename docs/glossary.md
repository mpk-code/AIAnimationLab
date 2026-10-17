# Glossary

The ubiquitous language of AIAnimationLab. These terms mean exactly this in skills, code and conversation. **Changes to any of them need an ADR** (`docs/adr/`). Seeded from `docs/project-definition.md` §Glossary.

| Term | Meaning |
| --- | --- |
| Production | One film run from seed to assembled output, stored in `productions/<id>/` |
| Seed | The human-written idea that starts a production |
| Deck | A curated list of constraints. A draw is a seeded random pick from a deck. |
| Anti-default | A banned pattern for a stage, kept in `antidefaults/<stage>.yaml` |
| Beat | A story unit: one change in situation or emotion |
| Shot | One continuous camera take, the unit of staging and rendering |
| Style | A versioned spec for one creative dimension, such as visual or storytelling |
| Style bible | A production's locked set of styles plus overrides |
| Style module | Reusable Blender code in `blender/lib/` that implements part of a style |
| Gate | A point where a human, or the harness during experiments, picks from options |
| Animatic | Blocking renders cut together on shot timing |
| Manifest | A per-production record of everything needed to reproduce it |
| Validator | A rule-based check of an artifact against its upstream artifacts |
| Critic | A model-based review run in a separate subagent context |

## Process terms

Used by the dev-process skills in `.claude/skills/`. Not film vocabulary.

| Term | Meaning |
| --- | --- |
| Quest | An independent unit of planned work with a rollout, in `sidequests/<slug>/`. Types: `spike`, `utility`, `feature`. There is no release or main rollout above quests. |
| Spike | A time-boxed investigation that answers a question, e.g. a Blender API probe |
| Rollout | A quest's plan: milestones broken into runs, each run sized for one agent session |
| Milestone | A group of runs inside one rollout, ending in an exit gate. M0–M5 in the project definition are the milestones of the studio v1 quest. |
| Run | One session-sized step of a rollout, numbered `<milestone>.<run>`, with acceptance criteria and a status report at `sidequests/<slug>/status/run<milestone>.<run>status.md` |
| Harness | The headless render runner in `blender/harness/`; the only way to render |
