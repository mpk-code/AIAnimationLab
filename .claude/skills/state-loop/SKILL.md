---
name: state-loop
description: >
  State Distillation for open-ended sessions (investigation, design, debugging marathons — e.g.
  chasing a non-reproducible render, a Blender API context error, a style that won't survive
  into frames): maintains a Working Memory File of hypotheses, rejected paths, established
  constraints and open questions so context can be pruned without losing the thread; the
  snapshot sub-action does one-shot session handoff. Use for /state-loop create|complete|resume|snapshot,
  "start a loop on X", "distill what we've learned so far", "we lost context, reload the loop",
  "resume the loop from yesterday", "checkpoint this session", "hand this off to another
  session", or wanting to "think through" or "explore" a problem with you. Note: `/loop <N><unit> ...`
  is the cron loop skill, not this one.
---

# Skill: State Loop (State Distillation for Interactive Sessions)

## Why this skill exists

Long investigative sessions — debugging a flaky render, probing the Blender API, designing a
validator, hunting a slow preview loop — accumulate transient context: tool output, log snippets,
rejected approaches, half-formed code. The valuable artifact is *not* the transcript. It is the
**mental model** built together: what is now believed, what was ruled out and why, what
constraints were discovered, what was agreed, and what is still uncertain.

Summaries keep the prose and lose the deductive leaps; auto-compaction keeps recency, not insight.
This skill replaces both with a curated working-memory file that survives context resets.

The loop file is **not a log**. It is a model of the current understanding, written so a colleague
who was never in the room could pick up the investigation tomorrow.

## Behavioral stance during a loop

- **Critical, not sycophantic.** Surface dissent. If a proposed direction looks weak, say so and
  offer 2–3 alternatives with tradeoffs. Honestly captured disagreements are the file's value.
- **Goal-anchored.** The frontmatter `goal` is the lodestar. If the goal itself drifts, that is a
  pivot — make it explicit.
- **Evidence-driven.** Confidence moves only on new evidence (a test result, a code reading, a
  render hash, a measurement, an authoritative source) — never on rhetoric.
- **Iterative.** Capture what is settled, mark what is provisional, name what is unknown.
- **Innovative collaborator.** Offer options the user hasn't considered; broaden the search, then
  help narrow it.

## Sub-actions

| User intent | Sub-action |
|---|---|
| `/state-loop create <name> [in sidequest <slug>] [to <description>]` or `/loop create ...` | **Create** |
| `/state-loop snapshot [name] [in sidequest <slug>]`, or any reactive "checkpoint / hand off / save state" request with no loop open | **Snapshot** |
| `/state-loop complete` or `/loop complete` (in an active loop) | **Complete** |
| `/state-loop resume <name> [in sidequest <slug>]` or `/loop resume ...` | **Resume** |

If the intent is ambiguous (e.g. `/loop foo` with no verb), ask which sub-action. If the user types
`/loop <duration> <command>` (e.g. `/loop 5m /foo`), that is the cron-style loop skill — defer to it.

---

## Sub-action: Create

### Storage location

- **Project scope (`project`):** `docs/plans/loops/<name>.md`
- **Sidequest scope:** `sidequests/<slug>/<name>.md` — verify the sidequest exists; if not, stop
  and ask whether to open one.

If the file already exists, do not overwrite. Ask whether the user meant **resume**.

**If the loop's purpose is orchestration rather than investigation** — a long-lived thread that
dispatches `/bug-fix`, `/run-process` or `/code-review` work into separate windows whose context is
cleared between cycles — use `.claude/skills/overseer/assets/overseer-loop-template.md` instead, add
`pattern: overseer` to the frontmatter, and defer to the `overseer` skill. The signal is the
interview: if the user has no falsifiable claims to track and instead describes sequencing several
windows' work, ask whether this is an overseer loop before writing the generic body.

### Interview the user

Creating a loop is a deliberate act. Ask one question at a time; don't re-ask what the conversation
already made obvious.

1. **Goal.** "What does success look like? When would we close it?" One sentence the user would
   still recognize in two weeks.
2. **Outcomes.** "What artifacts or decisions should exist when this loop closes?" (an ADR, a
   measurement, a fix, a recommendation to the parent quest)
3. **Starting lines of investigation.** Capture each as a candidate hypothesis with an initial
   confidence.
4. **Established facts coming in.** "What do we already know that we shouldn't re-litigate?" These
   become initial **Established Constraints**.
5. **Out of scope.** Prevents drift.
6. **Stop conditions.** "What would make us abandon this loop, not just close it?" (e.g. "if it's a
   Blender bug, we file it upstream and stop")

**Owner (auto-stamp, not a question).** Set `owner:` to `git config user.name` unless the user says
the loop belongs to someone else.

Propose the rendered frontmatter and section skeleton back to the user ("anything to add or
correct?"), then write.

### Loop file structure

The literal template is `assets/loop-template.md`; copy it. What each section is for:

- **Goal** — one paragraph: what success looks like and why it matters now.
- **Out of scope** — explicit guardrails.
- **Established Constraints** (`C<n>`) — load-bearing facts, each citing evidence (file:line,
  measurement, authoritative source). Not up for debate without explicit reopening.
- **Current Hypotheses** (`H<n>`) — the live frontier. Each has a confidence, a trend, why we
  believe it, what would raise confidence, what would falsify it, and a last-update line. At ~95%
  it migrates to Constraints; at ~5% to Rejected Paths.
- **Rejected Paths** (`R<n>`) — approach, *rejected because*, *would reopen if*. The reason field
  is what stops the rerun.
- **Human-AI Consensus** (`D<n>`) — decisions both parties signed off on. A constraint is a fact
  about the world; a consensus is a choice about how to proceed.
- **Open Questions** (`Q<n>`) — known unknowns, each answerable in principle, with what it is
  needed for and how to answer it.
- **Pivot Log** — timestamped changes of direction (*from / to / why*). The narrative spine; read
  it first on resume.
- **Scratch (volatile)** — working notes since the last distillation. Wiped at every distillation;
  non-empty on resume means the last session ended unclean.

### After writing

Confirm: "Loop `<name>` opened at `<path>`. Goal: <goal>. Starting hypotheses: H1, H2, …. I'll
distill into this file as we go."

---

## Sub-action: Snapshot

Create's reactive twin. **Create interviews because the investigation hasn't happened yet; Snapshot
reads the conversation that already happened** and distills it into the same loop file — no
interview. The output is a normal, resumable loop file.

1. **Distill the conversation so far** using the Signal-vs-noise rules below. Infer Goal,
   Established Constraints (with evidence pointers), Current Hypotheses (confidence + next step),
   Rejected Paths (with reasons), Open Questions, and the Pivot Log.
2. **Storage** — same as Create. If no name is given, propose one from the goal. Never overwrite an
   existing file; ask whether the user meant **resume**.
3. **Frontmatter** — `status: active`; `owner:` auto-stamped; `opened:` today; `last-distilled:` now.
4. **Propose, then write.** Say explicitly that the goal and constraints were *inferred*: "I
   distilled the session into loop `<name>` — check the Goal and Established Constraints; anything
   I misread?"

From then on the loop is live. For a one-time, file-less compaction of the current window, use the
`/compact` recipe in the appendix instead.

---

## Sub-action: Complete

Closing a loop is when its value gets harvested — produce the deliverables, don't just flip status.

1. **Final distillation.** Sweep the conversation since the last distillation; promote or discard
   everything in Scratch, then wipe it.
2. **Resolve every hypothesis** to one of: Established Constraint (≥ ~95%, solid evidence), Rejected
   Path (≤ ~5% or falsified), or an Open Question the loop did not resolve (say so honestly).
3. **Write the Conclusion section** at the bottom of the file:

   ```markdown
   ## Conclusion
   ### What we now believe
   ### What we decided          (each with rationale)
   ### What we ruled out        (each with reason)
   ### What we did not resolve   (each with who/when should pick it up)
   ### Recommended next actions
   ```

4. **Propagate to persistent artifacts.** Propose (never silently apply) whichever apply:
   - **ADR** under `docs/adr/` (`NNNN-slug.md` from `docs/adr/0000-template.md`, indexed in
     `docs/adr/README.md`) — for any decision that changes doctrine, a glossary term, a schema, or
     refines `docs/project-definition.md`.
   - **Project definition** — a clarified hypothesis, scope line, pipeline detail or exit gate in
     `docs/project-definition.md` (via ADR where the project's rules require one).
   - **Glossary** — a term sharpened or added in `docs/glossary.md` (needs an ADR).
   - **Sidequest deliverable** — if scoped to a sidequest, append findings to its deliverable
     section.
   - **Code change** — confirm a fix landed, or propose opening a `/bug-fix` or run.
   - **Deferred items** — anything parked with a revisit trigger goes to `docs/plans/followups.md`.

   Each propagation is a separate, reviewable change.
5. **Flip frontmatter** `status: complete`, set `closed: <YYYY-MM-DD>`.
6. **Status report.** Goal, conclusion bullets, what was propagated, what is still open.

If most hypotheses are unresolved and the user wants to stop, set `status: abandoned` and write the
conclusion honestly, including *why*. An honest abandoned loop beats a fake-completed one.

---

## Sub-action: Resume

Invoked after a context wipe, a restart, or the next day. The point is to **reconstruct the mental
model**, not skim the file. Read in this order:

1. **Frontmatter** — scope, goal, status, last-distilled. Warn if `turns-since-distill` > 30 or
   `last-distilled` is over 7 days old. **If the frontmatter carries `pattern: overseer`, read the
   `overseer` skill before continuing** — Current Hypotheses is deliberately unused there, and the
   `Read-first list` pointers must be opened as part of the resume.
2. **Goal + Out of scope** — state them back verbatim.
3. **Pivot Log** — oldest to newest. The spine.
4. **Established Constraints** — treat as true.
5. **Human-AI Consensus** — honor these.
6. **Current Hypotheses** — note confidence and trend; the frontier is here.
7. **Rejected Paths** — skim, to recognize them if they recur.
8. **Open Questions** — these point at the next move.
9. **Scratch** — if non-empty, the last session ended unclean. Promote what's worth keeping;
   discard the rest; don't silently absorb it.

Then emit a reorientation block:

```
Reorienting on loop `<name>` (scope: <scope>, opened <date>, last distilled <date>).

Goal: <goal>

Where we left off:
  - <most recent pivot, one sentence>
  - <highest-confidence open hypothesis>
  - <next concrete move from Open Questions or hypothesis next-steps>

Established (won't re-litigate): C1 ... Cn
Rejected (won't revisit unless): R1 ... Rn

Ready to continue. Anything changed since last session that I should know?
```

The trailing question matters: out-of-band events (a Blender update, a render on the other Mac, a
note from a rater) are invisible to the file.

---

## Distillation: when and what to write

Between create and complete the file must be **maintained**.

### Triggers

Distill when: consensus is reached; a hypothesis's confidence shifts materially (≥ ~20 points); a
hypothesis is rejected (move it, don't delete it); a new constraint is discovered; a pivot happens
(append immediately — pivots are easiest to lose); an open question crystallizes; a
sub-investigation ends; context is getting heavy; or the user asks for a snapshot. Don't distill
every turn — over-writing erodes signal.

### Signal vs. noise

**Persist:** conclusions with confidence; pivots and their triggers; discovered constraints with
evidence pointers; decisions and their reasoning; falsifying evidence; disagreements and how they
resolved; pointers (file:line, commit, manifest path) — never pasted blobs.

**Let die with the context:** raw tool output, logs, full file contents, exploratory code (if it
mattered, it was committed), step-by-step narration, restatements, hedging, failed invocations and
retries, deliberation about which tool to call.

The test: **would a colleague who was never in the room need this to make the next decision?**

### Confidence scale

Coarse (`low` ≤30% / `medium` 30–70% / `high` ≥70%) for early hunches; numeric `0–100%` once evidence
accumulates. Always pair with a **trend** (↑ ↓ →) and a **last-update date**. A hypothesis that
hasn't moved in two weeks is either converged or stuck.

If a confidence change is driven by user sentiment without new evidence, flag it: "Confidence on H2
raised 40 → 60% on your reasoning, but we have no new evidence — recommend we run X to validate."

### Pruning

After a distillation, raw outputs, snippets, intermediate reasoning and superseded hypothesis states
fall out of context; everything in Signal is in the file; the current turn's live details (the next
experiment, the file being edited) stay in conversation only. Be willing to lose context on
purpose — the loop file is the safety net.

---

## Capturing intent and deductive leaps

- **Always write the *why*.** "Rejected Cycles for the reproducibility test" is useless. "Rejected
  Cycles for the exact-hash test because two GPU renders of the same seed differed at 1/255 per
  pixel — see `<manifest path>`" is recoverable.
- **Name the inflection.** "This is a `bpy.ops` context problem, not a driver problem" *is* the
  artifact — write it as a Pivot with its trigger.
- **Capture the dissent.** If agent and user disagreed and one was convinced, record both positions
  and what convinced the loser.
- **Joint voice.** "We concluded…", not "the user said… the agent said…".
- **Survive translation.** If an entry needs the transcript to make sense, it is incomplete.

---

## Interaction with other skills

- **`sidequest`** — a sidequest-scoped loop lives in that sidequest's folder; closing it usually
  writes to the sidequest's deliverable.
- **`run-process` / `bug-fix`** — directive skills with acceptance criteria; loops are
  non-directive. If a conclusion implies a run or a fix, propose opening one — don't start coding
  outside the loop's scope. A loop drifting into building the thing means exploration is done.
- **`grill`** — a grill session can run inside a loop; concepts it resolves append to the loop's
  Established Constraints.
- **`defect-filing`** — a defect the loop finds and leaves unfixed is filed with that skill and
  named `issue #<n>` in the loop file; a hypothesis not yet shown to be a defect is not filed.
- **`commit`** — loops do not commit. Loop file edits are committable and should ride with the
  related work where reasonable.
- **`overseer`** — an orchestration loop runs on this skill's create/resume/snapshot mechanics with
  the overseer template; `pattern: overseer` in the frontmatter marks it and changes Resume step 1.
  Use it when the content is sequencing, dispatch and commit decisions rather than hypotheses.
- **The built-in `loop` skill (cron-style intervals)** — unrelated; defer to it for
  `/loop <duration> <command>`.

---

## Anti-patterns

- **Writing a transcript.** If the file grows linearly with the conversation, you're doing it wrong.
- **Hoarding hypotheses.** Stale hypotheses need new evidence or a move to Constraints, Rejected or
  Open Questions.
- **Polite confidence inflation.** Raising confidence because the user seems committed corrupts the
  file. Push back.
- **Silent compaction.** If you remove content when rewriting the file, say so in the next message.
- **Resuming without reading.** Read the whole file before the first substantive turn.
- **Letting Scratch grow.** Three turns of growth with nothing promoted means distill now.

---

## Quick reference

| Situation | Action |
|---|---|
| Starting an open-ended investigation | `/state-loop create <name>` |
| Deep in a session, need a handoff file (no loop open) | `/state-loop snapshot [name]` |
| Hit a real conclusion | Distill — promote to the right section |
| Conversation getting heavy | Pre-emptive distill, then willingly drop context |
| Context just got wiped | `/state-loop resume <name>`; read the whole file first |
| Reached the goal (or decided not to) | `/state-loop complete`; propose ADR / doc updates |
| User typed `/loop 5m /foo` | Not this skill — cron-style loop skill |

---

## Appendix: in-place `/compact`

For the lighter, file-less alternative — compress the live window and keep working — drive Claude
Code's `/compact` with an asymmetric-compression prompt:

```
/compact "Distill into: 1) DEAD ENDS — each abandoned path + one-sentence reason, no implementation details. 2) FIXED GROUND — completed work as architectural facts. 3) OPEN QUESTIONS — unresolved uncertainties affecting current direction. 4) CURRENT VECTOR — hypothesis, next step, success criteria. 5) GUARDRAILS — what not to revisit and why. Drop all raw logs and intermediate code."
```

`/compact` only reshapes the current window (nothing survives a wipe); `snapshot` writes the durable
file. If in doubt, `snapshot`.
