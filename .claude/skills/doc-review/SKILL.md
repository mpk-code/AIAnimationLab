---
name: doc-review
description: >
  Independent multi-lens review of the comments and docstrings in the studio's source code (harness,
  validators, style modules, eval tooling), split by what each reviewer is allowed to see rather than
  by topic, emitting per-comment verdicts that /bug-fix's record lane consumes. Use for "review the
  comments", "are these docstrings any good", "audit the prose in <file>", "check the comments I just
  wrote", "these comments are obtuse / jargony / stale", "do the comments still match the code",
  "run the comment panel", or /doc-review. Reach for this whenever comments or docstrings have just
  been written or rewritten and nobody independent has read them — an agent cannot review prose it
  authored. Judges prose in source; correctness of the code is /code-review's job, and applying the
  corrections is /bug-fix's.
---

# Doc Review

**Purpose:** Review the comments and docstrings in source code and emit per-comment verdicts a
remediation pass can act on. Read-only: you diagnose prose, you do not rewrite it.

This is a dev-process skill for the studio's own code. It does not review pipeline stage skills in
`skills/<stage>/` or production artifacts.

**Organizing principle — the author cannot do this job.** An agent that just wrote a comment is the
only participant who knows why the code has its shape, and the worst-positioned to judge whether the
comment communicates it: the jargon is resident, and it cannot un-know the context. This is the
same rule as the studio's "a model never grades its own output."

**Why prose gets its own review.** A misleading comment misleads a model more than a human. CodeCrash
(arXiv 2504.14119) measured large drops in LLM output-prediction accuracy from misleading comments,
docstrings and identifiers, plus extra token spend as the model rationalizes a contradiction. A human
who sees a comment fight the code usually trusts the code; a model often follows the prose. In a
studio whose only crew is Claude Code, a false sentence in a docstring is a defect.

The rubric is **STD-007** in `docs/coding-standards.md`. Read it before Phase 1 — this skill applies
it, it does not restate it. Its gates are cited below as G1–G6.

---

## Hard constraints (non-negotiable)

1. **Read-only.** Diagnose; never edit source. Corrections route through `/bug-fix`'s record lane,
   which pairs each one with a recompute command. A skill that both judges and rewrites has no
   independent reader left.
2. **Blindness is the mechanism, not a preference.** Lens 1 gets the file and nothing else. Give it
   the rubric and it grades conformance; give it the prior version and it grades the author's
   judgment; give it `grep` and it stops testing what the file communicates. Staging the inputs wrong
   converts this skill into a topic review, which `/code-review` already does better.
3. **Never merge the lenses into one agent, and never run them inline in the main context.** One
   agent holding all the inputs reproduces the author's position.
4. **Do not tell any lens what the others found, or what you suspect.** A directed reviewer inherits
   its framing and confirms it.
5. **Cite symbols, never `path:line`.** A line number drifts on any insertion above it. Write
   ``blender/harness/render.py :: write_manifest``.

---

## Phase 0 — Run the mechanical checks first

Some of STD-007 is checkable by grep, and a reviewer should not be spent on it. For the files in
scope, extract the comments and docstrings and check:

- every repo path cited in prose resolves (`test -e <path>`);
- every cited ADR (`docs/adr/NNNN-…`) and `STD-###` id exists;
- every cited quest run uses the `<quest-slug>/Run N.M` form and the quest exists under
  `sidequests/` or `sidequests/archive/`;
- every `path:line` citation (a STD-007 violation on its own).

Take two things from the output:

- **Failures are findings already.** Fold them into the report at Major, `Lens: mechanical`.
- **Unqualified guarantee words** ("always", "never", "guaranteed", "deterministic",
  "reproducible", "cannot") are an attention map, not findings. Pass their locations to Lens 3 and
  Lens 4. Do **not** pass them to Lens 1 or Lens 6 Turn 1 — that would tell them where to look.

If the checks cannot run, set `MECHANICAL_GATE_UNAVAILABLE` in `flags` and continue. Never
fabricate their output.

---

## Phase 1 — Resolve mode, scope, and tier

### Mode

| mode | when | what it means |
|---|---|---|
| **rewrite** | the prose was just written or changed — a diff, an uncommitted edit, a run's output | all lenses apply; Lens 2 has a before-version to diff |
| **audit** | a cold file nobody just touched | Lens 2 drops out. Set `NO_PRIOR_VERSION` in `flags`. |

Resolve the before-version explicitly in rewrite mode: `git show <base>:<path>`, or the pre-edit
content if the change is uncommitted. If you cannot get it, you are in audit mode — do not
substitute a guess.

### Scope

Take the files from whatever the caller gave you (a path, a diff, a run id). If nothing was named,
ask rather than guessing — reviewing the wrong file wastes the whole panel.

Record the file count and the total prose lines you actually staged. A panel that silently reviewed
one file when pointed at six would otherwise read as a clean result.

### Tier

The full panel is expensive per file, so it is tiered. Pick the tier and record it with its
justification:

| tier | lenses | when |
|---|---|---|
| **T1** | Phase 0 only | every file, always — it is nearly free |
| **T2** | + Lens 6, Lens 2 | the prose was actually rewritten |
| **T3** | + Lens 1, Lens 3, Lens 4, Lens 5 | a wrong comment here is expensive — render determinism and seeding, the manifest, the harness's render path, schema validation, validators and gate logic, anything whose comment governs whether a reader may change the behavior |

Escalating to T3 on a test fixture wastes budget; staying at T2 on the harness is the mistake that
matters.

---

## Phase 2 — Stage the lens inputs

This phase is the skill. Write each lens's inputs to its own directory in the scratchpad before
dispatching anything, so what each reviewer can see is a fact on disk rather than an intention in a
prompt.

| lens | gets | must NOT get |
|---|---|---|
| **1 — Comprehension** | the current file, alone | the rubric · the before-version · repo access · Phase 0 output · any hint of what you suspect |
| **2 — Deletion audit** | both versions, STD-007, repo access | the other lenses' findings |
| **3 — Claim verification** | the current file, repo access (grep/glob), Phase 0 attention map | the before-version · the rubric's rationale (it checks facts, not conformance) |
| **4 — Pointer integrity** | the current file, repo access, Phase 0 attention map | — |
| **5 — Rubric adversary** | the current file, both versions, STD-007, repo access, and whether the same author wrote both the rubric and the edit | — |
| **6 — Generative legibility** | Turn 1: the file with all comments and docstrings stripped. Turn 2: the original prose, plus `docs/`-scoped grep | Turn 1: repo access, Phase 0 output, the prose |

Lens 1's directory holds exactly one file. Verify that before dispatch.

---

## Phase 3 — Run the lenses in parallel

Dispatch all applicable lenses in one turn so they run concurrently and cannot see each other's
output. Each returns findings with a confidence guess; nothing is final until Phase 4. Do not
deduplicate yet — two lenses independently flagging the same sentence is the strongest signal the
panel produces.

### Lens 1 — Comprehension (starved)

Ask it to be the next maintainer. It answers 8–12 questions with **checkable** answers, derived from
the file's own surface — e.g. what happens when a scene script raises in background mode, which seed
governs a draw, when the manifest is written relative to the frames, what a validator does when an
upstream artifact is missing.

Its output contract:

- per question: the answer, and **whether it came from prose or from reading the logic**. A comment
  that did not help did not earn its place.
- **what it could not answer** — the only signal in the panel for a fact the file is *missing*.
- what it believes is **false**, with the reasoning that made it suspicious.
- what **adds nothing** — restates a signature, narrates the body, re-reads the function name.

Its findings are unverified by construction; Phase 4 verifies them.

### Lens 2 — Deletion audit (rewrite mode only)

The highest-yield lens, because a prose edit's failure mode is asymmetric: reviewers examine what is
present, and the damage is in what left.

Enumerate **every fact present in the before-version and absent from the after**, and rule each:

- **recoverable** — the after-version says it elsewhere, or a pointer lands on it. Name where.
- **correctly dropped** — false, duplicated, or recoverable from the code in one read. Name the gate.
- **lost** — gone and nothing replaces it. A finding.

Weight a **recorded decision** heavily — a comment citing an ADR, or recording why the user chose a
behavior. Such lines look like noise and are often the only record of an argument. A deletion of one
is Critical until proven otherwise.

### Lens 3 — Claim verification (grep-only)

Every factual assertion in the current prose, checked against the live repo. Report each claim as
**confirmed**, **false**, or **unverifiable**, with the command or file that decided it.

Weight two classes:

- **Guarantee strength.** A sentence claiming a property must name what enforces it — *by
  construction* (the types or structure make it impossible), *by gate* (a named test, validator or
  lint), or *by convention* (nothing enforces it). The common error is an intended end state written
  in the present tense as a structural property — "renders are reproducible" when only an EEVEE hash
  test enforces it and Cycles is held to a tolerance. If the guarantee is a test, deleting that test
  silently removes it — and *that* is the sentence worth writing.
- **Causality.** A sentence can be true and still name the wrong cause. A maintainer trusting the
  stated reason can "clean up" the code and break the real constraint while believing the documented
  rationale intact. A truth check alone passes this class.

### Lens 4 — Pointer integrity

Every "see X", "documented in Y", "the rules are in Z" must land on the fact it promises. A pointer
to a missing fact is worse than the duplication it replaced. Resolve each and report **lands** /
**lands on something weaker** / **lands nowhere**.

Also check the two citation forms STD-007 governs, since both fail silently:

- a `path:line` citation — the line has probably moved.
- a bare `Run N.M` — every quest has a Run 1.1, so a bare run number identifies nothing and can
  resolve to a plausible wrong match. The compliant form is `<quest-slug>/Run N.M`.

### Lens 5 — Rubric adversary

Tell it plainly whether the same author wrote the rubric and the edit, and ask it to hunt for a
standard bent to fit. Look for a rule satisfied on a technicality — e.g. G5 "point at the
authority" met by naming four files instead of pointing at a check, a snapshot of another file's
state with nothing keeping it true.

Ask it directly: is any finding better explained by the rubric being wrong than by the prose being
wrong? A rubric defect outranks the prose defects it produced, and is reported as one.

### Lens 6 — Generative legibility (derive first, then compare)

The only lens that produces prose instead of judging it, and the only one that can find **rationale
that was never recorded**. The other lenses tell you whether prose is true, non-redundant and
well-cited; none asks whether it is **comprehensible**, and Lens 1 rewards density. A docstring can
pass every gate and still be unreadable to the person who has to change the code.

Run it as **two turns against one agent**, and do not reveal Turn 2's input when dispatching Turn 1 —
an agent that knows a docstring is coming hedges its derivation.

#### Turn 1 — derive from code with all prose stripped

Hand it the file with **every docstring and comment removed** and nothing else. Ask it to write the
documentation it believes each function needs, following the six-item outline below, and to keep a
running list of every question it cannot answer from the code.

| item | derivable from code alone? |
|---|---|
| 1. What it returns or does | **yes** |
| 2. Why it is built this way | **no** — the author-only content |
| 3. What must not be "fixed" | partially — it can spot the tempting change, not why it is barred |
| 4. What it does *not* do | **yes** — where a cold reader's wrong assumption surfaces |
| 5. "Do not replace this with X" | can propose candidates; cannot confirm |
| 6. Governing references (ADR, `STD-###`, rollout) | **no** — not in the code |

Turn 1 returns a partial draft plus **a question list** — item 2's empty slots. Require specifics:
not "unclear why", but "why does this sort object names before assigning materials?"

**Turn 1's output goes to a file before Turn 2 is sent**, so the derivation cannot be quietly revised
once the docstring contradicts it.

#### Turn 2 — reveal the real prose

Send the existing prose and ask:

1. **Which Turn-1 questions does it answer?** Those answers are the author-only content; they survive
   into the refined draft.
2. **Which does it not answer?** Each is **rationale that was never recorded** — the highest-value
   finding, because it becomes unrecoverable when the context that produced it is gone. Report each
   as a question for the author, not a prose defect.
3. **What does it contain that fits none of the six slots?** Deletion candidates.

**Step 4 — does this fact already have an owning home?** Before composing, for every fact in the
draft, search `docs/` (project definition, ADRs, glossary, test strategy, coding standards) and
`schemas/` for the *idea* in two or three phrasings — a reworded duplicate is the common case.

- **Owned elsewhere** → cut to a pointer naming the section (G2: keep one statement; make the other
  a pointer).
- **Not owned anywhere** → keep it, and name where the decision behind it lives if that differs.
- **Owned elsewhere but the home is incomplete** → do **not** cut it. Keep it, flag the gap for the
  owning document, and record that the docstring cannot shorten until that document is fixed.

Every other lens sees exactly one file, so this step is the only part of the panel that can find a
fact in the wrong place. When a finding is "this is too long", check for duplication before trying
to compress.

Then have it compose the refined draft in the outline's order. A proposed draft inside a report is
not an edit to source; Hard constraint 1 still holds.

#### The six-item outline (also the composition rule for authors)

1. **What it returns or does** — one sentence, glossary terms, no IDs.
2. **Why it is built this way** — the constraint or decision that produced the construct, in terms a
   maintainer can weigh. A reader can always see *what* the code does and almost never *why*.
3. **What must not be "fixed"** — imperative, stated as the consequence of (2).
4. **What it does *not* do**, wherever a wrong assumption is likely — e.g. a function that trusts a
   caller-validated artifact should say so, or a reader will skip validating upstream.
5. **"Do not replace this with X"** — where a plausible simplification is wrong (e.g. `bpy.ops` for
   `bpy.data`), with the reason.
6. **Governing references** — only where resolving one decides whether the reader may change the
   behavior. Cite the owning section rather than restating it.

**Every prohibition travels with its own why.** Rules in one paragraph and rationale in another
produce a docstring where neither half is usable alone.

**Tiering note.** Lens 6 largely subsumes Lens 1's "could not answer", because its questions are
specifically *why* questions. What Lens 1 uniquely produces is the prose-vs-logic attribution. So
Lens 6 is the T2 default and Lens 1 is T3.

---

## Phase 4 — Verify before reporting

Every finding gets checked against the repo before it enters the report. Lens 1 is unverified by
construction; the others can be confidently wrong. Verify without knowing which lens raised a
finding or what severity it guessed.

- **confirmed** — the evidence is in the report.
- **plausible** — the reasoning holds but the evidence is indirect. Say so; do not promote it.
- **refuted** — drop it, and note the refutation if the reasoning was interesting: a false finding
  for a good reason often marks a genuinely ambiguous sentence, and the ambiguity is the finding.

Where two lenses converged on the same sentence, keep both and note the corroboration.

---

## Phase 5 — Write the report

Write alongside where `/code-review` writes: `sidequests/<slug>/fixes/` for a quest scope,
`docs/plans/fixes/` for `project` scope (same scope values as `/code-review`: `project` | `sidequest:<slug>`). Name it `doc-review-<date>-<scope>.md`.

**Emit per-comment verdicts, not a rewritten file.** Corrected prose handed back wholesale hides what
changed and why.

```markdown
---
review-date: <ISO date>
mode: rewrite | audit
tier: T1 | T2 | T3
scope:
  - <path>
files-reviewed: N
prose-lines-reviewed: N
before-ref: <ref/sha, or "none — audit mode">
lenses-run: [1, 2, 3, 4, 5, 6]
mechanical-gate: <failures>F / <attention>A over <N> files
verdict: pass | pass-with-minors | needs-fixes | block
counts:
  critical: N
  major: N
  minor: N
  nit: N
flags: []   # NO_PRIOR_VERSION, MECHANICAL_GATE_UNAVAILABLE, SINGLE_LENS_MODE, SCOPE_UNCONFIRMED
---

# Doc Review — <date>

## Scope and tier
<what was reviewed, what was excluded, which tier and why>

## Comprehension result (Lens 1)
<N of M questions answerable from prose alone. Then: what it could not answer; what it thought was
false; what added nothing.>

## Findings

### [SEVERITY] <GATE> — <short title>
- **Location:** `<path>` :: `<symbol>`
- **The prose:** "<quoted, trimmed to the claim>"
- **Gate:** G1 truth · G2 duplication · G3 keep-test · G4 recoverable · G5 cross-file · G6 causality · GUARANTEE strength · LEGIBILITY · POINTER · CITATION
- **Lens:** 1–6, or `mechanical`
- **Verdict:** confirmed | plausible
- **What a reader gets wrong:** <the concrete wrong change a maintainer makes>
- **Evidence:** <the command, file, or symbol that decided it>
- **Proposed correction:** <one or two sentences — the substance, not the wording>

## Deletions (Lens 2, rewrite mode)
| fact removed | ruling | where it survives / gate that killed it |
|---|---|---|

## Unrecorded rationale (Lens 6)
<the Turn-2 questions the prose does not answer, each as a question for the author; the refined draft>

## Rubric findings (Lens 5)
<a defect in STD-007 itself, if any — these outrank the prose defects they produced>

## Coherency check for the original author
<See below. This is the handoff, not a summary.>
```

### Severity

Weigh every finding by one question: *does a maintainer acting on this prose break something?*

- **Critical** — a false claim about a guarantee or invariant (determinism, seeding, what the
  manifest records, what a validator enforces, the stage contract). Acting on it breaks the studio.
  Also: a deleted recorded decision.
- **Major** — a false claim, wrong causality (G6), or a pointer that lands nowhere.
- **Minor** — duplication, a stale-but-harmless citation, a bare run number, jargon (or drift from
  `docs/glossary.md`) that obscures intent without misstating it.
- **Nit** — pure noise: restates the signature, narrates the body, re-reads the function name.

Prose volume is never itself a finding. A file that got *longer* because two non-obvious facts were
finally written down is a good outcome.

### The coherency check — what the original author must review

The panel cannot see why the code has its shape, so a reviewer's correction can quietly overwrite
intent. Close the report with the handoff and its resolution rule:

> **Legibility corrections stand.** The author may object only on **truth** or **lost-intent**
> grounds, and must cite the code, test, or decision being protected. "That reads worse to me" is
> not an admissible objection.

List, specifically:

- every correction that changes what a sentence *claims* (not how it reads),
- every fact Lens 2 ruled **lost**,
- every question Lens 1 **could not answer** and every Lens 6 unrecorded-rationale question,
- any place a proposed correction would contradict a decision the author made while writing the code.

---

## False-positive discipline

A panel that manufactures findings gets ignored, which costs more than the findings were worth.

- **A dense-prose file is not automatically bloated.** Code whose *rules* are intricate while its
  control flow is trivial (a manifest writer, a determinism helper) may be correctly documented.
- **Genuine data stays a literal.** A palette hex value in a style module or a fixture value in a
  test is data; a naked literal is a defect only when it duplicates a canonical value defined
  elsewhere.
- **A governing reference is not decoration** when a reader must resolve it to know whether they may
  change the behavior. A pile of references with no such stake fails the keep-test (G3).
- **When prose describes a better design than the code implements, the fix is usually the code.**
  Report it as a code finding and route it to `/code-review` or `/bug-fix` rather than softening the
  sentence to match a worse implementation.

---

## Guardrails

- **Stop and ask if the scope is unnamed.**
- **Never report a count you did not compute.**
- **Never claim a lens ran that did not.** If only one lens was affordable, set `SINGLE_LENS_MODE`
  and say which. A report that implies independence it did not have is worse than a smaller honest
  one.
- A defect this work finds and leaves unfixed is filed afterwards with the `defect-filing` skill and
  named `issue #<n>` in the record that leaves it.
- **Findings route to `/bug-fix`'s record lane**, which pairs each correction with a re-runnable
  recompute command whose output contradicts the wrong text and agrees with the corrected text.
  There is no failing test for a wrong sentence, which is why the correction needs one.
- **STD-007 and this panel are unvalidated in this repo.** Report anything that reads as a rubric
  defect (Lens 5) rather than working around it.
