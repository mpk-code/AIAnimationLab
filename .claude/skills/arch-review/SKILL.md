---
name: arch-review
description: >
  Architecture-conformance review: does the studio's structure still serve its quality objectives
  (render reproducibility/determinism, render cost, stage isolation, schema/validator coverage,
  Blender API drift resilience)? Emits a remediation report /bug-fix and /run-process consume.
  Use for "review the architecture", "arch audit", "architecture conformance", "does the design
  still hold", "are we drifting", "will renders still reproduce", "is the pipeline still
  re-runnable stage by stage", or /arch-review. Emergent-attribute gate, not per-diff review
  (that is /code-review).
---

# Architecture Review Skill

You evaluate whether AIAnimationLab's **structure** still serves its **objectives** — global,
emergent quality attributes that no single file owns and that a per-file sweep cannot see. You
produce one markdown remediation report and stop; you do not edit source, commit, or move tags.

## What this reviews — and what it does NOT (the boundary)

**Discriminator — apply to every candidate finding:** *Could a single-file, diff-local reading
find this?* **Yes** → it belongs to `/code-review` (a defect in changed code) or
`/complexity-review` (reader-level obtuseness); **stay silent.** **No** — it needs composing
several regions against an objective/scenario, reasoning about the design on paper (Adequacy), or
a measurement (Empirical) → it is yours.

Adequacy and Empirical are yours exclusively. On the shared Conformance edge the split is
altitude: `/code-review` checks whether *a diff* follows documented patterns; you check whether
the *enacted architecture as a whole* matches the model (matches / divergences / absences),
reporting only drift a per-diff read could not see. When a failing concern decomposes into a
local fix, **name the concern and route the fix to `/bug-fix`** — never re-emit the defect
yourself. Aggregate related local issues into a *risk theme* tied to the objective they threaten.

## Scope and review subject

- **Quest scope** resolves as in `/code-review` and `/run-process` (`project` vs. `sidequest:<slug>` from `in sidequest <slug>`);
  the report lands in `docs/plans/fixes/` (`project`) or `sidequests/<slug>/fixes/` (side quest), named
  `arch-review-<subject-slug>-<YYYY-MM-DD>.md`.
- **Review subject** — default: **the studio core** (`blender/harness/`, `blender/lib/`,
  `validators/`, `schemas/`, and the stage skills' generated-code paths under `skills/`). Accept an
  explicit override ("review the architecture of `<path>`").

## The three reference points (substrate)

- **Objectives** — the *why*: `docs/project-definition.md` (§Hypotheses and success criteria,
  §Control surface, §Risks, §Milestones exit gates), the doctrine in `CLAUDE.md`, the active
  quest's acceptance criteria, and tradeoffs recorded in `docs/adr/`.
- **Architecture** — the *how-as-planned*: `docs/project-definition.md` §System concept,
  §Pipeline (stages 0–8, Gates A/B/C, "each stage reads only upstream artifacts"),
  §Repository structure, §Artifact schemas; accepted ADRs in `docs/adr/`; `docs/glossary.md`.
- **Code** — the *how-as-built*: the enacted structure under the review subject.

## The quality objectives

| Attribute | Objective | Why it matters here |
|---|---|---|
| `reproducibility` | Same scene + same seed → same frames (EEVEE exact frame hashes; Cycles GPU within a per-pixel tolerance); every render's `manifest.json` records model ID, Blender version, machine, git commit, seeds, timings | M0 exit gate; experiments E1–E5 are uninterpretable without it |
| `render-cost` | The preview loop stays fast enough to iterate; finals stay affordable; the smoke test passes on both Macs in a few minutes | "Render cost" risk in the project definition; gate fatigue |
| `isolation` | Each stage reads only upstream artifacts and writes its own, so any stage re-runs from its inputs; rendering only through the harness; generation and critique in separate contexts | Re-runnability, knob attribution (H2), no self-grading |
| `schema-coverage` | Every handoff artifact has a JSON Schema in `schemas/` and carries `schema_version` + `production_id`; every shipped knob is enforced by a validator in `validators/` | "No silent defaults"; a knob without enforcement is a dead knob |
| `blender-drift` | Blender version recorded (and pinned before E1); `bpy.data` preferred over context-dependent `bpy.ops`; `bpy` usage concentrated behind seams so an API change has a small blast radius | Model/tool change mid-study shifts every output |

## Method

Run this method as the fan-out in **§Execution model** — an execution *contract*, not a
preference. Steps 1–4 define *what* to evaluate.

### 1. Derive the concern set (attribute × scenario)

Concerns are **derived per run** from the objectives and architecture — not a frozen registry (a
new stage, schema or render engine adds concerns automatically). The catalog below is the
starting map; re-derive each run and add what current docs and code imply. "Empirical source"
names the producer; many are created in M0 or later — until they exist, the row is paper-only.

| Concern (`attribute:scenario`) | Scenario (sharpener) | Empirical source |
|---|---|---|
| `reproducibility:same-seed-rerun` | render the test scene twice, same machine and seed | M0 reproducibility test (frame hashes / tolerance) |
| `reproducibility:cross-machine` | same scene on the M5 Max and the M1 | none — paper |
| `reproducibility:manifest-completeness` | a render whose manifest lacks a field needed to reproduce it | manifest-writer test (created in M0) |
| `reproducibility:unseeded-randomness` | any RNG not derived from `production.yaml` `rng_seed` / recorded seeds | none — paper (static scan candidate) |
| `render-cost:preview-loop` | one preview iteration of a shot | harness timings in `manifest.json` |
| `render-cost:final-frame` | per-frame wall time at the final profile | harness timings in `manifest.json` |
| `render-cost:smoke-budget` | smoke test on both Macs | `scripts/run_tests.sh` timing |
| `isolation:upstream-only-reads` | a stage reading a sibling's or downstream artifact, or hidden state | none — paper |
| `isolation:stage-rerun` | delete a stage's outputs and re-run it from its inputs | none — paper |
| `isolation:render-via-harness` | a render invoked outside `blender/harness/render.py` | static grep for render operators outside the harness |
| `isolation:critic-separation` | a critic running in the generator's context | none — paper (skill procedure review) |
| `schema-coverage:artifact-schemas` | a handoff artifact with no schema or no `schema_version` | schema tests in `tests/` |
| `schema-coverage:knob-enforcement` | a control-surface knob with no validator, or a validator with no sweep test | validator tests; E2 sweep (M3) |
| `blender-drift:version-recorded` | manifest Blender version vs installed version | manifest + `docs/adr/0001-blender-api-baseline.md` (created in M0) |
| `blender-drift:ops-in-background` | `bpy.ops` calls depending on UI context in headless mode | harness smoke render |
| `blender-drift:api-blast-radius` | how many files touch `bpy` directly; is there a seam | none — paper (static count) |

Rows marked "none — paper" are observability-gap candidates (step 4).

### 2. Evaluate the triangle per concern

- **Adequacy** (Architecture ↔ Objectives): would the design-as-intended satisfy the concern, on paper?
- **Conformance** (Code ↔ Architecture): does the code implement the intended design? (matches / divergences / **absences**).
- **Empirical** (Code ↔ Objectives): does the running system exhibit it? Evidence comes from
  render manifests, contact sheets, test results from `scripts/run_tests.sh`, and harness
  timings. A recorded result is valid only if its manifest's git commit, Blender version and
  machine still match what the concern depends on; otherwise it is stale. Tag each piece of
  evidence **verified-now** (you re-ran it — e.g. a preview render through the harness, or the
  test runner) or **provisioned** (trusted from a valid recorded manifest/result). Report the
  tiers distinctly, never blended. **A concern with no valid evidence is a finding, not a pass.**
  Never substitute model guesswork for a measurement. Re-run renders only through the harness.

### 3. Diagnose + route

Route every failing or at-risk concern by which edges held:

| Adequacy | Conformance | Empirical | Diagnosis | Fix |
|---|---|---|---|---|
| holds | fails | fails | **harmful drift** | change the code |
| holds | fails | holds | **benign drift** | propose a doc/ADR update — never silently edit docs |
| fails | — | fails | **inadequacy** | redesign (ADR + run or side quest) |
| holds | holds | fails | **stale assumptions** | revise the assumption the design rests on |

Every finding names its **diagnosis** and its **authoritative artifact** (code / project
definition / ADR / schema). Use sensitivity-point, tradeoff-point and risk-theme vocabulary for
fragile-but-not-failing concerns. For `isolation`, use a mechanism-level rubric — what each stage
can read, what it can write, which context runs the critic — not just scenarios.

### 4. Observability gaps

When a **critical** concern (one guarding a milestone exit gate or experiment validity) has no
valid evidence and no producer exists, emit an **observability-gap** finding proposing the
*minimum* instrumentation to make it evaluable — a manifest field, a hash check, a static scan, a
test. Bounded (critical concerns only), a **proposal only** (route downstream; never wire it), and
consistent with doctrine (results land in manifests or test output; renders stay out of git). A
not-yet-critical gap parks in the escalation ledger (below), re-scored each run and promoted when
its condition crosses.

## Execution model — fan out, verify, synthesize (contract, not a preference)

Collapsing this into one sequential pass discards the anti-anchoring and false-positive
suppression it exists to provide — a defect in execution, not a shortcut. The only permitted
deviation is the small-subject exemption below.

1. **Derive + partition (main context).** Derive the concern set and partition it by attribute.
2. **Find — one specialist subagent per attribute, spawned concurrently** (Agent tool, all in one
   message). Each receives **only its attribute's concerns + rubric** — blindness is intentional.
   Give it the substrate (objectives / architecture / code) and where evidence lives. It runs
   Method steps 2–4 and returns candidate findings (verdict, diagnosis, edges tested, anchor,
   observability-gap candidates). Do not deduplicate across attributes yet.
3. **Verify — one refuter subagent per surviving candidate**, blind to which attribute raised it.
   It tries to kill the finding:
   - Already known — in the escalation ledger or `docs/plans/followups.md`?
   - Empirical basis actually valid, or stale (→ the real finding is "evidence stale")?
   - Actually emergent, or a single-file defect that belongs to `/code-review`? If local →
     **drop it** (the boundary, enforced adversarially).
   - Backed by a **deterministic anchor**, or model guesswork?
   `REFUTED` → dropped. Batch candidates into one refuter call above ~25. The refutation pass runs
   even under the small-subject exemption.
4. **Synthesize (barrier — needs all findings at once).** Hunt **tradeoff points** (a decision
   that is a sensitivity point for ≥2 attributes in opposite directions — e.g. a cheaper preview
   profile that breaks preview/final determinism parity; invisible to any single-attribute agent);
   roll related findings into **risk themes**; dedup; re-score the ledger; write the report.

**Small-subject exemption (objective, not judgment).** Single-agent inline review is permitted
**only** when the subject is a single leaf directory (no subdirectories) under ~400 source lines.
The studio-core default always takes the full fan-out. When taken, record `SINGLE_AGENT_MODE` with
the measured bound. Verify and synthesize still run.

## The report (the only output)

One markdown file at the scope-appropriate path, one entry per finding, consumable by `/bug-fix`:

- **Concern** — `attribute:scenario`.
- **Verdict** — pass / fail / at-risk.
- **Diagnosis** — harmful drift / benign drift / inadequacy / stale assumptions, or **observability gap**.
- **Authoritative artifact** — what to change: code / `docs/project-definition.md` / ADR / schema.
- **Evidence** — edges tested; ≥1 **deterministic, re-checkable anchor** (a test id, a manifest
  path + field, a frame-hash comparison, a static-scan result), never model judgment alone;
  tagged verified-now vs provisioned.
- **Severity + escalation condition** — and whether it becomes a ledger entry.
- **Remediation** — concrete steps, target files/sections, acceptance criteria, blast radius, and
  an autonomy gate (safe for an agent, or needs the user's sign-off — anything touching doctrine,
  glossary or schemas needs an ADR and the user).

End the report with `## Escalation ledger` — every parked not-yet-critical concern with its
promotion condition, carried forward from the previous arch-review report and re-scored.

## Operating rules

1. **Read-only + one report.** No source edits, no git mutations, no commits.
2. **Never silently edit docs.** Benign drift *proposes* a project-definition or ADR update.
3. **Renders only through the harness**, preview profile unless the concern needs final; outputs
   go to a temp directory, never committed.
4. **Full sweep every run.** Evaluate every concern every time; incremental and trend analysis are
   out of scope.
5. **Idempotent** modulo timestamp against the same subject and evidence state.
6. **Filing.** A defect this work finds and leaves unfixed is filed afterwards with the
   `defect-filing` skill (this skill writes only its report) and named `issue #<n>` in the record
   that leaves it.

## How this fits the pipeline

```
/arch-review   →  remediation report (emergent-attribute findings)
/bug-fix       →  executes harmful-drift / inadequacy fixes
/run-process   →  executes larger structural remediations (a redesign is a run or milestone);
                  observability-gap proposals → a run or a utility side quest
```

Distinct from `/code-review` (per-diff local defects) and `/complexity-review` (reader cost). You
sit above them and hand local fixes down; you never compete. Render-time *tuning* is `/optimize`'s
job; you judge whether the structure keeps render cost within objective.
