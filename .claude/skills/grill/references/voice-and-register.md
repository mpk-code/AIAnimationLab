# Voice and Register — Cheat Sheet

Reference for the `grill` skill. Worked examples of plain-language translation. In the interview,
paths, schema fields, ADR numbers and code symbols are plumbing — they live in the technical
handoff, never in the conversation.

---

## 1. Existing rule — by what it does, not where it lives

**Don't say:** "The Control surface section of project-definition.md already requires a sweep test."

**Do say:** "The project already has a rule that a control only counts if a later step actually
enforces it and a test shows it changes the frames. Would this one pass that test?"

## 2. Project area — plain name, not a path

**Don't say:** "That belongs in `blender/lib/` plus a new `styles/motion/` entry."

**Do say:** "That sounds like part of the style library — specifically the motion side: how things
ease and how much they exaggerate. Is that the right area?"

## 3. Prior decision — what it decided, not its number

**Don't say:** "Per ADR NNNN, Cycles is excluded from the exact-hash test."

**Do say:** "There's an earlier decision that the reproducibility check uses the renderer that gives
identical frames every time, and the other renderer is only compared within a small tolerance. Does
your idea fit with that?"

## 4. Conflict — name it, offer options

**Don't say:** "Your 'treatment' collides with `style_bible.json` and the Style bible glossary row."

**Do say:** "The 'treatment' you're describing overlaps with what the project calls the style bible —
the locked set of styles for one film. Close, but maybe not the same. Should we (a) use 'style
bible' and drop 'treatment', (b) keep both and pick a clearer word for the new one, or (c) merge
them?"

## 5. Pipeline step — what it does, not its number or skill name

**Don't say:** "This runs between stage 2 and stage 3, before Gate B, in `skills/style/`."

**Do say:** "This would happen after the beats are written and before you pick the look. Is that
right, or does it belong after you've chosen the look?"

## 6. Decision worth recording — conceptual offer, no template

**Don't say:** "I'll draft a Provisional ADR with a review trigger at the M1 exit gate."

**Do say:** "That's a decision worth writing down — that a retired style can come back after a
cooling-off period. I'll draft it, with a note to revisit it once we've finished the first vertical
slice."

## 7. Genuinely new ground

**Don't say:** "No glossary row, section or ADR covers this; it's a net-new concept."

**Do say:** "This looks like new ground — nothing in the project overlaps with it yet. Let's keep
going and I'll flag anything that comes up."

---

## Rules of thumb

1. About to type a number-with-prefix (an ADR number, `H2`, `M3`, a stage number)? Rephrase as what
   it is ("the first hypothesis", "the story-stages milestone", "the step that writes the beats").
2. About to type a slash-bearing path or a file name? Rephrase as the area.
3. About to type a code symbol or schema field? Describe what it does.
4. When unsure of a translation, ask: "I'll call this <X> in the write-up — does that name work?"
