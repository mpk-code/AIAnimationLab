---
name: complexity-review
description: >
  Reviews a bounded unit of studio work (a harness component, style module, validator set, stage
  skill's code, side-quest output) for conceptual obtuseness — code harder to understand than the
  problem it solves requires. Use for "review the complexity of X", "is this over-engineered?",
  "obtuseness pass on X", "did we over-abstract?", "is this earning its keep?", or
  /complexity-review. Reads the unit end-to-end, not a diff; correctness and perf are
  /code-review's job.
---

# Complexity Review Skill

This skill answers one question: **is this code harder to understand than the
problem it solves requires?** `/code-review` audits a diff for defects;
`/arch-review` audits whether the structure serves the studio's quality
objectives. This skill fills the gap: code-and-shape-level review for
**conceptual cost imposed on the reader**, scoped to a coherent unit of work.

It produces exactly one artifact — a markdown findings report — and stops.
Downstream skills (`/bug-fix` for mechanical fixes; `/sidequest open` for
structural work) consume the report.

---

## Hard constraints (non-negotiable)

1. **Read-only on git.** Read-only commands (`log`, `show`, `diff`) only, and
   only when the target type requires them (run-cluster).
2. **Never edit source files.** The report is the end of the job.
3. **Write only to the resolved fixes location** (§1.3). Nowhere else.
4. **Never run renders.** This is a reading review; render behavior belongs to
   `/arch-review` and `/optimize`.
5. **Idempotent on a given target** modulo timestamp and declared constraints.

---

## Workflow

Resolution comes before reading code — discovering scope is cheap; premature
review wastes context.

### Phase 1 — Resolve the target unit of work

#### 1.1 Target types

This skill does **not** review "the codebase." Exactly one target per invocation.

| Target type | What "the unit" is | Phrasing that picks it |
|---|---|---|
| **Component** | One coherent source area: a harness component under `blender/harness/`, a style module under `blender/lib/<area>/`, a validator set under `validators/`, a schema family under `schemas/`, or the code a stage skill in `skills/<stage>/` generates or drives. | "review the complexity of the render harness", "is `blender/lib/camera` obtuse" |
| **Side-quest output** | A side-quest's deliverables. `spike` → `findings.md` + any probe scripts. `utility` / `feature` → the paths in `spec-refs:` and the source that implements them. | "review the complexity of sidequest `<slug>`" |
| **Milestone output** | What one milestone of a quest's rollout produced, bounded by that milestone's runs. | "complexity pass on what M1 built" |
| **Run cluster** | The union of files touched by 1–4 recent runs, bounded by run IDs or a git ref the user names. | "review the complexity of runs 1.3 and 1.4" |

If the target is ambiguous, ask one clarifying question and stop (`AMBIGUOUS_TARGET`).
**Do not guess.**

#### 1.2 Quest scope (`project` vs. `sidequest:<slug>`)

| Concept | **Project scope** (`project`) | **Side-quest scope** (`sidequest:<slug>`, from `in sidequest <slug>`) |
|---|---|---|
| Spec sources | `docs/project-definition.md` (§System concept, §Pipeline, §Repository structure, §Artifact schemas) + relevant `docs/adr/` | each path in the quest's `spec-refs:`, with `docs/project-definition.md` as fallback |
| Report placement | `docs/plans/fixes/` | `sidequests/<slug>/fixes/` |
| Soft integration gate | note any closed side-quest with `integrated: false` whose subject overlaps the target | N/A |

Scope resolution priority: (1) user-specified "in sidequest `<slug>`";
(2) inferred active side-quest (working dir, recent rollout/status edits) —
state the inference in `## Scope`; (3) `project` scope. A `Side-quest output`
target implies side-quest scope for that slug.

#### 1.3 Report placement

- **Project scope** → `docs/plans/fixes/complexity-review-<target-slug>-<YYYY-MM-DD>.md`
- **Side-quest scope** → `sidequests/<slug>/fixes/complexity-review-<target-slug>-<YYYY-MM-DD>.md`

`<target-slug>` slugifies the target (e.g. `component-render-harness`,
`sidequest-toon-ramp-style`, `runs-1.3-1.4`).

- Create the `fixes/` directory if missing.
- The `complexity-review-` prefix is part of the contract — it disambiguates
  this report from `/code-review` and `/bug-fix` outputs. Don't let it be renamed.
- One report per invocation. Announce the resolved path during pre-flight.
- If the path already exists, append `-1`/`-2`/… rather than overwriting.

#### 1.4 The "known constraints" input

Without this, the reviewer keeps flagging abstractions whose justification lives
outside the target. At the start, ask the user once:

> "Any constraints I should know about before reviewing? Things that look like
> over-engineering but exist for a real reason."

Examples relevant here:

- "The harness must run identically on both Macs and record the machine."
- "Render profiles are parameterized because preview and final must share one code path."
- "This indirection keeps `bpy` imports out of code that runs under plain pytest."
- "Style modules take every value as a parameter because a knob must be sweepable (H2)."

**Also auto-detect** constraints from the loaded docs: the doctrine in
`CLAUDE.md` (render only through the harness, prefer `bpy.data`, every
decision in a schema-validated artifact, stage isolation), accepted ADRs in
`docs/adr/`, and terms in `docs/glossary.md`.

Record both lists in the report frontmatter (`constraints-declared:` and
`constraints-auto-detected:`). When in doubt, fold a candidate into
`## Considered-but-dropped` with "kept because of constraint X".

#### 1.5 The reader profile

Every finding is evaluated against a specific imagined reader — the
load-bearing concept of the review:

> A competent generalist developer joining AIAnimationLab six months from now.
> They know Python 3.11+, pytest, JSON Schema, and the basics of Blender's
> Python API (`bpy.data`, objects, materials, keyframes). They have read
> `CLAUDE.md`, `docs/project-definition.md`, and `docs/glossary.md`. They do
> **not** know:
>
> - Advanced or exotic language features beyond common usage
> - Niche design patterns
> - Undocumented internal conventions of this codebase
> - Why any particular abstraction exists

Find places where this reader would stop, re-read, look something up, or hold
too many concepts at once — *and* where that cost isn't earning its keep
against a requirement, ADR, or declared constraint. Every finding must point at
a specific stuck moment; findings that can't go in `## Considered-but-dropped`.

---

### Phase 2 — Collect inputs

1. Load specs per §1.2.
2. Load `docs/glossary.md` — glossary terms are pre-justified vocabulary.
3. Load ADRs referenced from the loaded docs.
4. Capture `constraints-declared` verbatim.
5. `project` scope only: scan `sidequests/*/` rollout frontmatter for
   `status: done` + `integrated: false` quests whose subject overlaps the target;
   note them in `## Scope` (`UNINTEGRATED_SIDEQUESTS`).

---

### Phase 3 — Read the target end-to-end (no notes)

The most commonly skipped step and the cause of the most common failure:
pattern-matching on surface signals before the unit's shape is in your head.

Read the public surface and shape first, then the implementation. Do not start
a findings list yet. For a component: its entry points (e.g. `render.py` CLI,
a module's public functions) and top-level files. For a side-quest: the
deliverables in the order produced. For a run cluster: files touched, grouped by run.

Large targets (~3000+ lines or ~25+ files): flag `MASSIVE_TARGET` and ask
whether to narrow or proceed at a higher level. Don't refuse.

---

### Phase 4 — Two-pass review

#### 4.1 Large-scope pass (structural)

Look for:

- **Abstraction layers for flexibility not currently needed** — plugin systems,
  registries, factory hierarchies with one current consumer.
- **Indirection without two real consumers** (rule of three).
- **Generalization ahead of the second use case** — parameters no caller varies.
  *Exception:* a style-module parameter that is a documented knob is justified
  by the control-surface rule even with one caller.
- **Patterns imported wholesale when a fragment was needed** — an event bus
  where a function call would do.
- **Boundaries that don't match how code changes together.** If two "modules"
  always co-change, the boundary is fictional.
- **Custom concepts that overlap well-known ones** — custom protocols or state
  machines that reinvent something standard.
- **Custom concepts that overlap the glossary.** A new name for an existing
  glossary term (shot, beat, style module, manifest…) is obtuse even if clean.
- **Stage-isolation leaks as a complexity symptom.** A stage's code reaching
  for something other than its upstream artifacts is both a layering issue and
  a sign its shape is misaligned with its role.

#### 4.2 Small-scope pass (local readability)

Look for:

- **Clever one-liners** — chained comprehensions, dense regex, bit tricks.
- **Advanced language features where a straightforward construct would do** —
  metaclasses, descriptors, decorator stacks, dynamic class generation. Don't
  flag advanced features that are the simplest expression of the problem.
- **Non-obvious control flow** — buried early returns, exception-driven logic,
  callbacks where sequential code would do, implicit state in dict updates.
- **Names that need hidden knowledge to decode** — single letters in long
  bodies, acronyms not in the glossary, names describing *how* not *what*.
- **Drift from idiomatic `bpy`** — `bpy.ops` with context overrides where a
  `bpy.data` call would do; hand-rolled math `mathutils` provides; magic
  numbers for colors/lens/timing that should come from the style bible or
  `production.yaml`.
- **Reinvented wheels** — custom code for what the stdlib, `jsonschema`, or a
  pinned dependency provides.

#### 4.3 Non-goals

Drop findings that drift here:

- Bugs, missing tests, functional defects, performance — `/code-review`,
  `/unit-test-review`, `/optimize`. Note real defects briefly under
  `## Adjacent findings`.
- Style preferences with no readability impact (formatting is ruff's job).
- Complexity genuinely warranted by the domain (e.g. Blender's own data model,
  color-space handling, deterministic seeding). The code should reflect it.
- Patterns that are merely different, not worse.
- Anything justified by a declared constraint or ADR.
- Code outside the target — unless the target aggravates it (e.g. adds a fifth
  caller to an already-confusing function).

**Discipline rule:** if you can't name a specific reader-confusion moment or a
specific maintenance scenario that gets harder, drop it.

---

### Phase 5 — The cut step (the heart of the skill)

Re-read every finding. Each must pass all four:

1. **Reader-confusion moment** — can you name where the reader gets stuck?
2. **Maintenance scenario** — can you name what gets harder?
3. **Independence from taste** — justified apart from your preferences?
4. **Not pre-justified** — not covered by a constraint, ADR, or glossary term?

Failures move to `## Considered-but-dropped` with a one-line note. **Five sharp
findings beat twenty soft ones.** That section is mandatory — it records your
restraint and stops the same questions recurring.

---

### Phase 6 — Overall assessment and write the report

Pick a verdict in 2–4 sentences:

- **well-pitched** — conceptually right for the problem
- **over-engineered** — paying cognitive cost without earning it
- **under-engineered-for-clarity** — a hard problem in code that hides its
  hardness, so the next maintainer will break invariants they didn't know
  existed (e.g. an unstated seed-ordering assumption the reproducibility gate
  depends on). Fix is usually documentation, naming, or invariant assertions.
- **mixed**

Write the report to the §1.3 path. Do not run linters, edit code, or open `/bug-fix`.

---

## Report schema (the only output, and the contract with `/bug-fix`)

Markdown only; `/bug-fix` parses it directly. Field names, headings and finding
format must match exactly.

```markdown
---
review-date: <ISO date>
review-type: complexity
target-type: component | sidequest-output | milestone-output | run-cluster
target: <slug or path>
scope: project | sidequest:<slug>
scope-inferred: true | false
specs-loaded:
  - <path>
constraints-declared:
  - <one line per user-declared constraint>
constraints-auto-detected:
  - <one line per doctrine/ADR-derived constraint>
verdict: well-pitched | over-engineered | under-engineered-for-clarity | mixed
counts:
  high: N
  medium: N
  low: N
flags: []   # AMBIGUOUS_TARGET, NO_SPECS_FOUND, MASSIVE_TARGET, ADJACENT_DEFECTS_FOUND, UNINTEGRATED_SIDEQUESTS
---

# Complexity Review — <target> — <date>

## Scope
<What was reviewed, what is in vs out, any scope inference, any flags.>

## Reader profile applied
<Phase 1.5 instantiated for this target.>

## Overall assessment
<2–4 sentences defending the verdict. The most important paragraph.>

## Findings

### High
<Finding blocks, or "None.">

### Medium
<Finding blocks, or "None.">

### Low
<Finding blocks, or "None.">

## Cross-cutting
<Findings spanning many files: short header, the concept imposed, the
reader-confusion moment, a suggested direction. Or "None.">

## Considered-but-dropped
- **<short title>** — dropped because <reason>.

## Adjacent findings (not in scope)
<Likely defects or architecture issues with a one-line referral, e.g.
"Unseeded `random` at `blender/lib/motion/jitter.py:42` — refer to `/code-review`." Or "None.">

## Recommendation
<Exactly one downstream path per the decision rule, citing the dominant finding(s).>
```

### Finding block format

```markdown
### [SEVERITY] <short title>

- **Location:** `<file path>:<line range>` for small-scope, or `<architectural area>` for large-scope
- **Scope:** small | large
- **Lens:** the concept being imposed on the reader — named specifically
- **Why it isn't earning its keep:** what would be lost by simplifying it? If "nothing concrete, just hypothetical flexibility", say so.
- **Suggested simplification:** concrete, with a sketch if non-obvious. For large-scope findings needing human design judgment, write "manual handling".
- **Reader-confusion moment:** the specific point where the reader gets stuck.
- **Severity rationale:** one line on why High / Medium / Low.
```

Within each severity group: large-scope before small-scope, then by file path.
Empty groups keep the heading and write "None.". Bullet labels appear in that
exact order and casing. Paths are repo-relative; line ranges use current numbering.

---

## Severity scale (three tiers — do not harmonize with code-review's four)

Obtuseness is rarely an emergency, so there is no "Critical".

- **High** — a maintainer will likely *misread or break* this. Fix before the unit closes if possible.
- **Medium** — a maintainer will lose *meaningful time*. Batch into a cleanup.
- **Low** — a maintainer will *pause but recover quickly*.

---

## Recommendation decision rule

| If findings look like… | Recommend… |
|---|---|
| Local, concrete, the *what* is obvious — renames, inlining a one-use abstraction, naming a hidden invariant | `/bug-fix` against this report |
| Structural, real, the *what* isn't known yet | `/sidequest open spike <slug>` (deliverable `findings.md`) |
| Structural, the *what* is known, substantial (multi-area, would be one oversized commit) | `/sidequest open feature <slug>` → `/generate-rollout` → own runs |
| Three+ places reinventing the same concept that should be one shared module (e.g. in `blender/lib/`) | `/sidequest open utility <slug>` |
| Nothing actionable, or the fix is documentation/naming/assertions only | State plainly: no quest needed |

Center of mass: all Highs small-scope → `/bug-fix`; a High large-scope finding
with a known replacement → `feature` (or `/bug-fix` if trivially small);
unknown replacement → `spike`; repeated concept across 3+ areas → `utility`;
only Medium/Low → `/bug-fix` or "defer, batch with a future review".

**One path per report.** Fold secondary actions in as a note. When torn between
`spike` and `feature`, prefer `spike` — cheaper to reclassify later.

---

## Edge cases

- **No specs for the target.** Raise `NO_SPECS_FOUND`; review code-only. Note
  that a missing spec may itself cause obtuseness.
- **Spike side-quest.** `spec-refs:` is empty by design. Review probe scripts
  and the clarity of `findings.md`; don't flag missing specs.
- **Side-quest still in flight.** Note it in `## Scope`; partial code can still
  be reviewed for shape.
- **Reviewer disagrees with an ADR.** ADRs are inputs, not subjects. If the
  finding is "I'd have decided differently", drop it. If the ADR's
  *implementation* is obtuse, keep it and note "ADR-NNNN's decision is taken as
  given; the finding is about how it is expressed in code."
- **Under-engineering-for-clarity.** Look for it as actively as over-engineering.

---

## Operating rules

1. **Read end-to-end before taking notes** (Phase 3).
2. **Apply the reader profile literally.** Restate abstract complaints as the reader's stuck moment.
3. **The cut step is non-optional.** `## Considered-but-dropped` is mandatory.
4. **Scope discipline.** Pre-existing obtuseness is out of scope unless the target aggravates it.
5. **Respect declared constraints.**
6. **Severity discipline.** High means "predictable bug from misreading."
7. **Don't fix anything.** `/bug-fix` executes; this skill diagnoses.
8. **Don't drift.** Defects → `## Adjacent findings` + `/code-review`; structural
   objective issues → `/arch-review`; plan/doc-level over-engineering → `/doc-review`.
9. **Filing.** A defect this work finds and leaves unfixed is filed afterwards
   with the `defect-filing` skill and named `issue #<n>` in the record that leaves it.

---

## Pipeline position

| Skill | Reviews | When to use |
|---|---|---|
| `/code-review` | A diff for defects and smells | Before closing a run or milestone |
| `/arch-review` | Structure vs the studio's quality objectives | When a structural decision is in flight or recently landed |
| `/complexity-review` (this skill) | Conceptual obtuseness of a bounded unit | When a unit is "done enough" to read end-to-end, or feels harder than it should |
| `/bug-fix` | Consumes findings from any of the above | After a report has actionable findings |

Post-hoc by design — not for a hot loop. Typical moments: after a `utility`
side-quest closes, before others consume it; after a `feature` side-quest (e.g.
a new style module) proposes its changes; after a milestone closes; whenever
the user senses something is harder than it should be.

---

## Tools and boundaries

- Read across the repo; write only to the resolved fixes location.
- Read-only git only for run-cluster targets. No network.
- Working directory: repo root (`cd "$(git rev-parse --show-toplevel)"`).
