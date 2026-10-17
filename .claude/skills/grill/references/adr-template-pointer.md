# ADR Template — Reference Card

Reference for the `grill` skill. **Does not duplicate the template.** The canonical template is
`docs/adr/0000-template.md`; read it and fill it in. The index and the rules for when an ADR is
required are in `docs/adr/README.md`.

## Numbering and placement

- Proposed file name: `docs/adr/NNNN-<short-slug>.md`, with `NNNN` the next free number after the
  highest row in the `docs/adr/README.md` index (and any `docs/adr/[0-9]*.md` file not yet indexed).
  If another open grill session or quest already proposes that number, say so in the handoff.
- Grill **does not create the file**. The full draft lives in the session file's technical handoff,
  together with the index row to add to `docs/adr/README.md`.

## Status

- `Proposed` — the default for a grill draft: awaiting the user's acceptance.
- `Provisional` — when the user wants the decision in force now but revisited. The template requires
  a **review trigger** and an **expiry** (date or milestone, e.g. "before E1", "M1 exit gate"). Never
  leave Provisional open-ended.

## When grill drafts one

Required (per `docs/adr/README.md`): a glossary term change, a `CLAUDE.md` doctrine change, an
artifact schema change after M1, or pinning/changing the Blender version.

Offered: a change to a hypothesis, scope line, pipeline stage, gate, control or exit gate in
`docs/project-definition.md`; a deliberate deviation from the obvious path; a resolution of a
conflict the session exposed; a decision with test or validator implications.

## Drafting rules

- **Context** references `docs/project-definition.md` sections (and H1–H3, milestones) rather than
  copying them.
- **Decision** is one specific sentence — specific enough to test.
- **Alternatives considered** lists only alternatives genuinely discussed, each with its specific
  reason for rejection. No hollow alternatives.
- **Consequences** names what becomes harder as well as easier, and what now needs a test, validator
  or manifest field.

## Framing the offer to the user

Conceptually, never structurally:

> _"This sounds like a decision worth recording — about whether retired styles can come back. I'll
> draft it for review."_

Not: _"This needs a Proposed ADR, number 0004, with a supersedes field."_
