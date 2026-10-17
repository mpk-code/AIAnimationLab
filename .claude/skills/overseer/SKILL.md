---
name: overseer
description: >
  Role-standard for running a long-lived orchestration thread alongside separate implementation
  windows whose context gets cleared between cycles (workers that invoke /bug-fix, /run-process,
  /code-review, or a directed measurement task such as a render-timing or reproducibility check).
  The overseer holds sequencing, cross-cycle decisions and commit authority so a worker window can
  be as narrow and disposable as its task. Use whenever the user says "let's resume the overseer",
  "resume the loop for <quest or milestone>", "dispatch a worker window", "run this as
  overseer/worker", asks to set up or continue a pattern where one thread orchestrates several
  others, or is driving a quest (e.g. a milestone of a quest's rollout) that spans more sessions than one context
  window holds. Also use when checking whether an overseer loop file has drifted from this
  template, or deciding what belongs in the loop file versus a rollout, fix doc or status doc.
---

# Overseer

An overseer is a role, not a workflow step: a long-lived thread that holds the sequencing and
decision context for a body of work while implementation happens in separate windows that get
`/clear`ed between cycles. Clearing the overseer's own context should cost nothing — everything it
needs to resume is in a worker's committed output or in the loop file this skill shapes.

## Composition

This skill runs on top of `state-loop`. Create the loop file with `/state-loop create <name>`
(`project` scope: `docs/plans/loops/<name>.md`; `sidequest:<slug>` scope: `sidequests/<slug>/<name>.md`), replace
the generic body with `assets/overseer-loop-template.md`, and add `pattern: overseer` to the
frontmatter — that key makes `/state-loop resume` load this skill. `/state-loop resume` and
`/state-loop snapshot` are used unchanged. Mark state-loop's **Current Hypotheses** section
explicitly unused rather than deleting it, so a reader knows the omission was a choice.

## What an overseer is actually for

**An overseer's value is combining artifacts no single worker window could see at once, and
catching a record's claim about itself before it gets believed — not its own top-down scope or
priority judgment.** A worker with a narrow, well-posed task and fresh evidence will out-perform
the overseer's reasoning about that evidence, because the overseer works from a compressed history
and the worker from the thing itself. Treat a scheduling or scoping call made without a worker's
measurement behind it as provisional; the loop file makes it cheap to revise.

**Give a worker the observation, not the conclusion you expect.** Every dispatch distinguishes
"here is what I measured" from "here is what I think it means", and lets the worker re-derive the
second half.

## Inward-facing verification

It is natural to demand rigor from workers while applying none to your own dispatch drafts. That
asymmetry is the failure mode. Before sending a dispatch or writing a claim into the loop file,
label it:

- **MEASURED** — cite the exact command, read or artifact that produced it.
- **INFERRED** — a conclusion from a measured premise. State the premise separately; a verified
  premise does not verify the inference.
- **SPECULATIVE** — a guess with no evidence yet. Fine to write down, never fine to hand a worker
  as fact.

**A zero-hit search is not evidence of absence** without a **pattern control** (a synthetic
positive must hit) and a **path control** (something known present at the same path must hit). A
control controls only the command it shares a pattern, flags and revision with.

**A hit needs checking too — the more common failure.** A search that matched something *next to*
the target returns an answer, so no control fires. **A MEASURED claim that a document says X at
line N quotes the text the search matched**, not only the command. State a count's unit (lines,
occurrences, files) and the flag that produced it — `grep -c` counts matching lines.

**Check the pipeline before believing the number.** `| head`, `-m`, a viewer's row cap or a tool's
default result limit turn a sample into a figure indistinguishable from a census. Count with
`wc -l` or `grep -c` on the unpiped result. The tell is a round number.

- **A superlative is a claim.** "Most", "only", "sole", "first", "largest" — re-read the derivation
  as you write the word, or write the list instead.
- **When you correct a sentence, verify every clause in it.** A freshly corrected sentence reads as
  checked, which is why the clause you didn't look at survives. The unit of review is the sentence,
  not the error.

### Verify the instrument, not only the answer

The labels catch an unverified *claim*; they don't catch a **verified claim produced by a broken
tool**, which returns a plausible number. **Make an instrument state its own scope** — print the
iteration count, file list, match count and control so a vacuous measurement announces itself.

Known false-zero mechanisms: a hard-wrapped phrase breaks a multi-word `grep`; `\b` silently matches
nothing in `git grep -E` (use `-w` on whole identifiers or `git grep -P`); a pattern matching only
one of two conventions in a file; a relative path resolved from the wrong base; zsh not word-splitting
`$(...)`, so `for f in $(...)` runs once on one giant argument; `find -newermt` erroring on macOS;
a keyword count reported as though it answered a routing question.

Corollaries: **before reporting a variance from someone else's measurement, re-read their stated
method**; and **an identifier copied out of a spec or ADR is unverified until grepped** — an ADR's
revision log can disagree with its Decision text, and the later text wins.

**The forward half: before spending machine time, state what effect size the design can resolve,
and against which spread.** A render-timing comparison whose two arms use different instruments, or
whose run-to-run spread exceeds the effect, cannot answer its question — and there is no number yet
to look wrong. A design whose resolvable effect size is unstated is not yet a measurement.

**Figures** (render wall time, preview-loop time, test-suite time, frame-hash agreement):

1. A figure written into a durable artifact carries its instrument and its `n`.
2. A total and its breakdown come from one command.
3. A measurement taken under worse conditions (another render running, the other Mac, a busy GPU)
   cannot attribute one taken under better conditions. When attribution fails, record the figure
   with the failed attribution beside it.

A deferred figure carries its recompute command. **Don't write environment state into a dispatch**
("the tree is dirty", "you're the only window") — state the arrangement and let the worker measure.

## The loop file template

**Non-duplication is the organizing rule.** The loop file holds *only* state with no other home.
Anything with an owning artifact — the rollout's Resume state, a fix doc's RCA, a status doc's
measurement, an ADR's decision, a `manifest.json`, `git log` — is linked, never copied. A copy
drifts, and the drift breaks resumes. **This applies within the file too:** a summary line beside
the table it summarizes goes stale fastest. Delete the summary or point it at the table.

**The literal template is `assets/overseer-loop-template.md`.** Copy it; the prose here says why
each section exists.

Sections shared with state-loop's template (`.claude/skills/state-loop/assets/loop-template.md`)
keep their meaning but hold pattern-level content:

- **Established Constraints** — facts about *the pattern itself* (who commits, how many
  write-capable workers run at once, what a worker is trusted to do), each with a cited pointer.
  A constraint without one is an opinion.
- **Human-AI Consensus** — choices about the pattern agreed with the user.
- **Rejected Paths, Open Questions, Pivot Log, Scratch** — generic meaning. Pivot Log is used
  heavily: a reversed scoping call is this pattern's most common product.

Sections state-loop lacks:

- **The non-duplication rule** — restated as the file's first section, because the temptation to
  paste a summary arrives while editing.
- **Read-first list** — ordered paths to open on resume (the rollout's Resume state, active fix
  docs, `git log`, the latest run status). Paths only, never summaries.
- **In flight** — worker windows running now. Drains at each cycle boundary.
- **Decided-but-not-yet-in-a-doc** — a decision made in conversation not yet in its owning
  artifact. Drains **the same session**; it is one `/clear` from being lost.
- **Homeless follow-ons** — follow-ons with no owning doc and no trigger. Drains when an owner
  exists (often `docs/plans/followups.md`).
- **Pattern observations** — a dated, append-only log of defect classes in *how the pattern is
  executed*, so a mistake is recognizable the second time.
- **Standing grants (agentic mode)** — empty in a manual-mode loop.

**Empty is the target for In flight and Decided-but-not-yet-in-a-doc.** Check both at every cycle
boundary; a section that has never been empty is being appended to, not drained. Measure section
sizes rather than trusting the rule:

```bash
awk '/^## /{if(h)printf "%6d  %s\n", n, h; h=$0; n=0} {n++} END{printf "%6d  %s\n", n, h}' <loop-file>
```

A measurement of a file an active window owns is true only as of the moment it ran.

## Bounding the distillation chain: the one-prior-link rule

The `last-distilled` frontmatter field accretes on every resume. **Each distillation keeps exactly
one prior-link clause and drops everything older.** Before dropping a clause, name the artifact that
now owns its content; if none does, it belongs in a section above, not discarded. Renaming a dropped
clause into a `superseded-<date>:` key is compliance theatre — write it into its owning artifact.

This rule bounds only the frontmatter. **Pattern observations** is where a long loop grows; prune it
by *promotion*: when an observation is enforced somewhere (a skill, a test, a validator, `CLAUDE.md`
via ADR), replace it with one line naming where it landed. An observation with nowhere to go stays in
full.

## Dispatch modes

- **Manual mode — default and fallback.** The user carries each dispatch prompt to a worker window
  and carries its return back. Everything outside `## Agentic dispatch mode` applies.
- **Agentic mode — opt-in per loop.** The overseer runs each worker itself as a background subagent
  in a worktree it manages. Needs a grant in force in the loop file's `## Standing grants (agentic
  mode)`, and Claude Code.

Any act no grant in force covers is done in manual mode. `## Rules for both dispatch modes` holds
in both.

## Dispatching worker windows

A worker should never have to guess it is part of an orchestrated pattern. Give it a specific,
evidence-backed task, and mark the dispatch with:

```
Dispatched by: overseer <path-to-loop-file>
```

`/bug-fix`, `/run-process` and `/code-review` recognize this header: a worker that finds a wrong
claim outside its scope corrects it at the source (rewrite or dated annotation), and its completion
output ends with a structured return block. Name both behaviors in the dispatch — restating the
rule here doesn't enforce it.

**The header path is a citation, not a reading assignment; the prompt is self-contained.** A worker
that opens the loop file inherits the compressed framing this skill warns against and burns its
budget on someone else's conclusions. Everything the worker needs — the observation, paths,
acceptance criteria — goes in the prompt. "It's in the loop file" is not a dispatch.

**Name an issue as `issue #<n>`, never `/bug-fix #<n>`**, in dispatches and commit subjects. GitHub
closes an issue on `close(s|d)`, `fix(es|ed)` or `resolve(s|d)` followed by `#<n>`, even after a
`/`, so the dispatch commit would close the issue before the fix exists. The issue closes only
through the fix commit `commit` writes (`Closes #<n>`) or by hand.

A worker returning NO-GO, or refusing to paper over a failed acceptance criterion, is the pattern
succeeding. The decision belongs to the overseer thread. Don't ask a worker to soften it.

## Sweep each worker's return before acting on it

Worker-side rules are instructions; the overseer's sweep is the half with teeth. When a worker
returns, before its output informs any decision:

0. **Read the diff of the write set** — `git diff` / `git show` over every touched file, not the
   return block's description. The checks below test *claims*, and a claim can only be wrong about
   what it mentions; an undeclared change (a rename beyond the one asked for, a file outside the
   fence) appears only in the diff.
1. **Is the structured return block there?** If not, the header was missed; the sweep is on you and
   the next dispatch restates the header.
2. **Did the report disprove a claim in a record the worker doesn't own?** Read its findings against
   the rollout's Resume state and your own dispatch prompt.
3. **What did the report hand back to you?** Write anything a return assigns you into
   `Decided here but not yet in a doc`. A defect found outside the worker's scope comes back as a
   drafted filing: file it with `defect-filing` (confirm with the user before creating the issue),
   then name it in the record that left it as `issue #<n>:` — or `not a defect: <reason>`.
4. **Re-run one number** a scheduling decision depends on, using the command the return cites. A
   tally inside a code fence is not proof it was computed. This verifies a number, not the work — it
   never substitutes for step 0.
5. **Check your dispatch prompt against what came back.** A contradicted premise was INFERRED or
   SPECULATIVE sent as MEASURED — record it in Pattern observations.

Then commit the worker's output or send it back.

**A `/bug-fix` return can carry a write that is yours:** the fix-summary comment for the GitHub
issue. The worker drafts it in the return block; you post it. A draft left in a return block is
written nowhere.

## Rules for both dispatch modes

- **Every push has a human in the loop.** A push to a remote, on any branch, is the user's decision.
  No grant covers it.
- **A red in a fresh worktree is an environment claim first.** Initialise the worktree's gitignored
  environment (Python virtualenv, Git LFS objects) and re-run before attributing the red to the
  change.
- **A background gate's verdict comes from its own exit file:**
  `scripts/run_tests.sh > log 2>&1; echo $? > exit`, then read `exit`. A completion notification
  reports the invocation's last command, not the gate.
- **A return block is not a record.** When a later step depends on a worker's findings, copy them
  verbatim into committed text, or cite them as "the worker's return, not committed".
- **A rule you derived from the user's words is labelled INFERRED** — inside the dispatch, even after
  the user confirms the set. Confirming a proposal is not checking each consequence.
- **Read the working tree before each commit:** `git status --short` and `git diff --cached` for work
  that is not yours.
- **Every dispatch names its base and the worker's check** — the branch, the base HEAD must contain,
  and a command that confirms it (e.g. "`git log --oneline -1 -- <dispatch path>` prints a commit"),
  never a SHA.

### The gate

The commit gate is the overseer's: `scripts/run_tests.sh` (pytest + ruff + mypy), run **bare** — no
pipe, no redirect, nothing after it — so the exit code you read is the gate's. Never read a gate
through `| tail` / `| grep` or a trailing `; echo`. For a change touching render code (`blender/`),
confirm the run included the render smoke tests in `tests/` (preview profile through the harness). Run the gate over
the union of what you are committing, after the last edit and the last worker's return; a worker's
targeted green is never the gate. Run it before any push as well. Record in the commit body the gate
you ran and its exit code.

## Scaling to more than one worker

Disjoint write paths are not enough: two windows can corrupt each other's *measurements* — a
before/after render-timing reading taken while another window renders or lands changes reads as a
defect in the measurer's work. Name which measurements are sensitive to a concurrent write or a
concurrent render.

**Default: at most one write-capable worker per shared worktree;** read-only workers (a code review,
a unit-test audit) may overlap freely. Parallel worktrees — one write-capable worker each — beat
relaxing that, but they share the stash stack, the process table and the machine's GPU.

### Parallel workers share four resources — and the gate is the overseer's

1. **The gate.** A full run covers the *union* of every window's uncommitted work; its green says
   nothing about one change, and a red belongs to nobody. Concurrent runs contend for caches and the
   GPU. **Direct each parallel worker to run only checks scoped to its change** (the tests it touched,
   ruff/mypy on its files) and state that the gate is the overseer's, run once on the union at the
   commit point. A worker that believes its change can't be verified without the full gate **stops
   and reports** — that is a scheduling problem.
2. **The index.** `git commit` takes the whole index; a worker's staged paths are absorbed by your
   next commit. **Check `git diff --cached` before every commit while any window is live.**
3. **The process table.** **Never instruct a worker to kill by pattern** (`pkill -f`, e.g. on
   `Blender`) — it reaches the other window's renders. A window stops only processes it started, by
   pid.
4. **The stash stack.** `refs/stash` is shared by every worktree. **Tell every worker never to run a
   bare `git stash`;** read a "before" state with `git show HEAD:<path>`, and use `git stash create`
   (writes no ref) for a snapshot a tool must consume.

**Diff a second fence against the first.** Before sending prompt N+1 while window N is open, list
window N's files from *its* prompt and diff the two lists — a contradiction becomes visible to you,
and an item neither fence covers shows up as a gap instead of vanishing.

**Don't write "you are the only window open" into a dispatch.** State the arrangement ("another
window is live; targeted checks only").

## Commit and clear discipline

Workers report and leave work uncommitted. In manual mode, commit authority stays with the overseer
behind the `commit` skill's approval gate; in agentic mode, a commit-and-merge grant in force replaces
per-commit approval.

**Commit the overseer's own artifacts before dispatching.** The loop file edit and the dispatch
prompt are the overseer's write set; left dirty they trip `/run-process`'s clean-tree pre-flight. A
committed prompt is also citable, and a prompt that names no tree state can't go stale. The cost is
one extra commit per cycle — correct, since the dispatch is a record of what was asked whatever the
verdict.

**Rewrite a Run's Status headline in the commit that records its merge** (or the user's ruling that
resolves it). Before committing, grep the quest's rollout and `sidequests/<slug>/status/` files for
the Run's identifier and correct every hit still stating the pre-merge state. The same applies to any
item resolved outside a Run (a merged non-Run change, a ruling, a deleted branch): grep for each name
the item goes by, and correct or close every live line asserting the ended state.

**Clear the overseer's context only after committing.** `commit` recalls intent from the live
session; a cleared session knows *what* changed but not *why*.

## Agentic dispatch mode (Claude Code only)

The overseer runs each worker as a background subagent in a worktree it manages. Opt-in per loop;
use it only while `## Standing grants (agentic mode)` records a grant in force, and do every act no
grant covers in manual mode.

**No gate approval, commit or merge without a recorded grant in force.** Check before each such act —
it is a precondition of the act, not of the loop. A grant records who agreed and the date; the
authority (`gate delegation`, `commit-and-merge`, or both); its scope; when it ends; what always
escalates; and what stays the user's, which always includes every push.

**Before creating a worktree or dispatching a background worker, read
`references/agentic-dispatch-mode.md`** — the dispatch checklist, what a grant allows, worktree
creation, relaying questions, and the lifecycle from worktree to push.

## Anti-patterns

```
// WRONG: a fact in a dispatch prompt with no MEASURED / INFERRED / SPECULATIVE label
// WRONG: a zero-hit grep as proof of absence — run pattern and path controls first
// WRONG: reporting what a search found without quoting the matched text
// WRONG: parking a dropped distillation clause under a "superseded-<date>:" key
// WRONG: copying a rollout's Resume state, a fix doc's RCA or a manifest's numbers into the loop file
// WRONG: letting "Decided here but not yet in a doc" sit for days
// WRONG: dispatching a task whose context is "in the loop file"
// WRONG: deleting a Pattern observations entry because the file is long — prune by promotion
// WRONG: "the sole blocker", "the only Run" from memory of an earlier derivation
// WRONG: fixing the stale number in a sentence and shipping the rest of the sentence unchecked
// WRONG: scheduling a render-timing comparison without stating the effect size it can resolve
// WRONG: committing a worker's write set after checking its claims but not reading its diff
// WRONG: asking a worker to soften a NO-GO or route around a failed acceptance criterion
```
