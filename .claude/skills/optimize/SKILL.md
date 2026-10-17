---
name: optimize
description: >
  Autonomous optimization search loop: iteratively improves render wall time, preview-loop time
  or test-suite time on a disposable git branch under anti-overfitting guardrails — including a
  visual-output guard (frame hashes / contact sheets must not change unless declared) — until a
  threshold is reached. Use for "make renders faster", "speed up the preview loop", "speed up the
  tests", "performance search loop", "tune until threshold", or /optimize. Never pushes, merges,
  or touches your working branch.
---

# Skill: Optimize (Autonomous Search Loop)

The agent establishes a statistical baseline (timing *and* visual output), then runs a
mutate → measure → judge loop on a disposable branch, with guardrails against overfitting,
regressions and silent changes to what the film looks like. Output is a deductive status report
under the active quest's `status/` directory plus a branch the user can review and cherry-pick from.

This skill is a **safety harness around an LLM that wants to "make it faster"**. Without
guardrails, performance-mutating LLMs routinely:
- hollow out the work — delete validation or caches, or for renders quietly drop samples,
  resolution, frames, shadows, line art or motion blur ("it renders faster" because it renders less);
- overfit to the fixture — specialize for the 48-frame test scene or the one shot being timed;
- break determinism — the M0 reproducibility gate and every experiment depend on it;
- claim improvements inside measurement noise (laptop thermals, shader compilation);
- leave the user's working branch half-mutated after a dead end.

Every section below serves one of those failure modes.

## Sub-actions

| User intent | Sub-action |
|---|---|
| `/optimize goal <metric> limit <iterations\|time> test <command>` | **Start** |
| `/optimize status` | **Status** |

`/optimize` with no arguments → ask for `goal`, `limit`, and `test`. Don't guess — those three are the contract.

## Scope and paths

Status lives under the active quest:
`sidequests/<slug>/status/`. "for sidequest \<slug\>" / "in sidequest \<slug\>" selects the quest
explicitly; otherwise use the active quest and state the inference. Every quest (spike, utility,
feature) lives in `sidequests/<slug>/`; if no quest is active, ask which one this work
advances rather than inventing a location.

| Artifact | Path |
|---|---|
| Status report | `sidequests/<slug>/status/optimize-<metric>-<ts>.md` |
| Search journal | `sidequests/<slug>/status/optimize-<metric>-<ts>.journal.md` |
| Witness (text) | `sidequests/<slug>/status/optimize-<metric>-<ts>-witness/` — timing logs, profiler output, frame-hash lists, manifests |
| Witness (renders) | a scratch directory **outside git** (renders and contact sheets are never committed); the journal records each path plus its hash |

`<ts>` is `YYYYMMDD-HHMMSS` at loop start. `<metric>` is a kebab-case slug (`render-frame-time`,
`preview-loop-time`, `test-suite-time`).

## Contract: what the user must give you

1. **`goal <metric>`** — resolve to a concrete extraction:
   - `render time`, `frame time` → mean per-frame render wall time from the harness `manifest.json`
     timings, for a named scene and profile (`preview` or `final`).
   - `preview loop` → wall time of one full preview iteration: `blender/harness/render.py --scene
     <script> --profile preview --out <dir>` through contact-sheet output.
   - `test time`, `suite time` → wall time of `scripts/run_tests.sh`.
   - Anything else → ask how to extract one number. Don't guess.
2. **`limit <iterations|time>`** — `30 iterations`, `2h`; whichever hits first wins.
3. **`test <command>`** — run every iteration; self-contained, idempotent, emits the number.
   Render measurements go through the harness only — never ad-hoc render operators. Agree the
   parse logic **before** the baseline; it must not change mid-loop.
4. **Visual contract** (required when the goal is a render or preview metric; for test-suite time
   the equivalent is "same tests, same outcomes"):
   - the **reference scene(s)** and profile whose output is the guard;
   - the **comparison rule**: exact frame hashes for EEVEE; a stated per-pixel tolerance for
     Cycles on GPU;
   - any **declared intended visual change** (e.g. "the preview profile may drop to half
     resolution"). Declared up front, in writing, before the baseline. Anything not declared is
     unintended. The declaration cannot be widened mid-loop.

## Start

### Phase 0 — Pre-flight

1. Working tree clean (committed or stashed). If not, stop.
2. Record `<source-branch>`.
3. `git checkout -b optimize/<slug>-<ts>`.
4. Create the witness directories and an empty journal.
5. Dry-run the test command once. If it fails, stop — there's no signal.
6. Record the machine and Blender version. **Never switch machines mid-loop**; the M5 Max and the
   M1 are different baselines.

### Phase 1 — Baseline establishment

Run the test command **3 times back-to-back**, with cleanup between each. Compute
`baseline_mean`, `baseline_stddev`, `baseline_cv = stddev / mean`.

**Refuse to enter the loop if `baseline_cv > 0.15`.** Report the variance and ask for a stabler
test or a larger N (common causes: thermal throttling, shader compilation on first run, background
load). Never proceed with a wider tolerance.

**Visual baseline.** Render the reference scene(s) through the harness and record the frame
hashes (or tolerance-reference frames) and the contact sheet. Render twice: if the baseline does
not reproduce itself, stop — the guard is meaningless and the M0 reproducibility gate is already
failing; route that to `/bug-fix`. For test-suite time, record the collected test IDs and outcomes.

Write `## Baseline` to the journal: 3 raw values, mean, stddev, CV, machine, Blender version,
seeds, frame-hash list path, contact-sheet path.

### Phase 2 — Mutation loop

For each iteration `i`:

1. **Profile / hypothesize.** Read available profiling (`cProfile`, per-stage manifest timings,
   Blender's render stats, the prior iteration's hot path) and write **one** hypothesis naming a
   mechanism into the journal **before** mutating. "Scene build dominates: 40 materials are
   rebuilt per frame in `blender/lib/shaders/` — build once and reuse" is good; "make it faster" is not.
2. **Mutate.** One mechanism per iteration. Multiple changes destroy attribution.
3. **Cleanup.** Run the agreed cleanup (clear the scratch render output, any frame/bake caches,
   temp `.blend` files). Iteration `i` must not benefit from `i-1`'s state. If the test command
   lacks a cleanup, ask the user what it is before measuring. Agree up front whether shader
   compilation is measured warm or cold.
4. **Measure.** Run the test command 3 times. Compute `iter_mean`, `iter_stddev`.
5. **Judge.**
   - **Regression** (worse than `best_so_far_mean` by > 1×`baseline_stddev`):
     `git reset --hard <best_so_far_commit>`; log `verdict: regression`.
   - **Noise** (within ±1×`baseline_stddev`): reset; log `verdict: noise`. Don't promote noise.
   - **Improvement** (better by > 1×`baseline_stddev`): run **Phase 3** before promoting. If it
     passes, commit atomically on the optimize branch and update `best_so_far_*`; log
     `verdict: improvement` with the trade-off line.
6. **Witness.** Save raw measurement output as `iter-<i>-<verdict>.<ext>` and reference it. No
   witness, no claim — the iteration does not count.

Journal row:
```
| iter | hypothesis | diff (1-line) | mean | stddev | Δ vs baseline | Δ vs best | visual | verdict | witness | trade-off |
```

### Phase 3 — Self-assessment guardrail (before promoting any improvement)

The agent is judging its own work, so the rules are explicit.

1. **Visual-output check — "does the film still look the same?"** Re-render the reference
   scene(s) through the harness and compare with the Phase 1 visual baseline using the agreed rule.
   - Any difference not covered by the declared intended change → **reject**: reset, log
     `verdict: visual-change` with which frames differ, continue.
   - A declared intended change → allowed, but save the new contact sheet beside the baseline one
     and list both in the report for the user's eye.
   - Run the reproducibility check on the mutated code too (render twice, same seed). A change that
     makes output vary between reruns → **reject** as `verdict: nondeterministic`, even if faster.
   - For test-suite time: same test IDs collected, same outcomes. A test removed, skipped,
     `xfail`-ed, de-parametrized, or moved out of the canonical runner → reject as `hollowed-out`.
2. **Cross-validation — "did we hollow out the work?"** Read the diff. Reject (`verdict:
   hollowed-out`) if it:
   - removes validation, schema checks, `None` guards or error handling at a boundary
     (filesystem, subprocess, Blender launch);
   - lowers render quality settings (samples, resolution, frame range, light bounces, shadow/AO,
     line art, motion blur) or switches engine — unless that exact change was declared;
   - removes a cache or short-circuit that guarded edge cases, or adds a cache that leaks across
     runs or stages (breaks stage isolation: each stage reads only upstream artifacts);
   - stops writing a manifest field, a seed, or a contact sheet;
   - bypasses the harness, or swaps `bpy.data` for context-dependent `bpy.ops`;
   - narrows a contract (e.g. only the test scene's aspect ratio or fps works).
3. **Trade-off analysis — required, no exceptions.** State exactly what was traded, e.g.
   "preview loop ↓35% at cost of reusing one material per style module (materials are now shared
   datablocks)"; "suite time ↓40% at cost of one fewer Blender launch — two smoke tests now share a
   session". No articulable trade-off → reject as `verdict: unexplained`; you can't write the
   deductive summary later if you don't understand the mechanism now.
4. **Generalization check — "is this fixture-coupled?"** If the change exploits the test scene or
   the timed shot (hardcoded frame counts or object counts, skipping work only that scene lacks,
   tuning to its resolution), flag `Candidate for Overfitting` and **stop the loop**. Ask for a
   broader reference set (e.g. a second scene or a second style module) before continuing.

### Phase 4 — Termination

Stop on **any** of:
- `limit` reached.
- Last 3 promoted improvements each < 0.1% over the prior best (asymptote).
- Self-assessment flagged unrecoverable overfitting.
- Measurements became noisy (CV > 0.15 on a re-baseline of `best_so_far`).
- The visual baseline stopped reproducing itself.
- More than 50% of the last 10 iterations were reverted.

Write the Final Status Report and leave the optimize branch intact. **Never delete it.** Print
the branch name prominently.

### Phase 5 — Final status report

```markdown
# Optimize: <metric> — <ts>
**Source branch:** <source-branch>
**Optimize branch:** optimize/<slug>-<ts>   ← winning code lives here
**Quest:** <slug>
**Machine / Blender:** <machine> / <version>
**Iterations:** <n_run> / <limit>   (promoted: <n_promoted>, reverted: <n_reverted>)
**Termination reason:** <a Phase 4 condition>

---

## Headline result
- Baseline: <mean> ± <stddev> (<unit>)
- Best-So-Far: <mean> ± <stddev> (<unit>)
- Δ: <pct>%   (<absolute>)

## Visual-output guard
- Reference scene(s) / profile / comparison rule: <...>
- Declared intended changes: <none | the declaration verbatim>
- Result at best-so-far: <frame hashes identical | within tolerance | declared change — contact sheets: <baseline path>, <new path>>
- Reproducibility re-check at best-so-far: <pass | fail>

## Optimization technique(s) selected
<each technique in best-so-far, with iteration number>

## Deductive summary — *why* the winning change worked
<The mechanism, specific enough that another engineer could re-derive it. If you cannot write
this, the change should not have been promoted — revert.>

## Adversarial review results
<Everything self-assessment flagged: visual changes, nondeterminism, hollowed-out diffs,
candidate overfits, borderline trade-offs — with iteration numbers and resolution.>

## Failed experiments — what did NOT pan out
<Per notable rejected hypothesis: hypothesis, 1–2 line diff, measured result, why it didn't work.
The most valuable section for the next loop.>

## Trade-offs accepted
<one bullet per promoted iteration>

## Witness artifacts
<paths, one bullet per promoted iteration; render paths are outside git>

## Reproduction
- Source branch `<source-branch>` at `<sha>`; optimize branch at `<sha>`
- Test command: `<exact>`; cleanup: `<exact>`
- N per measurement: 3; variance threshold: CV ≤ 0.15

## Recommendation
<cherry-pick as-is | cherry-pick iterations <a,b,c> only | discard — gains inside noise |
discard — overfitting flagged | needs broader reference set before adoption>
```

Keep the journal beside the report — it is the audit trail.

---

## Status

`/optimize status`: find the latest `optimize-*.journal.md` under the active quest's `status/`
whose final row is not a termination row. If none is running, print the latest completed report's
headline. Otherwise:

```
Optimize <metric> — running
Branch:           optimize/<slug>-<ts>
Iterations:       <i> / <limit>   (promoted: <p>, reverted: <r>, hollowed-out: <h>, visual-change: <v>)
Baseline:         <mean> ± <stddev>
Best-So-Far:      <mean> ± <stddev>
Δ vs baseline:    <pct>%   (<absolute>)
Last 3 deltas:    <i-2: ±x%>, <i-1: ±y%>, <i: ±z%>
Last verdict:     <improvement|noise|regression|hollowed-out|visual-change|nondeterministic|unexplained>
Asymptote check:  <true|false>
```

---

## Constraints

- **Never push. Never merge** to `main` or the source branch. Never modify or auto-commit on the source branch.
- **Never change visual output silently.** Undeclared frame-hash or contact-sheet change = reject.
- **Never trade away determinism** for speed.
- **Never commit renders, frames or contact sheets.** Text witnesses only; render witnesses live outside git, referenced by path and hash.
- **Render only through the harness.**
- **Never widen the variance threshold** or the declared visual change mid-loop.
- **Never promote without a witness file**, and **never promote a change you can't explain**.

## Anti-Patterns

```
// WRONG: "dropped samples from 128 to 32 and it's 4x faster"
//   Undeclared quality cut. The contact sheet changed. verdict: visual-change.

// WRONG: "the hashes differ only slightly, close enough"
//   EEVEE frames are compared exactly. Tolerance applies only to Cycles GPU, and only
//   the tolerance agreed before the baseline.

// WRONG: "cached the built scene in /tmp so the next stage loads it instantly"
//   Cross-run/cross-stage cache: breaks cleanup and stage isolation.

// WRONG: "skipped the slow smoke render to speed up the suite"
//   Hollowed-out test suite. Same test IDs, same outcomes.

// WRONG: "the test scene has 48 frames, so I precompute 48 keyframes"
//   Overfitting. Stop; ask for a broader reference set.

// WRONG: "it got faster but I don't know why"
//   Unexplained. Revert.

// WRONG: baseline on the M5 Max, iteration 7 on the M1
//   Different machines are different baselines.

// WRONG: three optimizations in one iteration; writing the report only on success;
//   deleting the optimize branch; running on a dirty tree; no cleanup between iterations.
```

## Critical Adoption Review

- [ ] Working tree clean before `git checkout -b optimize/<slug>-<ts>`
- [ ] Baseline: 3 runs, CV ≤ 0.15, one machine recorded
- [ ] Visual contract (reference scenes, comparison rule, declared changes) written before the baseline; visual baseline reproduced itself
- [ ] Every iteration has a hypothesis written **before** the mutation
- [ ] Cleanup ran before every measurement
- [ ] Every promoted iteration passed the visual check and reproducibility re-check, and has a trade-off line, witness and mechanism
- [ ] Termination triggered by an explicit Phase 4 condition
- [ ] Final report has Visual-output guard, Deductive summary, failed experiments, Recommendation
- [ ] Optimize branch unpushed, unmerged, named in the report
- [ ] No renders committed
