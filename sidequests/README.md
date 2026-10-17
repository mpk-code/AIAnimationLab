# Quests

All planned development work on the studio runs as a **quest**. A quest folder is a **narrative container**: it holds the rollout, status reports, fixes and (for spikes) findings. **Persistent specs live elsewhere** — in `docs/`, `schemas/`, `styles/` and `docs/adr/` — and each quest declares the ones it changes in its `spec-refs:` frontmatter field.

A quest is temporary (a plan with a beginning and an end). Specs, schemas and styles are persistent (they describe what the studio *is*). The quest folder captures the narrative; the persistent paths capture the system.

**No top-level structure.** There is no main rollout and there are no releases. Every quest is independent and of the same kind — a Blender API probe, a style module, a stage skill, a supporting utility, or a larger body of work such as building studio v1 (whose rollout's milestones are M0–M5 from `docs/project-definition.md` §Milestones). A quest may spawn another; the `parent:` field records that link and nothing else.

**Active vs archived.** While a quest is open it lives at `sidequests/<slug>/`. When it closes (`/sidequest close` or `/sidequest abandon`), the whole folder moves to `sidequests/archive/<slug>/` and a row is upserted into `sidequests/archive/index.md`. A slug exists in exactly one of those locations at a time — never both.

## Vocabulary and numbering

- A quest rollout is divided into **milestones** (`Milestone 1`, `Milestone 2`, …). Each milestone delivers a testable increment.
- Each milestone contains **runs**. A run is one 2–3 hour agentic session. Run IDs are `<milestone>.<run>` — `Run 2.3` is the third run of milestone 2.
- A run's status report is `sidequests/<slug>/status/run<milestone>.<run>status.md` (e.g. `run2.3status.md`).
- Example: the project definition's M0–M5 are the milestones of the studio v1 quest's rollout, so that quest's runs are numbered `0.1`, `0.2`, … for M0 and `1.1`, … for M1.
- In commit messages a run is cited `[R2.3]`, or `[<slug>-R2.3]` when the quest isn't obvious from context.

## The three types

Type lives in the rollout's frontmatter (`type:`), not in the directory name. Reclassification is a one-line edit (`/sidequest reclassify`).

### `spike` — throwaway experiment
- Goal: learn something (e.g. probe the installed Blender API).
- Code is assumed disposable unless explicitly promoted at close.
- `spec-refs: []`. Findings live in `sidequests/<slug>/findings.md`.

### `utility` — supporting code with its own lifecycle
- Outlives the quest and may be reused (e.g. a contact-sheet tool, a validator library).
- `spec-refs:` lists the persistent records of its contract: an ADR (`docs/adr/NNNN-<slug>.md`) and any schema it defines in `schemas/`. `/sidequest open` scaffolds the ADR from `docs/adr/0000-template.md` if absent.

### `feature` — a piece of the studio's scope, worked as its own quest
- E.g. a style module, a stage skill, a validator, or a body of work such as studio v1 (where a rollout milestone's exit gate comes from `docs/project-definition.md`).
- `spec-refs:` lists the persistent paths the quest will modify (`styles/<dimension>/<style-id>/style.yaml`, `schemas/<name>.schema.json`, `docs/glossary.md`, …).
- At close, the deliverable proposes changes to those paths; the user applies them via shown diffs.

**Default when uncertain: `spike`.** Lowest ceremony, easiest to upgrade later.

| Question | If yes → |
|---|---|
| Is the goal "find out whether X works" rather than "ship X"? | `spike` |
| Will the code keep living as shared infrastructure after this quest closes? | `utility` |
| Is it part of the studio's scope, to be shipped? | `feature` |
| Still unsure? | `spike` (reclassify later) |

## Directory layout

Quests live flat under `sidequests/<slug>/`; closed ones flat under `sidequests/archive/<slug>/`. Hierarchy is the `parent:` field, never nested directories.

```
sidequests/
  <slug>/                        # active quests
    <slug>-rollout.md            # required (frontmatter + body)
    findings.md                  # spike only
    plans/                       # optional ad-hoc planning artifacts
    status/
      run<N.M>status.md          # written by /run-process
      carry-forward.md           # routed cross-run handoffs (seeded by /generate-rollout)
    fixes/
      fix-<desc>-<YYYY-MM-DD>.md # written by /bug-fix when scoped
  archive/                       # closed quests (status: done | abandoned)
    index.md                     # managed by /sidequest only
    <slug>/                      # moved verbatim at close
```

Project-wide fix and review reports not tied to a quest go in `docs/plans/fixes/`; deferred items with revisit triggers go in `docs/plans/followups.md`.

## Frontmatter contract

Every quest rollout starts with:

```yaml
---
parent: none          # 'none' for a standalone quest, or the slug of the quest that spawned this one
type: spike           # spike | utility | feature
triggered-by: <run id or context>
purpose: <one sentence>
deliverable: <expected artifact, finding, or integration>
spec-refs: []         # persistent paths this quest changes (docs/, schemas/, styles/, docs/adr/); empty for spikes
status: active        # active | done | abandoned
integrated: false     # flipped to true by the user after applying proposed changes
opened: <YYYY-MM-DD>
worktree: .claude/worktrees/<slug>   # optional — omit unless a worktree was created
---
```

`spec-refs:` is the bridge between the quest and the persistent paths it changes. `/run-process` loads context from those paths. `integrated:` is the only field the user flips outside `/sidequest` — it tells the soft gate the deliverable has been applied (or consciously waived).

## Invoking from other skills

Use the phrase **`in sidequest <slug>`** (or `in quest <slug>`). `/run-process`, `/generate-rollout` and `/bug-fix` scope their paths to that quest. Without it they infer the quest from a `worktree-<slug>` branch, or from the only active quest, and otherwise ask.

Context that is always global: `docs/project-definition.md`, `docs/adr/`, `docs/glossary.md`, `docs/coding-standards.md`, `docs/test-strategy.md`, `CLAUDE.md`. When `spec-refs:` is empty, skills fall back to those.

## Lifecycle

- **Open:** `/sidequest open` — prompts for the frontmatter fields, scaffolds the folder (and, for utilities, the ADR stub), and, when the parent is another quest, adds a back-reference under the triggering run in the parent's rollout: `> spawned sidequest: <slug> (<type>)`. For `parent: none` no back-reference is written; persistent docs such as `docs/project-definition.md` are never auto-edited.
- **Plan:** `/generate-rollout in sidequest <slug>` — fills in milestones and runs and seeds `status/carry-forward.md`.
- **Run:** `/run-process in sidequest <slug>` — pre-flight, implementation, post-flight, status report.
- **Commit:** `/commit` — groups changes by unit of work and commits only after explicit approval.
- **Close:** `/sidequest close <slug>` — captures the deliverable, sets `status: done`, surfaces proposed changes as diffs, moves the folder to the archive, rewrites citations of the quest's files to their archived paths, and upserts the archive index. Never auto-edits persistent specs.
- **Abandon:** `/sidequest abandon <slug>` — closes as dropped: an `## Abandonment` block (reason + outstanding), `status: abandoned`, archived. Abandoned quests never trigger the soft gate.
- **Reopen:** `/sidequest reopen <slug>` — the only sanctioned way to amend a closed quest.
- **Reclassify:** `/sidequest reclassify <slug> <type>`.
- **Status:** `/sidequest status [<slug>|all|--all]`.

## The soft gate

`/run-process` pre-flight enumerates quest frontmatter in `sidequests/*/` and `sidequests/archive/*/`. Any quest with `status: done` and `integrated: false` whose `parent:` is the quest being run is surfaced as a warning, and the run asks for confirmation before proceeding. The type-specific condition for flipping `integrated: true`:

- **feature** — proposed changes applied to the `spec-refs:` paths (and any exit-gate evidence reviewed).
- **utility** — the persistent records at `spec-refs:` exist and reflect the as-shipped utility.
- **spike** — findings acknowledged.

It is a nudge, not a block — it prevents a closed quest's proposed changes from never landing.

## Don'ts

- Don't put specs inside a quest folder. They live at their persistent paths and are referenced via `spec-refs:`.
- Don't nest quest folders or sort them by type. Use `parent:` and `type:`.
- Don't auto-edit persistent specs at close — surface diffs for the user.
- Don't edit `sidequests/archive/index.md` or files under `sidequests/archive/<slug>/` by hand. Reopen first.
- Don't rewrite the `> spawned sidequest: <slug> (<type>)` back-reference at close. It is historical fact.
- Don't conflate these dev-process quests with productions. A film run lives in `productions/<id>/` and is driven by the pipeline stage skills in `skills/<stage>/`.
