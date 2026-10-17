---
name: <loop-name>
scope: project | sidequest:<slug>
pattern: overseer                 # makes `/state-loop resume` load the overseer skill
goal: Hold the orchestration thread for <quest> — sequencing, cross-cycle decisions and commit
  authority — so context here can be cleared without losing the ability to orchestrate.
opened: <YYYY-MM-DD>
owner: <git-user-name>
status: active | complete | abandoned
last-distilled: >-
  <YYYY-MM-DD, one paragraph of current state: what is running, what the tree is at, what the next
  decision is. Then exactly ONE prior-link clause and nothing older:>
  — *prior distill (<YYYY-MM-DD>), one clause:* <the single sentence worth carrying forward>
turns-since-distill: 0
---

# Loop: <name>

## Goal
<One paragraph. What the orchestration is for, what "done" looks like for the quest it serves (for a
rollout milestone that delivers project-definition scope, its exit gate in `docs/project-definition.md`), and why the work needs more
sessions than one context window holds.>

## ⚠ The non-duplication rule — read before writing anything here

This file holds **only** state with no other home. Anything with an owning artifact — the rollout's
Resume state, a fix doc's RCA, a status doc's measurement, an ADR's decision, a `manifest.json`,
`git log`'s record of what shipped — is read from there, never copied in. A copy is a second record
that will drift, and the drift is what breaks a resume.

Before writing a paragraph here, ask: does an artifact already own this? If yes, put a pointer in
the Read-first list instead.

## Read-first list (pointers, never summaries)

Read on every resume, in this order. Paths only.

1. `<sidequests/<slug>/<slug>-rollout.md>` — §Resume state
2. `git log --oneline -10` — what actually shipped
3. `<docs/plans/fixes/... active fix doc(s)>`
4. `<sidequests/<slug>/status/run<N.M>status.md — most recent run status>`

## Out of scope
- <what this loop deliberately does not decide>

## Established Constraints
> Facts about **the pattern itself** — who commits, how many write-capable workers run at once,
> what a worker window is trusted to do. Each cites its evidence. A constraint without a pointer is
> an opinion wearing a rule's clothes.

- **C1.** <constraint> — *evidence:* <pointer>

## Human-AI Consensus
> Choices about the pattern agreed with the user. A gate ruling made under a gate delegation is
> recorded here too, citing the `G<n>` it was made under.

- **D1.** <decision> — *agreed:* <YYYY-MM-DD> — *rationale:* <why>

## Standing grants (agentic mode)
> **Stays empty in a manual-mode loop.** An act no grant in force covers, including any act after a
> grant has ended, is done in manual mode. No grant covers a push. While a grant is in force, the
> rules are in `.claude/skills/overseer/references/agentic-dispatch-mode.md`.

- **G1.** — *agreed by:* <user> — *date:* <YYYY-MM-DD> — *authority:* gate delegation |
  commit-and-merge | both — *scope:* <what it covers> — *ends:* <date or event> — *always
  escalates:* <what> — *stays the user's:* every push to a remote<, plus anything else>

## Current Hypotheses

**Intentionally unused.** This is an orchestration loop, not an investigation. Investigative loops
opened *from* this thread get their own loop files.

## In flight
> Worker windows running right now. **Drains at each cycle boundary.** A non-empty entry after a
> cycle closes is an overdue drain.

- <window> — dispatched <YYYY-MM-DD HH:MM> — task: <one line> — expects to return: <what>

## Decided here but not yet in a doc
> **Drains the same session the decision is made.**

- <decision> — <YYYY-MM-DD> — *belongs in:* <artifact that should own it>

## Homeless follow-ons
> A follow-on with no owning doc and no trigger. Drains when an owning doc exists (often
> `docs/plans/followups.md`).

- <item> — *surfaced:* <YYYY-MM-DD> — *would be owned by:* <artifact, once it exists>

## Pattern observations across cycles
> Dated log of defect classes in **how the pattern is being executed**, not in the quest's code.
> Append-only. Prune by *promotion*: when acted on, replace the entry with one line naming the
> skill, test, validator or doctrine change that now enforces it.

- **<YYYY-MM-DD> — <one-line defect class, stated so it is recognizable next time>**
  - *what happened:* <the specific instance>
  - *why it survived:* <the check that should have caught it and didn't>
  - *promoted to:* <where, once it is — otherwise "not yet">

## Rejected Paths
- **R1.** <approach> — *rejected because:* <reason> — *would reopen if:* <condition>

## Open Questions
- **Q1.** <question> — *needed for:* <which decision> — *how to answer:* <approach>

## Pivot Log
> The spine. A reversed scoping call is the most common thing this pattern produces — record it
> here rather than quietly re-deciding.

- **<YYYY-MM-DD HH:MM> — <one-line pivot>**
  - *From:* <prior framing> · *To:* <new framing> · *Why:* <trigger, with its evidence>

## Scratch (volatile)
> Wiped at every distillation. Non-empty on resume means the previous session ended without a clean
> distillation — treat its contents as suspect.

<free-form>
