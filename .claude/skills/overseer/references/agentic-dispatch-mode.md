# Agentic dispatch mode — the rest of the rules

Read from `SKILL.md` `## Agentic dispatch mode (Claude Code only)`, which holds the mode's condition
and the grant check. A section this file cites and does not hold is in `SKILL.md`.

### Every agentic dispatch names (pointers only)

- the `Dispatched by: overseer <loop-file-path>` header, a self-contained task, and any issue as
  `issue #<n>` — `## Dispatching worker windows`
- the branch, the base the worker's HEAD must contain, and the command that confirms it —
  `## Rules for both dispatch modes`
- targeted checks only, the gate is the overseer's, and stop and report — `### Parallel workers
  share four resources`, item 1
- no pattern kill, no bare `git stash` — the same subsection, items 3 and 4
- the arrangement it is in, never "you are the only window open" — the same subsection
- the worktree path (when you created it), its scratch subdirectory, and, when the run edits a
  skill, to read the skill file in its worktree — `### Creating the worktree`, below
- that the user is not reachable, and which files another worktree may also extend —
  `### While the worker runs`, below

### The standing grant

- **Within a commit-and-merge grant:** sweep the return (`## Sweep each worker's return`), read the
  full diff, commit on the worktree branch, and merge into the parent branch after a green gate
  (`### The gate`), without asking per commit. Workers still do not commit.
- **Record each gate ruling made under a gate delegation** in the loop file's `## Human-AI
  Consensus`, with its date, the `G<n>` it was made under, and its reason. Flag for the user any
  ruling that changes a cost or a premise the user accepted.

### Creating the worktree

- **Settle the base every dispatch.** Compare the local parent branch with the remote default branch
  in both directions (`git rev-list --count` each way). If they differ, settle the base first so the
  committed dispatch prompt is reachable from the worker's HEAD. Harness worktrees may start from the
  remote branch, not the local parent. Write the arrangement and the worker's check into the
  dispatch, never a SHA.
- **A dispatch that may stop before writing anything runs in a worktree you created** with
  `git worktree add` under `.claude/worktrees/`, from the parent branch; pass its path. A harness
  worktree with no changes may be removed, branch included, when its worker returns, leaving nothing
  to resume in.
- **Initialise the worktree's gitignored environment** (Python virtualenv, Git LFS objects) or tell
  the worker to.
- **Each parallel dispatch names its own scratch subdirectory** — background workers in one session
  share the session's scratch directory.
- **A background worker's Skill tool loads skills from the session's tree, not its worktree.** When
  the two may differ (the run edits a skill, or the bases differ), tell the worker to read the skill
  file in its worktree as text.

### While the worker runs

Each agentic dispatch says, in its own text:

- that the user is not reachable from the worker. Where its skill would stop for the user, the
  worker ends its turn with the question as its final message, and the overseer replies by message;
- its scratch subdirectory, when other background workers run in the session;
- which files another worktree may also extend, and that the two workers do not coordinate.

**Answer a worker's question from a ruling in force, or relay it** to the user and reply with the
user's answer.

**Rebase the second of two parallel worktrees** that may extend the same files onto the first merge
before merging it.

**Don't run two workers' renders concurrently on one machine** when either one measures render time
or reproducibility; GPU contention moves both numbers.

### The lifecycle, from worktree to push

1. Settle the base; if the dispatch may stop early, create the worktree yourself.
2. Commit your own dispatch prompt, then dispatch.
3. Answer or relay the worker's questions.
4. Sweep the worker's return.
5. Read the full diff, run the gate (`scripts/run_tests.sh`) on the worktree, then commit on the
   worktree branch with the gate line in the body.
6. Merge into the parent branch; if the merge is not a fast-forward, run the gate on the merged tree
   before committing the merge.
7. Remove the worktree and its branch with the commands that refuse to discard work:
   `git worktree remove <path>` (no `--force`), then `git branch -d <branch>`. If either refuses,
   keep the worktree and find out why. A worktree whose branch is not merged is kept.
8. Before any push, run the gate on the tree being pushed.
9. Leave the push decision to the user.
