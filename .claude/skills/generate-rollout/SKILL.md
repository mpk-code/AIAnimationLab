---
name: generate-rollout
description: >
  Fill in a quest rollout's body — milestones and runs, each run sized for one agentic session — in a
  rollout file /sidequest open already scaffolded. Use for "generate a rollout", "plan the
  rollout", "plan M1", "decompose this quest into runs", "build the run plan", "break this into
  runs", or /generate-rollout. Runs after a quest exists; opening and closing quests is
  /sidequest's job, executing runs is /run-process's.
---

# Skill: generate-rollout

Decompose a quest into a milestone-and-run plan, sized so each run is a single 2–3 hour agentic coding session. The quest must already be open (`/sidequest open`). Quests are independent — there is no main rollout.

| User intent | Target rollout file |
|---|---|
| "generate rollout in sidequest \<slug\>" / "plan \<slug\>" | `sidequests/<slug>/<slug>-rollout.md` |
| "plan M\<n\>" / "plan milestone \<n\> of \<slug\>" | the named milestone section of the quest whose rollout holds it (e.g. M1 of the studio v1 quest) |

If the scope is ambiguous (no slug, several active quests, or no quest whose rollout holds the named milestone), ask. If the work has no quest yet, tell the user to `/sidequest open` it first.

**Vocabulary** (from `sidequests/README.md`): a rollout is divided into **milestones**; each milestone has **runs**; a run ID is `<milestone>.<run>` and its status report is `sidequests/<slug>/status/run<milestone>.<run>status.md`. Example: the studio v1 quest's rollout milestones are the project definition's M0–M5 (`## Milestone 0`, …), so its runs are `0.1`, `0.2`, … for M0 and `1.1`, … for M1.

## Role

You are a senior systems architect and delivery planner. The output is a plan that the user plus an AI coding agent can execute run by run.

## Inputs to read before writing

Fill in the body only — not the frontmatter, not the deliverable template. Before generating, read:

1. **The rollout frontmatter** — `parent`, `type` (`spike` | `utility` | `feature`), `triggered-by`, `purpose`, `deliverable`, `spec-refs`.
2. **Each `spec-refs:` path** — existing docs/schemas/styles for `feature`; possibly a fresh ADR stub for `utility`; usually none for `spike`.
3. **`docs/project-definition.md`** — when the quest delivers project-definition milestones, their rows in §Milestones (scope and exit gate; for M0 also §M0: first quest); plus the sections the quest touches: §Hypotheses, §Scope, §Pipeline, §Control surface, §Style library, §Repository structure, §Artifact schemas, §Evaluation.
4. **`docs/adr/`** — ADRs that amend the project definition (a later ADR wins).
5. **`docs/glossary.md`**, **`docs/coding-standards.md`**, **`docs/test-strategy.md`** where they exist.
6. **Existing code** — `ls` the directories the quest will touch (`blender/`, `schemas/`, `validators/`, `skills/`, `styles/`, `eval/`, `tests/`, `scripts/`) so runs cite real paths.
7. **The parent quest's rollout** if `parent:` is a slug — the triggering run, related runs, constraints.
8. **`CLAUDE.md`** — Blender rules (render only through the harness, prefer `bpy.data`), global bans, ADR-gated changes.

If a critical input is missing — vague purpose, an exit gate that isn't testable, empty `spec-refs` that should have content, a deliverable template that doesn't match `type` — **flag it under `## Input Gaps` at the top of the body**: the gap, the assumption you made, and the input that would resolve it. Don't interview the user mid-generation.

## What you write (and do not write)

Edit the rollout **in place**:
- **Do not modify** the YAML frontmatter.
- **Do not modify** the `## Deliverable` template at the bottom — it stays empty until close.
- **Replace** the scaffold's `## Approach` placeholder with the plan body (see "Output structure"). If the deliverable template doesn't match `type`, flag it under `## Input Gaps`.

---

## Sizing rules — hold these firmly

### Run sizing
- A run completes in **one 2–3 hour agentic session** — code + tests + a brief demo (a test run, a preview render through the harness, a contact sheet). This is the hard constraint.
- Target ~200–600 lines of meaningful code. Soft target; the session constraint wins.
- Minimum ~1 hour of focused work. Below that, merge with an adjacent run.
- Touches **no more than 3–5 files or modules**.
- Done means: `scripts/run_tests.sh` passes and a demo can be produced.

### Milestone sizing
- Each milestone delivers a **testable increment** the user can exercise — a render reproduces, a validator passes on both styles, a stage writes a schema-valid artifact.
- Earlier milestones establish foundations; later milestones add richness.

### Parallelism
- Within a milestone, design runs for **maximum parallel execution** (separate sessions or worktrees) with minimal blocking.
- Where parallel runs must agree on an interface — a JSON Schema, a style-module function signature, a harness CLI flag, a manifest field — schedule a **contract-first run** early that defines it.
- Name **integration runs** explicitly — runs that wire parallel outputs together and verify them.

A milestone whose graph is fully sequential (`A → B → C → D`) is under-decomposed; find the contract-first run that unblocks parallel work.

---

## Quest-type guidance

### `spike`
- Runs are investigation-oriented: probes, prototypes, measurements. The deliverable is learning.
- Runs may be smaller than standard if one session yields a finding.
- Acceptance criteria are "a documented answer" or "a reproducible measurement" rather than "tests pass".
- The final run synthesizes `findings.md`; if the finding is a project-level decision, it drafts an ADR.

### `utility`
- The first run fills in the ADR (and any schema) at `spec-refs:` — a contract-first run the rest depend on.
- Later runs implement against it.

### `feature`
- Runs modify existing modules and the `spec-refs:` paths.
- A run that proposes a spec change notes it so it can be collected into `### Proposed changes to referenced persistent specs` at close.
- Style modules and stage skills: include a run that proves the knob or style actually moves the rendered frames (a sweep or a validator check), per the project's dead-knob rule.
- Schema changes after M1, glossary changes and `CLAUDE.md` changes need an ADR — plan a run that writes it.
- **Project-definition milestones** (e.g. the studio v1 quest, whose rollout milestones are M0–M5): each milestone's exit gate (`docs/project-definition.md` §Milestones) is its acceptance; the milestone ends with a run that demonstrates it with evidence (commands, hashes, manifests) for the `### Exit gate evidence` section.
- **M0 (greenfield):** Milestone 0 must include the prerequisites for parallel work: repo skeleton, `scripts/run_tests.sh` (pytest + ruff + mypy), the render harness contract (`blender/harness/render.py --scene <script> --profile preview|final --out <dir>`), the manifest writer, and the API-probe spike's ADR. Later milestones reuse that infrastructure.

### Quest-close review (`utility`, `feature`)

The final milestone ends with a **quest-close review** run that audits five dimensions and writes `sidequests/<slug>/status/run<milestone>.<run>status.md` with a pass / fail / triaged status per dimension and a "blocks closure?" verdict at the top:

1. **Reviews ran.** `/code-review` or `/complexity-review` ran against the implementation runs, with Critical/High findings fixed via `/bug-fix` or deferred with rationale. Stage skills and critics were reviewed in a separate subagent context from their author.
2. **Per-run discipline.** Each run has its status report; fixes went through `/bug-fix`; contract-first and TDD ordering were honored where the run's prompt strategy called for them.
3. **Knowledge promoted.** Every "Architecture Decisions" entry is classified *quest-local* or *project-level → ADR drafted under `docs/adr/`*. Every milestone-level "Key risks" entry and realized risk is classified *quest-local* or *durable → entry in `docs/plans/followups.md`*.
4. **Deferred findings routed.** Every deferred review finding, "Open Issues" item and `TODO:`/`FIXME:` in touched code gets one disposition: resolved here, surfaced to closure, promoted (ADR), filed as a new quest, filed to `docs/plans/followups.md`, or no action with rationale.
5. **Closure surface populated.** `### Proposed changes to referenced persistent specs` and `### Open questions surfaced` are filled so `/sidequest close` can present them.

No dimension is optional; if one doesn't apply, record why in one line.

---

## Plan overview (rollouts with 4+ milestones)

Include a top-level graph of how milestones connect, after `## Input Gaps` (if any) and before the first milestone. Text or mermaid.

## Milestone format

```markdown
## Milestone <N>: <Name>

**Theme:** <one-line value delivered>
**Testable capability:** <what the user can verify after this milestone>
**Session estimate:** <N sessions>
**Entry criteria:** <what must be true before this milestone starts>
**Exit criteria / Definition of Done:** <what must be true to finish this milestone>
**Testing strategy:** <unit | schema | validator | render smoke (preview profile) | determinism (EEVEE hash / Cycles tolerance) — and what infrastructure must exist>
**Key risks:** <top 1–3 risks for this milestone>

### Dependency graph

\`\`\`
<text or mermaid diagram of run sequencing and parallelism>
\`\`\`

### Run <N.M>: <Name>

- **Summary:** <2–3 sentences on what is built>
- **Scope:** <modules, stages, schemas, style modules, harness pieces touched>
- **Files/Modules:** <3–5 paths; for existing files mark each extend | refactor | integrate | replace>
- **Spec-refs touched:** <subset of the quest's spec-refs; mark each [Read] or [Modify]>
- **Traces to:** <the project-definition section, exit-gate item, or ADR this run serves, e.g. `docs/project-definition.md` §M0 Acceptance item 1>
- **Dependencies:** <run IDs that must complete first, or "None — can start immediately">
- **Integration points:** <interfaces, schemas, CLI flags, manifest fields produced or consumed>
- **Acceptance criteria:**
  - [ ] <specific, demonstrable criterion>
  - [ ] <specific, demonstrable criterion>
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** <1 session | 2 sessions — justify if >1>
- **Parallelizable with:** <run IDs in this milestone>
- **Prompt strategy:** <TDD | interface-first | spike-then-implement | straight-implementation; one-phrase justification>
- **Risk flags:** <NOVEL-TECH | COMPLEX-ALGO | UNCERTAIN-SCOPE | CRITICAL-PATH | none>
```

## The self-containment rule (the most important one)

Each run's `Summary + Scope + Files/Modules + Spec-refs touched + Integration points + Acceptance criteria + Prompt strategy` must form a complete agent prompt. Handing the run section plus its `spec-refs` to a coding agent should yield productive work without re-deriving context. If it can't, add detail or split the run.

For existing files, state the **nature of the change**: "touch `render.py`" is not enough; "extend `blender/harness/render.py` with a `--seed` flag recorded in the manifest" is.

## Quality bar — verify before saving

1. Frontmatter unchanged.
2. Deliverable template unchanged and matching `type`.
3. Every run fits one 2–3 hour session; any `2 sessions` run has a one-line justification.
4. Every run touches at most 3–5 files/modules.
5. Every milestone has a testable capability the user can exercise.
6. Each milestone's dependency graph shows real parallelism.
7. Contract-first runs precede the parallel runs that depend on them.
8. `NOVEL-TECH` / `COMPLEX-ALGO` runs (e.g. new Blender API surface) are scheduled early in their milestone.
9. Every run passes the self-containment test.
10. Every spec-ref a run cites appears in the frontmatter `spec-refs:`; otherwise flag it under `## Input Gaps`.
11. Input gaps are flagged, not silently filled.
12. The carry-forward ledger stub exists at `sidequests/<slug>/status/carry-forward.md`, and the body has the `## Carry-forward ledger` note.
13. Every render a run produces goes through the harness, and determinism-sensitive runs say which check applies (EEVEE exact hash or Cycles per-pixel tolerance).

## Example — dependency graph within a milestone

```
Milestone 2: Style survives
  ├── Run 2.1: style_bible JSON Schema + palette validator contract   ──┐ (contract-first)
  │         ↓                                                           │
  ├── Run 2.2: style module A (shaders/toon_ramp)                      ─┤ (parallel after 2.1)
  ├── Run 2.3: style module B (lines/ink)                              ─┤
  ├── Run 2.4: camera-grammar validator                                ─┘
  │         ↓
  └── Run 2.5: render both styles through the harness; validators pass (depends on 2.2–2.4)
```

## Carry-forward ledger (seed it)

`/run-process` carries routed cross-run knowledge — a contract a later run must reuse, a gotcha, a decision deferred to its first consumer — through one cumulative **carry-forward ledger** per quest, which pre-flight reads (filtered to the starting run) and post-flight appends to. It is how a run that starts after a context clear inherits what earlier runs learned.

1. **Create the stub** at `sidequests/<slug>/status/carry-forward.md` with this exact header and no entries:

   ```markdown
   # Carry-forward ledger — <slug>

   > Cumulative, machine-loaded channel for routed cross-run handoffs. `/run-process` pre-flight
   > prints the entries routed to the run being started; post-flight appends a run's handoffs.
   > Format — one routed conclusion per line, ≤5 per run:
   >
   >     - [<from-run>] -> <targets> | <class> | <one-line conclusion>
   >
   > <targets>: comma-separated run IDs (no spaces), and/or `surface` (any run, any quest, on this
   > surface) / `quest` (any later run here). <class>: contract | gotcha | deferred | decision.
   > ROUTING RULE: an entry exists ONLY if addressed to a future audience — un-routed noise stays
   > in the status report's Open Issues. See the run-process "Carry-forward ledger" section.
   ```

2. **Point at it** with the `## Carry-forward ledger` note in the body.

Don't pre-populate entries. Where a contract-first run has obvious consumers, say so in its `Integration points` so it knows to route a `contract` line forward.

## Output structure

Replace the scaffold's `## Approach` section with:

```markdown
## Input Gaps          <!-- only if gaps exist -->
- <gap>: <assumption made> — <input that would resolve it>

## Plan overview       <!-- only if 4+ milestones -->
<top-level graph across milestones>

## Carry-forward ledger
Routed cross-run handoffs for this quest accumulate in `sidequests/<slug>/status/carry-forward.md`.
`/run-process` reads it at pre-flight and appends at post-flight. Routed items only.

## Milestone 1: <Name>
...

## Milestone 2: <Name>
...
```

Keep the scaffold's `## Context`, `## Spec refs` and `## Runs` sections. Headings start at H2.

## Constraints

- **Never modify the frontmatter** — it is the contract with the rest of the workflow.
- **Never fill in `## Deliverable`** — that happens at `/sidequest close`.
- **Never silently add to `spec-refs:`** — flag under `## Input Gaps`.
- **Never commit.** The user runs `/commit`.
- **Don't interview mid-generation** — surface uncertainty under `## Input Gaps`.
- **Don't pad runs** — merge anything under ~1 hour.
- **Don't plan film productions here.** Producing a film is a pipeline run in `productions/<id>/`; a quest builds the studio that makes it.

## Anti-patterns

```
// WRONG: rewriting the frontmatter to "fix" missing spec-refs
// Flag it under ## Input Gaps; the user updates spec-refs deliberately.

// WRONG: filling in ## Deliverable during planning
// Deliverable is a closure artifact.

// WRONG: naming rollout groupings "Leg 1, Leg 2" or "Phase 1, Phase 2"
// Rollouts have milestones (Milestone 1, Milestone 2); run IDs are <milestone>.<run>.

// WRONG: a milestone whose graph is A → B → C → D → E
// Find the contract-first run (a schema, a harness flag) that unblocks parallel work.

// WRONG: "implement the palette validator" with no file list
// Self-containment requires concrete paths and acceptance criteria.

// WRONG: a run whose acceptance is "render looks right"
// Name the check: a validator passing, a frame hash matching, a contact sheet the user reviews.

// WRONG: scheduling a NOVEL-TECH Blender API run last in its milestone
// Risky work goes early so failures surface while there's time to react.
```
