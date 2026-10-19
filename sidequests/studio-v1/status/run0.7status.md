# Run 0.7: Integration — smoke, reproducibility, exit gate — status

**Quest:** studio-v1 (feature)  **Date:** 2026-10-19  **Status:** COMPLETE — M1 Laptop evidence received and reviewed 2026-10-19; ADR-0001 Accepted.
**Spec trace:** `sidequests/studio-v1/studio-v1-rollout.md:218-236` (Run 0.7), `:72-80` (M0 header and exit criteria), `:46` (Input Gap "both Macs"), `:48` (M0 Tasks 1–2 done); `docs/project-definition.md:299-325` (§M0 Tasks and Acceptance); `docs/adr/0001-blender-api-baseline.md` Decision and Consequences (tolerance policy; M1 probe); `docs/adr/0002-python-toolchain-and-layout.md:23-25` (gate lanes, scene-script contract); `docs/test-strategy.md` Layers and Rules; `docs/coding-standards.md` STD-001/003/005/006; `CLAUDE.md` §Blender.

## Acceptance Criteria Checklist
- [x] **Smoke and determinism tests pass on this machine (M5 Max Laptop); the status report quotes both runs' frame hashes and manifest paths.** `tests/test_render_smoke.py` (4 tests) and `tests/test_render_determinism.py` (4 tests) pass in the bare gate. The hashes and manifest paths are in "Exit gate evidence" below. They are **provisional**: the tree was dirty (`git_dirty: true`). The post-commit commands below re-capture them.
- [x] **The user runs `scripts/run_tests.sh` on the second Mac; its output and wall time are quoted here (both under "a few minutes").** M1 Laptop, clean tree at `b11b130`: gate run 1 (cold, includes Cycles' Metal kernel compile) exit 0, `real 183.02` s, blender lane 172.33 s; gate run 2 (warm) exit 0, `real 65.53` s, blender lane 63.65 s. Both runs: unit 61 passed, blender 15 passed. See "M1 Laptop evidence" below.
- [x] **"Exit gate evidence" section ready to paste, including M0 Tasks 1–2 (`b24c5bc`, `eaf4bc7`).** Below, with M5 Max Laptop and M1 Laptop rows filled from clean-tree runs. It is pasted into the rollout's `### Exit gate evidence` at `/sidequest close`.
- [x] **`scripts/run_tests.sh` passes.** All lanes ok, exit 0, 46.3 s wall; the blender lane took 43.78 s (output under Test Counts).

## What Changed
- `blender/harness/render.py` — `run_render` now builds `<out>/contact_sheet.png` and writes `<out>/manifest.json` after the render. `main` prints the manifest path and turns `UnknownMachineError` into exit 1 with its message.
- `blender/harness/contact_sheet.py` — adds `EVERY_N = 6`, `COLUMNS = 4` and `FILE_NAME = "contact_sheet.png"`, with a comment citing Run 0.7 decision 2.
- `blender/harness/manifest.py` — adds `load_rgba(path)`, which decodes a frame to 8-bit RGBA and refuses lossy modes. `pixel_sha256` and `compare.py` both use it. Behaviour is unchanged; `tests/test_manifest.py` is green.
- `blender/harness/compare.py` (new) — `compare_runs(out_a, out_b) -> Comparison`, read from both manifests:
  - EEVEE frames must have equal `pixel_sha256`.
  - Cycles frames pass when `max |a−b| <= CYCLES_MAX_ABS_DIFF = 1` (8-bit levels; Pillow decode, numpy int16 diff on the host).
  - It refuses runs that differ in scene, profile, engine, seeds, resolution, samples or frame_count, and refuses an engine that has no policy.
  - The CLI prints a JSON summary and exits 0 on a match, 1 otherwise.
- `tests/test_compare.py` (new, unit, 11 tests) — metadata-only difference, off-by-1 and off-by-2 per engine, CLI verdict and summary, and the refusals.
- `tests/test_render_smoke.py` (new, blender, 4 tests) — `render.py` as a script, preview profile, plain scene, seed 0. It checks 48 frames, a schema-valid manifest with the M0 fields, a 4×2 contact sheet whose sha256 the manifest records, and `wall_s < SMOKE_BUDGET_S = 120`.
- `tests/test_render_determinism.py` (new, blender, 4 tests):
  - EEVEE 48-frame preview with seed 0 ×2: exact match.
  - Seed 1 changes every frame (the negative control).
  - Runs with different seeds are refused.
  - Cycles, a 1-frame wrapper of the plain scene at the final profile ×2: match within 1/255.
  - There is no GPU skip.
- `docs/test-strategy.md` — a one-line exception: the Cycles reproducibility check renders 1 frame at the final profile.
- `sidequests/studio-v1/studio-v1-rollout.md` — Run 0.7 status PARTIAL; criteria 1 and 4 ticked.
- `sidequests/studio-v1/status/carry-forward.md` — 4 lines appended, 7 consumed 0.7 lines folded, and the git_dirty gotcha re-routed to `surface`.

## How to Test
- `scripts/run_tests.sh`, the gate.
- To render and compare by hand, use the "Post-commit M5 evidence" commands below. Open `<out>/contact_sheet.png`: 8 tiles (frames 1, 7, …, 43), 4 columns by 2 rows, with the camera dollying around the boxes.

## Architecture Decisions
All are the user's choices (2026-10-19), from the plan's recommended options:
1. **Cycles determinism in the blender lane.** It renders 1 frame of the plain scene at the final profile, Cycles' only profile. `docs/test-strategy.md` carries the exception. A 48-frame final pair would take about 6 min on the M5.
2. **Contact-sheet constants live in `contact_sheet.py`** (every 6th frame, 4 columns). The followups row for long and final-profile sheets is below, for the parent to apply.
3. **`compare.py` has a CLI** (JSON, exit 0/1), used to get quotable evidence on both Macs.
4. **No GPU skip.** The harness refuses a CPU fallback, so a missing Metal device fails the test.
5. **M5 evidence is re-captured after the commit**, so `git_dirty` reads false.

Also accepted: the wiring sits inside `run_render`, so every render writes a manifest whether it comes from the CLI or code; `SMOKE_BUDGET_S = 120`; and the `load_rgba` refactor.

**Project-level ADR candidate:** none new. The measured Cycles non-identity belongs in ADR-0001's evidence; see the update plan below.

## Open Issues
- not a defect: **Cycles final on Metal is not bit-identical.** Two same-seed 1-frame 1920×1080 renders differed by max 1/255 in 73 of 2,073,600 pixels; an earlier 2-frame scratch pair also showed max 1/255. This is within ADR-0001's tolerance, and it shows the tolerance path is needed in practice. ADR-0001's "measured diff 0" was a 256×256 probe frame.
- not a defect: `tests/test_harness_cli.py::test_final_renders_on_cycles_with_the_metal_gpu` also renders one final-profile frame. It asserts the device, not pixels, so the test-strategy rule ("never assert on…") still holds with the one exception.
- not a defect: final-profile contact sheets are 7680×2160 (4 tiles of 1920×1080 per row). That is acceptable for M0; see the followups row.
- not a defect: `tests/conftest.py` `_blender_bin()` still repeats `render.blender_bin()` (already noted in Run 0.4). The module-scoped fixtures in the new tests call `render.blender_bin()` directly, because a module-scoped fixture cannot take the function-scoped `blender_bin` fixture.

## Exit gate evidence
*(Ready to paste into the rollout's `### Exit gate evidence` at `/sidequest close`. All rows are from clean-tree runs at `b11b130`; the dev-tree M5 block further down is kept only as history.)*

**M0 — Reproducible render.** A scripted scene renders headless and gives the same output on rerun.

| §M0 item | Evidence |
| --- | --- |
| Task 1 — repo skeleton; `docs/project-definition.md` committed; CLAUDE.md names it the source of truth | `b24c5bc` (no run planned; rollout Input Gaps) |
| Task 2 — `CLAUDE.md` v0: Blender version, `bpy.data` over `bpy.ops`, render only through the harness, doctrine changes need an ADR | `b24c5bc`, `eaf4bc7` |
| Task 3 — API probe spike → ADR-0001 | Run 0.3 (`d7b93e8`); M5 Max Laptop and M1 Laptop probes quoted in ADR-0001, now **Accepted** |
| Task 4 — render harness `render.py --scene --profile preview\|final --out` | Run 0.4 (`8e0eee3`); `tests/test_harness_cli.py` |
| Task 5 — plain test scene, 48 frames | Run 0.6 (`5c021e4`); `tests/test_plain_scene.py` |
| Task 6 — manifest writer and contact sheet (every Nth frame on one PNG) | Run 0.5 (`8e0eee3`); wired into every render in Run 0.7 (`b11b130`); `tests/test_render_smoke.py` |
| Task 7 — smoke test runs the preview render | Run 0.7, `tests/test_render_smoke.py` |
| Acceptance 1 — same machine, same seed: EEVEE exact pixel hash, Cycles GPU within tolerance | **M5 Max Laptop:** EEVEE 48/48 frames pixel-equal, max diff 0; Cycles final 1 frame max diff 1/255 (61 px), within ≤ 1/255. **M1 Laptop:** EEVEE 48/48 pixel-equal, max diff 0; Cycles final 1 frame max diff 1/255 (32 px), within ≤ 1/255. `compare.py` exit 0 for all four pairs. (Across machines EEVEE differs — see ADR-0001 Consequences; the criterion is same-machine.) |
| Acceptance 2 — manifest records model ID, Blender version, machine, git commit, seeds, timings | Schema-valid manifests (`schemas/manifest.schema.json`) from every render; asserted by `test_preview_smoke_manifest_is_valid_and_records_m0_fields` |
| Acceptance 3 — smoke test passes on both Macs in a few minutes | **M5 Max Laptop:** whole gate 46–58 s (blender lane 44–58 s). **M1 Laptop:** whole gate 183 s cold (first run, Cycles kernel compile) and 66 s warm. Smoke render: 6–11 s (M5), 7.6 s (M1, EEVEE 48 frames). |

**M5 Max Laptop, dev tree (provisional; HEAD `8e0eee338f181ba590873af9d6ead03bebd561c7`, `git_dirty: true`).** Rendered with the commands in "Post-commit M5 evidence" into the scratchpad `/private/tmp/claude-501/-Users-mpkirby-projects-AIAnimationLab/b8f02529-7e31-4167-a7be-13d2b15adcba/scratchpad/r07evidence/`:

| Run | Manifest | wall_s | Result |
| --- | --- | --- | --- |
| EEVEE preview seed 0, run a | `…/r07evidence/eevee-a/manifest.json` | 5.7 | — |
| EEVEE preview seed 0, run b | `…/r07evidence/eevee-b/manifest.json` | 5.2 | `compare.py` exit 0: 48/48 hash-equal, max_abs_diff 0 |
| Cycles final seed 0, frame 1, run a | `…/r07evidence/cycles-a/manifest.json` | 4.4 | — |
| Cycles final seed 0, frame 1, run b | `…/r07evidence/cycles-b/manifest.json` | 3.4 | `compare.py` exit 0: 0/1 hash-equal, max_abs_diff 1, 73 differing px, tolerance 1 |

Frame hashes (`pixel_sha256`, the same in runs a and b unless shown):
- EEVEE frame 1: `1ed82d480a2ffb937e3ce2254d9eb0fcb2a3d19f4ced81b6abce875448212d2d`
- EEVEE frame 48: `e814ab4f2955fb184e80616b87db0aa1b506d676b3072c2adf32b7feb2e152fa`
- All 48 per frame: `…/r07evidence/compare-eevee.json`
- Cycles frame 1: a `7db1d622180807a9b9c7d010486ec96a0f78b626a6265faca4b78ebe72f99e3a`, b `a7ce8b92392b094acc26c7fafcc6d97456ca5795534b809042ac67376a020ff3`

**M5 Max Laptop, committed tree:** see the clean-tree block below.
**M1 Laptop:** see "M1 Laptop evidence" below.

**M5 Max Laptop, clean tree (re-captured by the parent after `/commit`, 2026-10-19; replaces the provisional M5 rows).** Commands: "Post-commit M5 evidence" below, output under the session scratchpad `aial-r07-evidence/`. Both runs of each pair record `git_commit: b11b130619e89d5d05fabb557a3be2737d901944`, `git_dirty: false`, machine "M5 Max Laptop", Blender 5.2.2 LTS.

| Pair | Profile / engine | Frames | Verdict (`compare.py`, exit 0) | Max abs diff | Differing pixels | Pixel sha256 (run a) |
| --- | --- | --- | --- | --- | --- | --- |
| eevee-a / eevee-b | preview / BLENDER_EEVEE, seed 0 | 48 | match (exact) | 0 | 0 | frame 1 `1ed82d480a2ffb937e3ce2254d9eb0fcb2a3d19f4ced81b6abce875448212d2d`; frame 48 `e814ab4f2955fb184e80616b87db0aa1b506d676b3072c2adf32b7feb2e152fa` |
| cycles-a / cycles-b | final / CYCLES Metal GPU, seed 0 | 1 | match (≤ 1/255) | 1/255 | 61 of 2,073,600 | frame 1 `268bde302a921a9b1509df7bf452b13f3ed0cd4d1d01ac2e0d09a6426945cf5a` |

The EEVEE hashes equal the provisional dev-tree values. Cycles again differs by at most 1/255 (61 pixels this time, 73 before): not bit-identical, within ADR-0001's tolerance. Wall time per render: EEVEE 48 frames 11.0 s, Cycles 1 frame 6.1 s.

## Post-commit M5 evidence (for the parent, after `/commit`)
Run these from a clean tree. The `git status` line must print nothing, so the manifests read `git_dirty: false`. Manifests land in `$E/<run>/manifest.json`.
```
cd /Users/mpkirby/projects/AIAnimationLab
git status --porcelain
E="$TMPDIR/aial-r07-evidence"; rm -rf "$E"; mkdir -p "$E"
cat > "$E/plain_scene_frame1.py" <<EOF
import importlib.util
_spec = importlib.util.spec_from_file_location("_plain_scene", "$PWD/tests/scenes/plain_scene.py")
_plain = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_plain)
FRAME_COUNT = 1
build = _plain.build
EOF
export AIAL_MODEL_ID=fixture/run0.7-evidence
for r in a b; do .toolchain/uv/bin/uv run --locked python blender/harness/render.py --scene tests/scenes/plain_scene.py --profile preview --out "$E/eevee-$r" --seed 0 > "$E/eevee-$r.log" 2>&1; echo "eevee-$r exit $?"; done
for r in a b; do .toolchain/uv/bin/uv run --locked python blender/harness/render.py --scene "$E/plain_scene_frame1.py" --profile final --out "$E/cycles-$r" --seed 0 > "$E/cycles-$r.log" 2>&1; echo "cycles-$r exit $?"; done
.toolchain/uv/bin/uv run --locked python blender/harness/compare.py "$E/eevee-a" "$E/eevee-b" > "$E/compare-eevee.json"; echo "compare eevee exit $?"
.toolchain/uv/bin/uv run --locked python blender/harness/compare.py "$E/cycles-a" "$E/cycles-b" > "$E/compare-cycles.json"; echo "compare cycles exit $?"
echo "$E"
```
Quote both `compare-*.json` files: `matches`, `max_abs_diff`, `runs[].manifest`, `runs[].git_commit`, `runs[].git_dirty`, and the frame 1 and frame 48 hashes. They replace the provisional M5 rows above.

## M1 Laptop: what to run
*(Replaced by the parent, 2026-10-19: the command list became `README.md` §New machine plus `scripts/collect_machine_evidence.sh`.)*

1. Follow `README.md` §New machine (Xcode command-line tools, Homebrew, Blender 5.2.2, clone, `make setup`). The M1 Laptop's `MacBookPro18,2` is already in `MACHINE_LABELS`.
2. On a clean tree in the clone: `scripts/collect_machine_evidence.sh`. It runs doctor, the gate twice (timed, cold and warm), the probe twice (hostname replaced by the machine label), and the EEVEE and Cycles render pairs with `compare.py`.

**Send back:** the `~/aial-evidence-m1-laptop-<time>.tar.gz` it prints (`machine.txt`, `doctor.log`, `run_tests-1/2.log`, `probe-run1/2.json`, `renders/*/manifest.json`, `renders/compare-*.json`, `exits.txt`; no frames).

## M1 Laptop evidence (received 2026-10-19)
The user ran the collection on the M1 Laptop and sent `aial-m1-evidence-20261019-141723.tar.gz`. The parent extracted it into an empty scratchpad folder and read it as data (nothing executed).

- **Machine:** `hw.model` `MacBookPro18,2` → label "M1 Laptop"; Apple M1 Max, arm64, 64 GB, macOS 26.6.2; Blender 5.2.2 LTS (hash `d13f752e3b9c`); HEAD `b11b130619e89d5d05fabb557a3be2737d901944`, `git status --porcelain` empty.
- **`make doctor`:** all checks pass (uv 0.12.24, just 1.53.0, Python 3.13.13 uv-managed, Blender 5.2.2, bundled Python 3.13.13, ffmpeg 9.0.2, shellcheck 0.11.0).
- **Exit codes:** doctor, gate 1, gate 2, probe 1, probe 2, eevee-a/b, cycles-a/b, compare eevee, compare cycles — all 0.
- **Gate:** run 1 `real 183.02` (blender lane `15 passed … in 172.33s`); run 2 `real 65.53` (blender lane `15 passed … in 63.65s`); unit `61 passed` both times.
- **Probe (×2):** engines `BLENDER_EEVEE`, `BLENDER_WORKBENCH`, `CYCLES`; Cycles `METAL`, device "Apple M1 Max (GPU - 32 cores)"; EEVEE pixel_sha256 `ea34063d…3ead4b68` and Cycles `f07c4402…1a86deba`, each equal across all four renders, max diff 0. Quoted in ADR-0001.
- **Harness pairs** (both manifests `git_dirty: false`, machine "M1 Laptop"): EEVEE preview 48 frames, `matches: true`, max diff 0, frame 1 `814a99dae2cca6ed33015e00ecb811c9ee785468968aa440232bad75be77e0eb`, frame 48 `d16bf83016ba53dfb9aa4cb33fe88ca7486725fac189d654e69d96e803c39a1b`; Cycles final 1 frame on "Apple M1 Max (GPU - 32 cores)", `matches: true`, max diff 1/255 in 32 pixels, frame 1 (run a) `d9555b6c611b2422483a80940514560cf3d278588952396c8dad03b66b109cd7`.
- **No hostname** in any file; the probe's `hostname` field reads "M1 Laptop".
- **Finding:** EEVEE pixels for the same scene and seed differ between the two Macs (frame 1 `814a99…` here vs `1ed82d…` on the M5 Max Laptop; probe `ea3406…` vs `d7e06e…`), while the 256×256 Cycles probe frame matched across Macs. Recorded in ADR-0001 Consequences: reproducibility is per machine.

## Proposed changes to referenced persistent specs (for `/sidequest close`)
`docs/project-definition.md` §M0 (Tasks `:305-315`, Acceptance `:319-321`): tick all seven Tasks and all three Acceptance boxes, `- [ ]` → `- [x]`; the M1 evidence has passed. Not edited in this run.

## Shared-file edits for the parent to apply
1. **`docs/plans/followups.md`: add a row.** *(Applied by the parent, 2026-10-19.)* Contact sheets for long productions and the final profile: `blender/harness/contact_sheet.py` fixes `EVERY_N = 6` and `COLUMNS = 4` at native tile size. A 2,400-frame production would tile 400 frames, and a final-profile sheet is 7680×2160 for 4 tiles. Scale `every_n` to frame count, or downscale tiles. **Revisit trigger:** `production.yaml` lands, or the first render over 48 frames.
2. **`docs/adr/0001-blender-api-baseline.md`, when the M1 evidence arrives.** *(Applied by the parent, 2026-10-19: both checks passed; ADR-0001 Accepted, with the M1 subsection, the harness-level evidence and a per-machine reproducibility consequence; README row updated.)*
   - **If** both M1 probe runs show EEVEE `pixel_hash_equal: true` and Cycles `max_abs_diff_255 <= 1`, **and** the M1 `compare-*.json` both report `matches: true`:
     - set frontmatter `status: Accepted`;
     - rewrite §Status to "Accepted <date> after the M1 Laptop probe (Run 0.7)", dropping the review trigger and expiry;
     - add an "M1 Laptop" evidence subsection: machine facts, the probe command, the determinism table, and run-1 JSON verbatim with `hostname` replaced by "M1 Laptop";
     - add a "Harness-level evidence (Run 0.7)" paragraph: EEVEE 48-frame preview is exact on both Macs; Cycles final 1920×1080 on the M5 differs by up to 1/255 (73 px), so the tolerance is exercised, not hypothetical (both Macs' compare figures quoted);
     - update the ADR row in `docs/adr/README.md` to Accepted.
   - **If either check fails:** do not accept. ADR-0001's Consequences send it to the tolerance path for both engines, which needs an amendment to §M0 Acceptance. Stop and bring options to the user.
3. *(Applied by the parent, 2026-10-19, except pasting into the rollout's Deliverable, which waits for `/sidequest close`.)* **After ADR-0001 is Accepted:** fold the ledger line `[0.3] -> 0.7 | deferred | Rerun … on the M1 Laptop` to `~ M1 probe: deferred 0.3, landed 0.7 (ADR-0001 Accepted)`. Mark Run 0.7 COMPLETE in the rollout, tick criteria 2–3, and paste "Exit gate evidence" into the rollout's `### Exit gate evidence`.

## Carry-forward
```
- [0.7] -> quest | contract | render.run_render itself writes <out>/contact_sheet.png and <out>/manifest.json; callers never call write_manifest/build_contact_sheet directly.
- [0.7] -> quest | contract | Reproducibility = blender/harness/compare.py compare_runs(out_a, out_b) or its CLI (JSON, exit 0 = match); refuses runs differing in scene/profile/engine/seeds/resolution/samples.
- [0.7] -> surface | gotcha | Cycles final on Metal is not bit-identical: a same-seed 1080p frame differed by 1/255 in 73 px (M5 Max). Never assert Cycles by hash; use compare.py.
- [0.7] -> quest | decision | Only the 1-frame Cycles determinism check asserts on final-profile pixels in the default lane (docs/test-strategy.md); other pixel assertions use preview.
```
Folded the 7 consumed `-> 0.7` lines. Kept `[0.3] -> 0.7 | deferred` (M1 probe) live until the M1 evidence lands. Re-routed `[0.5] git_dirty` from `0.7` to `surface`.

## Test Counts
`/usr/bin/time -p scripts/run_tests.sh` (exit 0). Blender's per-frame render lines are omitted; the full log was in the scratchpad `gate.log`:
```
=== lane: environment
  ok    uv 0.12.24
  ok    just 1.53.0
  ok    Python 3.13.13 (uv-managed: …)
  ok    Blender 5.2.2
  ok    Blender's bundled Python 3.13.13 = .python-version
  ok    ffmpeg: ffmpeg version 9.0.2 …
  ok    shellcheck: 0.11.0
doctor: all checks pass.
=== lane: environment — ok
=== lane: locks — ok
=== lane: static
All checks passed!
41 files already formatted
Success: no issues found in 20 source files
=== lane: static — ok
=== lane: unit
tests/test_compare.py ...........
tests/test_contact_sheet.py ......
tests/test_harness_cli.py .............
tests/test_manifest.py ...........................
tests/test_toolchain_pins.py ....
====================== 61 passed, 15 deselected in 1.06s =======================
=== lane: unit — ok
=== lane: blender
tests/test_harness_cli.py ...
tests/test_plain_scene.py ...
tests/test_render_determinism.py ....
tests/test_render_smoke.py ....
tests/test_toolchain_pins.py .
====================== 15 passed, 61 deselected in 43.78s ======================
=== lane: blender — ok
=== run_tests.sh: all lanes ok (environment locks static unit blender)
real 46.32
```
- **Unit:** 61 passed (11 new).
- **Blender:** 15 passed (8 new), 0 skipped.
- **Blender lane:** 43.78 s; the whole gate 46.3 s on the M5 Max Laptop.

## Confidence Report
- **A. Assumptions made.**
  - The M1 Laptop's `hw.model` is `MacBookPro18,2` (Run 0.5's map). If it isn't, every harness render there fails with "add a row", and the M1 list checks this first.
  - M1 timings are not measured. My estimate is 3–5× the M5, plus a one-time Cycles kernel compile; that is why the gate runs twice.
- **B. Deviations from existing patterns.**
  - The rollout said "Cycles check … skipped with reason if no GPU". By user decision 4 there is no skip.
  - The Cycles check renders 1 frame, not the 48-frame test scene (decision 1).
- **C. Thin context.** No spec owns contact-sheet layout or the smoke time budget. Both are now Run 0.7 decisions recorded in code comments.
- **D. Conflicts found.** test-strategy's "never assert on a full-resolution final render in the default lane" against the Cycles tolerance check. Resolved by user decision 1A, with a one-line exception.
- **E. Complexity concentrations.** `compare.compare_runs` holds the field-equality refusals, the per-engine policy and the decode. It is about 40 lines and covered by 11 unit tests.

## Next Unblocked Run
M0's exit gate evidence is complete (this report). Milestone 1 can start: Run 1.1 (artifact schemas and schema IO) and Run 1.2 (style-module contract) are both unblocked and can run in parallel. Run 1.3/1.4 need the user to name the two contrasting styles first (rollout Input Gaps).
