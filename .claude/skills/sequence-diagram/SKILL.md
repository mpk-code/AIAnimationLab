---
name: sequence-diagram
description: >
  Author and maintain narrated sequence diagrams — prose design intent paired with a Mermaid
  sequenceDiagram fence, embedded in the design doc it illustrates (an ADR, a quest rollout, a
  section of docs/). Three verbs: create, update, drift-check. Use for "draw a sequence diagram",
  "diagram this interaction", "show how the harness calls the scene script", "document who calls
  whom", "add a sequence diagram to <doc>", "check my diagrams for drift", or /sequence-diagram.
  Not for flowcharts, gantt, or class diagrams, and not a renderer.
---

# Skill: sequence-diagram

Author and maintain **narrated sequence diagrams**: a prose narrative and a Mermaid
`sequenceDiagram` fence, as a pair, under a heading of their own, inside the doc they
illustrate.

## The invariant every verb preserves

**Prose is design intent — canonical. The diagram is a derived projection.** On any
divergence, the diagram is regenerated from the prose; the prose is never rewritten to
match a stale diagram.

## Authoring rules

1. **Heading, then prose, then fence.** The prose (1–3 paragraphs) says who calls whom, in
   what order, and why. Every important rationale is a plain "so that …" clause. Write for a
   human reader: plain language, spell out a term the first time, bold only a warning or a
   critical term (never the "so that" clauses or participant names).
2. **Participants** are the interacting elements (modules, classes, Blender, the harness, the
   user as `actor`). Group a module's participants in `box ModuleName … end`; use
   `participant Alias as qualified.Name` when the qualified name helps. Collapse a module to
   one participant when its internals don't matter here; an external system is one participant.
3. **Sanctioned features only:** `participant`/`actor`, sync `->>` and reply `-->>` arrows,
   activation `+`/`-`, `alt`/`else`, `opt`, `loop`, `par`/`and`, `break`,
   `Note over/left of/right of`, `box`, `autonumber`. Construction reads as a call:
   `A->>B: new(arg1, arg2)`.
4. **Width budget:** at most ~12 participants and ~40 messages. Wider than that, split into
   linked diagrams, one per phase, each with its own narrative.
5. **Gotchas:**
   - Never `;` inside message or Note text — it is a Mermaid statement separator. Use `—` or `,`.
   - Never parentheses in a `box <color> <label>` title — they break color parsing.
     Parentheses in message text are fine.
   - Always a heading before each narrated block.

**Self-check before returning:** prose precedes fence; every "so that" in the diagram's
logic appears in the prose; no `;` in labels; no `(` in box titles; features within the
sanctioned list; budget respected.

## Verb: create

Input: an interaction described in conversation (any fidelity — "object1 calls method1 on
object2" up to a full architectural narrative), plus a target design doc.

1. Ground the interaction: if it concerns real code (the render harness, a validator, a
   stage skill's handoff), read the sources and `docs/project-definition.md` so participants
   and calls are true, not invented. Ask the user only when the interaction itself is
   ambiguous (which component owns a step, sync vs. async).
2. Author the narrated pair **into the doc it illustrates** — never a standalone diagram dump.
3. Self-check, then verify the fence renders (GitHub, VS Code, Obsidian or any Mermaid
   renderer).

## Verb: update

Input: an existing narrated pair + a described change (or a direct prose edit).

1. Apply the change to the **prose first** — it is the canonical channel.
2. Regenerate the fence from the updated prose (full re-derivation, not a patch —
   partial diagram edits are how drift starts).
3. Never alter the prose to accommodate what the old diagram happened to say.
4. Self-check + render-verify as in create.

## Verb: drift-check

Input: a doc (or glob) containing narrated pairs.

For each fence: read its paired prose, re-derive what the diagram *should* contain
(participants, boxes, call order, fragments, notes), and diff against the actual fence.
Report per diagram: **in-sync** | **drifted** (with the specific divergences: missing/extra
calls, renamed participants, rationale in the diagram absent from prose) | **orphaned**
(fence with no preceding narrative). Offer to regenerate drifted fences from their prose
(that is an `update`).

## Rendering

This skill authors; it does not render. GitHub, VS Code and Obsidian render the fences
natively.

## Anti-patterns

```
// WRONG: hand-patching one arrow in a fence to "quickly fix" a review comment
// The prose is canonical — change the prose, regenerate the fence (update verb).

// WRONG: authoring a diagram with invented participant names for real code
// Read the source first; narrated diagrams are true or they are noise.

// WRONG: a fence with no preceding narrative paragraph
// That is an orphaned diagram — the pair is required.
```
