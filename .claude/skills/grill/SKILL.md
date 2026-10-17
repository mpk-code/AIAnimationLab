---
name: grill
description: >
  Concept-first interview about a new idea for the studio — a new stage, knob, style dimension,
  gate, validator, experiment or change to how the pipeline works — integrating it with the
  project's existing vocabulary, surfacing conflicts with concepts and decisions already in the
  project definition, glossary and ADRs, and emitting a proposed-changes document (edits to the
  project definition and glossary, plus draft ADRs) under docs/plans/grill/. Use for "I want to
  add...", "let's talk this idea through before I change the project definition", "help me think
  this through before we write it up", "interview me about this concept", "is this already in the
  pipeline somewhere?", "I'm not sure where this fits", or /grill. Not for building the thing —
  that is a quest (/sidequest, /run-process).
---

# Skill: Grill (Domain-Language Grilling for Ideas)

## Why this skill exists

AIAnimationLab has a project definition (hypotheses, scope, pipeline, control surface, milestones),
a glossary whose terms "mean exactly this in skills, code and conversation", and ADRs that amend
both. When a new idea arrives, the risk is not that its *what* and *why* are unclear. The risk is
that it arrives with new vocabulary that drifts from what the project already calls the same
thing — "look", "style", "style bible" and "treatment" all meaning roughly one thing — and the
next agent has to guess which is canonical. In this project vocabulary drift is also creative
drift: wording in skills and doctrine biases every stage.

This skill is the concept-first interview that prevents that drift. It speaks in plain creative
and production language — no paths, no schema field names, no ADR numbers — while internally
consulting the glossary, the project definition and the ADRs so it can recognize overlap and
surface it *conceptually*.

The output is one **proposed-changes document** with two audiences: a plain-language summary for
the user, and a technical handoff for the downstream agent (proposed glossary entries, a diff
against `docs/project-definition.md`, draft ADRs, precomputed `spec-refs:` for the recommended
quest). **Nothing is applied to the live docs by this skill.** Glossary terms and doctrine need an
ADR here, so every change is a proposal.

## Behavioral stance during a grill

- **Critical, not sycophantic.** If a proposed name or framing conflicts with existing vocabulary,
  say so and propose alternatives. Agreement that papers over a real overlap is a failure.
- **Translator, not stenographer.** When the user's words match an existing concept under another
  name, say so plainly. When they don't, capture the new word carefully — verbatim if the user has a
  strong preference, with a proposed canonical alternative when the word is loose.
- **Concept-first, ID-last.** The interview stays in conceptual space; paths, field names and ADR
  numbers are internal plumbing.
- **Proactive — help the user remember what they're forgetting.** When a new idea arrives, silently
  consult the glossary, project definition and ADRs, and *volunteer* any overlap.
- **Goal-anchored.** If the conversation drifts into adjacent territory, surface it: "We've drifted
  into how raters are recruited; pursue that here or open a separate session?"

## Sub-actions

| User intent | Sub-action |
|---|---|
| `/grill feature <name>` or "I want to add..." / "let's grill this idea" | **Feature** — primary use |
| `/grill start <plan> [in sidequest <slug>]` | **Plan** — stress-test an existing plan against current vocabulary |
| `/grill resolve <term>` (in an active session) | **Resolve** — settle one term |
| `/grill close` (in an active session) | **Close** — verify termination criteria, write the handoff |

If the intent is ambiguous, ask which — leading with **Feature**. A bare `/grill` followed by
something that reads like an idea defaults to Feature; confirm.

---

## Pre-flight checks

1. **Find the glossary.** Read `docs/glossary.md`. If it does not exist yet (it is created in M0),
   use the Glossary table in `docs/project-definition.md` as the current glossary and say so in the
   session file.
2. **Read the sources of truth:** `docs/project-definition.md` and the ADR index `docs/adr/README.md`
   (plus any ADR the idea plausibly touches). A later ADR wins over the project definition.
3. **Scope.** Default is `project` (project-wide). For "in sidequest <slug>" (`sidequest:<slug>`), verify `sidequests/<slug>/`
   exists and read the rollout's `spec-refs:` — those paths constrain what the handoff may propose
   to edit (fall back to `docs/project-definition.md` when empty, as for spikes).
4. **Soft integration warning.** In `sidequest:<slug>` scope, if any quest rollout under
   `sidequests/` or `sidequests/archive/` has `parent: <slug>`, `status: done` and
   `integrated: false` (`python3 -I .claude/skills/run-process/scripts/soft_gate.py --scope <slug>`
   lists them); in `project` scope, if any quest at all is done but unintegrated — say once, in
   plain language, before starting:

   > _"Before we start: <N> finished quests haven't had their proposed changes applied yet, so some
   > of the vocabulary we're about to use might still be in flux. Run anyway, or pause?"_

   A nudge, not a gate.

---

## Voice and register (the most important constraint)

The interview MUST:

- **Speak in concept names, not identifiers** — _"the rule that a knob only counts if a sweep shows
  it changes the frames"_, not a section name or ADR number.
- **Refer to project areas by plain names** — "the story stages", "the style bible", "the
  storyboard and animatic", "the render loop", "the gates", "the style library", "the anti-default
  lists", "the constraint decks", "the experiments".
- **Refer to prior decisions by what they decided** — "there's a decision to use one renderer for
  reproducibility tests and another for finals" — not by number.
- **Translate** — _"what you're describing sounds like what the project calls a 'draw' from a
  'deck' — same thing, or different?"_
- **Use short, plain sentences.** Define any technical word it must use.

The interview MUST NOT use ADR numbers, file paths or directory names, schema or YAML field names,
section anchors, code symbols (`bpy` calls, module names), or frontmatter fields. Refer to pipeline
stages by what they do ("the step that picks the look"), not by stage number or skill name.

These rules apply to **the interview only**. The handoff is written for the downstream agent and
**does** carry paths, ADR numbers and field names. Worked examples: `references/voice-and-register.md`.

---

## Sub-action: Feature (the primary case)

### Step 1 — Open the session

Session file:

- **Project scope:** `docs/plans/grill/<YYYY-MM-DD>-<topic-slug>.md`
- **Sidequest scope:** `sidequests/<slug>/grill/<YYYY-MM-DD>-<topic-slug>.md`

Create the directory if needed. The file is the working area *and* the handoff.

```yaml
---
topic: <topic-slug>
scope: project | sidequest:<slug>
opened: <YYYY-MM-DD>
status: active
canonical-concepts-touched: []
new-concepts-introduced: []
adrs-drafted: []
spec-refs-proposed: []           # precomputed list for the recommended quest
---
```

```markdown
# Grill session: <topic>

## What we're exploring
<one paragraph the user would recognize in two weeks>

## Interview transcript
<one-question / one-answer pairs; the narrative record, not the handoff>

## Concepts touched
### Already in the project (matched)
### New (introduced in this session)
### Renames or deprecations proposed

## Conflicts surfaced
<each conflict named conceptually + the user's resolution>

## Decisions drafted
<one-line plain summary per draft ADR; the full drafts live in the handoff>

## Proposed changes
### Plain-language summary (for you)
### Technical handoff (for the next agent)
```

### Step 2 — The opening interview

One question at a time, with a proposed answer when context supports one:

1. **What you want.** _"In a sentence — what do you want to add or change?"_ Capture verbatim.
2. **What it does.** _"Walk me through it — what happens in a production when this is there? Just
   the story; we'll worry about words later."_
3. **What part of the studio it touches** — propose the plain area name that fits best ("the story
   stages", "the look", "the storyboard", "the render loop", "the experiments"…); ask to confirm.
4. **When it happens** — before or after which gate? During a production, between productions, or
   only in experiments?

Stop after these four and let the user respond.

### Step 3 — The proactive cross-reference scan (the load-bearing affordance)

After the first substantive answer, **silently** consult the glossary, the project definition
(System concept, Pipeline, Control surface, Style library and lifecycle, Evaluation, Risks,
Milestones) and the ADRs. Look for:

- **Direct vocabulary matches** — a term already in the glossary.
- **Synonym matches** — a word an entry's "Avoid aliases" funnels to a canonical term.
- **Concept matches** — something the project already handles under another word.
- **Adjacent overlap** — areas the project already has rules about: gates and gate modes, the knob
  rule, the style lifecycle and fatigue, anti-defaults, separate-critic rule, render-only-through-
  the-harness, the out-of-scope list (rigging, diffusion models, other engines), deferred audio.

Then **volunteer the match-up in plain language, all at once**:

> _"Before we go further — what you just described touches three things the project already has:
> the way a style gets retired when it's overused, the lists of banned defaults, and the rule that
> a critic never grades its own work. Want me to walk through each, so we can see what's new?"_

This is the single most valuable thing the skill does. Do not skip it. If nothing overlaps, say so:

> _"This looks like new ground — nothing in the project overlaps with it yet. Let's keep going and
> I'll flag anything that comes up."_

### Step 4 — Iterate, one concept at a time

- **Same concept, different name:** ask whether to (a) adopt the project's name, (b) keep the new
  name and propose a rename, or (c) treat them as distinct concepts that overlap. Record the choice.
- **Conflicting concept** (overlaps, not the same): name the conflict and offer options — reuse the
  existing word, keep both with a different word for the new one, or merge. Never resolve
  unilaterally.
- **Genuinely new:** propose a short, plain canonical name in the glossary's register; confirm.
- **Stated intent contradicts the project:** _"You described it as <X>, but the project currently
  says <Y>. Which should change?"_ Never silently update either the user's words or the project.
  This includes the project's standing rules — e.g. an idea that adds a creative control must say
  how a later stage enforces it and how a sweep would show it moves the frames, or it isn't a knob
  yet; an idea that needs diffusion models or another engine collides with the v1 scope.
- **Record each resolved term in the session file** as a proposed glossary entry
  (`references/glossary-entry-structure.md`). Do not edit `docs/glossary.md` or the project
  definition — glossary changes need an ADR in this project. Renames carry an "Avoid aliases" line
  pointing to the canonical name.

### Step 5 — Draft ADRs where the project requires or warrants one

**Required** (per `docs/adr/README.md`): any change to a glossary term, to `CLAUDE.md` doctrine, to
an artifact schema after M1, or to the pinned Blender version. Every proposed glossary change is
paired with an ADR draft.

**Offer one** when the decision changes a hypothesis, scope line, pipeline stage, gate, control or
exit gate in the project definition; deliberately deviates from the obvious path; resolves a
conflict this session exposed; or has test or validator implications.

Frame the offer conceptually:

> _"This sounds like a decision worth recording — about whether the human picks at the storyboard
> or the harness does. I'll draft it for review; you'll see the plain version at the end."_

Never show the user the template, frontmatter or numbering. If the user isn't ready to decide,
capture the open question and continue. Drafting rules: `references/adr-template-pointer.md`.

### Step 6 — Iterate until the termination criteria are met

Not on a turn count.

---

## Sub-action: Plan

Same flow as Feature, starting from an already-articulated plan. Skip Step 2 questions the plan
already answers and go straight to Step 3 against the plan as written — catching the overlaps the
author missed is most of the value here. `in sidequest <slug>` rebases the session file to
`sidequests/<slug>/grill/` and constrains the handoff to that quest's `spec-refs:`.

## Sub-action: Resolve

Inside an active session, settle one term:

1. Look it up in the glossary; if present, restate the definition plainly and ask whether anything
   needs to change.
2. If absent, run Step 4's single-concept loop.
3. Record the result in the session file's "Concepts touched" and as a proposed entry.
4. Return to where the conversation was.

## Sub-action: Close

1. **Verify the termination criteria.** List any unmet ones in plain language; the user resolves
   them or explicitly waives them (record the waiver).
2. **Write the Proposed changes block** (both sections, same file — see "Handoff artifacts").
3. **Walk the user through Section 1 only.** If asked to see Section 2, show it, leading with: _"This
   is the structured version for the next agent; the readable version is above it."_
4. **Flip frontmatter** `status: complete`, set `closed: <YYYY-MM-DD>`.
5. **Print a short summary**: topic, recommended next action, session file path. **Do not commit.**

### Hard rules at close

- **Never apply the proposed changes.** They are proposals; the user (or an explicitly invoked
  downstream agent) applies them, glossary and doctrine changes through their ADRs.
- **Never set `integrated: true`** on the recommended quest — that is the user's signal that the
  changes landed.
- **Never record as agreed a term the user did not confirm.** Unconfirmed terms appear in the
  handoff marked unconfirmed.

---

## Scope-awareness

- **Project scope:** session file under `docs/plans/grill/`; the handoff proposes edits to
  `docs/project-definition.md`, `docs/glossary.md` and new ADRs under `docs/adr/`.
- **"in sidequest <slug>":** session file under `sidequests/<slug>/grill/`; proposed edits are
  limited to the quest's `spec-refs:` (fallback `docs/project-definition.md`).
- **The glossary and doctrine stay global.** A glossary change proposed in a sidequest session still
  targets `docs/glossary.md`, and the quest's `spec-refs:` should include it.

## When to use it

- Before opening a `feature` quest for a new idea — the usual next action is
  `/sidequest open feature <slug>` with the handoff's `spec-refs:`.
- Before `generate-rollout` or at `run-process` pre-flight, to check a run breakdown uses canonical
  vocabulary (glossary proposals only).
- During `bug-fix` root-cause analysis, when a defect is described in non-canonical words.
- Inside an active `state-loop`: resolved concepts append to the loop's Established Constraints.

---

## Termination criteria

The session ends when all three are true:

1. **Every concept the user introduced** is matched to a glossary term, has a confirmed proposed
   entry, or is explicitly noted out of scope.
2. **No open conflicts remain** between what the user described and the project definition, the
   glossary and the ADRs.
3. **The user can restate the idea in canonical vocabulary only**, without their original loose
   terms.

If any is false, the session is not done. Say what's missing; do not flip status.

---

## What this skill must not do

- Surface ADR numbers, paths, field names or code symbols in the interview.
- Edit `docs/project-definition.md`, `docs/glossary.md`, `CLAUDE.md`, ADRs, schemas or skills. It
  writes only the session file.
- Resolve a conflict between stated intent and existing material unilaterally.
- Propose a new ADR template, a second glossary, or a parallel hierarchy — the output locations are
  fixed.
- Run code, run tests, render, or modify source. Building belongs in the quest the handoff
  recommends.
- Commit. `commit` is the only commit path and needs the user's approval.

---

## Handoff artifacts at session close

One file (`docs/plans/grill/<YYYY-MM-DD>-<topic-slug>.md`, or the sidequest equivalent), whose
`## Proposed changes` block has two sections.

### Section 1 — Plain-language summary (for the user)

- New concepts introduced, in plain words.
- Conflicts surfaced and how they were resolved.
- What the glossary would gain or change.
- Each drafted decision in one sentence.
- The recommended next action, conceptually: _"Open a feature quest for the storyboard gate change;
  the proposed edits below go in with it."_

### Section 2 — Technical handoff (for the downstream agent)

- **Proposed glossary entries** — in the structure of `references/glossary-entry-structure.md`,
  each marked new / changed / renamed, each tied to the ADR draft that authorizes it.
- **Proposed project-definition edits** — a unified diff against `docs/project-definition.md`
  naming the sections touched (Hypotheses, Scope, Pipeline, Control surface, Style library,
  Artifact schemas, Evaluation, Risks, Milestones, Open questions).
- **Draft ADRs** — full drafts from `docs/adr/0000-template.md`, with the proposed file name
  `docs/adr/NNNN-<slug>.md` (next free number per `docs/adr/README.md`) and the index row to add.
  Status `Proposed`, or `Provisional` with a review trigger and expiry when the user wants it in
  force while being revisited. Drafts stay in this file until applied.
- **Precomputed `spec-refs:`** for the recommended quest — paths in `docs/`, `schemas/`, `styles/`
  or `docs/adr/`; always `docs/glossary.md` when glossary entries are proposed.
- **Other affected artifacts** — doctrine (`CLAUDE.md`), schemas, stage skills
  (`skills/<stage>/SKILL.md`), validators or anti-default lists the idea would touch, named so the
  quest can scope them. Not edited here.
- **State-loop back-references** — if a loop is active in scope, the lines to append to its
  Established Constraints, with evidence pointers.

---

## Anti-patterns

```
// WRONG: "per ADR 0003" or "the shots schema's camera_move field" in the interview
// Say what the decision decided, or "the list of camera moves a shot can use".

// WRONG: editing docs/glossary.md "inline" as terms resolve
// Glossary terms need an ADR here. Record a proposed entry in the session file.

// WRONG: silently renaming a concept the user introduced
// Propose the rename explicitly and let the user choose.

// WRONG: batching the cross-reference scan to the end
// It belongs after the first substantive answer, before the user invests in new words.

// WRONG: accepting a new "knob" with no enforcing stage and no sweep that would show it works
// Surface the project's knob rule as a conflict and let the user resolve it.

// WRONG: opening the quest from inside the skill
// Recommend it and precompute spec-refs; the user runs /sidequest open.

// WRONG: running the interview as a batch of questions
// One question at a time, with a proposed answer when context supports one.
```

---

## Interaction with other skills

- **`sidequest`** — the usual next step; the handoff's `spec-refs:` is its input. Grill never opens
  the quest.
- **`generate-rollout`** — runs after the quest exists; grill's vocabulary informs the run
  breakdown.
- **`run-process` / `bug-fix`** — directive skills. If a grill conclusion implies a run or a fix,
  recommend it in the handoff — never start coding.
- **`state-loop`** — a grill can run inside a loop; resolved concepts append to its Established
  Constraints.
- **`commit`** — the only commit path; the user invokes it to land the session file.

## Quick reference

| Situation | Action |
|---|---|
| "I want to add something that..." | `/grill feature <name>` |
| A written plan to stress-test against current vocabulary | `/grill start <plan>` |
| Settle one term mid-session | `/grill resolve <term>` |
| Done | `/grill close` — termination checks, write the handoff |
| User's word matches an existing concept | Translate: "sounds like X — same thing, or different?" |
| Idea changes a glossary term, doctrine or schema | Draft an ADR; describe it conceptually |

## Supporting files

- `references/glossary-entry-structure.md` — the shape of a proposed glossary entry.
- `references/adr-template-pointer.md` — how to draft ADRs from `docs/adr/0000-template.md`.
- `references/voice-and-register.md` — worked plain-language translations.
