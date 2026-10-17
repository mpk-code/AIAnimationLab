---
name: sidequest
description: >
  Manage quests — independent units of dev work (spike, utility, feature), each at
  sidequests/<slug>/: open a new one, close and archive one, abandon, reopen, reclassify,
  or report status. Use for "open a quest", "open sidequest", "new sidequest", "start a quest",
  "close sidequest <slug>", "abandon sidequest <slug>", "reopen sidequest <slug>", "reclassify
  sidequest <slug>", "sidequest status", or /sidequest. Planning runs is /generate-rollout's
  job; executing them is /run-process's.
---

# Skill: Sidequest

A lightweight registry workflow for quests. There is no top-level structure — no main rollout, no releases. Every quest is independent, of type `spike`, `utility` or `feature`; `parent:` records only which quest (if any) spawned it.

A quest folder is a **narrative container** only: rollout, status reports, fixes, optional findings or plans. Persistent specs live at their own paths (`docs/`, `schemas/`, `styles/`, `docs/adr/`); the link between a quest and the paths it changes is the `spec-refs:` frontmatter field.

**Active vs archived.** An open quest (`status: active`) lives at `sidequests/<slug>/`. On close (`status: done` or `abandoned`) this skill moves the folder to `sidequests/archive/<slug>/` and upserts a row into `sidequests/archive/index.md`. Closure triggers the move whether or not `integrated:` has been flipped — the soft gate looks in both locations.

The convention is documented in `sidequests/README.md` (vocabulary: a rollout has *milestones*, milestones have *runs*, run IDs are `<milestone>.<run>`). This skill is the operational entry point. These are dev-process quests for building the studio — not productions (`productions/<id>/`), which the pipeline stage skills in `skills/<stage>/` drive.

## Sub-actions

| User intent | Sub-action |
|---|---|
| "open a quest/sidequest", "new sidequest", "start a quest" | **Open** |
| "close sidequest \<slug\>" | **Close** (status → `done`, then archive) |
| "abandon sidequest \<slug\>" | **Close** in abandon mode (status → `abandoned`, then archive) |
| "reopen sidequest \<slug\>" / "amend sidequest \<slug\>" | **Reopen** |
| "reclassify sidequest \<slug\> [as \<type\>]" | **Reclassify** |
| "sidequest status [\<slug\>\|all]", "sidequest status --all" | **Status** |

If the intent is ambiguous, ask. Do not guess between Open and Reclassify, or between Close and Abandon.

## Frontmatter contract

Every quest rollout begins with this exact block (field order as shown):

```yaml
---
parent: none          # 'none' for a standalone quest, or the slug of the quest that spawned this one
type: spike           # spike | utility | feature
triggered-by: <run id or context>
purpose: <one sentence>
deliverable: <expected artifact, finding, or integration>
spec-refs: []         # persistent paths this quest changes (docs/, schemas/, styles/, docs/adr/); empty for spikes
status: active        # active | done | abandoned
integrated: false     # flipped to true by the user after applying proposed changes
opened: <YYYY-MM-DD>
worktree: .claude/worktrees/<slug>   # optional — omit unless a worktree was created
---
```

- `spec-refs:` is the bridge between the temporary quest and the persistent paths it modifies. `/run-process` loads context from them.
- `integrated:` is the soft-gate signal read by `/run-process` pre-flight. **Never set it to `true` from this skill.**
- `worktree:` is present only when the user opted into a worktree. Never write `worktree: null`.

## Spec-refs by type

- **spike** — `[]`. Findings live in `sidequests/<slug>/findings.md`.
- **utility** — the persistent records of the utility's contract: an ADR `docs/adr/NNNN-<slug>.md` (next free number; scaffolded at Open from `docs/adr/0000-template.md` if absent) plus any schema it defines in `schemas/`. They persist after the quest closes.
- **feature** — the persistent paths the quest will modify, e.g. `styles/<dimension>/<style-id>/style.yaml`, `schemas/<name>.schema.json`, `docs/glossary.md`. Not auto-scaffolded: they must exist or be created deliberately. A change to `docs/glossary.md`, a schema, or `CLAUDE.md` needs an ADR, so include the ADR path too.

## Deliverable templates (appended after the body)

**Spike:**
```
## Deliverable
### Findings
### Decisions or recommendations for parent quest
### Code disposition (archive | promote specific files | discard)
### Open questions surfaced
```

**Utility:**
```
## Deliverable
### Artifacts (with paths)
### Integration points (how the parent consumes this)
### API surface / public interface
### Spec confirmation (paths in spec-refs)
### Open questions surfaced
```

**Feature:**
```
## Deliverable
### Exit gate evidence (only when the rollout's milestones carry exit gates, e.g. from docs/project-definition.md; with proof)
### Artifacts
### Proposed changes to referenced persistent specs (paths in spec-refs)
### Open questions surfaced
```

---

## Open

### Prompts (one at a time, validating each)

1. **slug** — kebab-case, `^[a-z][a-z0-9-]*$`. Reject if it exists under `sidequests/` or `sidequests/archive/`.
2. **type** — `spike` | `utility` | `feature`. Default `spike` if the user is uncertain.
3. **parent** — `none` for a standalone quest, or the slug of the active quest that spawned this one (validate the directory exists). Default `none`.
4. **triggered-by** — free text; encourage a run ID or context (`Run 2.4`, `bug-fix of harness hash drift`).
5. **purpose** — one sentence.
6. **deliverable** — one sentence. When the quest delivers project-definition scope (e.g. studio v1), propose the relevant exit gate(s) from `docs/project-definition.md`.
7. **spec-refs** — per "Spec-refs by type". Spikes auto-set `[]`. Never invent a path silently; if unclear, ask.

### Scaffold

Create:
- `sidequests/<slug>/<slug>-rollout.md` — frontmatter + body skeleton:
  ```markdown
  # Quest: <slug>

  ## Context
  <why this exists, from purpose + triggered-by; when it delivers project-definition scope, the relevant scope rows>

  ## Approach
  <to be filled in by /generate-rollout>

  ## Spec refs
  <listed from frontmatter for convenience>

  ## Runs
  <run status reports land in status/>

  <type-appropriate ## Deliverable template>
  ```
- `sidequests/<slug>/status/.gitkeep` and `sidequests/<slug>/fixes/.gitkeep`
- **spike only:** `sidequests/<slug>/findings.md` — `# <slug> — Findings`
- **utility only:** for each `spec-refs:` ADR path that doesn't exist, copy `docs/adr/0000-template.md` to it and set its title; leave the body for the quest to fill. Add it to `docs/adr/README.md`'s index as `Proposed`.

Never scaffold spec files inside the quest folder.

### Back-reference

When `parent:` is a quest slug, find the heading in `sidequests/<parent>/<parent>-rollout.md` that matches `triggered-by` (a run or milestone heading) and append on its own line:

```
> spawned sidequest: <slug> (<type>)
```

If the location is unclear, ask — never place it at the top of the file. When `parent: none`, write no back-reference anywhere — persistent docs such as `docs/project-definition.md` are never auto-edited.

### After scaffolding

Print the files created and the back-reference location. Suggest `/generate-rollout in sidequest <slug>` as the next step. Do not commit.

### Worktree offer (optional)

For `utility` or `feature` quests likely to span several sessions, offer (don't execute):

> **Optional: isolated worktree** — keeps this quest's commits on their own branch while `main` moves, and lets skills infer the quest from the branch name:
> ```bash
> git worktree add .claude/worktrees/<slug> -b worktree-<slug>
> ```
> If you do this, I'll add `worktree: .claude/worktrees/<slug>` to the frontmatter so Close can remind you to clean up.

Only on the user's opt-in: print the command (don't run it) and add the `worktree:` line. Never suggest it for spikes.

---

## Close

Two modes — **done** (the work landed) and **abandoned** (dropped). Both end with the quest archived.

1. **Read** `sidequests/<slug>/<slug>-rollout.md`. Require `status: active`; otherwise refuse and point to `/sidequest reopen <slug>`.
2. **Worktree alignment.** If `worktree:` is declared, Close runs on `main` (archive on main, then merge the branch — step 10). If `git rev-parse --abbrev-ref HEAD` is `worktree-<slug>`, warn that archiving here complicates the merge and wait for the user.
3. **Mode:** "close" → done; "abandon" → abandoned. If ambiguous, ask.
4. **Done mode — prompt by type:**
   - `spike` — findings, recommendations, code disposition, open questions. Remind the user to migrate substantive `findings.md` content into `### Findings`.
   - `utility` — artifacts, integration points, API surface, open questions. Confirm each `spec-refs:` path exists and isn't still the unfilled template (warn, don't block).
   - `feature` — exit-gate evidence when the rollout's milestones carry exit gates (commands run and their results, e.g. the reproducible-render hashes and `manifest.json` path for the studio v1 quest's M0), artifacts, proposed changes to each `spec-refs:` path as diff-style blocks, open questions.

   **Abandoned mode** — skip the deliverable; write an `## Abandonment` block with `### Reason` (one paragraph) and `### Outstanding` (what was left undone, what was learned, artifacts the next reader should know about).
5. **Write** the answers into the rollout. **Set** `status: done` (or `abandoned`). Do not touch `integrated:`.
6. **`feature` done mode:** offer (don't perform) a diff per `spec-refs:` path applying the proposed changes. Apply only on explicit per-file confirmation. Do this before the archive move.
7. **List the citations the move will break:**
   ```bash
   git grep -n -F '`sidequests/<slug>/' -- '*.md'
   git grep -n -E '\]\([^)]*sidequests/<slug>/' -- '*.md'   # markdown links: listed, not repaired
   ```
8. **Move to archive:**
   ```bash
   mkdir -p sidequests/archive
   git mv sidequests/<slug> sidequests/archive/<slug>
   ```
   Fall back to plain `mv` if the folder has untracked files, then stage the tracked files' move (`git add -A -- sidequests/<slug> sidequests/archive/<slug>`, unstaging any untracked file it picked up) — the rewriter reads the move from the index.
9. **Rewrite the backticked citations the move broke** (in every markdown file, records included — only the location changed, not the claim). Dry run, check against step 7's list, then apply:
   ```bash
   git grep -lz -F '`sidequests/<slug>/' -- '*.md' | xargs -0 python3 .claude/skills/sidequest/scripts/rewrite_citations.py --only archived
   git grep -lz -F '`sidequests/<slug>/' -- '*.md' | xargs -0 python3 .claude/skills/sidequest/scripts/rewrite_citations.py --only archived --apply
   ```
   Re-run the dry run: it must report `archived 0` or print nothing. `moved` / `moved-ambiguous` / `gone` lines are never applied here; list them as follow-ups.
10. **Upsert `sidequests/archive/index.md`** (see "Archive index format").
11. **Review block** for the user: the deliverable or abandonment contents; the new path; the index row; the citation rewrite (step 7 count, the rewriter's summary line, `git diff --stat`, and every unapplied line and markdown link as follow-ups); and for done mode the condition for flipping `integrated: true`:
    - `spike` → "acknowledge findings, then flip `integrated: true`"
    - `utility` → "confirm the records at `spec-refs:` reflect the as-shipped utility, then flip `integrated: true`"
    - `feature` → "apply the proposed changes to each `spec-refs:` path (e.g. tick exit-gate boxes in `docs/project-definition.md`), review any exit-gate evidence, then flip `integrated: true`"
12. **Worktree cleanup reminder** if `worktree:` is set:
    > After committing the close, from the main repo root:
    > ```bash
    > git merge --no-ff worktree-<slug> -m "feat(<slug>): merge quest into main [<slug>]"
    > # edit sidequests/archive/<slug>/<slug>-rollout.md → integrated: true, then /commit
    > git worktree remove .claude/worktrees/<slug>
    > git branch -d worktree-<slug>   # optional
    > ```
    > `--no-ff` keeps the quest's history grouped. If `main` has moved, compare `git diff --name-only <merge-base>..main` with the quest's files; rebase if they intersect.

**Back-references** (`> spawned sidequest: …`) are never rewritten — they name a slug, not a path, and are historical fact. Readers resolve a slug by checking `sidequests/<slug>/` then `sidequests/archive/<slug>/`.

**Hard rule:** never auto-edit `docs/project-definition.md`, `CLAUDE.md`, or any `spec-refs:` path. They change only on explicit confirmation of a shown diff, or by the user's own authoring.

---

## Reopen

The only sanctioned way to amend a closed quest.

1. Locate `sidequests/archive/<slug>/<slug>-rollout.md`; refuse if absent.
2. `git mv sidequests/archive/<slug> sidequests/<slug>`.
3. List the citations Close archived, now broken, and show the count. The rewriter has no reverse mode; offer to fix them by hand with the user's confirmation.
   ```bash
   git grep -n -F '`sidequests/archive/<slug>/' -- '*.md'
   ```
4. Set `status: active`. Leave `integrated:` as it was.
5. Remove the slug's row and `## <slug>` section from the archive index (keep the header even if the table empties).
6. Report the active path: "Reopened — close again when amendments are done."

Reopen doesn't re-prompt fields, touch back-references, or alter the rollout body.

## Reclassify

1. Read the frontmatter; confirm the new type.
2. Update `type:` (a one-line edit when no scaffolding is needed).
3. **Promotion:**
   - `spike → utility`: scaffold the ADR per "Spec-refs by type"; update `spec-refs:`. Leave `findings.md` in place.
   - `spike → feature`: ask which persistent paths it will modify; confirm they exist or ask before creating.
   - `feature → utility`: scaffold the utility ADR if missing; update `spec-refs:`.
4. **Demotion** (e.g. `utility → spike`): leave persistent records in place — they belong to the system, not the quest. Set `spec-refs: []` and note "records at <paths> remain".
5. If the `## Deliverable` template no longer matches the type, swap it, preserving filled-in content under `### Notes (from previous type)`.

---

## Status

### `sidequest status <slug>`

Look in `sidequests/<slug>/`, then `sidequests/archive/<slug>/`. Print:
- Location (active / archived) and the full frontmatter (plus `closed:` from the index if archived).
- For each `spec-refs:` path: exists? stub or substantive?
- Counts of `status/run*status.md` and `fixes/*.md`; whether `status/carry-forward.md` exists.
- For spikes: presence and size of `findings.md`.
- Whether `## Deliverable` (or `## Abandonment`) is filled in (any non-empty `###` subsection).
- If `status: done && integrated: false`, the type-specific blocker (see Close step 11). Abandoned quests never flag.

### `sidequest status all` (active only)

For each `sidequests/*/` except `archive/`, one line:
```
<slug>  type=<type>  status=<status>  integrated=<bool>  parent=<parent>
```
Then a `Pending integration:` heading listing every quest — **active or archived** — with `status: done && integrated: false`, archived rows prefixed `[archived]`.

### `sidequest status --all`

Same format across `sidequests/*/` and `sidequests/archive/*/`, archived rows prefixed `[archived]`. If the user's wording is ambiguous between the two, ask.

---

## Archive index format

`sidequests/archive/index.md` is owned by this skill — only Close and Reopen write it.

```markdown
# Side-Quest Archive

Closed quests are listed here in reverse-chronological order of closure (newest at top). Active quests live one level up at `sidequests/<slug>/`. This file is managed by `/sidequest` — never edit it by hand.

| Slug | Type | Status | Integrated | Parent | Opened | Closed | Last commit | Spec-refs | Summary |
|------|------|--------|------------|--------|--------|--------|-------------|-----------|---------|
| [<slug>](<slug>/) | spike | done | false | studio-v1 | 2026-10-20 | 2026-10-22 | 2026-10-22 | — | One-line summary. |

## <slug>

- **Type:** spike \| utility \| feature
- **Status:** done \| abandoned
- **Integrated:** true \| false \| n/a (abandoned)
- **Parent:** none \| <parent-slug>
- **Opened / Closed:** YYYY-MM-DD / YYYY-MM-DD
- **Last commit:** YYYY-MM-DD (`<short-sha>`)
- **Spec-refs:** one bullet per path, or —
- **Path:** [`sidequests/archive/<slug>/`](<slug>/)

### Summary
One or two sentences on what shipped; for abandoned quests, why it was dropped.

### Outstanding
- From the deliverable's `### Open questions surfaced` (done) or the `## Abandonment` `### Outstanding` (abandoned), plus any `integrated: false` reminder still owed.
```

Field sources: frontmatter at close time for Type, Status, Integrated (`n/a` when abandoned), Parent, Opened, Spec-refs; Closed is today; Last commit is `git log -1 --format="%cs %h" -- sidequests/archive/<slug>/` (fall back to the pre-archive path if the move isn't committed yet); Summary is supplied by the user at close.

**Upsert rules:** table rows and `## <slug>` sections are both ordered by Closed descending, Slug as tiebreaker, and always in the same order. Replace an existing row/section in place, or insert in sorted position. Never touch other slugs' entries. If the file is missing, create it with the header and an empty table. Reopen removes the row and section together — no half-entries.

---

## Constraints

- **Never commit.** This skill edits files only; the user runs `/commit`.
- **Never set `integrated: true`.** That is the user's signal.
- **Never auto-edit** `docs/project-definition.md`, `CLAUDE.md`, or `spec-refs:` paths without per-file confirmation of a shown diff.
- **Never scaffold spec files inside a quest folder.**
- **Never nest quest folders or sort them by type.**
- **Never create or remove worktrees** — offer the commands; the user runs them.
- **The archive is owned by this skill.** Other skills (`run-process`, `bug-fix`, `commit`) read from it but never write. A slug is never in both locations.

## Anti-patterns

```
// WRONG: scaffolding <slug>-spec.md inside the quest folder
// Quest folders are narrative-only. Specs live at their spec-refs paths.

// WRONG: auto-applying a feature quest's proposed changes to styles/... or schemas/...
// Offer a diff per file and wait for confirmation.

// WRONG: setting integrated: true at close
// Close sets status only. The user flips integrated after applying changes.

// WRONG: writing a back-reference into docs/project-definition.md for parent: none
// The project definition is the source of truth and is never auto-edited; back-references go only into a parent quest's rollout.

// WRONG: opening a "main" quest, or treating one quest as the top-level parent of all others
// There is no main rollout. Quests are independent; type is spike | utility | feature, parent is none or the spawning quest.

// WRONG: leaving a closed quest at sidequests/<slug>/, or archiving without the citation rewrite
// Close always moves, rewrites the archived citations, and upserts the index.

// WRONG: editing files in sidequests/archive/<slug>/ to amend a closed quest
// Reopen first, then re-close.

// WRONG: opening a quest for a film
// Productions live in productions/<id>/ and run through the pipeline stage skills, not quests.
```
