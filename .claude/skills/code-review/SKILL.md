---
name: code-review
description: >
  Structured multi-lens review of one or more runs' diff — security, reliability,
  maintainability, functional defects (including studio doctrine), structural debt — writing a
  remediation report /bug-fix consumes. Use for "review the runs", "review what just landed",
  "audit the recent changes", "QA the diff", "is the run ready to close?", "is the milestone
  ready to close?", "should we merge yet?", a pre-merge or pre-close quality gate, or /code-review.
---

# Code Review Skill

This skill is phase 1 of a three-phase pipeline:

```
/code-review   →  produces remediation report (markdown)
/bug-fix       →  reads remediation report, makes changes
/commit        →  commits the resulting changes
```

`/code-review` owns **diagnosis**. `/bug-fix` owns **execution**. `/commit` owns
**recording**. This skill produces exactly one artifact — a markdown remediation
report — and stops cleanly. No source edits, no commits, no tag mutations.

These are dev-process reviews of the studio's own code (harness, validators, schemas, style
modules, eval tooling). They are not the film pipeline's critic stage in `skills/<stage>/`.

---

## Hard constraints (non-negotiable)

These are not preferences. Violating any of them is a defect in the skill itself.

1. **Never run `git tag`, `git commit`, `git push`, `git reset`, or any mutating
   git command.** Read-only git only.
2. **Never edit source files.** Producing the markdown report is the end of the
   skill's job.
3. **Never render.** Do not run the render harness or Blender to check a finding. If a finding
   needs a render to confirm, say so in the finding and leave the render to `/bug-fix`.
4. **Write only to the resolved fixes location.** `docs/plans/fixes/` for `project` scope,
   `sidequests/<slug>/fixes/` for a quest. Nowhere else.
5. **Idempotent.** Running the skill twice against the same window must produce
   the same report modulo timestamp. No state outside the fixes location.
6. **Never collapse the lens fan-out except under the objective small-diff
   exemption.** The five-lens parallel fan-out (Phase 3a) and the separate
   refutation subagents (Phase 3c) are mandatory. Merging the lenses into one agent,
   or running them inline in the main context, is permitted *only* when the Phase 3a
   small-diff exemption applies **and** the report records it. The reviewer must never
   be the author's context — the same rule that keeps generation and critique apart in
   the pipeline.

---

## Overseer-dispatched work (optional)

If the prompt carries a `Dispatched by: overseer <loop-file-path>` header (see the `overseer`
skill), three rules change:

1. **Append the overseer return block** below to the report, as its last section, after
   `## Recommendation`, under its own `## Overseer return block` heading so it sits outside
   `## Findings` and the four group headings `/bug-fix` parses. Its Verdict line holds the
   report's `verdict` value.
2. **Confirm HEAD before reading anything.** Run the check the dispatch names and confirm HEAD
   contains the base it names. A review whose HEAD lacks that base reviews a different diff.
3. **Where this skill would stop for the user, end the turn with the question as the final
   message** (for example `MASSIVE_DIFF`'s "ask the user"). Do not use an interactive prompt.

**Do not read the loop file.** The path is there so findings can cite it. If the dispatch prompt
doesn't name the review window or the scope, say so and ask; a prompt that can only be understood
by opening the loop file is a defective dispatch.

The rule that matters most to an overseer — never dropping a record the diff *disproves* as
"pre-existing, out of scope" — is unconditional and lives under "Scope discipline" below.

```
## Overseer return block (only if dispatched by an overseer)
- Verdict: the report's `verdict` value (pass | pass-with-minors | needs-fixes | block).
- What changed: nothing in the tree; one line naming the report path.
- Still open: anything the review found but could not settle, including a flag it raised
  (for example BASE_UNRESOLVED or MASSIVE_DIFF) and what the overseer must decide about it.
- Claims and their standing: one line per claim the overseer might carry into a scheduling
  decision, tagged MEASURED / INFERRED / SPECULATIVE. A MEASURED tag is only valid with the command
  string inline — runnable text, not "verified by grep". An INFERRED claim states its premise
  separately.
```

---

## Workflow

Four phases in order: discover scope, resolve the review window, review the diff, write the
report. Establishing scope precedes reading any source code — discovery is cheap, premature
review wastes context.

### Phase 1 — Discover scope

Every quest — spike, utility, or feature — lives in `sidequests/<slug>/` with a
`<slug>-rollout.md`; there is no main rollout. Pick exactly one scope per invocation:
`project` (project-wide, not tied to a quest) or `sidequest:<slug>`.

1. **User-specified quest.** If the user names a quest ("review the runs in `<slug>`"), use
   `sidequest:<slug>`.
2. **Inferred active quest.** If context clearly points at one quest — recent `run-process`
   invocations against it, recent edits to its rollout or status files, the working directory
   under `sidequests/<slug>/` — use it. State the inference in `## Scope`.
3. **Default to `project` scope** when no quest signal is present, *or when context is genuinely
   ambiguous*. Wrong scoping is worse than the default.

**Scope-mismatch check.** After resolving scope *and* the review window (Phase 2), cross-check:
does the chosen scope match the in-window runs/fixes? If the user picked `project` but every
in-window run belongs to one quest (or the reverse), raise `SCOPE_MISMATCH`, surface it in
`## Scope`, and recommend a re-run at the matching scope in `## Recommendation`. Do **not**
silently switch scope: the user's declaration wins.

| Concept | `project` scope | `sidequest:<slug>` scope |
|---|---|---|
| Rollout | none — project-wide intent is `docs/project-definition.md` | `sidequests/<slug>/<slug>-rollout.md` |
| Run status notes | every `sidequests/*/status/run<N.M>status.md` | `sidequests/<slug>/status/run<N.M>status.md` |
| Fix plans / review reports | `docs/plans/fixes/` | `sidequests/<slug>/fixes/` |
| Spec sources | the always-loaded set (Phase 2e) | the always-loaded set + each path in the quest's `spec-refs:` |

### Phase 2 — Resolve the review window and inputs

#### 2a. Resolve the base ref

The review window is `<base>..HEAD`. Resolve `<base>` in this priority:

1. **User override.** Explicit ref passed in the invocation (tag, branch, sha, `HEAD~N`).
   Document it in the report header.
2. **Most recent `code-review/*` tag that is an ancestor of `HEAD`.** List tags newest-first
   with `git for-each-ref --sort=-committerdate 'refs/tags/code-review/*'`, then take the
   **first whose commit is an ancestor of `HEAD`** (`git merge-base --is-ancestor <tag> HEAD`).
   **Single-quote the ref pattern** — zsh otherwise tries to glob it against the filesystem,
   produces "no matches", and silently drops the skill to rule 3.

   **The ancestor filter is load-bearing for branches and worktrees.** Tags share one namespace
   across branches and worktrees, so the newest tag can sit on a divergent branch. `git diff
   <base>..HEAD` is an endpoint comparison, so a non-ancestor base surfaces the other branch's
   commits as spurious deletions. When the global-newest tag is skipped for this reason, raise
   `CROSS_BRANCH_TAG_IGNORED` and name the skipped and chosen tags in `## Scope`.
3. **Merge-base with `main`.** When no `code-review/*` tag is an ancestor of `HEAD`. Say in the
   report that this is a first-ever review when no tag existed at all.
4. **Status-note attribution batch** (when HEAD is on `main` and merge-base equals HEAD, giving
   an empty window). Walk commits backward from HEAD, mapping each to a run or fix via its status
   note or fix plan. The base is the parent of the oldest commit in a contiguous attributable
   streak. Raise `BASE_UNRESOLVED` with a `chose-batch:` annotation in `## Scope` recording the
   range and run/fix list.
5. **Unresolved.** If nothing maps to runs/fixes, raise `BASE_UNRESOLVED` without an annotation
   and ask the user for an explicit ref. Stop.

`HEAD` is always `HEAD` unless the user passes an explicit end ref.

#### 2b. Tag handling — delegated to `/bug-fix`

This skill **does not** create, move, or delete tags. When `/bug-fix` runs against this report
it advances the `code-review/*` tag as its final step after all gates are green, or defers and
records the manual recovery command in its fix plan. `## Recommendation` therefore names the
report path and does **not** append a `git tag -f` command.

#### 2c. Identify in-scope runs and fixes

A "run" is a unit of agentic work, marked complete by a status note. A run/fix is in scope if
its status note or fix plan was added or modified within the git window, or records a completion
commit inside it. Scan the status-note and fix locations from the Phase 1 table.

Build a list: run id (or fix slug), completion sha if known, one-line summary from the note.
List it at the top of the report.

Commits that do **not** map to any in-scope run or fix go under `## Unaccounted Changes`. These
are the highest-risk diffs — no agent claimed them.

#### 2d. Compute the diff to review

Exclude process artifacts but keep spec changes *in* (specs are load-bearing for the review):

```bash
git diff <base>..HEAD \
  -- ':(exclude)docs/plans/**' \
     ':(exclude)sidequests/*/status/**' \
     ':(exclude)sidequests/*/fixes/**' \
     ':(exclude)sidequests/*/findings.md' \
     ':(exclude)sidequests/*/*-rollout.md'
```

Directory excludes use the trailing `/**` form because `:(exclude)<dir>/` matches the directory
entry, not the files within it.

Notes:
- **`docs/project-definition.md`, `docs/adr/`, `docs/glossary.md`, `schemas/`, `CLAUDE.md` and
  `skills/<stage>/SKILL.md` are NOT excluded.** A change to any of them is part of the review
  subject.
- **Generated and cache outputs.** Skip `__pycache__/`, `.venv/`, `.pytest_cache/`,
  `.mypy_cache/`, `.ruff_cache/`, and render output (frames, contact sheets) with a one-line note
  in `## Scope`.
- **Binary files** (renders, `.blend` files, LFS pointers' targets). Skip with a note.
- **Reverted changes.** Note under `## Scope` ("Reverted in window") and exclude.

For each changed file, read the **post-change full file**, not just the hunk. The diff says
*where to look*; the file says *what's actually there now*.

**Retrieval posture.** The diff is the scope; every file is already enumerated. The provers are
**grep** (exact `file:line`, "no non-test callers", proving a negative), a **REPL** ("does this
exception actually get caught?", "will this test really fail against current code?"), **git**
(`git show`/`git log` for provenance), and **reading** the post-change file end to end.

#### 2e. Load specs the changes touch

**Always loaded:** `docs/project-definition.md` (§System concept, §Pipeline, §Control surface,
§Repository structure, §Milestones), `CLAUDE.md`, `docs/glossary.md`, and every ADR in
`docs/adr/` whose title plausibly matches the diff (`docs/adr/README.md` is the index). A later
ADR wins over the project definition where they conflict.

**`docs/test-strategy.md`** is loaded when the diff adds or modifies tests. Tests that don't fit
the strategy's layers become Maintainability findings.

**`docs/coding-standards.md`** is loaded whenever the diff touches source. Lens 3 checks the diff
against it and cites the violated `STD-###` id; a documented standard overrides generic
maintainability heuristics where they disagree.

**Quest scope adds `spec-refs:`.** Read the rollout frontmatter. Behavior depends on `type:`:

- **`type: spike`** (e.g. a Blender API probe) — `spec-refs:` is empty by design. Spec
  Conformance reads "N/A — spike (deliverable is findings, not spec conformance)." Do *not* emit
  `SPECS_NOT_DECLARED`.
- **`type: utility`, `feature`** — `spec-refs:` lists the paths in `docs/`, `schemas/`,
  `styles/`, or `docs/adr/` the quest changes. Check the code honors them. The quest rollout's
  acceptance criteria — including the in-window rollout milestone's exit criteria (and, for a quest
  delivering project-definition milestones such as studio v1, that milestone's exit gate) — are
  part of the spec.

If `spec-refs:` is empty for a non-spike quest, raise `SPECS_NOT_DECLARED`, proceed with
behavioral review, and flag it for the user to fix the frontmatter.

If the diff modifies a spec file directly, that file is part of the review subject and must be
scrutinized for coherence with the code.

#### 2f. Report placement

- **`project`:** `docs/plans/fixes/code-review-<YYYY-MM-DD>-<short-sha>.md`
- **`sidequest:<slug>`:** `sidequests/<slug>/fixes/code-review-<YYYY-MM-DD>-<short-sha>.md`

Create the `fixes/` directory if missing. The `code-review-` prefix distinguishes the report from
`/bug-fix`-authored plans (`fix-<description>-<date>.md`). `<short-sha>` is the 7-character
abbreviation of `HEAD`.

### Phase 3 — Review the diff through five lenses

#### 3a. Dispatch — parallel independent reviewers

**Execution contract.** Run each of the five lenses as its own subagent via the Agent tool
(`subagent_type: general-purpose`), all spawned in a single message so they run concurrently.
Run the Phase 3c refutation as **separate** subagents. Collapsing the fan-out discards the
anti-anchoring and false-positive suppression it exists to provide — a defect in execution, not
a shortcut. Each subagent receives:

- The rubric for **its one lens only**. Blindness is intentional: an agent that doesn't know what
  the others look for can't anchor on their conclusions.
- The Phase 2d diff and the full post-change content of every changed file.
- The specs from Phase 2e relevant to its lens (Lens 4 needs all of them; Lens 3 needs
  `docs/coding-standards.md` to cite `STD-###` ids).
- The Phase 4 finding-block format, so it returns candidates ready to merge.
- The retrieval-posture note from Phase 2d.

Each returns **candidate findings** with its own severity guess. Do not deduplicate across lenses
yet; if two lenses flag the same line, keep both and let Phase 3c note the corroboration.

**Small-diff exemption (objective, not judgment).** Inline single-agent review is permitted
**only** when the diff is under **100 changed lines across at most 2 files, with no spec or
contract-surface change** (nothing under `docs/`, `schemas/`, `skills/`, or `CLAUDE.md`). A diff
that exceeds *either* bound or touches *any* such file takes the full fan-out. When the exemption
is taken, the report MUST record it:

- Set `SINGLE_AGENT_MODE` in frontmatter `flags`.
- State it in `## Scope` with the measured counts, e.g. *"Single-agent mode: 34 changed lines
  across 1 file, no spec changes — small-diff exemption."*

Phase 3c still runs in single-agent mode — the exemption removes the fan-out, not the filter.

#### 3b. Lens rubrics

Every finding declares which lens it came from — this prevents drift into "I don't like this."

**Lens 1 — Security.** Injection vectors (command, template, prompt), especially subprocess
calls that build a Blender command line from strings; unsafe deserialization (`yaml.load`
without a safe loader, `pickle`); hardcoded secrets or API keys; missing input validation where
an artifact or CLI argument crosses into code that executes it; unsafe file paths (traversal or
symlink escape from `--out` or a production folder); logging of secrets; dependency
vulnerabilities introduced by `pyproject.toml` / `requirements*.txt` diffs.

**Lens 2 — Reliability.** Unhandled error paths, swallowed exceptions, resource leaks (file
handles, subprocesses, temp dirs), missing timeouts on Blender subprocesses or network calls,
retries without backoff or idempotency, off-by-one (frame ranges are a classic), unguarded
`None`, shared mutable state, **nondeterminism** — unseeded randomness, iteration over unordered
collections feeding output, seeds not recorded in the manifest, wall-clock or machine-dependent
values leaking into frames — and test coverage gaps for new code paths.

**Lens 3 — Maintainability.** *In-place, defect-shaped local risk* — issues whose remedy is to
**relabel, annotate, or delete in place**, not to move or restructure code (that is Lens 5's).
Look for: unclear or misleading naming (including drift from `docs/glossary.md` terms), missing
or stale comments where intent is non-obvious, undocumented public APIs, magic numbers, dead code,
commented-out code, TODOs without an owner or a `docs/plans/followups.md` entry, inconsistent
style, and **violations of a `docs/coding-standards.md` standard — cite the `STD-###` id.** Tests
that don't fit the layer `docs/test-strategy.md` prescribes land here. Ask: *"will a reader
stumble, or is there latent local risk?"* If the honest fix is "move / extract / bundle / replace
the shape," it belongs in Lens 5. Comment *prose* quality in depth is `/doc-review`'s job; flag
here only what is plainly wrong or missing.

**Lens 4 — Functional defects.** Cross-reference the diff against loaded specs and each run's
stated goal:

- Acceptance criteria declared as met but not actually implemented.
- Edge cases the spec or rollout calls out but the code misses.
- Behavior that contradicts the project definition or an ADR.
- Off-spec assumptions baked into code (hardcoded values the spec says are configurable).
- **Stage contract violations.** Each pipeline stage reads only upstream artifacts and writes its
  own. Flag a stage or validator that reads downstream artifacts, writes another stage's
  artifact, or bypasses a schema.

**Studio doctrine (MUST check, per `CLAUDE.md`):**
- Rendering outside the harness (`bpy.ops.render.*` or a direct Blender invocation that is not
  `blender/harness/render.py`) → Major.
- `bpy.ops` where `bpy.data` would do (breaks in background mode) → Major.
- **Silent defaults:** a creative choice (palette, easing, camera move, timing, composition)
  hardcoded instead of read from a written artifact (`style_bible.json`, `shots.yaml`, deck
  draw, `production.yaml`) → Major.
- A manifest that no longer records model ID, Blender version, machine, git commit, seeds and
  timings → Major.
- A change to `CLAUDE.md`, `docs/glossary.md` terms, or a schema under `schemas/` with no ADR in
  the window → Major.
- Generation and critique sharing one context (a critic or validator that runs in the generator's
  context) → Major.
- Renders or other large binaries committed outside Git LFS → Major.
- Image or video diffusion models introduced anywhere → Critical.

When no spec is available (typically spikes), look for "this can't be what they meant" — code
internally inconsistent or contradicting obvious intent from naming and comments.

**Lens 5 — Refactoring.** *Structural debt whose remedy is a named refactoring* — code whose
**shape** is picking up debt that a specific, well-known refactoring would pay down. Lens 3 asks
"is this locally hard to read / risky?"; Lens 5 asks "is the structure wrong, and does a named
refactoring fix it?"

Match each finding to a smell and its remedy (Fowler, *Refactoring* ch.3), and **name the
refactoring** — if none fits, it is not a Lens 5 finding:

- **Duplicated Code** → extract the shared shape, call it from both.
- **Long Function / Large Class** → Extract Function / Extract Class.
- **Feature Envy** → move the method onto the data it envies.
- **Data Clumps** → Introduce Parameter Object.
- **Primitive Obsession** (e.g. a raw tuple or string standing in for a palette, a shot, a frame
  range) → Replace Primitive with Object.
- **Repeated Switches** → Replace Conditional with Polymorphism, or one shared map.
- **Shotgun Surgery** → gather what changes together into one module.
- **Divergent Change** → split so each module changes for one reason.
- **Speculative Generality** → inline back / delete until a real need shows.
- **Message Chains** → Hide Delegate.
- **Middle Man** → inline it, call the real target.
- **Refused Bequest / Inappropriate Intimacy**, including a **dependency-direction violation**
  (e.g. a style module in `blender/lib/` reaching into harness or production code) → Replace
  Inheritance with Delegation / move features / invert the dependency.
- **Structural test smells** — assertion roulette, mystery guests, mocks of value objects,
  brittle string-match assertions on log lines → restructure the test.

**Constraints:**
1. **Diff-scoped.** Only structural debt the diff *introduced or aggravated*.
2. **Named remedy required.**
3. **Feeds `/bug-fix`'s refactor classification.** Write `**Suggested fix:**` so it maps cleanly
   onto that decision.

**Non-overlap:** unit-scale over-engineering ("is this earning its keep?") is
`/complexity-review`'s job. Pure renames and in-place hygiene are Lens 3's.

#### 3c. Adversarial confidence filter

Before any candidate reaches the report, try to kill it. Spawn an independent subagent
(`subagent_type: general-purpose`) whose only job is to **refute** each candidate. It does not see
which lens raised it or the severity guess — only file, lines, description, and enough
surrounding code to judge. It checks:

- Is this **pre-existing** — not introduced or aggravated by the diff?
- Is it correct/intended behavior that only looks wrong out of context?
- Would **ruff or mypy** (run by `scripts/run_tests.sh`) already catch it? Assume that gate runs
  separately.
- Was it **explicitly deferred** in the run's status note or in `docs/plans/followups.md`?
- Is it **already silenced** in code (`# noqa`, `# type: ignore`, or equivalent)?

The verifier returns `REFUTED` (one-line reason) or `CONFIRMED`. **Drop every `REFUTED` finding
entirely** — not even as a Nit. Above roughly 25 candidates, batch several into one verifier call
rather than one subagent each.

If more than one lens flagged the same issue and both survive, keep them as separate findings
(different `Lens:` values) and note the corroboration in `**Why it matters:**`.

This step runs on every diff.

#### Severity scale

- **Critical** — security hole, data corruption (e.g. a production's locked artifact
  overwritten), a doctrine global ban broken, or guaranteed runtime failure. Must fix before the
  run or milestone closes.
- **Major** — likely failure, a broken determinism or doctrine rule, maintainability debt, or a
  clear functional gap against spec. Debt the diff introduces is never deferred: it is fixed
  before close, like a Critical. Any other Major is fixed before close or deferred by filing it
  with the `defect-filing` skill.
- **Minor** — worth addressing but not blocking. If left unfixed, file it with `defect-filing`.
- **Nit** — style or preference. Mention but don't dwell. Not filed.

A deferred Major or Minor is named `issue #<n>` in the review and in the record of the work that
leaves it. Critical means *block-the-merge* critical; inflated severity produces noisy
`/bug-fix` work.

#### Scope discipline

The review covers the **diff**, not the whole codebase. Pre-existing issues in unchanged code are
out of scope *unless the diff aggravates them* (e.g. adds a fifth caller to an already-bad
function). Ask: "does this tell the engineer something useful about *this* batch of work?" A real
defect dropped this way is not a finding; after the review, file it with `defect-filing`.

A record whose claim the diff *disproves* — a status note, rollout, ADR, or doc sentence the diff
shows is now false — is never "pre-existing, out of scope." Flag it as a finding naming the
record's path so `/bug-fix` can correct it at the source; this skill cannot (Hard constraint 2).

Respect each run's stated scope. If a status note says "implemented X, deliberately deferred Y,"
do not flag Y as missing.

Process artifacts (`docs/plans/`, quest status notes, rollouts) are out of scope.

### Phase 4 — Write the remediation report

The report is markdown only; there is no JSON sidecar. `/bug-fix` parses the markdown directly,
so the schema below is a contract — field names, headings and finding format must match exactly.
Changing them requires changing `/bug-fix` first.

---

## Report schema (contract surface with `/bug-fix`)

Write to the path resolved in Phase 2f.

```markdown
---
review-date: <ISO date>
base-ref: <ref name and sha>
head-ref: HEAD (<sha>)
scope: project | sidequest:<slug>
scope-inferred: true | false
target-location: <path where this report lives>
runs-in-scope:
  - quest: project | sidequest:<slug>
    run: <run-id>
    completion-sha: <sha>
    summary: <one line>
fixes-in-scope:
  - quest: project | sidequest:<slug>
    fix: <fix-plan-slug>
    completion-sha: <sha>
    summary: <one line>
specs-loaded:
  - <path>
verdict: pass | pass-with-minors | needs-fixes | block
counts:
  critical: N
  major: N
  minor: N
  nit: N
flags: []        # SPECS_NOT_DECLARED, BASE_UNRESOLVED, MASSIVE_DIFF, SCOPE_MISMATCH, CROSS_BRANCH_TAG_IGNORED, SINGLE_AGENT_MODE
---

# Code Review — <date>

## Scope

<Two short paragraphs at most: what was reviewed, which runs/fixes, the base ref and why, any
overrides, any flags raised, any scope inference.>

## Runs and fixes in this review

<Bulleted list of runs and fixes with one-liners and paths to their status notes / fix plans.>

## Findings

### Critical

<Finding blocks, or "None.">

### Major

<Finding blocks, or "None.">

### Minor

<Finding blocks, or "None.">

### Nit

<Finding blocks, or "None.">

## Unaccounted Changes

<Commits in the window with no corresponding run or fix: sha, author, date, one-line summary.
If empty, write "None." — don't omit the heading.>

## Spec Conformance

<For each loaded spec, a short note on whether the diff honors it, contradicts it, or leaves it
ambiguous — including the quest's acceptance criteria and the in-window milestone's exit criteria. For
`type: spike` quests, write "N/A — spike (deliverable is findings, not spec conformance)".>

## Recommendation

<One paragraph. Typical patterns:
 - "Run `/bug-fix` against this report. No criticals; the majors are mechanical."
 - "Run `/bug-fix` against this report. Criticals are present and must be addressed before the
    run closes."
 - "Review is incomplete — see flags above. Resolve and rerun `/code-review`."
 - "Nothing to fix. Close the run."
Do not append a manual `git tag -f` command.>
```

### Finding block format (one per finding)

```markdown
### [SEVERITY] <short title>

- **File:** `<repo-relative path>`
- **Lines:** `<start>-<end>` (or `<line>` for a single line, post-change numbering)
- **Lens:** security | reliability | maintainability | functional | refactoring
- **Run:** <run-id or fix-slug, if attributable, else `unaccounted`>
- **Description:** <what's wrong, in 1–3 sentences>
- **Why it matters:** <consequence if unfixed>
- **Suggested fix:** <concrete change; sketch the approach in 3–5 lines if non-trivial>
```

**Order within each group:** by file path, then line number (deterministic for `/bug-fix`).

**Cross-cutting findings.** An issue that spans many files and is not reducible to one
file/line goes under a `## Cross-cutting Issues` section (prose), not a severity group; note in
`## Recommendation` that it needs manual handling rather than mechanical `/bug-fix`.

### Format rules `/bug-fix` relies on

- Frontmatter exists, is valid YAML, and contains every field above.
- Findings appear under exactly four group headings (`### Critical`, `### Major`, `### Minor`,
  `### Nit`), in that order. Empty groups keep the heading and write "None."
- Each finding's bullet labels appear in the exact order and casing above.
- File paths are repo-relative; line ranges use post-change numbering.

---

## Edge cases

- **Empty review window.** Diff empty or only excluded paths: write a one-paragraph "nothing to
  review" report with `verdict: pass` and exit.
- **Massive diff.** Over ~8000 lines or ~80 files: raise `MASSIVE_DIFF` and ask the user whether
  to proceed, narrow the window, or split. Don't refuse — milestone-close reviews legitimately
  span many runs.
- **Merge commits in window.** Review the net diff, not each parent.
- **Scope-inference ambiguity.** Multiple quests look active: fall back to `project` and say so.
- **`spec-refs:` empty but type is not spike.** Raise `SPECS_NOT_DECLARED`, review behavior only,
  and call it out in `## Recommendation`.

---

## Operating rules (the contract with the user)

1. **Read the repo first.** Detect scope, resolve the base, list in-scope runs and fixes, decide
   report placement, and load specs *before* opening any source file.
2. **No surprises.** If the base or scope can't be resolved confidently, changes are unaccounted
   for, or the diff is massive, surface it before the substantive review. The user decides.
3. **Diff-scoped.** Findings tie to changed lines or to unchanged code the diff materially
   affects. No full-repo audits.
4. **Respect explicit deferrals.**
5. **Cite the lens.**
6. **Verify before reporting.** Every candidate passes Phase 3c. Skipping it because a finding
   "looks obviously real" defeats its purpose.
7. **Severity discipline.** Critical means block-the-merge critical.
8. **Don't touch tags.** Tag advancement is `/bug-fix`'s job.
9. **Don't fix anything, and don't render.**

---

## Tools and boundaries

- **Tools:** read-only `git` (`diff`, `log`, `tag -l`, `for-each-ref`, `merge-base`, `show`,
  `rev-parse`); filesystem read across the repo; filesystem write only to the resolved fixes
  location; the Agent tool (`subagent_type: general-purpose`) for the Phase 3a fan-out and the
  Phase 3c filter — read-only in effect.
- **No network required.** Dependency-advisory lookups are nice-to-have; degrade gracefully.
- **Working directory:** repo root. If invoked elsewhere, `cd "$(git rev-parse --show-toplevel)"`.

---

## Pipeline position

| Skill | Reads | Writes | Touches git tags? |
|---|---|---|---|
| `/code-review` | git diff, specs, run status notes, fix plans | remediation report (md) | No |
| `/bug-fix` | remediation report, or a freestanding defect description | fix plan (md) + code changes | Yes — advances `code-review/*` in review-driven mode only |
| `/commit` | working tree | git commit | No |

- The report's frontmatter and finding format are the contract with `/bug-fix`, especially
  `base-ref`, which `/bug-fix`'s tag-advancement step parses.
- `/bug-fix`'s adversarial self-review covers only its own fix; `/code-review` is the broader
  review.
- `/doc-review` judges comment and docstring prose in depth; `/code-review` judges the code.

---

## Worked example

> The user has been working in feature quest `style-ink-line` (a visual style module,
> `parent: none`). Runs `1.2` and `1.3` have status notes since tag
> `code-review/2026-11-02-1a2b3c4`. The user types: "review the runs since the last review."
>
> The skill:
>
> 1. Infers scope `sidequest:style-ink-line` from recent edits under `sidequests/style-ink-line/`.
> 2. Resolves base to `code-review/2026-11-02-1a2b3c4` (an ancestor of HEAD).
> 3. Lists runs `1.2` and `1.3` from `sidequests/style-ink-line/status/` and one fix plan.
> 4. Reads the rollout frontmatter: `type: feature`, `spec-refs:
>    [styles/visual/ink-line/style.yaml, schemas/style_bible.schema.json]`.
> 5. Loads those, the always-loaded set, and `docs/test-strategy.md` (tests changed).
> 6. Computes the diff: five files, ~280 lines, one under `schemas/` — the fan-out runs.
> 7. Spawns five lens subagents in parallel. They return 8 candidates.
> 8. Refutation drops 3 (one pre-existing, one a `# type: ignore` the lens missed, one an
>    exception caught a frame up). 5 survive.
> 9. Writes `sidequests/style-ink-line/fixes/code-review-2026-11-09-9f8e7d6.md` with two Majors
>    (the schema gained a field with no ADR in the window; the module hardcodes line weight
>    instead of reading it from the style bible — flagged by both Functional and Refactoring,
>    noted as corroborated), two Minors and a Nit.
> 10. `## Recommendation`: *"Run `/bug-fix` against this report. No criticals; add the ADR and
>     route line weight through the style bible before the run closes."*
>
> The user runs `/bug-fix` on the report; on green gates it advances the tag. `/commit` records
> the changes, and the next `/code-review` scopes from the new tag.
