---
name: run-process
description: >
  Execute a quest run — pre-flight, implementation loop, post-flight, status report and
  carry-forward handoffs. Use for "run 2.3", "start the next run", "next unblocked run",
  "execute run <N.M> in sidequest <slug>", "run pre-flight", "write the status report", or
  /run-process. Runs come from a rollout /generate-rollout wrote; committing is /commit's job.
---

# Skill: Run Execution Process

## Where things live

Every run belongs to a quest. Quests are independent (`type: spike | utility | feature`); there is no main rollout. Conventions: `sidequests/README.md`.

| Concept | Path |
|---|---|
| Rollout (run order + acceptance criteria) | `sidequests/<slug>/<slug>-rollout.md` |
| Status reports | `sidequests/<slug>/status/run<milestone>.<run>status.md` (e.g. `run2.3status.md`) |
| Carry-forward ledger | `sidequests/<slug>/status/carry-forward.md` |
| Fix reports | `sidequests/<slug>/fixes/` (quest-scoped) or `docs/plans/fixes/` (project-wide) — written by `/bug-fix` |
| Quest specs | each path in the rollout's `spec-refs:` (`docs/`, `schemas/`, `styles/`, `docs/adr/`) |
| Project definition | `docs/project-definition.md` — §Milestones (exit gates), §Pipeline, §Control surface, §Repository structure, §Artifact schemas |
| Decisions | `docs/adr/NNNN-slug.md` (index `docs/adr/README.md`) |
| Glossary | `docs/glossary.md` |
| Coding standards | `docs/coding-standards.md` (`STD-###`) — read before writing code |
| Test strategy | `docs/test-strategy.md` |
| Follow-ups | `docs/plans/followups.md` |
| Test runner | `scripts/run_tests.sh` (pytest + ruff + mypy; created in M0) |
| Render harness | `blender/harness/render.py --scene <script> --profile preview\|final --out <dir>` (created in M0) |

Run IDs are `<milestone>.<run>`, where the milestone is a grouping in the quest's rollout (`Milestone 2` → `Run 2.3`). Example: the studio v1 quest's rollout milestones are the project definition's M0–M5, so its runs are `0.1`, `0.2`, … for M0.

## Scope

The user names the quest with **"in sidequest \<slug\>"** (or "in quest \<slug\>"). Otherwise infer it from a `worktree-<slug>` branch, else from the only active quest; if several are active, ask. Never default silently.

**Loading context:**
1. Read the rollout frontmatter and parse `spec-refs:`.
2. Read each `spec-refs:` path as the authoritative spec for this quest.
3. If `spec-refs:` is empty (typical for spikes), fall back to `docs/project-definition.md` and `docs/adr/`.
4. The quest folder holds no specs — never look for them there.

A run that modifies a persistent spec edits it in place at its own path. Changes to `CLAUDE.md`, `docs/glossary.md` or a schema (after M1) need an ADR in the same run.

**Worktree alignment.** If the rollout declares `worktree:`, the run's commits belong on `worktree-<slug>`. Pre-flight warns when you're on another branch; switch into the worktree or confirm with the user.

## Constraints

1. **Document priority:** quest rollout → `docs/project-definition.md` → `docs/adr/` (a later ADR wins over the project definition) → `docs/glossary.md` → `docs/coding-standards.md` → `docs/test-strategy.md`.
2. **Commits go through `/commit`**, and only when the user asks. Never commit from this skill.
3. **Stop and report on conflicting guardrails** — propose 2–3 resolution options; don't pick one.
4. **Stop on missing decisions** — propose the smallest choice set. Nothing is silently defaulted.
5. **Render only through the harness.** Never call render operators ad hoc. Prefer `bpy.data` over `bpy.ops`.
6. **A model never grades its own output.** Reviews and critics run in a separate subagent context from the author.

## Scripts

In `.claude/skills/run-process/scripts/`, run from the repo root:

- `preflight.sh <run-id> --scope <slug>` — non-interactive. FAILs on a dirty tree or a missing quest; WARNs on worktree mismatch, a missing prior-run status report, a re-run, being behind `origin/main`; prints the carry-forward lines routed to this run; and runs the soft integration gate (`soft_gate.py`). Every WARN is yours to put to the user.
- `soft_gate.py --scope <slug>` — lists the quests with `parent: <slug>` that are `status: done` and `integrated: false`.

Post-flight is `scripts/run_tests.sh`. Until M0 creates it, say so in the status report and record the commands you ran instead.

## Carry-forward ledger

Runs accumulate knowledge the next runs need — a contract to reuse, a gotcha, a decision deferred to its first consumer. Status reports capture it, but they're verbose audit records and context is cleared between runs. The ledger is the thin channel that survives a context clear: one file per quest at `sidequests/<slug>/status/carry-forward.md`. `/generate-rollout` seeds it; if absent, the first run with something to hand forward creates it with the header from that skill.

**Routing rule (the anti-bloat mechanism): an item earns a line only if it is addressed to a specific future audience.** Otherwise it stays in the status report's Open Issues.

```
- [<from-run>] -> <targets> | <class> | <one-line conclusion>
```

- `<from-run>` — the run that learned it (`1.2`).
- `<targets>` — comma-separated, no spaces: run IDs (`2.1,2.3`), `surface` (anything touching this surface, including future quests), or `quest` (any later run here).
- `<class>` — `contract` (reuse exactly: a schema field, a harness flag, a module function) · `gotcha` (a trap that costs re-derivation) · `deferred` (punted to its first consumer) · `decision` (settled; don't re-litigate).
- conclusion — one line, ≤~160 chars, stated as fact.

```
- [1.2] -> 1.4,2.1 | contract | render.py takes --seed and writes it to manifest.json "seeds.render"; reuse it, don't add a second flag.
- [1.3] -> surface | gotcha | bpy.ops.object.* fails headless without a context override — build meshes via bpy.data.
- [2.1] -> quest | decision | palette validator compares in linear RGB, not sRGB.
```

**Discipline:** ≤5 lines per run. Conclusions, not narrative. Route as narrowly as is true — `surface`/`quest` load for every run. Durable `surface`/`decision` lines promote to an ADR at quest close; the ledger is transit, not a home.

**Fading.** The top of the file is the **live band** (lines in the grammar above — all pre-flight reads). Below a `<!-- folded: consumed/resolved residues; pre-flight does not read past here -->` marker is the **folded band**: one-line residues starting with `~`, which pre-flight's parser skips. At post-flight, after appending, fold what this run consumed or resolved:

| class | fade when… | residue |
|---|---|---|
| `contract` | the code self-documents it (exported and imported at its consumers) | `~ <thing> lives in <file> (est. 1.2)`, or drop |
| `deferred` | the resolution lands | `~ <theme>: deferred 1.2, landed 2.1` |
| `decision` | always foldable | the choice + one-clause why |
| `gotcha` | **resists** — a faded trap is the worst state | keep the actionable core verbatim |

A gotcha that gains an enforcement mechanism (a test, a validator, a coding standard) becomes one line naming where it landed. Pre-flight's `>15` live-entry warning is the backstop: a fold pass is overdue. If the band is mostly gotchas, ask which a test or validator could hold instead.

## Overseer-dispatched work (optional)

If the prompt carries a `Dispatched by: overseer <loop-file-path>` header (see `/overseer`):

1. **Correct a wrong record at its source.** If this run disproves a claim in another run's status report, a rollout, or an ADR, edit that record in place (or annotate it, per `/bug-fix`'s rule for that kind of record), as well as noting it in Open Issues.
2. **Append the overseer return block** below to the status report.
3. **Every numeric claim carries the command that produced it**, with its output pasted verbatim (redirect to a file and paste the file), or says plainly that it is a summary. The overseer re-runs one of your numbers.
4. **Confirm HEAD contains the base the dispatch names** before reading anything.
5. **Read pre-flight's worktree line against the branch the dispatch names.** If you're on that branch, proceed; if not, stop and put the mismatch to the overseer.
6. **Where this skill would stop for the user, end the turn with the question as the final message** — not an interactive prompt.
7. **Run the checks the changed paths need** and leave the commit to the overseer.

**Do not read the loop file.** The header path is for citation. If the dispatch lacks something you need, ask.

```
### Overseer return block (only if dispatched by an overseer)
- Verdict: GO | NO-GO against this run's acceptance criteria.
- What changed: one line, pointing at the What Changed section.
- Still open: anything found but unresolved, including records corrected outside this run's scope (file:line and what changed).
- Claims and their standing: one line per claim, tagged MEASURED / INFERRED / SPECULATIVE. MEASURED needs the runnable command inline; INFERRED states its premise.
```

## Procedure

### Pre-flight

```
1. bash .claude/skills/run-process/scripts/preflight.sh <N.M> --scope <slug>
   - Read the carry-forward lines it prints before planning.
   - Soft-gate WARN: ask the user whether to continue; don't bypass silently.
2. Read the quest rollout — confirm the run's dependencies are complete (their status reports
   exist and the rollout marks them done). Don't start a blocked or deliberately skipped run.
3. Load context (spec-refs, project-definition sections the run traces to, relevant ADRs,
   coding standards, test strategy).
4. Extract the run's acceptance criteria into a task list.
5. Propose a minimal implementation plan, including `Reuse checked: <helper + file:line>` or
   `none — <reason>`. Wait for the user to confirm before writing code.
```

### Implementation loop

```
1. Implement with TDD in small steps.
   - Look for an existing helper or style module before writing a new one.
   - No unrequested abstractions: no protocol with one implementation, no map keyed by a
     dimension with one entry, no config value that never varies, no scaffolding "for later".
   - Prefer editing an existing file over creating one.
   - Never simplify away input validation, error handling that prevents data loss, schema
     validation of artifacts, or anything the acceptance criteria ask for.
   - Determinism is a property: record seeds in the manifest; test EEVEE renders by exact frame
     hash and Cycles GPU renders by per-pixel tolerance.
   - Update every record the change falsifies — a docstring, comment, schema description, or
     doc sentence asserting the old behaviour is part of the run.
   - A defect found outside the run's scope is not fixed here: file it with /defect-filing and
     list it in Open Issues as `issue #<n>:`; a non-defect Open Issue begins `not a defect: <reason>`.
2. Add or update tests per docs/test-strategy.md. Render smoke tests use the preview profile
   through the harness.
3. Post-flight: scripts/run_tests.sh — the gate. Don't build ad-hoc pytest command lines for a
   gate decision. A failing run is not complete.
4. Mark the run complete in the quest rollout.
5. Write the status report: sidequests/<slug>/status/run<N.M>status.md (template below).
6. Append this run's routed handoffs (≤5) to the carry-forward ledger and fold what it consumed.
   Nothing routed → write nothing.
7. Tell the user the run is ready to commit via /commit. Don't commit.
```

### Status report template

```markdown
# Run <N.M>: <Name> — status

**Quest:** <slug> (<type>)  **Date:** YYYY-MM-DD  **Status:** COMPLETE | PARTIAL | BLOCKED
**Spec trace:** <path:line you actually opened for each spec/ADR/project-definition section this run serves — or `none — <reason>`>

## Acceptance Criteria Checklist
- [x] <criterion from the rollout> — <evidence: test name, command, render path, hash>

## What Changed
- `<path>` — <one line>

## How to Test
<commands: scripts/run_tests.sh, harness invocations, what to look at in the contact sheet>

## Architecture Decisions
<decisions made and why; flag any that are project-level ADR candidates — or "None.">

## Open Issues
- issue #<n>: <defect filed> | not a defect: <reason>

## Carry-forward
<the lines appended to the ledger this run — omit the section when none>

## Test Counts
<passed / failed / skipped from scripts/run_tests.sh; render smoke results; runtime>

## Confidence Report
A. Assumptions made — B. Deviations from existing patterns — C. Thin context (specs you wished
existed) — D. Conflicts found — E. Complexity concentrations. "None." per category when nothing applies.

## Next Unblocked Run
<run ID(s) now unblocked, from the rollout's dependency graph>
```

**The spec trace must cite a `path:line` you actually opened**, or say `none — <reason>`. Both are valid; an unsourced list is not. Status reports filled from memory are the failure this rule exists to stop.

## Anti-patterns

```
// WRONG: implementing without reading the quest rollout first
// The rollout holds dependencies, acceptance criteria and skip decisions.

// WRONG: committing at the end of the run
// Hand off to /commit only when the user asks.

// WRONG: starting a run whose dependencies have no status report
// It is blocked. Pick an unblocked run or ask.

// WRONG: calling bpy.ops.render.render() from a test or scene script
// Render through blender/harness/render.py so the manifest and profiles apply.

// WRONG: writing the status report to docs/plans/status/ or naming it run(2.3)status.md
// It is sidequests/<slug>/status/run2.3status.md.

// WRONG: looking for <slug>-spec.md inside the quest folder
// Specs come from spec-refs:. Empty spec-refs → docs/project-definition.md + docs/adr/.

// WRONG: ignoring the soft-gate warning
// Apply the closed quest's changes and flip integrated: true, or get the user's explicit go-ahead.

// WRONG: having the authoring context review its own stage skill or critic output
// Reviews run in a separate subagent (/code-review, /arch-review, …).
```

## Checklist

- [ ] `preflight.sh <N.M> --scope <slug>` ran; every WARN put to the user or resolved
- [ ] Carry-forward lines routed to this run read before planning
- [ ] Dependencies and skip decisions checked in the rollout
- [ ] Acceptance criteria extracted; plan with `Reuse checked:` confirmed before coding
- [ ] Renders only through the harness; seeds recorded
- [ ] `scripts/run_tests.sh` passes
- [ ] Rollout marked complete
- [ ] Status report written at `sidequests/<slug>/status/run<N.M>status.md` with a sourced spec trace
- [ ] Routed handoffs appended to the ledger (≤5) and consumed lines folded — or none
- [ ] No commits without the user's request; commits go through `/commit`
- [ ] If overseer-dispatched: return block appended, with every out-of-scope correction cited as `file:line` plus the text written, or `none — nothing outside this run's scope was disproved`
