---
name: commit
description: >
  Smart commit workflow: recalls session intent, groups changes by unit of work, shows the
  proposed plan, and commits only after explicit user approval. Use for "commit", "let's
  commit", "commit the changes", "commit what we did", "commit this run", "commit and push",
  "commit everything", or /commit. NEVER commit without user approval.
---

# Skill: Smart Commit

Commit the results of an agentic coding session cleanly and traceably: commits that say what changed, why, and which run, quest or decision they serve — without making the user think about any of that.

## Architecture — parent synthesizes, subagent reads

This skill runs in the **main (parent) conversation**, which knows *why* the work was done and where the approval gate and `git commit` side effects stay visible. The context-heavy part — reading the full diff, status and fix documents, and test output — goes to an isolated **Explore subagent** that returns only a structured inventory. The raw diff never lands in the parent context.

## Step 1 — Recall session intent (parent)

Before reading anything, write down from session memory what was done and *why*: the run(s) or fix(es), the reasoning, and the quest slug, run IDs, ADRs or issue numbers you already know. The subagent has no conversation history; this is the parent's unique contribution.

In a fresh session with no memory of the work, say so — you'll rely on the subagent's reading of the status and fix documents.

## Step 2 — Delegate inventory and tests to a read-only subagent

Spawn the **Agent tool** with `subagent_type: Explore` (read-only — it can inspect but not commit) and `model: sonnet` (the reading is mechanical). Give it this prompt as-is:

> You are inventorying a working tree for a commit. Do NOT commit, stage, or edit anything.
> Return a structured summary only — **do not paste raw diff hunks back**.
>
> 1. Run `git status --short`, `git diff --stat HEAD`, and
>    `git ls-files --others --exclude-standard`. Write the full tracked diff to a file inside
>    `.git` (`git diff HEAD > "$(git rev-parse --git-path commit-inventory.diff)"`) and read it
>    from there. Read each untracked new file directly.
> 2. Run `scripts/run_tests.sh` once, bare (no pipe, no redirect), and record its exit code and
>    its summary lines. If the script does not exist yet, say so and run nothing else.
> 3. Read every changed or new status report (`sidequests/*/status/run*status.md`), carry-forward
>    ledger, rollout, and fix document (`sidequests/*/fixes/*.md`, `docs/plans/fixes/*.md`). These
>    are the authoritative record of what was done: quest, run ID, acceptance criteria, files.
> 4. Flag sensitive or accidental files: `.env`, credentials, renders and other large binaries
>    (`*.png`, `*.exr`, `*.mp4`, `*.blend`, anything over 1 MB) not tracked by Git LFS, files under
>    `productions/*/renders/`, `__pycache__/`, `.pytest_cache/`, `.DS_Store`.
>
> Return exactly:
> - **Test results:** exit code and summary lines of `scripts/run_tests.sh` (or "runner absent").
> - **Candidate work-unit groupings:** each = the status/fix document it maps to (if any), its
>   file list, and the anchors found (quest slug, run ID, ADR, issue number).
> - **Per-file change descriptions:** one line each.
> - **Sensitive/accidental files:** listed separately; NOT in any grouping.

**If tests fail** (non-zero exit): stop. Report the failure summary and tell the user the commit is blocked. Do not proceed.
**If tests pass:** say so and continue. **If the runner is absent** (before M0 creates it): say so in the plan; the user decides whether to commit without it.

## Step 3 — Synthesize groupings and messages (parent)

Combine Step 1's *why* with the subagent's *what*. Group by **unit of work** — one commit per distinct thing done, usually 1–3; don't split artificially.

- **One run** (code + tests + its status report + rollout tick + ledger lines): one commit.
- **One bug fix**: one commit naming what was broken and how it's fixed.
- **Bookkeeping** (quest open/close, archive moves, index updates): a separate `docs:` or `chore:` commit unless it documents exactly the run being committed.
- **Unrelated changes**: separate commits.

The scope tag names the *area*, not the file type: `harness`, `manifest`, `schemas`, `validators`, `style/<style-id>`, `blender-lib`, `skills/<stage>`, `eval`, `decks`, `antidefaults`, `quests`, `doctrine` (CLAUDE.md), `dev-skills` (`.claude/skills/`).

**Message format:**
```
<type>(<area>): <description> [<anchor>]

- What specifically changed
- What specifically changed

<trailer per "Co-author trailer" below>
```

Types: `feat`, `fix`, `test`, `chore`, `docs`, `refactor`.

**Provenance anchor (graduated by type).** `feat`/`fix`/`test` commits MUST carry an anchor in the `[...]` bracket tracing the change to the authority that motivated it. `refactor`/`chore`/`docs` carry one when a run, quest or decision is directly served. Cite at the altitude that best serves a future reader:

- **Run** — `[R2.3]`, the run's status report already says the rest. Qualify with the slug when the quest isn't obvious from context: `[studio-v1-R2.3]`. The run ID is `<milestone>.<run>` within that quest's rollout.
- **Quest** — `[style-ink-line]` — for a change that spans a quest (or several runs of one rollout milestone); cite runs rather than a bare milestone number.
- **Decision** — `[ADR-0003]`; coding standard `[STD-004]`.
- **Issue** — `[issue 12]` (never `#12` next to a verb — see below).

Before Step 4, check every `feat`/`fix`/`test` message for an anchor. If one is missing, recover it from the status/fix documents and rollout, or surface the gap in the plan so the user can supply or waive it — never silently ship one without.

**Closing a GitHub issue.** `/bug-fix` does not close issues; this line does. GitHub closes the issue when the commit reaches `main`. Put `Closes #<n>` on its own line above the trailer **only** when a fix document in the commit meets all four conditions:

- its header reads `**Issue:** #<n>`;
- its first `**Status:**` stamp is `COMPLETE`;
- its first `**Reproduces after change:**` line starts with the word `no`;
- its first `**Lane:**` line reads `code`. A record-lane fix changes no product code; its issue is **closed by hand on GitHub as *not planned*** once the commit is on `main`.

Anything else — `DRAFT`, `IN PROGRESS`, a `yes — …`, `not yet checked`, a missing line — leaves the keyword out and the issue open. Read the headers from the files, not memory. Pass the group's fix documents to this loop (it reads untracked files too):

```bash
for f in <fix-doc-1> <fix-doc-2>; do
  awk -v f="$f" '
    !i && /^\*\*Issue:\*\* *#[0-9]+/ { i = $0; sub(/^\*\*Issue:\*\* *#/, "", i); sub(/[^0-9].*$/, "", i) }
    !s && /^\*\*Status:\*\*/          { s = $0; sub(/^\*\*Status:\*\* */, "", s) }
    !r && /^\*\*Reproduces after change:\*\*/ { r = $0; sub(/^\*\*Reproduces after change:\*\* */, "", r) }
    !l && /^\*\*Lane:\*\*/            { l = $0; sub(/^\*\*Lane:\*\* */, "", l) }
    END {
      if (i == "") exit
      done = (s ~ /^COMPLETE([^A-Za-z_-]|$)/)
      gone = (r ~ /^no([ \t:,.;-]|—|$)/)
      code = (l ~ /^code([^A-Za-z_|-]|$)/) && (l !~ /^code[ \t]*[|]/)
      print i "\t" (done && gone && code ? "CLOSE" : "OPEN") "\t" f "\t" (s == "" ? "(no Status stamp)" : s) "\t" (r == "" ? "(no reproduction line)" : "reproduces: " r) "\t" (l == "" ? "(no lane line)" : "lane: " l)
    }
  ' "$f"
done
```

In the Step 4 plan, show every line it prints:
- `CLOSE` → `Closes #<n>` goes in the message; the user approves the closure with the commit.
- `OPEN` → no keyword, plus a plan line `#<n> stays open — <file> is <status>; <reproduction>; <lane>`. If the only reason is `lane: record`, say instead `#<n> is closed by hand — record-lane fix; close it on GitHub as "not planned" once this is on main`.

If one document says `CLOSE` and another `OPEN` for the same issue, `CLOSE` wins.

**No other closing keyword anywhere in a message.** GitHub closes an issue on `close`, `closes`, `closed`, `fix`, `fixes`, `fixed`, `resolve`, `resolves` or `resolved` followed by `#<n>`, case-insensitively and even straight after `-` or `/` (`/bug-fix #14` reads as `fix #14`). Run this over every planned message and keep only the `Closes #<n>` lines the loop emitted; reword any other hit (`issue 14`, `the issue-14 fix`):

```bash
grep -n -i -E '(^|[^[:alnum:]_])(close[sd]?|fix(e[sd])?|resolve[sd]?):?[[:space:]]+#[0-9]+' <message-file>
```

**Co-author trailer.** Use the attribution of the model *currently running this skill*, as the harness states it in its environment or system instructions — never a hardcoded or remembered value. Format: `Co-Authored-By: <model name> <noreply@anthropic.com>`. If the session supplies its own attribution lines, use those exactly. Omit the trailer for a pure docs/bookkeeping commit with no substantive implementation.

## Step 4 — Present the plan and wait for approval

**A user instruction to commit ("commit this", "commit run 2.3") STARTS this workflow; it is never approval of a plan.** Approval is only a user message sent *after* the plan is shown. Your own confidence in a diff you wrote this session is not approval either.

```
## Proposed commits

### Commit 1 of 2 — feat(harness): reproducible preview render with seeded manifest [studio-v1-R0.3]
Files:
  blender/harness/render.py
  blender/harness/manifest.py
  tests/test_render_determinism.py
  sidequests/studio-v1/status/run0.3status.md
  sidequests/studio-v1/studio-v1-rollout.md

### Commit 2 of 2 — docs(quests): open sidequest style-ink-line
Files:
  sidequests/style-ink-line/style-ink-line-rollout.md

Excluded (flagged): productions/p-0001/renders/frame_0001.png — large binary, not in LFS

Does this look right? Any changes to grouping or messages before I commit?

⏸ AWAITING COMMIT APPROVAL — reply to approve or amend.
```

The plan **must end with that literal marker line**, so the waiting state is never invisible or later misremembered as approved. If the user amends, update and show again.

## Step 5 — Execute (parent)

For each group, in order:

```bash
git add <file1> <file2> ...
git commit -m "$(cat <<'EOF'
feat(harness): description [R1.3]

- What changed
- What changed

Co-Authored-By: <model name> <noreply@anthropic.com>
EOF
)"
```

Then show `git log --oneline -5`. Push only if the user asked for it.

## Important rules

- **Never commit sensitive or accidental files** — `.env`, credentials, renders and large binaries outside Git LFS (manifests point to renders; renders don't go in git), caches. Exclude them and say so.
- **Never `git add -A` or `git add .`** — stage specific files.
- **Every commit in this repository goes through this skill**, including docs-only commits and diffs you wrote yourself this session.
- **Never amend** an existing commit unless the user asks. **Never force-push** without explicit instruction.
- One approval covers this plan only — no blanket future approval.
- Changes to `CLAUDE.md`, `docs/glossary.md` or a schema should travel with their ADR; if the ADR is missing from the diff, say so in the plan.
