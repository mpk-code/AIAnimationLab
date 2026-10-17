---
name: bug-fix
description: >
  Disciplined defect workflow — RCA, blast-radius analysis, refactor classification, TDD,
  adversarial review — for any bug, defect, or broken behavior in the studio (harness, style
  modules, validators, schemas, eval code, stage skills), with or without a GitHub issue.
  Use for "fix this bug", "there's a defect", "something is broken", "this isn't working",
  "the render is wrong", "the harness crashes", "the validator passes something it shouldn't",
  "patch this", "troubleshoot", a GitHub issue number in a fix context, or /bug-fix. ALWAYS use
  this skill rather than patching a defect directly, however small the fix looks — skipping it
  produces fixes that mask root causes.
  Also covers wrong records, not just wrong code — a document, docstring, comment, acceptance
  criterion, ADR citation, or status field that misstates what the system actually does. Use for
  "this doc says the wrong number", "the rollout cites a line that moved", "our status doc
  contradicts the code", "that docstring is stale", "the project definition doesn't match the
  implementation", "the manifest description is wrong", "fix the stale citation in the rollout".
  Correcting a record by hand skips the same discipline as patching code by hand, and the
  corrected sentence then ships unverified — this skill's record lane substitutes a re-runnable
  recompute command for the failing test.
---

# Bug Fix Skill

A disciplined, end-to-end process for fixing bugs without cutting corners. Every
step must be completed in order. Do NOT skip steps or abbreviate them.

This is a **dev-process** skill for building the studio. It is not a pipeline stage skill
(`skills/<stage>/SKILL.md`). A defect *in* a stage skill is still fixed with this skill.

## Key Document Paths
- Project definition (source of truth): `docs/project-definition.md` — §Hypotheses, §Scope,
  §System concept, §Pipeline, §Control surface, §Repository structure, §Milestones (exit gates)
- Doctrine: `CLAUDE.md` (changes need an ADR)
- ADRs: `docs/adr/NNNN-slug.md` (template `docs/adr/0000-template.md`, index `docs/adr/README.md`)
- Glossary: `docs/glossary.md`
- Coding Standards: `docs/coding-standards.md` — `STD-###` conventions the fix must conform to
- Test Strategy: `docs/test-strategy.md`
- Schemas: `schemas/` (JSON Schema; changes need an ADR)
- Styles: `styles/<dimension>/<style-id>/style.yaml`, modules in `blender/lib/`
- Render harness: `blender/harness/render.py --scene <script> --profile preview|final --out <dir>` (created in M0)
- Test runner: `scripts/run_tests.sh` (pytest + ruff + mypy; created in M0)
- Fix Plans: `docs/plans/fixes/`
- Code Review Reports (source for review-driven fixes): `docs/plans/fixes/code-review-*.md` (`project` scope) or `sidequests/<slug>/fixes/code-review-*.md` (side-quest scope)
- Followups index: `docs/plans/followups.md`

## Overseer-dispatched work (optional)

If the prompt carries a `Dispatched by: overseer <loop-file-path>` header (see the `overseer`
skill), six things change:

1. **Correct a wrong record at the source, not only in this fix's own report.** When the fix
   disproves a claim living in a record outside this fix's own write set — a rollout trace line,
   another fix doc, a status doc — edit that record in place before finishing (a dated annotation
   for a process record; a spec takes the Step 4 rewrite-or-annotate choice), and also note it in
   this fix's completion summary. A diagnosis that stays only in the diagnosing fix's report leaves
   the wrong sentence where the next reader will find it first.
2. **End Step 8's completion summary with the structured return block** below.
3. **Every numeric claim carries the command that produced it, and its output goes in verbatim**
   (Step 5r's rule). The overseer may carry the number into a scheduling decision several cycles
   later, and it will re-run one of your numbers before acting — write them to be re-run.
4. **The overseer does the outward writes of a GitHub-issue fix.** You draft the Step 11 summary
   comment and any `docs/plans/followups.md` row, and put both in the return block. The overseer
   posts and writes them.
5. **Confirm HEAD before reading anything, and stop by ending the turn.** Run the check the
   dispatch names and confirm HEAD contains the base it names. Where this skill would stop for the
   user (the §Scope branch warning, approval of the Step 5 plan and Step 5b recommendation), end
   the turn with the question as the final message. Do not use an interactive question prompt.
6. **Run only the checks this fix's changed paths reach, and leave the commit gate to the
   overseer.** List the changed paths (`git diff --name-only <base>` plus `git status --short`) and
   run the parts of `scripts/run_tests.sh` they reach. If you believe the fix cannot be verified
   without the full run, stop and report.

**Do not read the loop file.** The path in the header is there so this fix can cite it. If the
dispatch prompt is missing something you need, say so and ask; a prompt that can only be
understood by opening the loop file is a defective dispatch.

## Environment

**1. Never depend on the shell's working directory.** It is not guaranteed to persist between Bash
calls. Use **absolute paths** for interpreters, scripts and the Blender binary
(`/Applications/Blender.app/Contents/MacOS/Blender`).

**2. Render only through the harness.** Reproducing or verifying a render defect means running
`blender/harness/render.py`, never an ad-hoc `bpy.ops.render` call. Prefer `bpy.data` over
`bpy.ops` in any diagnostic script — `bpy.ops` depends on UI context and breaks in background mode.

**3. A blast-radius search scopes to the REPO ROOT.** Step 4 asks who else depends on the thing you
are changing — and in the record lane, who has already repeated the wrong sentence. The citations
that did the damage live in other quests, in `docs/`, in `skills/`, and in commit messages, not
only inside the quest directory.

## Scope

Default scope is `project` (project-wide, reports in `docs/plans/fixes/`). When the user says **"in sidequest \<slug\>"**, this skill
rebases its path roots to that side-quest (`sidequest:<slug>`). There is no main rollout. See `sidequests/README.md` for the convention.

A side-quest folder is **narrative only** — it does not carry its own spec files. Persistent specs
live under `docs/`, `schemas/`, `styles/` and `docs/adr/`, and the quest declares which ones it
touches via the `spec-refs:` frontmatter field in its rollout.

| Concept | Project scope (`project`) | Side-quest scope (`sidequest:<slug>`, from `in sidequest <slug>`) |
|---|---|---|
| Intent / acceptance | `docs/project-definition.md` (incl. §Milestones exit gates) + `docs/adr/` | the quest rollout's acceptance criteria, plus each `spec-refs:` path (fall back to `docs/project-definition.md` if `spec-refs:` is empty) |
| Architecture | `docs/project-definition.md` §System concept, §Pipeline, §Repository structure + `docs/adr/` | each `spec-refs:` path under `docs/`, `schemas/` or `docs/adr/` (same fallback) |
| Doctrine / stack | `CLAUDE.md` | (always project-wide) |
| Test Strategy | `docs/test-strategy.md` | (always project-wide) |
| Fix Plans | `docs/plans/fixes/` | `sidequests/<slug>/fixes/` |

**Loading context for a side-quest fix:**

1. Read the quest rollout's frontmatter and parse `spec-refs:`.
2. Read each `spec-refs:` path as the authoritative spec for this fix.
3. If `spec-refs:` is empty (typical for spikes), fall back to `docs/project-definition.md`.
4. The quest folder itself contains no spec files — never look there for one.

When a fix modifies a persistent spec, the modification happens in place at its persistent path.
Fix plans still land under `sidequests/<slug>/fixes/`.

**Worktree alignment (check before implementing).** When the scoped quest's rollout frontmatter
declares a `worktree:`, this fix's commits belong on that quest's `worktree-<slug>` branch:

```bash
git rev-parse --abbrev-ref HEAD
sed -n 's/^worktree:[[:space:]]*//p' sidequests/<slug>/<slug>-rollout.md | head -1
```

Without an overseer header, if the quest declares a worktree and you are not on `worktree-<slug>`,
warn — *"quest `<slug>` declares a worktree at `<path>`; commits will land on `<current-branch>`,
not the worktree. Switch into the worktree, or confirm you intend to commit here."* — and wait for
the user before committing. Under the header, compare against the branch the dispatch names
instead, and put a mismatch to the overseer as your final message. With no `worktree:` and no
header, proceed normally.

The workflow steps are unchanged across scopes — only the path roots shift.

---

## Step 0 — Classify the Defect

1. **Is this a GitHub issue?** Look for an issue number (e.g., `#123`) or URL in the prompt.
   - If YES → fetch the issue **and its comments**:
     `gh issue view <n> --repo mpk-code/AIAnimationLab --comments`. Note the number, title,
     description, labels and state. List any attached image or file you did not open.
   - **Read the issue's initial hypotheses.** An issue may carry a reporter's hypothesis — in the
     body, or in any comment beginning `Initial hypothesis:`. Record each in the Step 0 summary,
     attributed and split into separate claims: suspected causes, ruled-out areas, and any quest or
     milestone it names. They are claims for Step 1 to test, not findings. With none, write
     "no initial hypothesis".
   - If NO → treat as an unmanaged defect. **Do NOT create a GitHub issue** unless the user
     explicitly asks for one (then use the `defect-filing` skill).

2. **Is this a visual/render problem or a logic/code problem?** (May be both.) A visual defect —
   wrong palette, banned camera move, nondeterministic frames, a style that does not survive
   rendering — is reproduced and verified through the harness and its contact sheets (Step 6).

3. **Summarize the bug** in 2–3 sentences: observed behavior, expected behavior, and the known
   reproduction path (scene script, profile, machine, seed — if any).

4. **Is this a code-review-driven fix?** Detect via (priority order):
   - (a) `code-review-` filename prefix on the invocation path (the canonical signal;
     `/code-review` always uses this prefix).
   - (b) A `**Source review:**` field already present in a fix plan header the user points at.
   - (c) Explicit user statement ("fix the issues from the code review report at \<path\>").

   If any hold → **review-driven**; record the source review path. Step 12 will run.
   Otherwise → **freestanding**; Step 12 short-circuits.

---

## Step 0b — Lane: code defect or record defect?

This skill's central discipline is TDD, and **there is no failing test for a wrong sentence.**
Records go wrong the same way code does and need the same RCA, blast radius, refactor
classification and adversarial review — but not a red-to-green test. So the skill runs two lanes
that differ in exactly one step: what stands in for the failing test. The lane lives here rather
than in its own skill because you usually cannot tell which lane a defect belongs to until the RCA
is under way.

Classify by **what the correct fix changes**, not by the file's extension:

- **Code lane** — the fix changes executable behavior: source, a style module, a `style.yaml` or
  `production.yaml` value code reads, a schema, a validator, or a test. Full TDD. A `.md` file is in
  the code lane when its text is executed (a doctest, or a command a runbook expects run verbatim).
  A stage skill's procedure is in the code lane when the defect is what it makes the pipeline do.
- **Record lane** — the fix changes only text that *asserts something about the system*, and no
  behavior changes. A `.py` file is in the record lane when only its docstring is wrong.

**The code-adjacent middle resolves to the record lane.** A stale docstring, a `file:line` in a
comment that has moved, an ADR number that no longer resolves — the code is right and the sentence
about it is wrong. The boundary is *which one was wrong*, never *which file it lives in*.

**Three things that look like record defects and are not:**

1. **The record is right and the code is wrong.** Run the recompute *before* you settle the lane —
   recomputing the claim is what tells you which side is at fault. If the output convicts the code,
   this is an ordinary code defect with a documentation update riding along.
2. **Both are wrong.** Split into two fixes. Bundling them is how a code fix ships without a red test.
3. **The record describes intended, not present, behavior.** An unmet acceptance criterion or an
   unbuilt milestone task is unfinished work, and belongs to `/run-process`, not here.

Record the lane in the Step 0 summary; it carries into the fix plan header's `**Lane:**` field,
written as exactly `code` or `record`.

**The lane also decides how a GitHub issue ends.** The `commit` skill writes `Closes #<n>` only for
a `**Lane:** code` fix document. A record-lane fix changes no product code, so its issue is
**closed by hand on GitHub with the close reason *not planned*** once the fix is on `main`.

---

## Step 1 — Root Cause Analysis (RCA)

Before planning the fix, understand *why* the bug exists.

- Trace the bug to its origin: a logic error, a missing guard, a schema/artifact contract violation,
  a `bpy` API change or background-mode context error, nondeterminism (unseeded randomness, GPU
  variance), a missing test, or a design gap?
- **Test every hypothesis Step 0 recorded, never inherit one.** For each part, give a verdict of
  **confirmed** or **refuted**, with the evidence (a command and its output, or a `file:line`), in
  the fix document's `## Hypotheses` section, one line per part.
  - **A ruled-out area** narrows the search only after you have run your own check of it. The
    reporter's check is where you start looking, not evidence you can cite.
  - **A named quest or milestone** is a claim like any other. Check it against the rollout.
  - A part you can neither confirm nor refute means the investigation is not finished. If a part
    still cannot be decided, **STOP** and put it to the user (through the overseer if dispatched).
- State the root cause explicitly. Do not proceed to planning until it is understood, **or** you
  have concluded that it cannot be established, under the conditions below.
- **"Root cause not established" is a lawful outcome**, not a way to skip the analysis. You may
  conclude it only after a real investigation, and then:
  1. The fix document records **what was ruled out, and how**: each check, with its command and
     output or its `file:line`.
  2. Any change is labelled a **mitigation**, not a fix: in the title, in `### Changes Made`, and in
     the Step 11 summary.

  Write `**Root Cause:** Root cause not established — <what remains unknown>` in the header. A
  header that states a cause the evidence does not show is the failure this outcome replaces.
- Identify the **blast radius**: which stages, artifacts, style modules, styles, validators,
  schemas or productions could be affected by this bug or its fix?
- List related areas to check during testing.

---

## Step 2 — Intent Check

1. Read the intent documents for the active scope (Scope table): `docs/project-definition.md`
   sections and, for a quest, its rollout's acceptance criteria and `spec-refs:`.
2. Determine: **Is the correct behavior described or implied by an existing document?**
   - If YES → note the section or acceptance criterion. No update needed.
   - If NO → draft the missing statement of expected behavior.
     - **STOP. Present the draft to the user for review before continuing.**
     - Once approved, update the persistent spec at its path. If it changes doctrine
       (`CLAUDE.md`), the glossary, or a schema, it needs an ADR — draft one from
       `docs/adr/0000-template.md` and present it. **In a side-quest scope, only edit specs listed
       in `spec-refs:`**; a needed change elsewhere goes under the rollout's
       "Proposed changes to referenced persistent specs" section (for `feature` quests) or to the
       user for explicit confirmation.
3. **Record the evidence, not the conclusion.** Fill the fix plan's `**Requirements trace:**` with
   the section or criterion **and** the `file:line` you read it at — e.g.
   `§Control surface (docs/project-definition.md:101)` or
   `acceptance criterion 2 (sidequests/<slug>/<slug>-rollout.md:48)`. When nothing governs the
   change, write `none — <one-line reason>`; that is a valid answer for repo tooling and similar
   work. A trace written from memory is precisely what this field exists to prevent.

---

## Step 3 — Architecture & Stack Safety Check

1. Read `docs/project-definition.md` §System concept, §Pipeline and §Repository structure, the
   relevant ADRs in `docs/adr/`, `CLAUDE.md`, and any `spec-refs:` paths.
2. Assess: does the proposed fix require any change to:
   - The architecture — stage boundaries, which artifacts a stage reads or writes, a schema, the
     harness contract, the manifest fields, the generation/critique separation?
   - The stack — Blender version, a new Python dependency, a new external tool?
   - Doctrine or glossary?

**If YES to any:**
- **STOP. Do not proceed.**
- Flag the conflict to the user: what would change and why.
- Require explicit approval, and an ADR where doctrine, glossary or a schema changes.
- Consider whether this warrants its own quest instead.

**If NO** → document the confirmation and continue.

3. **Record the evidence, not the conclusion.** Fill `**Architecture trace:**` in the Step 2 form —
   e.g. `ADR 0001 (docs/adr/0001-blender-api-baseline.md:12)` or
   `§Pipeline (docs/project-definition.md:83)`. When the change is architecturally inert, write
   `none — <one-line reason>`. "Confirmed safe" with nothing cited is a claim, not a confirmation.

---

## Step 4 — Impact & Blast Radius Assessment

Using the RCA findings:
1. List all files, modules, style modules, schemas and validators that may be touched by the fix.
2. List the stages, styles and productions whose output could change (regressions). A change to a
   `blender/lib/` module changes every style that lists it in `modules:`.
3. List integration points: the harness, the manifest writer, validators reading the artifact,
   the eval harness.
4. Note any artifact-format or schema-version concerns (existing productions' artifacts must still
   validate, or the change needs an ADR and a migration note), and any **determinism** concern —
   whether rerun frame hashes (EEVEE exact; Cycles GPU per-pixel tolerance) will still match.

This list becomes the basis for the test plan in Step 5.

**In the record lane, blast radius means: who has already read the wrong sentence and repeated
it.** A record propagates by citation, not by call graph. Grep for the claim's distinctive wording,
its number, and the record's own path across `docs/`, `sidequests/`, `skills/`, `.claude/skills/`
and commit messages (`git log --grep`), and list every downstream copy. Correcting the source while
its copies survive leaves the defect intact everywhere it did damage.

**For a spec, decide here whether to rewrite it or annotate it.** A spec — `docs/project-definition.md`,
`docs/glossary.md`, `docs/coding-standards.md`, `docs/test-strategy.md`, a schema, a `style.yaml` —
is corrected by **rewriting it in place and putting the new text to the user for approval**. That
is the default; git and the fix document keep what it said before. Annotating is allowed only when
the old and new states will live side by side in the system for a while (e.g. a style module being
deprecated across several styles), so a reader needs both: keep the old text and add a dated
annotation stating the transition — what is moving, from what, to what. A change of mind alone is
never a reason to annotate. Record the choice under the fix plan's `## Scope of Change`, one line
per spec: the spec, `rewrite` or `annotate`, and the evidence (for `annotate`, what in the system
still matches the old text and what will complete the transition). A rewrite goes in marked
**DRAFT — AWAITING USER APPROVAL** until the user approves it with the plan at Step 5.

**When the transition is over**, the annotation should go and the text be rewritten — but that
cleanup is a planned Run, not part of a fix. A fix that finds dead annotations lists the spec under
`## Deferred Work` with the command showing the old state is gone, and routes it to the rollout of
the live quest whose `spec-refs:` lists the spec, or to a `docs/plans/followups.md` row proposed
under Step 8's promotion gate.

**Process records are not specs.** Rollouts, `docs/plans/followups.md`, status reports and fix
documents are histories; a correction is a dated annotation that leaves the original readable.
**An ADR is never rewritten** — a wrong decision is superseded by a new ADR; a wrong factual
statement in one takes a dated annotation. **A skill takes no annotation** — dev-process skills
(`.claude/skills/`) and stage skills (`skills/<stage>/`) are rewritten in place. Doctrine
(`CLAUDE.md`) is rewritten in place, with an ADR. For a record that is none of these, ask the user.

---

## Step 5 — Fix Plan (Test-Driven)

Read `docs/test-strategy.md` before writing the plan.

Create the fix plan at the scope-aware path:
- Project scope: `docs/plans/fixes/fix-<issue-or-short-description>-<YYYY-MM-DD>.md`
- Side-quest scope: `sidequests/<slug>/fixes/fix-<issue-or-short-description>-<YYYY-MM-DD>.md`

### Fix Plan Template
```
# Fix: [Short Title]
**Date:** YYYY-MM-DD
**Issue:** #<number> or "unmanaged"
**Lane:** code | record   (per Step 0b — write exactly one)
**Source review:** <path to code-review-*.md, or "none — freestanding">
**Requirements trace:** <section (path:line)>, or "none — <reason>"   (Step 2)
**Architecture trace:** <section or ADR (path:line)>, or "none — <reason>"   (Step 3)
**Reuse checked:** <existing helper/module/pattern + file:line>, or "none — <reason>"
**Root Cause:** [1–2 sentences], or "Root cause not established — <what remains unknown>"
**Status:** DRAFT
**Reproduces after change:** not yet checked   (GitHub issues only; set at Step 8)

## Hypotheses
[GitHub issues only. One line per part of each initial hypothesis: the claim, its source,
 confirmed | refuted, and the evidence. "No initial hypothesis" when there was none.]

## Scope of Change
- Files to modify:
- Schemas / artifact formats / harness interface to update:
- Specs to rewrite or annotate (Step 4):
- Tests to write (TDD — these come FIRST):

## Test-Driven Approach
List the failing tests that will be written BEFORE the fix:
1. [test name] — verifies [behavior]
2. ...

## Fix Steps
Ordered implementation steps, each small and verifiable:
1. Write failing tests
2. [implement step]
3. ...

## Regression Test Plan
Tests and renders to run to confirm no regressions (per blast radius in Step 4):
- ...

## Interface Changes
Schema, artifact-field, harness-CLI or manifest changes, with before/after contracts.

## Render Changes (if applicable)
Which styles/scenes render differently, and the preview contact sheets to compare (Step 6).

## Risks
Known risks or uncertainties in this approach.

## Deferred Work
Related issues found but intentionally left. `None.` or a list.
```

A defect found and left unfixed is filed with the `defect-filing` skill, and each list item in
`## Deferred Work` and `### Future Work Deferred` begins `issue #<n>:` or `not a defect: <reason>`.
A new capability is `not a defect` and goes to `docs/plans/followups.md` (Step 8). A guaranteed
failure, broken render determinism, corrupted artifacts, or significant maintainability debt that
this fix introduces is never deferred: it is fixed here.

**`Reuse checked:` is evidence too.** Before planning new code, look for the helper, style module,
validator or idiom the codebase already carries, and record the `file:line` you actually opened.
When nothing applies, write `none — <one-line reason>`. An unsourced assertion is not an answer.

**Record lane — one substitution, nothing else.** Replace `## Test-Driven Approach` with
`## Recompute check` per Step 5r, and let `## Fix Steps` step 1 read "run the recompute against the
current text". Every other section keeps its name and meaning.

**STOP. Present the plan to the user for approval before implementing.**

---

## Step 5r — The Recompute Check (record lane only)

In place of a failing test, a record-lane fix produces **a re-runnable command that recomputes the
claim the record asserts** — run against the wrong text and again against the corrected text. The
fix doc carries the command **and its pasted output**, not an assertion that it was run, and the
command is committed beside the record when it is more than a one-liner.

**The analogy with TDD breaks in one place.** A test goes red then green because the *code*
changed. A recompute that reads source usually prints the **identical output both times**, because
the code was right all along. The red step is "the output contradicts the sentence"; the green step
is "the same output now matches the sentence". If you find yourself editing the command to make it
agree with the corrected record, stop: you are tuning the measurement to the claim.

The artifact is required rather than the habit because a gate that demands a pasted output gets an
output, while a gate that demands diligence gets a claim of diligence.

### What the command has to be

**Falsifiable, not necessarily exit-coded.** A second reader must be able to look at the output and
say "the record's sentence is inconsistent with this."

**Prose claims qualify and are not exempt.** A sentence like "the harness writes the manifest
before rendering" has no number in it, but `git grep -n "write_manifest" -- blender/harness` shows
where it is called and settles it. Reading a record back to itself is not a check.

**Paste what the command printed, then say which lines carry the claim.** Trimming the output to
the part that agrees with you reintroduces the same failure one level up.

**A code fence does not launder a re-typed number.** The output goes in verbatim — same lines,
same order, same truncation the command chose — or the block says plainly that it is a summary.
Redirect to a file and paste the file; where you will act on the reading, diff the paste against a
fresh capture rather than reading it back.

**The obligation attaches to claims about system state** — what the code does, how many of X exist,
where something lives, what a render produced. Claims about intent, rationale or a human decision
are *attributed* ("the user chose X on <date> because …"), not recomputed. If a record asserts
system state and no command can recompute it, that is itself the defect: rewrite the claim into one
that can be checked, or restate it as attributed judgment.

### Three tiers, and what each honestly promises

| tier | the claim reads | the check | what it promises |
|---|---|---|---|
| **R1 — tracked source** | git-tracked files | a `git grep` / `rg` one-liner with an expected result | reproducible by anyone, anywhere, indefinitely |
| **R2 — derived** | git-tracked files, but needs parsing / counting / joining | a script committed beside the record | reproducible by anyone; the script records *how* the number was derived |
| **R3 — local render output** | untracked renders, frames or timings under `productions/<id>/` or a harness `--out` dir (kept out of git or in LFS) | a script or harness run on the machine that holds the output | re-runnable by hand only — **machine-specific and point-in-time** |

**An R3 reading is a timestamp, not a property.** Render time, frame hashes and GPU output depend on
the machine (M5 Max vs M1), the Blender version and the engine. So an R3 recompute records **when it
ran, on which machine, with which Blender version and seed** (the manifest has them — cite it), and
where its denominator came from. A number without that provenance is a snapshot masquerading as a
property of the system.

**Write a claim about a gate so it carries its own recompute.** Cite the **derivation**, not the
location: "a check `scripts/run_tests.sh` runs (`grep -n <check> scripts/run_tests.sh`)" rather than
a line number that rots the next time the file moves. Changing a gate's status is a repo-wide record
change, and nothing enforces the sweep. Propose a new automated checker only when a whole *class* of
claims shares one derivation — never for a single sentence.

---

## Step 5b — Refactoring Assessment

Now that the fix plan is drafted, assess whether refactoring is warranted. This judgment cannot be
made before the plan exists — the plan reveals the design quality of the code being touched.

Make **one of three recommendations**:

### Option A — Refactor as Part of the Fix

Choose this when the fix itself is simple but the current design is so poor that applying it
cleanly *requires* restructuring — otherwise you are adding complexity on bad foundations, or the
same class of bug will recur.

- Describe what needs refactoring and why it is necessary for a clean fix.
- Add a **Preparatory Refactor** section to the plan, before the fix steps:
  ```
  ## Preparatory Refactor (before fix)
  - Scope: [what is being restructured]
  - Rationale: [why this is necessary for the fix to be clean]
  - Constraint: NO behavior change. All existing tests must pass, and preview renders must be
    unchanged (same frame hashes for EEVEE).
  - Verification: Run scripts/run_tests.sh after refactor, before writing fix tests.
  ```
- Step 7's sequence becomes: refactor (green → green) → failing tests → fix (red → green) →
  refactor test code if needed (green → green).

### Option B(a) — No Refactor Needed

Choose this when the fix is self-contained, the design is adequate, and there is no meaningful
signal of a recurring pattern. State briefly why.

### Option B(b) — Refactor Warranted Later, Not Now

Choose this when the design has problems (repeated similar bugs, growing complexity, test
duplication, poor abstraction) but refactoring now would expand scope or risk significantly.

- Describe the design issue and the triggering pattern ("third bug in this module with this shape").
- Add a `TODO(refactor)` comment in the relevant production and/or test code:
  ```
  # TODO(refactor): [what should be generalized and why]
  # Deferred during fix of [issue/description] on [date]. See docs/plans/fixes/[plan-file].md
  ```
- Add to the fix plan:
  ```
  ## Deferred Refactoring
  **Decision:** Refactor warranted but deferred
  **Date:** YYYY-MM-DD
  **What:** [production code, test code, or both]
  **Why deferred:** [scope risk / timing / low recurrence so far]
  **Signal:** [what triggered this observation]
  **Recommended action:** Open a dedicated quest when [condition].
  ```

**In the record lane, "refactor" reads as: can this claim be made incapable of going stale?**
Option A replaces a hand-written inventory with a derivation — a generated table, a test that
enumerates from source, a script whose output is pasted in. Choose it when the same claim is
restated in several places, or when a future reader will rely on it without re-deriving. Option
B(b) is the honest answer when the derivation is real work: leave the prose, but say in the record
where the number came from and how to recompute it. The recurrence signal for Option A is a
*second* wrong count in the same document.

**Present the refactoring recommendation to the user alongside the fix plan.** The user approves or
adjusts both together before implementation begins.

---

## Step 6 — Render / Style Verification (if applicable)

If this is a visual defect, or the fix changes rendered output:

1. Reproduce through the harness before the fix, and keep the preview contact sheet and
   `manifest.json` as the "before" evidence.
2. Where the fix changes what a style does, update its `style.yaml` (and spec) in place per Step 4,
   and bump its `version`.
3. After the fix, render the same scene with the same seed and profile, and present the before/after
   contact sheets to the user if the visual change is non-trivial. A visual defect's failing test is
   preferably an automated one (a validator check, a frame-hash or pixel-tolerance assertion); the
   contact sheet is supporting evidence, not a substitute.

---

## Step 7 — Implementation

Once the plan and refactoring recommendation are approved:

**If Option A (Refactor as Part of Fix):**
1. **Perform the preparatory refactor first.** No behavior change.
2. Run `scripts/run_tests.sh` to confirm green before proceeding.
3. **Write the failing tests for the fix** (TDD). Confirm they fail for the right reason.
4. Implement the fix.
5. Confirm the new tests now pass.
6. **Refactor test code if needed** — remove duplication, extract helpers, parameterize. Keep green.
7. Run the full regression set from Step 4 (`scripts/run_tests.sh`, plus any harness renders it named).
8. Confirm all previously passing tests still pass.

**If Option B(a) or B(b) (No Refactor Now):**
1. **Write the failing tests first** (TDD). Confirm they fail for the right reason.
2. Implement the fix in the smallest possible change set.
3. Confirm the new tests now pass.
4. **Refactor test code if needed** (green → green). Do not skip this.
5. Run the full regression set from Step 4.
6. Confirm all previously passing tests still pass.
7. If B(b): confirm `TODO(refactor)` comments are in place.

**If the record lane:** the same sequence with the recompute standing in for the tests.

1. **Run the recompute against the current, wrong text first.** Paste the command and its output.
   This is the red step, and it confirms the lane — if the output agrees with the record, the record
   is not the defect and you are in the code lane after all.
2. Correct the record and every downstream copy Step 4 listed — rewrite or annotate each spec as the
   approved plan says, annotate each process record, rewrite a skill in place.
3. **Re-run the same command, unmodified, and paste the output again.** Read the corrected sentence
   against that output, not against your intent for it.
4. If the recompute is more than a one-liner, commit the script beside the record.
5. Run any existing check that covers the record's class, and note whether it is gated by
   `scripts/run_tests.sh` or hand-run.

**While writing the fix — the anti-structure rules (all options).** These constrain the
*structure* you add, never the size of the diff; "smallest possible change set" is the only size
pressure this skill applies.

1. **No unrequested abstractions.** No interface with one implementation, no factory for one
   product, no map keyed by a dimension with one entry, no config value for something that never
   varies, no scaffolding "for later".
2. **Prefer editing an existing file over creating a new one.**
3. **Never simplify away** input validation at trust boundaries (schema validation of artifacts),
   error handling that prevents data loss, seed recording, or anything the defect report explicitly
   asks for. A smaller change in the wrong place is a second defect.
4. **Update every record the fix falsifies.** A docstring, comment, spec sentence, `style.yaml`
   field or acceptance criterion that asserts the behavior you just changed is part of the fix, not
   scope creep. Rules 1–3 bound the structure you add; none of them bound the records you leave
   behind.

**All options:**
- Respect doctrine: render only through the harness; prefer `bpy.data` over `bpy.ops`; record every
  seed in the manifest; never commit renders outside Git LFS.
- If this is a GitHub issue, work on a branch named `fix/<issue-number>-<short-slug>`, **unless the
  scoped quest declares a `worktree:` or the prompt carries an overseer header** — then the
  dispatch's branch, or the quest's `worktree-<slug>` branch, wins (§Scope). The issue closes when
  the fix reaches `main` (Step 11), so the branch name has no bearing on closure.

---

## Step 8 — Plan Completion Update

**Before writing `Status: COMPLETE`, verify the fix is present in source.** Pick one distinctive
signature of the change (a new function name, assertion, or literal string), run
**`git grep --untracked <signature>`**, and record the `file:line` hit(s) under
`### Landed verification`. `--untracked` is not optional: plain `git grep` searches only tracked
files, so a fix that *adds* a file reports zero hits. Add `-i` when the signature's case varies. If
the grep returns nothing, the fix did **not** land and is not COMPLETE, whatever the session
appeared to do.

In the record lane the signature is a phrase from the **corrected sentence**, and the grep must
also return zero hits for the wrong phrase across every copy Step 4 listed. A corrected source with
a surviving copy elsewhere is a half-landed fix.

**For a GitHub issue, record whether the reported behaviour still reproduces.** Re-run the issue's
reproduction path (or the check that reproduced it before the fix), then set the header line:

- `**Reproduces after change:** no — <the check, and its result>`. The only value on which the
  `commit` skill writes `Closes #<n>`, and only in the code lane. A record-lane `no` is closed by
  hand as *not planned*.
- `**Reproduces after change:** yes — <the check, and its result>`. Right for a change that only
  adds diagnostics or fixes part of the defect. The issue stays open; closing it and filing the rest
  is the user's decision.

This is independent of the root cause. Keep the first word exactly `no` or `yes` — the `commit`
skill reads it. For an unmanaged defect, leave the line out.

Complete the fix plan, at the path Step 5 chose, in two distinct motions.

**1. Change the header's `Status` line; do not add a second one.** Edit `**Status:** DRAFT` to
`**Status:** COMPLETE` and add `**Completed:** YYYY-MM-DD` beside it. A fix doc carries exactly one
`**Status:**` stamp, in the header — a resume procedure reads the first stamp (`grep -m1`), so a
header left at `DRAFT` above a completion summary reads as "nothing landed", and two stamps that
disagree are a record defect.

**2. Append the completion summary below**, which carries no stamp of its own:

```
## Completion Summary
### Changes Made
[Files changed and what changed. Each labelled a mitigation if the root cause was not established.]

### Landed verification
[The signature grepped for and the `git grep --untracked` file:line hit(s). Required before COMPLETE.]

### Root Cause (confirmed)
[Confirm or revise the RCA. If not established, say so and list what was ruled out and how.]

### Test Results
[Code lane: new tests, regression results, renders compared (with manifest paths).
 Record lane: replace with `### Recompute results`.]

### Recompute results
[Record lane only. The command verbatim, its pasted output against the wrong text, and its pasted
 output against the corrected text. Name the tier (R1 / R2 / R3). For R3, record when it ran, the
 machine, Blender version and seed, and state that it is hand-run and point-in-time.]

### Adversarial review outcome
[Step 9's findings: each 🔴 HIGH / 🟡 MEDIUM / 🟢 LOW with its resolution, or "none — no findings".
 HIGH findings must be resolved before COMPLETE.]

### Refactoring Decision
- Option A: Preparatory refactor performed — [what was restructured]
- Option B(a): No refactor — [why not warranted]
- Option B(b): Refactor deferred — [what, why, TODO comments placed in: <files>]

### Risks Realized
[Any risks from the plan that materialized]

### Future Work Deferred
[`None.` or a list; each item begins `issue #<n>:` or `not a defect: <reason>`.]

### Overseer return block (only if dispatched by an overseer)
- **Verdict:** GO | NO-GO against this fix's acceptance criteria — state NO-GO plainly.
- **What changed:** one line, pointing at Changes Made.
- **Still open:** anything found but not fixed — including any record corrected outside this fix's
  write set (file:line and what changed there).
- **Drafts for the overseer:** the Step 11 issue comment and any followups row.
- **Claims and their standing:** one line per claim the overseer might act on, tagged MEASURED /
  INFERRED / SPECULATIVE. **MEASURED is valid only with the runnable command inline.** An INFERRED
  claim states its premise separately.

### Source review findings addressed
[Required when Mode = review-driven; omit otherwise. One bullet per source-review finding: severity,
 title, and resolved | deferred: <marker> (rationale) | not applicable (rationale). Criticals MUST be
 resolved. Majors may be deferred with rationale and a filed issue.]

### Mode
- review-driven (source: <path to code-review-*.md>) | freestanding
```

**Promote deferred items to the followups index.** For each `not a defect:` item in
`### Future Work Deferred` (an `issue #<n>:` item is already tracked), ask:

1. Does it have a **specific external trigger** (a Blender release, an upstream fix, a milestone
   starting)? Or
2. Is it a **concrete cross-cutting tooling investment** that would be hard to re-derive later?

If either holds, propose a row for `docs/plans/followups.md` (Open table): opened date, title, type,
trigger, action when triggered, source (link to this fix plan). If neither holds, leave it in the
fix plan. **Surface the proposal to the user and wait for approval before editing
`docs/plans/followups.md`.**

---

## Step 9 — Adversarial Review

Review the completed work as a skeptical reviewer actively trying to find problems. **Run it in a
separate subagent context** — a model never grades its own output (CLAUDE.md). Give the reviewer the
fix plan, the diff, and the Step 4 blast radius; not your reasoning.

The reviewer checks each area and produces a written findings report:

**Test Coverage**
- Edge cases not covered? Boundary, empty, zero-duration, single-frame or missing-field cases?
- Could any test pass for the wrong reason (false positive)?

**Integration**
- Does the fix interact correctly with everything in the blast radius?
- Environment-specific issues: background mode vs UI context, Blender version, machine (M5 Max vs
  M1), EEVEE vs Cycles, GPU vs CPU?
- Does render determinism still hold — same seed, same frames?

**Approach**
- Is there a simpler or safer fix that was overlooked?
- Does the fix address the root cause, or only a symptom?
- Does it introduce technical debt, or a silent default (a creative decision not written to an
  artifact)?

**Quality**
- Consistent with existing style and `docs/coding-standards.md` (`STD-###`)?
- Error messages clear and actionable?
- Does the manifest still record enough to reproduce and detect a regression?

Findings are rated:
- 🔴 **HIGH** — must fix before this work is done
- 🟡 **MEDIUM** — should fix; if deferred, file it with `defect-filing` and name it in the plan
- 🟢 **LOW / INFO** — noted; a LOW that is a defect and is left unfixed is filed the same way

Fix all HIGH findings before Step 10. Add each deferred finding to `## Deferred Work` as
`issue #<n>:` with a brief rationale. **Record the outcome in `### Adversarial review outcome`** —
every finding with its resolution, or `none — no findings`. A completion summary without that
section means the review is unverifiable and the fix is not done.

---

## Step 10 — Test Strategy Compliance & Final Test Run

1. Re-read `docs/test-strategy.md`.
2. Verify the new and updated tests align with its test types, coverage expectations, naming
   conventions, and test data / render-profile requirements.
3. Update `docs/test-strategy.md` if this fix established a new pattern or test category.
4. Run `scripts/run_tests.sh` one final time and confirm it passes. Read its exit code from a bare
   invocation — never through a pipe (`| tail`, `| grep`) or with a trailing `; echo`, which report
   the last command's status, not the gate's. Don't construct ad-hoc pytest command lines for the
   gate decision.
5. Document the final run in the fix plan.
6. **Check this fix's own doc.** Exactly one `**Status:**` line, in the header, reading `COMPLETE`:
   `grep -n '^\*\*Status:\*\*' <fix-plan>`. The test run gates the code the fix wrote and says nothing
   about the document written alongside it.

**Record lane:** steps 1–3 do not apply. The final run is the Step 5r recompute, executed once more
against the committed text, with its output pasted into `### Recompute results`. If the change
touched a docstring or comment inside a tested module, run that module's tests too — an edit inside
a `.py` file can still break collection.

---

## Step 11 — GitHub Report-back (GitHub issues only)

If this was a GitHub issue:

1. **The carrier of `Closes #<number>` is normally the commit message**, written by the `commit`
   skill when the fix document qualifies (item 3). You write no keyword yourself. If the fix lands
   through a pull request, its description references the issue (`Closes #<number>`, under the same
   condition), summarizes the root cause, lists key changes and notes deferred work.
2. Post a comment on the issue with a fix summary (`gh issue comment <n> --repo mpk-code/AIAnimationLab`).
   **If dispatched by an overseer, do not post it** — put the text in your return block:
   ```
   ## Fix Summary
   **Root Cause:** [1 sentence, or "Root cause not established" and what was ruled out]
   **Changes:** [brief list; each labelled a mitigation when the root cause was not established]
   **Reproduces after change:** [no | yes — the check]
   **Tests Added:** [count and description]
   **Deferred:** [any issues filed]
   ```
3. **Leave the issue open.** This skill does not close it. It closes when the fix reaches `main`,
   through `Closes #<number>` in the commit message or a merged PR. The `commit` skill adds the
   keyword only for a commit that includes a fix document with an `**Issue:** #<number>` header, a
   `COMPLETE` status, `**Lane:** code`, **and** `**Reproduces after change:** no — …`. This skill
   never closes the issue because it has no commit step; closing here would mark it fixed while
   `main` does not contain the fix.
4. **Record lane: say how the issue will be closed.** End the completion summary with:
   `#<number>: record-lane fix; once it is on main, close it by hand on GitHub as "not planned"`.
   Under an overseer, put that line in the return block.
5. **Never write a closing keyword by accident.** GitHub reads `fix #<n>` inside `/bug-fix #<n>` as
   closing the issue. In anything that may become a commit message, dispatch or PR title, write
   `issue #<number>`, never `/bug-fix #<number>`.

---

## Step 12 — Code-Review Tag Advancement

**Runs only when Mode = review-driven.** Freestanding invocations short-circuit: note
`Mode: freestanding` in the completion summary and exit.

This step closes the `/code-review → /bug-fix → /commit` loop: the next `/code-review` uses the
advanced tag as its base ref. It is always the *last* thing this skill does.

### 12.1 Parse the source review

Read the source review (path in the fix plan's `**Source review:**`) and extract its frontmatter
`base-ref:`.

- **Prior tag exists** — `base-ref:` is a `code-review/<YYYY-MM-DD>-<short-sha>` tag. Record it as
  `<old-tag>`.
- **First-ever review** — `base-ref:` is a commit ref (e.g. `HEAD~5 (4053903)` or a merge-base sha).
  Record `<old-tag>` as `none (first review)`.

### 12.2 Gate on completion state

Refuse to advance the tag if **any** hold:

- Step 9 left a 🔴 HIGH finding unresolved.
- Step 10's final verification is not recorded as green in the fix plan — in the record lane, that
  is `### Recompute results` carrying a pasted post-correction output.
- `### Source review findings addressed` is missing, or lists any **Critical** finding as anything
  other than `resolved`.
- The working tree is not clean.

On any gate failure, **do not** advance the tag. Append to the fix plan:

```
## Tag advancement: deferred
- **Reason:** [enumerate failing gates]
- **Manual recovery (after fixing):**
    git tag -f code-review/<YYYY-MM-DD>-<short-sha> HEAD
```

The rest of the fix is still considered done.

### 12.3 Compute the new tag

`code-review/<YYYY-MM-DD>-<short-sha-of-HEAD>` — today's date and `git rev-parse --short HEAD`.

### 12.4 Advance the tag

```
git tag -f <new-tag-name> HEAD
```

`-f` is required because a same-day re-run of `/code-review` may already have created today's tag.
Force-overwriting *today's* tag is the only legitimate `-f` case.

### 12.5 Never push

No `git push --tags`, no `git push origin <tag>`. The tag is local; propagating it is the user's
choice.

### 12.6 Record in the fix plan

```
## Tag advancement
- **Old tag:** code-review/<old-date>-<old-sha>   # or: none (first review)
- **New tag:** code-review/<new-date>-<new-sha>
- **HEAD sha:** <new-sha>
- **Pushed:** no (local only)
```

---

## Non-Negotiables

- **Never skip the user approval gates** at Steps 2, 5/5b, and 9.
- **Never write implementation code before the fix plan and refactoring recommendation are approved.**
- **Always write tests before writing the fix** (TDD) — in the code lane. The record lane's one
  substitution is the Step 5r recompute; "it's only a document" is not a reason to skip RCA, blast
  radius, or adversarial review.
- **Never correct a record without a pasted recompute output** — before and after the correction. A
  conclusion in that section ("verified", "confirmed against source") is the failure the lane exists
  to remove.
- **Never present an R3 (local render output) reading as a property of the system.** Record when,
  where, on which Blender version and seed it ran.
- **Always run the full regression set**, not just the new tests.
- **Refactor test code** when duplication or poor structure is encountered.
- **Never refactor and fix in the same step** unless following the Option A sequence.
- **Always document the refactoring decision** — "we considered it and chose not to" is a valid and
  required outcome.
- **Never write a `Requirements trace:`, `Architecture trace:` or `Reuse checked:` from memory.**
  Each carries a `file:line` you actually opened, or an explicit `none — <reason>`.
- **Never write `Status: COMPLETE` without a `### Landed verification` grep hit.**
- **Always record the Step 9 adversarial-review outcome**, and run that review in a separate
  subagent context.
- **Never write a guessed root cause.** Write "Root cause not established", record what was ruled
  out and how, and label every change a mitigation.
- **Never inherit an initial hypothesis.** Every part gets a confirmed or refuted verdict with evidence.
- **Never mark a GitHub-issue fix COMPLETE without its `**Reproduces after change:**` line.**
- **Never create a GitHub issue** for an unmanaged defect unless the user explicitly requests it.
- **If architecture, stack, doctrine, glossary or schema changes are required**, stop and escalate —
  never sneak them in; those need an ADR.
- **Never render outside the harness**, even to reproduce a bug.
- **In a side-quest scope, only edit persistent specs listed in the quest's `spec-refs:`.** Anything
  else is escalated, or recorded under the rollout's "Proposed changes to referenced persistent
  specs" section for `feature` quests.
- **Never advance the review tag when invocation is freestanding**, never push it, never advance it
  with unresolved HIGH findings, test failures or Critical source-review findings, and never
  force-move a `code-review/*` tag whose date is not today.
