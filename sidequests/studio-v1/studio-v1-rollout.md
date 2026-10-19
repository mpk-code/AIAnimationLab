---
parent: none
type: feature
triggered-by: docs/project-definition.md §Milestones (M0–M5); doctrine and dev-skills scaffold landed (eaf4bc7)
purpose: Build studio v1 — a production system that turns a seed idea into a finished Blender-rendered short through staged, human-gated decisions — and run experiments E1–E5 on it.
deliverable: Exit-gate evidence for every milestone — reproducible render (M0), style survives (M1), baseline ready (M2), knobs proven (M3), first full short (M4), H1–H3 accepted or rejected with the evidence (M5).
spec-refs:
  - docs/project-definition.md
  - docs/adr/0001-blender-api-baseline.md
  - docs/glossary.md
  - CLAUDE.md
  - schemas/
  - styles/
  - docs/adr/
status: active
integrated: false
opened: 2026-10-19
---

# Quest: studio-v1

## Context

This quest delivers the scope of `docs/project-definition.md`. Its rollout's milestones are that document's M0–M5, so run IDs are `0.1`, `0.2`, … for M0, `1.1`, … for M1, and so on. It was opened once the doctrine (`CLAUDE.md`, glossary, quest convention) and the dev-process skills had landed.

| Phase | Scope | Exit gate |
| --- | --- | --- |
| M0 Foundation | Repo, `CLAUDE.md`, glossary, headless render harness, manifest. Spike: probe the installed Blender API. | **Reproducible render:** a scripted scene renders headless, with the same output on rerun |
| M1 Vertical slice: style bible to animatic | Stages 3 and 4 with two contrasting style modules. First validators: palette, camera grammar. | **Style survives:** renders pass style-bible validators for both styles |
| M2 Baseline and evaluation harness | One-shot baseline on the same harness and library. Rater protocol and diversity metrics, fixed in advance. | **Baseline ready:** E1 protocol runs end to end on pilot seeds |
| M3 Story stages | Stages 0 to 2, constraint decks, anti-default lists. Critic subagent for premise and beats. | **Knobs proven:** every story knob moves the output in a sweep (E2) |
| M4 Full production | Stages 5 to 8 and a larger style-module library. Preview and final render profiles. | **First full short:** seed to finished film with human input only at gates |
| M5 Experiments | Run E1 to E5 and feed findings back into skills. Grow anti-default lists from rater feedback. | **Results:** H1 to H3 accepted or rejected with the evidence |

Each milestone must pass its gate before the next begins. Blender API probes may spawn spike quests, and new style modules may run as parallel feature quests from M1 onward (`parent: studio-v1`).

## Input Gaps

- **`spec-refs:` was narrower than the persistent paths this quest changes** — resolved 2026-10-19: the user added `schemas/`, `styles/` and `docs/adr/`. Runs also touch `skills/`, `decks/`, `antidefaults/` and `docs/coding-standards.md`; those stay under each run's **Files/Modules** only.
- **Host-side Python package layout is not in §Repository structure.** Draws, gates, schema IO and the stage runner need a home that is neither Blender-side nor a data directory. Assumption: a top-level `studio/` package for host-side orchestration; `validators/` and `eval/` are their own packages; `blender/` holds Blender-side code plus the host-side harness CLI. Run 0.2 records this in `docs/adr/0002-python-toolchain-and-layout.md`. — Resolve by approving or amending ADR-0002 in Run 0.2.
- **Git LFS is not installed and there is no `.gitattributes`.** Assumption: renders, frames and contact sheets stay out of git (written under gitignored output dirs or test tmp dirs); manifests reference them by path and sha256. `.gitignore` does not ignore `*.png` globally, so harness output dirs must be under ignored paths. — Resolve by deciding whether contact sheets (small PNGs) should be committed via LFS as review evidence. Deferred 2026-10-19 (Run 0.1): `docs/plans/followups.md` "Git LFS" row.
- **The harness cannot detect the model ID.** Assumption: `render.py` takes a required `--model-id` (fallback env `AIAL_MODEL_ID`) and fails if neither is set — no silent default. — Resolve by confirming the mechanism in Run 0.5. Resolved 2026-10-19 (Run 0.5): confirmed — required `--model-id`, fallback env `AIAL_MODEL_ID`, fail if neither; fixture renders pass `fixture/<test-name>`.
- **"Smoke test passes on both Macs"** needs the M1 Mac. Assumption: the user runs Run 0.7's evidence commands on the second machine and pastes the result. — Resolve by scheduling access to both machines for Run 0.7.
- **The two contrasting M1 styles are creative decisions not yet made.** Assumption: style A follows the project definition's `visual/cut-paper` sketch (toon ramp + ink line); style B is chosen at Run 1.4 pre-flight to contrast on every validated axis (palette family, shading model, no line, different camera grammar). — Resolve by the user naming style B (and confirming A) before Runs 1.3/1.4.
- **M1 stage 4 needs `beats.yaml`, but stage 2 is built in M3.** Assumption: Run 1.1 formalizes `schemas/beats.schema.json` now and M1 uses hand-written beat fixtures under `tests/fixtures/`. Changing that schema in M3 then needs an ADR. — Resolve by accepting the early beats schema.
- **M2's exit gate ("E1 protocol runs end to end on pilot seeds") precedes the story stages.** Assumption: the pilot's pipeline arm is the M1 slice fed hand-written premise/beats fixtures; the full pipeline arm arrives in M5. — Resolve by confirming this reading of the gate.
- **Baseline invocation and embedding models are unspecified.** Assumption: the one-shot baseline runs via non-interactive `claude -p` with a fixed prompt file and pinned model; text and keyframe embeddings use local, version-pinned models (e.g. sentence-transformers, open_clip) recorded in the manifest. — Resolve in Run 2.1's protocol.
- **Open questions in `docs/project-definition.md` gate later milestones:** raters (M2, M5), whether narration leads picture (before Run 3.1/4.1 schemas settle), the Blender pin (before E1 — `docs/plans/followups.md`), render-hardware split (M4/M5), and E5's compute cost (100 productions). Assumption: each is raised at the pre-flight of the first run that depends on it. — Resolve by answering them before the runs named.
- **The cross-production catalog (§System concept) is in no milestone's scope row**, yet E5 needs it. Assumption: Run 5.6 builds it. — Resolve by confirming or moving it earlier.
- **M0 tasks 1–2 are already done** (repo skeleton, `docs/project-definition.md` committed, `CLAUDE.md` v0 with Blender version, `bpy.data` rule, harness rule and ADR rule — commits `b24c5bc`, `eaf4bc7`). No runs are planned for them; Run 0.7 cites them in the exit-gate evidence.

## Plan overview

Each milestone passes its exit gate before the next begins (`docs/project-definition.md` §Milestones). Style-module side quests (`parent: studio-v1`) may run in parallel from M1 onward.

```
M0 Foundation ──gate: reproducible render──▶ M1 Style bible → animatic ──gate: style survives──▶
M2 Baseline + eval harness ──gate: baseline ready──▶ M3 Story stages ──gate: knobs proven──▶
M4 Full production ──gate: first full short──▶ M5 Experiments ──gate: H1–H3 results──▶ close

                     ┌─ style-module side quests (parallel, parent: studio-v1) ─┐
                     M1 ─────────────────────────────────────────────────────── M5
Infrastructure reuse: harness + manifest (M0) → schemas, validators, gates (M1) → metrics,
rater tooling (M2) → sweep harness (M3) → pipeline runner (M4) → experiments (M5)
```

## Carry-forward ledger

Routed cross-run handoffs for this quest accumulate in `sidequests/studio-v1/status/carry-forward.md`.
`/run-process` reads it at pre-flight and appends at post-flight. Routed items only.

## Milestone 0: Foundation

**Theme:** a scripted scene renders headless through one harness, writes a manifest, and reproduces on rerun.
**Testable capability:** `blender/harness/render.py --scene tests/scenes/plain_scene.py --profile preview --out <dir> --model-id <id>` renders 48 frames, a contact sheet and a schema-valid `manifest.json`; a second run matches.
**Session estimate:** 7 sessions
**Entry criteria:** repo skeleton and `CLAUDE.md` v0 committed (done); Blender 5.2.2 installed at `/Applications/Blender.app`; Homebrew present.
**Exit criteria / Definition of Done:** §M0 Acceptance in `docs/project-definition.md` — same-seed reruns match (EEVEE exact frame hash; Cycles GPU within per-pixel tolerance); the manifest records model ID, Blender version, machine, git commit, seeds and timings; the smoke test passes on both Macs in a few minutes. ADR-0001 records the API baseline.
**Testing strategy:** unit (manifest writer, contact sheet, schema); Blender integration (`@pytest.mark.blender`, scene builds in background mode); render smoke (preview profile); determinism (EEVEE exact sha256; Cycles tolerance). Infrastructure built here: the pinned toolchain bootstrap (`make setup` / `make worktree-init` / `make doctor`), `scripts/run_tests.sh`, `tests/conftest.py` Blender marker and binary discovery.
**Key risks:** host Python drifting from Blender's bundled Python (3.13.13 on 5.2.2) — code that passes host tests fails inside Blender; EEVEE on Metal may not be bit-identical across runs (would force the tolerance path for both engines and an amendment to §M0 Acceptance); `bpy.ops.render` is unavoidable and context-sensitive in background mode; mypy against `bpy` without stubs.

### Dependency graph

```
├── Run 0.1: pinned toolchain bootstrap (make setup / worktree-init / doctor)   ──┐
│         ↓                                                                       │
├── Run 0.2: test runner, pyproject + uv.lock, ADR-0002 layout + scene contract  ─┤ (contract-first)
├── Run 0.3: Blender API probe spike → ADR-0001 (NOVEL-TECH)                     ─┤ (parallel with 0.1, 0.2)
│         ↓                                                                       │
├── Run 0.4: harness runner (render.py + in-Blender entry, profiles)            ─┤ (after 0.2; consumes 0.3 engine IDs)
├── Run 0.5: manifest schema + writer + contact sheet                            ─┤ (after 0.2)
├── Run 0.6: plain test scene                                                    ─┘ (after 0.2)
│         ↓
└── Run 0.7: integration — smoke + reproducibility tests, exit-gate evidence (after 0.3–0.6)
```

### Run 0.1: Pinned toolchain bootstrap

- **Status:** COMPLETE 2026-10-19 — `sidequests/studio-v1/status/run0.1status.md`
- **Summary:** Port a slim version of docketScore's bootstrap model (`~/projects/docketSCore`: `Makefile` `setup` / `worktree-init` / `tooling-bootstrap` / `doctor`, `scripts/install_uv.sh`, `scripts/install_just.sh`, `scripts/check_tool_version.sh`) so every machine and worktree runs the same uv, just and Python. `make` only bootstraps; `just` runs repeatable tasks. Host Python is pinned to **Blender's bundled interpreter** (3.13.13 on Blender 5.2.2), because pure-Python harness code runs both on the host and inside Blender. Leave out everything docketScore needs and this project doesn't (node/pnpm, Sonar, tailnet, osv-scanner, ML models, direnv); target ≲150 lines across the Makefile and scripts.
- **Scope:** toolchain pins and bootstrap; read-only environment report.
- **Files/Modules:** `.python-version` (new: `3.13.13`); `uv.toml` (new: `python-preference = "only-managed"`, `required-version = "==<UV_VERSION>"`); `Makefile` (new: pins `UV_VERSION := 0.12.24`, `JUST_VERSION := 1.53.0`; targets `help`, `tooling-bootstrap` (install pinned uv and just into `.toolchain/`, `uv python install` the `.python-version` pin), `worktree-init` (bootstrap + `uv sync` once a `pyproject.toml` exists), `setup` (`brew bundle` + `worktree-init` + `doctor`), `doctor`); `scripts/install_tool.sh uv|just` (merged from docketScore's two installers, Run 0.1 decision), `scripts/check_tool_version.sh` (ported: download the pinned release, accept only when `.uv.sha256` / `.just.sha256`, the release's own checksum list and the file agree; link under `.toolchain/`); `.uv.sha256`, `.just.sha256` (new: aarch64- and x86_64-darwin lines for the pins); `scripts/doctor.sh` (new, read-only, exits 1 when anything needs action: uv/just/Python match their pins; `/Applications/Blender.app` reports 5.2.2 — **warn** until ADR-0004 pins Blender (Run 5.1), then fail; Blender's bundled `python3.x --version` equals `.python-version` — **fail**; ffmpeg and shellcheck present, versions printed; git-lfs deferred to `docs/plans/followups.md`); `Brewfile` (new: `ffmpeg`, `shellcheck`; Blender is not brew-installed — doctor checks it); `justfile` (new: `default` lists recipes; `doctor`); `.gitignore` (extend: `.toolchain/`).
- **Spec-refs touched:** `CLAUDE.md` [Read] §Blender, §Shell — note in the status report (don't apply) that §Blender should name `make setup` / `make worktree-init`; that doctrine change travels with ADR-0002 in Run 0.2.
- **Traces to:** `CLAUDE.md` §Blender ("record the version in every manifest. Pin before E1"); `docs/project-definition.md` §Risks (Blender API drift); user decision 2026-10-19 (pin the tech stack on docketScore's model).
- **Dependencies:** None — can start immediately.
- **Integration points:** `.python-version` and `UV_VERSION` are the pins Run 0.2's `pyproject.toml` `requires-python` must admit `.python-version`, and `uv.toml`'s `required-version` must equal `UV_VERSION` — the pins; `TOOL_PATH`-style PATH ordering (`.toolchain/uv/bin`, `.toolchain/just/bin` first) is what every recipe uses. Route a `contract` line to 0.2 and a `gotcha` line to 5.1 (Blender and Python pins move together).
- **Acceptance criteria:**
  - [x] In a fresh worktree, `make worktree-init` leaves `.toolchain/uv/bin/uv --version` = 0.12.24, `.toolchain/just/bin/just --version` = 1.53.0, and `uv python find` resolving a uv-managed 3.13.13 (not Homebrew's 3.14).
  - [x] A corrupted expected sha256 (in a temp copy) makes the install script refuse the download.
  - [x] `make doctor` exits 0 on this machine; changing `.python-version` to a value that differs from Blender's bundled Python makes it exit 1 naming the fix (checked, then reverted).
  - [x] `shellcheck scripts/*.sh` is clean (`scripts/run_tests.sh` lands in Run 0.2).
- **Session estimate:** 1 session — more than 5 files, but most are small scripts ported from docketScore with only the paths and pins changed.
- **Parallelizable with:** 0.3
- **Prompt strategy:** straight-implementation; port docketScore's scripts, then strip.
- **Risk flags:** CRITICAL-PATH (uv may not publish a 3.13.13 build: if `uv python install 3.13.13` fails, stop and report the nearest available 3.13.x rather than picking one)

### Run 0.2: Test runner, Python project and harness contract

- **Status:** COMPLETE 2026-10-19 — `sidequests/studio-v1/status/run0.2status.md`
- **Summary:** Create the Python project and the canonical test runner on the pinned toolchain, and record the host-side package layout, the toolchain pins and the scene-script contract every later run builds against. After this run `scripts/run_tests.sh` is green on an empty suite and Blender-dependent tests can be marked and skipped.
- **Scope:** Python project (pytest, ruff, mypy, locked deps), Blender test marker, pin-consistency checks, package layout decision, scene-script interface.
- **Files/Modules:** `pyproject.toml` + `uv.lock` (new: `requires-python = "==3.13.*"`, no `[tool.uv]` table (uv ignores it next to `uv.toml`, which stays the only uv config and holds `required-version` equal to the Makefile's `UV_VERSION` — Run 0.2 decision), deps pytest/ruff/mypy/jsonschema/pyyaml/Pillow/numpy, ruff + mypy config incl. `bpy` typed by `fake-bpy-module-5.2==20260730` (Run 0.2 decision)); `scripts/run_tests.sh` (new: the one gate, fail-fast, lanes in this order — (1) **environment**: `scripts/doctor.sh`; (2) **locks**: `uv lock --check`, before any `uv run`, which would silently rewrite a stale lock; (3) **static**: `ruff check`, `ruff format --check`, `mypy`; (4) **unit**: `uv run --locked pytest -m "not blender"`; (5) **blender**: `pytest -m blender` (render smoke and reproducibility join in Run 0.7). Each lane prints its name and result; non-zero on any failure; when `BLENDER_BIN` is unavailable the blender lane is reported as skipped, loudly — never silently); `tests/conftest.py` + `tests/test_toolchain_pins.py` (new: registers `blender` marker, resolves `BLENDER_BIN` defaulting to `/Applications/Blender.app/Contents/MacOS/Blender`; pin test — `uv.toml`, `pyproject.toml` and the Makefile agree on uv, and the running interpreter matches `.python-version`; a `@pytest.mark.blender` test that Blender's bundled Python matches it too); `justfile` (extend: `ci` runs `scripts/run_tests.sh` — the same gate under docketScore's name, never a second definition of it; `test`, `lint`, `typecheck` run single lanes for the per-edit loop); `docs/adr/0002-python-toolchain-and-layout.md` + `docs/adr/README.md` index row (new).
- **Spec-refs touched:** `CLAUDE.md` [Read] — ADR-0002 carries the proposed §Blender amendment from Run 0.1 (apply only on the user's confirmation of a shown diff); `docs/project-definition.md` [Read] §Repository structure; `docs/adr/` [Modify].
- **Traces to:** `docs/project-definition.md` §M0 Tasks (repo skeleton; smoke test); `CLAUDE.md` §Tests; `docs/test-strategy.md` §Rules.
- **Dependencies:** 0.1
- **Integration points:** ADR-0002 defines (a) the toolchain: `make` bootstraps, `just` runs tasks, `scripts/run_tests.sh` stays the canonical gate (`just ci` is its alias; the lane order above is part of the contract), host Python follows Blender's bundled Python; (b) `studio/` host package, `validators/`, `eval/` packages, Blender-side `blender/lib/`; (c) the **scene-script contract**: a scene script is a Python file defining `build(seed: int) -> None` that creates the scene through `bpy.data` only (STD-002), sets no render settings or output paths (STD-003), and declares `FRAME_COUNT`; (d) how Blender-side code finds repo modules (`sys.path` insert by the in-Blender entry). Route a `contract` line to 0.4, 0.5, 0.6.
- **Acceptance criteria:**
  - [x] `scripts/run_tests.sh` exits 0 on the empty suite and exits non-zero when a deliberately failing test or ruff violation is added (checked, then removed); `just ci` gives the same exit code and output.
  - [x] The gate fails in the environment lane when `.python-version` disagrees with Blender's bundled Python, and in the locks lane when `pyproject.toml` gains a dependency without `uv lock` (each checked, then reverted) — before any later lane runs.
  - [x] A `@pytest.mark.blender` test is collected when `BLENDER_BIN` resolves and reported as skipped with a reason when it doesn't.
  - [x] The pin test fails when `uv.toml`'s `required-version` is edited to differ from the Makefile (checked, then reverted).
  - [x] ADR-0002 is `Proposed`, indexed, and states the toolchain, layout and scene-script contract in one sentence each.
  - [x] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 0.3
- **Prompt strategy:** straight-implementation; tooling with a known shape.
- **Risk flags:** CRITICAL-PATH

### Run 0.3: Blender API probe spike → ADR-0001

- **Status:** COMPLETE 2026-10-19 — `sidequests/studio-v1/status/run0.3status.md`
- **Summary:** Write and run a probe that reports the installed Blender's version, render engine identifiers, Metal GPU devices and confirms a scene builds in background mode. It also pre-checks determinism: render one frame twice per engine and compare hashes. Findings go into ADR-0001, which decides the engine/determinism policy M0's exit gate uses.
- **Scope:** Blender 5.2.2 API surface in background mode; EEVEE and Cycles on Metal.
- **Files/Modules:** `blender/probe/api_probe.py` (new: runs under `blender -b --python`, prints one JSON report — `bpy.app.version_string`, available `scene.render.engine` enum items, Cycles device type and devices, a `bpy.data`-only scene build, per-engine 1-frame sha256 ×2); `docs/adr/0001-blender-api-baseline.md` (new from `docs/adr/0000-template.md`); `docs/adr/README.md` (index row).
- **Spec-refs touched:** `docs/adr/0001-blender-api-baseline.md` [Modify]; `CLAUDE.md` [Read] — propose (don't apply) a doctrine amendment if the probe contradicts it (e.g. the engine identifier); `docs/project-definition.md` [Read] §M0, §Risks (Blender API drift).
- **Traces to:** `docs/project-definition.md` §M0 Tasks item 3; exit gate "Reproducible render".
- **Dependencies:** None — can start immediately (its `scripts/run_tests.sh` check runs once 0.2 has landed).
- **Integration points:** produces the engine identifiers and the determinism decision (EEVEE exact hash vs tolerance; Cycles tolerance value, e.g. max abs diff ≤ 1/255) — route `contract` lines to 0.4 and 0.7. The probe's own render call is spike code, isolated per STD-002, and is not the harness.
- **Acceptance criteria:**
  - [x] Probe JSON from this machine is quoted in ADR-0001 (machine named); ADR is `Provisional` with review trigger "second Mac probed" if only one machine ran it.
  - [x] ADR-0001's Decision names the engine used for exact-hash reproducibility and the Cycles comparison tolerance, with the 2×-render hashes as evidence.
  - [x] Any contradiction with `CLAUDE.md` or §M0 Acceptance is listed in the status report as a proposed change, not applied.
  - [x] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 0.1, 0.2
- **Prompt strategy:** spike-then-implement; the API surface is unverified on 5.2.2.
- **Risk flags:** NOVEL-TECH, CRITICAL-PATH

### Run 0.4: Harness runner

- **Status:** COMPLETE 2026-10-19 — `sidequests/studio-v1/status/run0.4status.md`
- **Summary:** Build `blender/harness/render.py`, the host-side CLI that launches Blender headless, loads a scene script, applies a render profile and seed, and renders frames to `<out>/frames/`. Profiles live in one table so nothing else hardcodes render settings.
- **Scope:** host CLI, in-Blender entry, render profiles.
- **Files/Modules:** `blender/harness/render.py` (new: argparse `--scene <script> --profile preview|final --out <dir> --seed <int> --model-id <id>`; spawns `$BLENDER_BIN -b --factory-startup --python blender/harness/_inblender.py -- <args>`; returns Blender's exit code; records wall time); `blender/harness/_inblender.py` (new: inserts repo root on `sys.path`, imports the scene script, calls `build(seed)`, applies the profile, sets frame range from `FRAME_COUNT`, renders — the single isolated `bpy.ops.render.render` call per STD-002/003 with a why-comment); `blender/harness/profiles.py` (new: `preview` and `final` as data — engine, resolution, samples, device — single source per STD-001); `tests/test_harness_cli.py` (new: arg validation, profile table, missing `--model-id` fails; one `@pytest.mark.blender` test renders a 2-frame inline scene).
- **Spec-refs touched:** `CLAUDE.md` [Read] §Blender; `docs/adr/0001-blender-api-baseline.md` [Read] engine IDs.
- **Traces to:** `docs/project-definition.md` §M0 Tasks item 4; STD-002, STD-003, STD-004.
- **Dependencies:** 0.2 (layout, scene-script contract); uses 0.3's engine identifiers if landed, otherwise reads them from `bpy` at runtime and routes a `gotcha` line.
- **Integration points:** CLI flags above; produces a run-result object (frame paths, timings, seed, profile, engine, Blender version string read from inside Blender) that 0.7 hands to the manifest writer from 0.5. Route a `contract` line to 0.7.
- **Acceptance criteria:**
  - [x] Rendering a 2-frame scene with `--profile preview` writes 2 PNGs to `<out>/frames/` and exits 0.
  - [x] `--profile` outside `preview|final`, a missing `--scene`, or a missing model ID exits non-zero with a message.
  - [x] `grep -rn "render.render\|filepath" blender/ --include=*.py` finds render calls and output-path writes only in `blender/harness/` and `blender/probe/`.
  - [x] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 0.5, 0.6
- **Prompt strategy:** interface-first; the CLI is the contract 0.7 and every later stage consumes.
- **Risk flags:** CRITICAL-PATH

### Run 0.5: Manifest schema, writer and contact sheet

- **Status:** COMPLETE 2026-10-19 — `sidequests/studio-v1/status/run0.5status.md`
- **Summary:** Define `schemas/manifest.schema.json` and implement the writer that fills it, plus a contact-sheet builder that tiles every Nth frame onto one PNG. Both are pure Python, testable without Blender.
- **Scope:** manifest schema and writer; contact sheet.
- **Files/Modules:** `schemas/manifest.schema.json` (new: `schema_version`, `production_id` (test renders use a `t-<scene>` id), `git_commit`, `git_dirty`, `model_id`, `blender_version`, `machine` {label, hardware_model, chip, os, arch} (no hostname — user decision 2026-10-19), `seeds`, `timings` {wall_s, render_s}, `profile`, `engine`, `frames[]` {index, path, sha256}, `contact_sheet`); `blender/harness/manifest.py` (new: collects git/machine facts, hashes frames, validates against the schema before writing); `blender/harness/contact_sheet.py` (new: Pillow; `every_n` and columns as arguments); `tests/test_manifest.py`, `tests/test_contact_sheet.py` (new: synthetic PNGs; schema rejects a manifest missing `model_id`; dirty tree flagged).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Artifact schemas (`manifest.json`), §M0 Acceptance item 2; `docs/glossary.md` [Read] "Manifest".
- **Traces to:** `docs/project-definition.md` §M0 Tasks item 6; §M0 Acceptance item 2; `CLAUDE.md` §Blender (manifest fields); STD-006.
- **Dependencies:** 0.2
- **Integration points:** `write_manifest(run_result, out_dir) -> Path` and `build_contact_sheet(frames, every_n, out_path)`; manifest field names are the contract for every later run (schema changes after M1 need an ADR). Route a `contract` line to 0.7 and `quest`.
- **Acceptance criteria:**
  - [x] A manifest written from a synthetic run result validates against the schema and contains every §M0 Acceptance item 2 field.
  - [x] Each frame records `file_sha256` (matches `shasum -a 256` of the file) and `pixel_sha256` (matches an independent decode of the 8-bit RGBA pixels); reproducibility compares `pixel_sha256` (ADR-0001). (Reworded in Run 0.5 from "frame sha256 values match `shasum -a 256`": PNG bytes differ on every render.)
  - [x] A 48-frame synthetic set with `every_n=6` yields one PNG with 8 tiles.
  - [x] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 0.4, 0.6
- **Prompt strategy:** TDD; pure functions with crisp expected outputs.
- **Risk flags:** none

### Run 0.6: Plain test scene

- **Status:** COMPLETE 2026-10-19 — `sidequests/studio-v1/status/run0.6status.md`
- **Summary:** Write a deliberately plain scene script that satisfies the scene-script contract: a few objects, one light, a camera move, 48 frames, all through `bpy.data`. It is the fixture for smoke and reproducibility tests, not a style.
- **Scope:** test fixture scene; Blender integration test.
- **Files/Modules:** `tests/scenes/plain_scene.py` (new: `FRAME_COUNT = 48`, `build(seed)`; a module comment says it is a test fixture exempt from STD-005 because plainness is its purpose; any seeded variation uses `random.Random(seed)` per STD-004); `tests/test_plain_scene.py` (new, `@pytest.mark.blender`: builds in background mode with no `bpy.ops`; asserts object count, one light, camera has location keyframes at frames 1 and 48).
- **Spec-refs touched:** `CLAUDE.md` [Read] §Blender.
- **Traces to:** `docs/project-definition.md` §M0 Tasks item 5; STD-002, STD-004.
- **Dependencies:** 0.2
- **Integration points:** consumes the scene-script contract (ADR-0002); consumed by 0.7.
- **Acceptance criteria:**
  - [x] `grep -n "bpy.ops" tests/scenes/plain_scene.py` returns nothing.
  - [x] The Blender integration test passes in background mode.
  - [x] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session (short; merge into 0.4's session if 0.4 finishes early)
- **Parallelizable with:** 0.4, 0.5
- **Prompt strategy:** straight-implementation.
- **Risk flags:** none

### Run 0.7: Integration — smoke, reproducibility, exit gate

- **Summary:** Wire the manifest writer and contact sheet into `render.py`, add the preview smoke test and the reproducibility test, and produce M0's exit-gate evidence on both Macs.
- **Scope:** harness integration; render smoke; determinism.
- **Files/Modules:** `blender/harness/render.py` (integrate: call `write_manifest` and `build_contact_sheet` after render); `blender/harness/compare.py` (new: exact sha256 comparison and per-pixel max-abs-diff with the ADR-0001 tolerance); `tests/test_render_smoke.py` (new, `@pytest.mark.blender`: preview render of the plain scene writes 48 frames, a contact sheet and a valid manifest within a time budget); `tests/test_render_determinism.py` (new, `@pytest.mark.blender`: two same-seed preview runs match exactly; Cycles check at tolerance, skipped with reason if no GPU).
- **Spec-refs touched:** `docs/adr/0001-blender-api-baseline.md` [Read] (flip to `Accepted` if the second Mac confirms — [Modify]); `docs/project-definition.md` [Read] §M0 Acceptance — tick boxes as a proposed change at close.
- **Traces to:** exit gate "Reproducible render"; §M0 Acceptance items 1–3; §M0 Tasks item 7.
- **Dependencies:** 0.3, 0.4, 0.5, 0.6
- **Integration points:** consumes 0.4's run result, 0.5's writer, 0.6's scene, 0.3's tolerance. Every later render goes through this path.
- **Acceptance criteria:**
  - [ ] Smoke and determinism tests pass on this machine; the status report quotes both runs' frame hashes and manifest paths.
  - [ ] The user runs `scripts/run_tests.sh` on the second Mac; its output and wall time are quoted in the status report (both under "a few minutes").
  - [ ] The status report has an "Exit gate evidence" section ready to paste into `### Exit gate evidence`, including M0 Tasks 1–2 as already done (commits `b24c5bc`, `eaf4bc7`).
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** none (integration)
- **Prompt strategy:** TDD; write the determinism test first, then integrate until it passes.
- **Risk flags:** CRITICAL-PATH

## Milestone 1: Vertical slice — style bible to animatic

**Theme:** prove a written style survives into Blender frames before any story stage exists.
**Testable capability:** from a hand-written beats fixture and either of two locked style bibles, stages 3–4 produce `style_bible.json`, `shots.yaml`, blocking renders and an animatic through the harness; palette and camera-grammar validators pass for both styles and fail when the bibles are swapped.
**Session estimate:** 10 sessions
**Entry criteria:** M0 exit gate passed; the user has named the two contrasting styles (Input Gaps).
**Exit criteria / Definition of Done:** exit gate "Style survives" — renders pass the style-bible validators for both styles; cross-check shows each style's renders fail the other's palette validator (the validators are not tautological); one style parameter sweep moves the frames (dead-knob rule).
**Testing strategy:** schema (positive and negative fixtures per schema); unit (validators on synthetic images and YAML); Blender integration (style modules apply in background mode); render smoke (preview profile through the harness); determinism (EEVEE exact hash on styled renders).
**Key risks:** line treatment in Blender 5.x (Grease Pencil v3 line art vs Freestyle) is new API surface; palette fidelity under lighting/antialiasing may need a tolerance that makes the validator weak; stage 3/4 skills could copy examples (CLAUDE.md "never ship an example a skill could copy").

### Dependency graph

```
├── Run 1.1: schemas — style, style_bible, shots, beats + schema IO   ──┐ (contract-first)
├── Run 1.2: style-module contract + harness --style-bible            ──┤ (contract-first, parallel with 1.1)
│         ↓                                                             │
├── Run 1.3: visual style A + modules (NOVEL-TECH: lines)              ─┤ (after 1.1, 1.2)
├── Run 1.4: visual style B + modules                                  ─┤ (after 1.1, 1.2)
├── Run 1.5: camera styles ×2 + camera-grammar validator               ─┤ (after 1.1)
├── Run 1.6: palette validator (render vs style bible)                 ─┤ (after 1.1)
├── Run 1.7: camera-move primitives + shot blocking builder            ─┤ (after 1.2, 1.5)
├── Run 1.8: stage 3 skill + gate tooling (Gate B)                     ─┤ (after 1.1; options draw on 1.3/1.4 styles)
├── Run 1.9: stage 4 skill + animatic (Gate C)                         ─┘ (after 1.1, 1.7)
│         ↓
└── Run 1.10: integration — both styles through stages 3–4, validators, sweep (after all)
```

### Run 1.1: Artifact schemas and schema IO

- **Summary:** Formalize `style.yaml`, `style_bible.json`, `shots.yaml` and `beats.yaml` as JSON Schema, with shared definitions, and a single load-and-validate helper that every stage uses on read and write.
- **Scope:** schemas; host-side schema IO.
- **Files/Modules:** `schemas/_defs.schema.json` (new: `schema_version`, `production_id`, hex color, seconds); `schemas/style.schema.json`, `schemas/style_bible.schema.json` (one `style_id@version` per dimension + overrides), `schemas/shots.schema.json` (fields per §Artifact schemas, incl. audio-ready `narration`, `sound_cues`), `schemas/beats.schema.json` (new: id, start_s, duration_s, change described, optional narration/sound fields); `studio/artifacts.py` (new: `load_artifact(path, schema)` / `write_artifact(obj, path, schema)`, YAML and JSON); `tests/test_schemas.py` + `tests/fixtures/` (positive and negative fixtures per schema).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Artifact schemas, §Scope (audio-ready); `docs/glossary.md` [Read].
- **Traces to:** `docs/project-definition.md` §Artifact schemas ("formalizes them as JSON Schema … during M0 and M1"); STD-006.
- **Dependencies:** M0 complete.
- **Integration points:** schema field names are the contract for 1.3–1.10 and all later stages; after M1 they change only with an ADR. Route a `contract` line to `quest`.
- **Acceptance criteria:**
  - [ ] The project definition's `style.yaml` and `shots.yaml` examples validate; each negative fixture (bad hex, missing `schema_version`, negative duration) fails with a named path.
  - [ ] `write_artifact` refuses an invalid object and writes nothing.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 1.2
- **Prompt strategy:** TDD; fixtures first.
- **Risk flags:** CRITICAL-PATH

### Run 1.2: Style-module contract and harness style application

- **Summary:** Define how a style's `modules:` list resolves to Blender-side code, and extend the harness to apply a style bible's visual modules after the scene builds and record style versions in the manifest.
- **Scope:** style-module registry; harness flag; manifest fields.
- **Files/Modules:** `blender/lib/registry.py` (new: maps `shaders/toon_ramp`-style ids to `apply(params: dict, scene) -> None` callables; unknown id is an error); `blender/harness/render.py` + `blender/harness/_inblender.py` (extend: `--style-bible <path>`; resolves each `style_id@version` to `styles/<dimension>/<style-id>/style.yaml` and applies its modules after `build(seed)`); `schemas/manifest.schema.json` + `blender/harness/manifest.py` (extend: `styles` {dimension: `style_id@version`} — pre-M1 change, no ADR needed); `tests/test_style_registry.py` (new: a no-op test module registers and applies in background mode).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Style library, §Artifact schemas; `docs/glossary.md` [Read] "Style module".
- **Traces to:** `docs/project-definition.md` §Style library ("references modules in `blender/lib/`"); STD-001, STD-003.
- **Dependencies:** M0 complete.
- **Integration points:** `apply(params, scene)` signature and module-id convention consumed by 1.3, 1.4, 1.7; `--style-bible` flag consumed by 1.9, 1.10. Route `contract` lines to those runs.
- **Acceptance criteria:**
  - [ ] Rendering the plain scene with a style bible naming a test module records `styles` in the manifest and calls the module once.
  - [ ] An unknown module id fails the render before any frame is written.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 1.1
- **Prompt strategy:** interface-first.
- **Risk flags:** CRITICAL-PATH

### Run 1.3: Visual style A

- **Summary:** Author visual style A as `style.yaml` plus its Blender modules (e.g. a toon-ramp shader and an ink line treatment), and prove each parameter reaches the frames. Line treatment on Blender 5.x is new API surface, so it is probed first.
- **Scope:** one visual style and its modules.
- **Files/Modules:** `styles/visual/<style-a-id>/style.yaml` (new); `blender/lib/shaders/<module>.py` (new: node material built through `bpy.data`, params from style); `blender/lib/lines/<module>.py` (new: line art via the mechanism ADR-0001 or this run's probe selects); `tests/test_style_a.py` (new, `@pytest.mark.blender`: modules apply to the plain scene; changing `line.weight_px` or `ramp_steps` changes the frame hash).
- **Spec-refs touched:** `docs/adr/0001-blender-api-baseline.md` [Read]; `CLAUDE.md` [Read] §Global bans.
- **Traces to:** `docs/project-definition.md` §Milestones M1 ("two contrasting style modules"); H3; STD-005.
- **Dependencies:** 1.1, 1.2
- **Integration points:** consumes `apply(params, scene)`; its `style.yaml` is an input fixture for 1.6, 1.8, 1.10.
- **Acceptance criteria:**
  - [ ] `style.yaml` validates against `schemas/style.schema.json`.
  - [ ] A preview render through the harness with a bible naming style A writes a contact sheet; the status report links it for the user to review.
  - [ ] Each declared parameter moves the frame hash when changed (a parameter that doesn't is removed or wired).
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 1.4, 1.5, 1.6
- **Prompt strategy:** spike-then-implement; line art API is unverified.
- **Risk flags:** NOVEL-TECH

### Run 1.4: Visual style B

- **Summary:** Author visual style B, chosen to contrast with A on every validated axis (palette family, shading model, line on/off), with its modules and parameter checks.
- **Scope:** one visual style and its modules.
- **Files/Modules:** `styles/visual/<style-b-id>/style.yaml` (new); `blender/lib/shaders/<module>.py` (new, or extend one from 1.3 with a distinct mode — say which); `blender/lib/lighting/<module>.py` (new if B's contrast is in lighting, e.g. `key_fill_ratio`); `tests/test_style_b.py` (new, `@pytest.mark.blender`).
- **Spec-refs touched:** `CLAUDE.md` [Read] §Global bans.
- **Traces to:** `docs/project-definition.md` §Milestones M1; H3; STD-005.
- **Dependencies:** 1.1, 1.2
- **Integration points:** as 1.3; if it shares a module with 1.3, the shared signature is a `contract` line to 1.3/1.10.
- **Acceptance criteria:**
  - [ ] `style.yaml` validates; the status report states the contrast with A per axis.
  - [ ] Preview render contact sheet linked for user review; each parameter moves the frame hash.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 1.3, 1.5, 1.6
- **Prompt strategy:** straight-implementation (follows 1.3's pattern; if 1.3 hasn't landed, spike-then-implement).
- **Risk flags:** none

### Run 1.5: Camera styles and camera-grammar validator

- **Summary:** Author two contrasting camera-and-editing styles (allowed framings, moves, lens range, average shot length) and a validator that checks a `shots.yaml` against the bible's camera style.
- **Scope:** camera dimension styles; artifact-vs-upstream validator.
- **Files/Modules:** `styles/camera/<cam-a-id>/style.yaml`, `styles/camera/<cam-b-id>/style.yaml` (new); `validators/camera_grammar.py` (new: framing and move in vocabulary, lens within range, mean shot length within tolerance, shot times contiguous and within duration; returns structured violations); `tests/test_camera_grammar.py` (new: passing and violating `shots.yaml` fixtures per style).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Style library (camera dimension), §Risks (coherence drift); `docs/glossary.md` [Read] "Validator", "Shot".
- **Traces to:** `docs/project-definition.md` §Milestones M1 ("camera grammar" validator); H3.
- **Dependencies:** 1.1
- **Integration points:** camera style vocabulary (framing and move names) is consumed by 1.7's primitives and 1.9's skill — route a `contract` line to both. Validator output format is shared with 1.6 (`validators/` result type) — agree via the carry-forward ledger.
- **Acceptance criteria:**
  - [ ] Each violation fixture fails with a violation naming the shot id and rule; each passing fixture passes.
  - [ ] A `shots.yaml` valid for cam A fails cam B on at least one rule.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 1.3, 1.4, 1.6
- **Prompt strategy:** TDD.
- **Risk flags:** none

### Run 1.6: Palette validator

- **Summary:** Build the render-vs-style-bible palette check: sample frames, measure the share of pixels within a perceptual distance of the bible's palette, and fail below a threshold.
- **Scope:** render validator.
- **Files/Modules:** `validators/palette.py` (new: numpy + Pillow; CIELAB ΔE; every-Nth-frame sampling; threshold and ΔE taken from arguments sourced from the style, not literals — STD-001/005); `validators/result.py` (new, unless 1.5 landed it first: shared violation/result type); `tests/test_palette.py` (new: synthetic on-palette, off-palette and antialiased-edge images).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Risks (coherence drift), §Hypotheses H3.
- **Traces to:** `docs/project-definition.md` §Milestones M1 ("palette" validator); H3.
- **Dependencies:** 1.1
- **Integration points:** consumes frame paths from the manifest; consumed by 1.10. Route a `gotcha` line to 1.10 with the threshold rationale.
- **Acceptance criteria:**
  - [ ] An on-palette image passes, an off-palette image fails, and an antialiased on-palette image passes (edge pixels don't sink it).
  - [ ] Failure reports the off-palette share and the top offending colors.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 1.3, 1.4, 1.5
- **Prompt strategy:** TDD.
- **Risk flags:** none

### Run 1.7: Camera-move primitives and shot blocking builder

- **Summary:** Implement Blender-side camera primitives for each move in the camera styles' vocabulary, and a blocking builder that turns one `shots.yaml` entry into a scene script the harness can render.
- **Scope:** `blender/lib/camera/`; blocking scene generation.
- **Files/Modules:** `blender/lib/camera/moves.py` (new: one function per vocabulary move — e.g. static, dolly, pan — keyframed through `bpy.data`, easing from the motion style or an explicitly cited source, never stock linear — STD-005); `blender/lib/camera/framing.py` (new: framing name → camera distance/lens relative to the subject's bounds); `studio/blocking.py` (new: writes a per-shot scene script under the production or test output dir from a shot entry + blocking proxies); `tests/test_camera_moves.py` (new, `@pytest.mark.blender`).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Pipeline stage 4.
- **Traces to:** `docs/project-definition.md` §Pipeline (stage 4 "blocking renders"); STD-002, STD-005.
- **Dependencies:** 1.2, 1.5
- **Integration points:** consumes 1.5's vocabulary; generated scripts satisfy ADR-0002's scene-script contract; consumed by 1.9.
- **Acceptance criteria:**
  - [ ] Every move in both camera styles has a primitive; a move not in the vocabulary raises.
  - [ ] A generated blocking script for a 2.5 s shot renders `2.5 × fps` frames through the harness.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 1.8
- **Prompt strategy:** interface-first.
- **Risk flags:** none

### Run 1.8: Stage 3 skill and gate tooling (Gate B)

- **Summary:** Write the stage 3 skill that proposes N style-bible options from the style library and a gate tool that presents them and locks the pick as `style_bible.json`, in `human`, `auto-pick` or `random-pick` mode.
- **Scope:** pipeline stage skill; gates.
- **Files/Modules:** `skills/style-bible/SKILL.md` (new: reads `production.yaml`/fixtures and the active style catalog, writes `style_options/` with N options; no example bible a skill could copy); `studio/gates.py` (new: `run_gate(options, mode, rng_seed) -> pick`; records options shown and the pick for the manifest; `random-pick` seeded per STD-004); `tests/test_gates.py` (new); `tests/fixtures/production/` (new: a minimal production fixture for M1).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Pipeline (stage 3, Gate B), §Control surface (gate mode, divergence width); `docs/glossary.md` [Read] "Gate", "Style bible".
- **Traces to:** `docs/project-definition.md` §Milestones M1 ("Stages 3 and 4"); §Control surface.
- **Dependencies:** 1.1 (styles from 1.3/1.4 needed only for the demo)
- **Integration points:** gate decision record (options + pick) is a manifest field — extend `schemas/manifest.schema.json` (pre-M1-close, no ADR); `run_gate` reused for Gates A and C. Route a `contract` line to 1.9 and `quest`.
- **Acceptance criteria:**
  - [ ] `random-pick` with the same seed picks the same option; `auto-pick` and `human` paths are covered by tests (human via injected input).
  - [ ] The skill, run against the fixture, writes N schema-valid options and Gate B locks one `style_bible.json`.
  - [ ] The skill is reviewed for copyable examples by a separate subagent, and the review is noted in the status report.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 1.7
- **Prompt strategy:** straight-implementation for gates (TDD); skill drafted, then reviewed in a separate context.
- **Risk flags:** UNCERTAIN-SCOPE

### Run 1.9: Stage 4 skill and animatic (Gate C)

- **Summary:** Write the stage 4 skill that turns beats plus the locked bible into `shots.yaml`, renders blocking per shot through the harness, and cuts an animatic on shot timing for Gate C.
- **Scope:** pipeline stage skill; animatic assembly.
- **Files/Modules:** `skills/shots/SKILL.md` (new: reads `beats.yaml` + `style_bible.json`, writes `shots.yaml` in the camera style's vocabulary, runs `validators/camera_grammar.py` and loops back on failure); `studio/animatic.py` (new: ffmpeg concat of per-shot blocking frames at each shot's duration; output under a gitignored dir); `tests/test_animatic.py` (new: duration of the cut equals the sum of shot durations ± one frame); `tests/fixtures/beats/` (new: hand-written beats fixture per Input Gaps).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Pipeline (stage 4, Gate C), §Artifact schemas (`shots.yaml`); `docs/glossary.md` [Read] "Animatic".
- **Traces to:** `docs/project-definition.md` §Milestones M1; §Pipeline.
- **Dependencies:** 1.1, 1.7 (and 1.5, 1.8 transitively)
- **Integration points:** consumes `run_gate` (1.8), blocking builder (1.7), camera validator (1.5); produces the animatic consumed by 1.10.
- **Acceptance criteria:**
  - [ ] From the beats fixture and a locked bible, the skill writes a schema-valid `shots.yaml` that passes the camera-grammar validator.
  - [ ] The animatic's duration matches `shots.yaml` (ffprobe), and Gate C locks `shots.yaml`.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** none after 1.7 (1.8 may still be finishing)
- **Prompt strategy:** straight-implementation.
- **Risk flags:** UNCERTAIN-SCOPE

### Run 1.10: Integration — style survives (exit gate)

- **Summary:** Run stages 3–4 end to end for both style bibles, render through the harness, run both validators, cross-check swapped bibles, and sweep one style parameter to prove it moves the frames.
- **Scope:** integration; exit-gate evidence.
- **Files/Modules:** `tests/test_style_survives.py` (new, `@pytest.mark.blender`: both bibles render and pass; swapped palette fails); `scripts/evidence/m1_style_survives.sh` (new: reproducible evidence commands); `sidequests/studio-v1/status/run1.10status.md` (evidence).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Milestones M1 exit gate — tick as a proposed change at close.
- **Traces to:** exit gate "Style survives"; H3; §Control surface (dead-knob rule).
- **Dependencies:** 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9
- **Integration points:** everything in M1.
- **Acceptance criteria:**
  - [ ] Both styles' renders pass palette and camera-grammar validators; manifest paths and contact sheets quoted.
  - [ ] Style A's renders fail style B's palette validator and vice versa.
  - [ ] A 3-value sweep of one visual parameter yields 3 distinct frame-hash sets (EEVEE exact).
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** none (integration)
- **Prompt strategy:** TDD; evidence test first.
- **Risk flags:** CRITICAL-PATH

## Milestone 2: Baseline and evaluation harness

**Theme:** fix the comparison and its measures before any experiment runs.
**Testable capability:** for 3 pilot seeds, the one-shot baseline and the pipeline arm (M1 slice) render through the same harness; diversity metrics compute; a blind rater batch and a ratings import produce win rates.
**Session estimate:** 5 sessions
**Entry criteria:** M1 exit gate passed; rater pool question answered enough to write the protocol.
**Exit criteria / Definition of Done:** exit gate "Baseline ready" — the E1 protocol runs end to end on pilot seeds; rater instructions and criteria are written and frozen before any rating happens.
**Testing strategy:** unit (metrics on fixed vectors, batch randomization, CSV import); integration (pilot run end to end); render smoke on baseline output through the harness.
**Key risks:** the baseline accidentally gets less tooling than the pipeline (breaks the comparison's isolation); embedding models drift between runs; protocol details decided after seeing results.

### Dependency graph

```
├── Run 2.1: E1 protocol + eval config/ratings schemas (frozen)   ──┐ (contract-first)
│         ↓                                                         │
├── Run 2.2: one-shot baseline (NOVEL-TECH: headless model call)  ─┤ (parallel after 2.1)
├── Run 2.3: diversity metrics                                     ─┤
├── Run 2.4: blind rater batches + ratings import                  ─┘
│         ↓
└── Run 2.5: E1 pilot end to end (exit gate)
```

### Run 2.1: E1 protocol and evaluation contracts

- **Summary:** Write the E1 protocol (seeds, arms, pairing, rubric, rater instructions, targets) and the schemas for experiment configs and ratings, frozen before any rating.
- **Scope:** `eval/` protocol and schemas.
- **Files/Modules:** `eval/protocol/e1.md` (new: from §Evaluation and §Feedback rubric; names the baseline invocation and embedding models per Input Gaps); `schemas/eval_config.schema.json` (new); `schemas/ratings.schema.json` (new: one row per rater × pair × question, matching the CSV export in `eval/feedback/<round>/`); `eval/config/e1-pilot.yaml` (new: 3 pilot seeds); `tests/test_eval_schemas.py` (new).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Hypotheses, §Evaluation and experiments, §Feedback.
- **Traces to:** `docs/project-definition.md` §Milestones M2 ("Rater protocol … fixed in advance"); §Evaluation ("Criteria and rater instructions are fixed before E1 runs").
- **Dependencies:** M1 complete.
- **Integration points:** config and ratings schemas consumed by 2.2–2.5 and M5. Route `contract` lines to 2.2, 2.3, 2.4.
- **Acceptance criteria:**
  - [ ] Protocol covers every row of §Hypotheses' criteria table with a measure and target.
  - [ ] A sample ratings CSV validates; a malformed one fails with the row number.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** none (contract-first)
- **Prompt strategy:** interface-first.
- **Risk flags:** CRITICAL-PATH

### Run 2.2: One-shot baseline

- **Summary:** Build the one-shot arm: one fixed prompt per seed asks the model for a complete scene script, which renders through the same harness with the same style library available.
- **Scope:** `eval/baseline/`.
- **Files/Modules:** `eval/baseline/prompt.md` (new: fixed one-shot prompt; documents the harness and library exactly as the pipeline sees them); `eval/baseline/one_shot.py` (new: invokes the model non-interactively with pinned model ID, writes the script under the experiment output dir, renders via `render.py`, records model ID and tokens in the manifest); `tests/test_one_shot.py` (new: model call stubbed at the subprocess boundary; output path and manifest fields asserted).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Evaluation ("same Blender harness and style library").
- **Traces to:** `docs/project-definition.md` §Milestones M2 ("One-shot baseline on the same harness and library"); H1.
- **Dependencies:** 2.1
- **Integration points:** consumes the harness CLI and scene-script contract; produces renders + manifests consumed by 2.3 and 2.5.
- **Acceptance criteria:**
  - [ ] One pilot seed produces a baseline render through the harness with a manifest that records the model ID.
  - [ ] A script that fails to build is recorded as a failed sample, not retried silently.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 2.3, 2.4
- **Prompt strategy:** spike-then-implement; headless model invocation is untested here.
- **Risk flags:** NOVEL-TECH

### Run 2.3: Diversity metrics

- **Summary:** Implement embedding spread for scripts and keyframes — mean pairwise distance within a set — with version-pinned local models recorded in outputs.
- **Scope:** `eval/metrics/`.
- **Files/Modules:** `eval/metrics/embed.py` (new: text and image embedders, model name + version returned with vectors); `eval/metrics/spread.py` (new: mean pairwise cosine distance; set-vs-set comparison); `tests/test_spread.py` (new: fixed vectors with known spread; embedder smoke marked slow).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Hypotheses (divergence measure).
- **Traces to:** `docs/project-definition.md` §Milestones M2 ("diversity metrics"); H1 divergence row.
- **Dependencies:** 2.1
- **Integration points:** consumed by 2.5, 3.6 (keyframe distance for sweeps) and M5. Route a `contract` line to 3.6.
- **Acceptance criteria:**
  - [ ] Spread of identical vectors is 0; of orthogonal unit vectors is 1.
  - [ ] Outputs include embedder name and version.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 2.2, 2.4
- **Prompt strategy:** TDD.
- **Risk flags:** none

### Run 2.4: Blind rater batches and ratings import

- **Summary:** Build tools that assemble a blind batch (random order, anonymized names, sealed key) and import exported ratings CSVs into paired win rates.
- **Scope:** `eval/raters/`.
- **Files/Modules:** `eval/raters/batch.py` (new: seeded shuffle, anonymized filenames, sealed mapping file outside what raters see); `eval/raters/ratings.py` (new: validate CSV against `schemas/ratings.schema.json`, compute familiarity and quality win rates per pair, record rater IDs); `tests/test_raters.py` (new).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Feedback from family and friends.
- **Traces to:** `docs/project-definition.md` §Milestones M2 ("Rater protocol"); §Feedback.
- **Dependencies:** 2.1
- **Integration points:** consumed by 2.5 and M5.
- **Acceptance criteria:**
  - [ ] The same seed yields the same batch order; batch filenames reveal no arm.
  - [ ] A synthetic ratings CSV produces the expected win rates.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 2.2, 2.3
- **Prompt strategy:** TDD.
- **Risk flags:** none

### Run 2.5: E1 pilot end to end (exit gate)

- **Summary:** Run the E1 protocol on 3 pilot seeds: both arms render, metrics compute, a blind batch is built, and a (pilot) ratings CSV imports into a report.
- **Scope:** integration; exit-gate evidence.
- **Files/Modules:** `eval/e1/run.py` (new: drives the protocol from `eval/config/e1-pilot.yaml`); `eval/reports/e1-pilot/report.md` (new: generated); `tests/test_e1_pipeline.py` (new: end to end with stubbed model and tiny renders).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Milestones M2 exit gate — tick as proposed change at close.
- **Traces to:** exit gate "Baseline ready".
- **Dependencies:** 2.2, 2.3, 2.4
- **Integration points:** everything in M2; the pipeline arm is the M1 slice with fixtures (Input Gaps).
- **Acceptance criteria:**
  - [ ] `eval/e1/run.py --config eval/config/e1-pilot.yaml` completes and writes the report with spread, batch and win-rate sections.
  - [ ] Every render in the pilot has a manifest; the report lists their paths.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session (real rating rounds are elapsed time, not session time)
- **Parallelizable with:** none (integration)
- **Prompt strategy:** straight-implementation.
- **Risk flags:** CRITICAL-PATH

## Milestone 3: Story stages

**Theme:** decisions upstream of the look — seed, premise, beats — become written, constrained and swept.
**Testable capability:** from a seed, stages 0–2 write `production.yaml`, seeded deck draws, N premise options, a locked premise and `beats.yaml`; a critic in a separate context reviews premise and beats; a sweep of any story knob shows artifact and keyframe movement.
**Session estimate:** 8 sessions
**Entry criteria:** M2 exit gate passed; narration lead/follow answered (affects beats timing).
**Exit criteria / Definition of Done:** exit gate "Knobs proven" — every story knob moves the output in an E2 sweep; dead knobs are wired or removed.
**Testing strategy:** schema; unit (seeded draws, validators, anti-default matching); critic isolation check; knob sweeps (E2 harness).
**Key risks:** knobs that move text but not frames (dead knobs); critic sharing context with the generator (self-validation); seeded draws leaking non-determinism.

### Dependency graph

```
├── Run 3.1: production/premise/deck/anti-default/critic schemas + knob registry ──┐ (contract-first)
│         ↓                                                                        │
├── Run 3.2: stage 0 — production.yaml + seeded deck draws + initial decks        ─┤ (parallel after 3.1)
├── Run 3.3: stage 1 — premise options + Gate A + premise validator               ─┤
├── Run 3.4: stage 2 — beats skill + beats validator                              ─┤
├── Run 3.5: story critic (separate subagent) + loop-back                         ─┤
├── Run 3.6: E2 sweep harness                                                     ─┘
│         ↓
└── Run 3.7: sweep every story knob (exit gate)
```

### Run 3.1: Story contracts and knob registry

- **Summary:** Define schemas for `production.yaml`, premise options/locked premise, decks, anti-default lists and critic reports, plus a knob registry that names every story knob and where it is enforced.
- **Scope:** schemas; `eval/knobs.yaml`.
- **Files/Modules:** `schemas/production.schema.json`, `schemas/premise.schema.json` (frontmatter of `premise_options.md`/`premise.md`), `schemas/deck.schema.json`, `schemas/antidefault.schema.json`, `schemas/critic_report.schema.json` (new; schema changes after M1 — these are new schemas; any change to M1's `beats`/`shots` needs an ADR); `eval/knobs.yaml` (new: knob → enforcing stage → sweep values); `tests/test_story_schemas.py` (new).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Control surface, §Artifact schemas (`production.yaml`); `docs/glossary.md` [Read] "Deck", "Anti-default", "Critic".
- **Traces to:** `docs/project-definition.md` §Milestones M3; §Control surface ("A knob earns its place only if …").
- **Dependencies:** M2 complete.
- **Integration points:** consumed by 3.2–3.7. Route `contract` lines to each.
- **Acceptance criteria:**
  - [ ] The project definition's `production.yaml` example validates; negative fixtures fail.
  - [ ] Every knob in §Control surface's story rows appears in `eval/knobs.yaml` with an enforcing stage.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** none (contract-first)
- **Prompt strategy:** interface-first.
- **Risk flags:** CRITICAL-PATH

### Run 3.2: Stage 0 — seed, constraints and seeded draws

- **Summary:** Write the stage 0 tool that turns a seed text and config into `production.yaml` and draws from constraint decks with a seed derived from `rng_seed`, plus the initial decks.
- **Scope:** `studio/` stage 0; `decks/`.
- **Files/Modules:** `studio/draws.py` (new: `draw(deck, rng_seed, key) -> item`, per-deck sub-seed derivation per STD-004); `studio/stage0.py` (new: writes schema-valid `production.yaml` with draws); `decks/structure.yaml`, `decks/material_world.yaml`, `decks/cinematographer.yaml`, `decks/banned_register.yaml` (new: curated lists — the user reviews contents; no single "default" entry); `tests/test_draws.py` (new).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Control surface (constraint decks), §Pipeline stage 0.
- **Traces to:** `docs/project-definition.md` §Milestones M3 ("constraint decks"); STD-004.
- **Dependencies:** 3.1
- **Integration points:** `production.yaml` and draws consumed by 3.3, 3.4, 3.6.
- **Acceptance criteria:**
  - [ ] Same `rng_seed` → identical draws; different seeds → different draws across 20 seeds (distribution check).
  - [ ] The status report lists deck contents for user review.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 3.3, 3.4, 3.5, 3.6
- **Prompt strategy:** TDD.
- **Risk flags:** none

### Run 3.3: Stage 1 — premise options and Gate A

- **Summary:** Write the premise skill that generates N premise options honoring the draws and the premise anti-default list, a compliance validator, and Gate A locking `premise.md`.
- **Scope:** pipeline stage skill; validator; anti-defaults.
- **Files/Modules:** `skills/premise/SKILL.md` (new: N = `divergence_n`; no example premise a skill could copy); `antidefaults/premise.yaml` (new: seeded banned premises, user-reviewed); `validators/premise.py` (new: draws honored, no anti-default match); `tests/test_premise_validator.py` (new).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Pipeline stage 1, §Control surface.
- **Traces to:** `docs/project-definition.md` §Milestones M3; Gate A.
- **Dependencies:** 3.1 (uses 3.2's draws when landed; fixtures otherwise)
- **Integration points:** uses `studio/gates.py` (1.8) for Gate A; output consumed by 3.4, 3.5.
- **Acceptance criteria:**
  - [ ] From a production fixture, the skill writes N schema-valid options; the validator flags a fixture premise that contains a banned pattern.
  - [ ] Gate A in `random-pick` locks `premise.md` reproducibly.
  - [ ] Skill reviewed for copyable examples by a separate subagent.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 3.2, 3.4, 3.5, 3.6
- **Prompt strategy:** straight-implementation; skill reviewed in a separate context.
- **Risk flags:** UNCERTAIN-SCOPE

### Run 3.4: Stage 2 — structure and beats

- **Summary:** Write the beats skill that turns a locked premise and the structural-form draw into `beats.yaml`, and a validator for timing and form compliance.
- **Scope:** pipeline stage skill; validator.
- **Files/Modules:** `skills/beats/SKILL.md` (new); `antidefaults/beats.yaml` (new); `validators/beats.py` (new: beats tile `duration_s`, each beat states a change, structural form honored, audio-ready fields present); `tests/test_beats_validator.py` (new).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Pipeline stage 2, §Scope (audio-ready); `docs/glossary.md` [Read] "Beat".
- **Traces to:** `docs/project-definition.md` §Milestones M3.
- **Dependencies:** 3.1
- **Integration points:** consumes `schemas/beats.schema.json` (M1 — change needs an ADR); output feeds stage 4 (1.9) in place of fixtures.
- **Acceptance criteria:**
  - [ ] Beats with a gap or overrun fail; a palindrome-form fixture that isn't palindromic fails.
  - [ ] Skill output from a premise fixture validates and feeds stage 4 to a `shots.yaml`.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 3.2, 3.3, 3.5, 3.6
- **Prompt strategy:** TDD for the validator; skill straight-implementation.
- **Risk flags:** none

### Run 3.5: Story critic and loop-back

- **Summary:** Write the critic skill for premise and beats that runs in a separate subagent context, emits a schema-valid critic report, and sends failures back to the producing stage.
- **Scope:** critic skill; loop-back wiring.
- **Files/Modules:** `skills/critic-story/SKILL.md` (new: reads only the artifact and its upstream, never the generator's reasoning); `studio/critique.py` (new: spawns the critic in a separate context, validates the report, returns pass or loop-back with reasons; bounded retries recorded in the manifest); `tests/test_critique.py` (new: subprocess boundary stubbed; asserts the critic receives no generator transcript).
- **Spec-refs touched:** `CLAUDE.md` [Read] §Global bans (a model never grades its own output); `docs/glossary.md` [Read] "Critic".
- **Traces to:** `docs/project-definition.md` §Milestones M3 ("Critic subagent for premise and beats"); §Risks (self-validation).
- **Dependencies:** 3.1
- **Integration points:** critic report schema (3.1); loop-back used by 3.3, 3.4 and M4's stages.
- **Acceptance criteria:**
  - [ ] The critic invocation's inputs contain only artifact files (asserted).
  - [ ] A failing report loops back once and the retry count lands in the manifest.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 3.2, 3.3, 3.4, 3.6
- **Prompt strategy:** interface-first.
- **Risk flags:** none

### Run 3.6: E2 sweep harness

- **Summary:** Build the sweep harness: hold a production fixed, sweep one knob over 3–5 values, run the affected stages through to blocking renders, and measure artifact diff and keyframe distance.
- **Scope:** `eval/e2/`.
- **Files/Modules:** `eval/e2/sweep.py` (new: reads `eval/knobs.yaml`; reruns from the enforcing stage; renders keyframes via the harness preview profile); `eval/e2/distance.py` (new: artifact text diff + keyframe distance via `eval/metrics/`); `tests/test_sweep.py` (new: a stub knob that changes nothing is reported dead; one that changes frames is live).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Evaluation (E2), §Control surface.
- **Traces to:** `docs/project-definition.md` §Milestones M3 exit gate; H2.
- **Dependencies:** 3.1
- **Integration points:** consumes metrics (2.3), harness, stages 0–4; consumed by 3.7 and 5.3.
- **Acceptance criteria:**
  - [ ] Dead and live stub knobs are classified correctly; results record both artifact and frame distance.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 3.2, 3.3, 3.4, 3.5
- **Prompt strategy:** TDD.
- **Risk flags:** none

### Run 3.7: Sweep every story knob (exit gate)

- **Summary:** Run the E2 sweep for every knob in `eval/knobs.yaml`'s story rows, wire or remove dead knobs, and record the evidence.
- **Scope:** integration; exit-gate evidence.
- **Files/Modules:** `eval/reports/e2-story/report.md` (new: generated); `eval/knobs.yaml` (extend: status per knob); stage skills/validators from 3.2–3.4 (fix dead knobs as found — via `/bug-fix` if a defect).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Milestones M3 exit gate, §Control surface — removing a knob listed there is a proposed change at close.
- **Traces to:** exit gate "Knobs proven"; H2.
- **Dependencies:** 3.2, 3.3, 3.4, 3.5, 3.6
- **Integration points:** everything in M3.
- **Acceptance criteria:**
  - [ ] Every story knob shows non-zero artifact and keyframe distance, or is removed with a recorded reason.
  - [ ] The report lists seeds, values swept and manifests.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 2 sessions — sweeps are render-bound (knobs × 3–5 values × blocking renders) and dead-knob fixes are found mid-run.
- **Parallelizable with:** none (integration)
- **Prompt strategy:** straight-implementation.
- **Risk flags:** UNCERTAIN-SCOPE

## Milestone 4: Full production

**Theme:** close the loop from locked animatic to finished, assembled film.
**Testable capability:** `studio/pipeline.py` runs one seed from stage 0 to an assembled film with human input only at Gates A–C, with a complete production manifest.
**Session estimate:** 9 sessions
**Entry criteria:** M3 exit gate passed; render-hardware split decided (finals on the M5 Max).
**Exit criteria / Definition of Done:** exit gate "First full short" — seed to finished film with human input only at gates; the manifest records per-stage wall time, tokens, render time and each gate decision.
**Testing strategy:** unit (lint rules, assembly timing); Blender integration (generated scene/animation scripts build in background mode); render smoke (preview); final-profile render on one shot; end-to-end pipeline run.
**Key risks:** generated bpy scripts fail in background mode (API drift); final renders too slow for iteration; default-looking code slipping through (centered, symmetric, stock easing).

### Dependency graph

```
├── Run 4.1: pipeline contract — stage registry, generated-script contract, manifest ADR ──┐ (contract-first)
│         ↓                                                                                │
├── Run 4.2: stage 5 — scene build skill                                                  ─┤ (parallel after 4.1)
├── Run 4.3: default-look lint                                                            ─┤
├── Run 4.4: stage 6 — animation skill + motion styles/modules                            ─┤
├── Run 4.5: stage 7 — lighting + final profile                                           ─┤
├── Run 4.6: stage 8 — assembly (audio-ready)                                             ─┤
├── Run 4.7: style library expansion + distinctness check                                 ─┘
│         ↓
└── Run 4.8: pipeline runner end to end — first full short (exit gate)
```

### Run 4.1: Pipeline contract

- **Summary:** Define the stage registry (each stage's inputs, outputs, gate), the contract for generated per-shot scene and animation scripts, and the production manifest extension — with the ADR a post-M1 manifest change requires.
- **Scope:** `studio/pipeline.py` skeleton; manifest schema; ADR.
- **Files/Modules:** `studio/pipeline.py` (new: stage registry and `run(stage, production_dir)` that reads only upstream artifacts and writes its own — re-runnable per stage); `schemas/manifest.schema.json` (extend: per-stage wall time, tokens, critic retries, gate decisions, skill versions); `docs/adr/0003-production-manifest.md` (new) + `docs/adr/README.md` row; `tests/test_pipeline_contract.py` (new: a stage reading a non-upstream artifact fails).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Pipeline, §Artifact schemas (`manifest.json`); `docs/adr/0001-blender-api-baseline.md` [Read].
- **Traces to:** `docs/project-definition.md` §Milestones M4; §Pipeline ("any stage can be re-run from its inputs"); `docs/adr/README.md` (schema change after M1 needs an ADR).
- **Dependencies:** M3 complete.
- **Integration points:** stage registry and generated-script contract consumed by 4.2–4.8. Route `contract` lines to each.
- **Acceptance criteria:**
  - [ ] ADR-0003 `Proposed` with the manifest diff; schema change has positive/negative fixtures.
  - [ ] Stages 0–4 from M1/M3 register and run through `run()`.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** none (contract-first)
- **Prompt strategy:** interface-first.
- **Risk flags:** CRITICAL-PATH

### Run 4.2: Stage 5 — scene build

- **Summary:** Write the scene-build skill that turns locked shots and the style bible into per-shot `bpy` scene scripts using style modules, validated by building in background mode.
- **Scope:** pipeline stage skill.
- **Files/Modules:** `skills/scene-build/SKILL.md` (new: generated scripts satisfy the 4.1 contract, use `blender/lib/` modules, `bpy.data` only); `studio/stages/scene_build.py` (new: runs the skill, then a background-mode build check per script; loop-back on failure); `tests/test_scene_build_stage.py` (new).
- **Spec-refs touched:** `CLAUDE.md` [Read] §Blender; `docs/project-definition.md` [Read] §Pipeline stage 5.
- **Traces to:** `docs/project-definition.md` §Milestones M4; STD-002, STD-005.
- **Dependencies:** 4.1
- **Integration points:** output consumed by 4.4, 4.5; lint from 4.3 runs on its output once landed.
- **Acceptance criteria:**
  - [ ] From a locked M1-style fixture production, every shot's script builds in background mode.
  - [ ] Skill reviewed for copyable examples by a separate subagent.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 4.3, 4.4, 4.5, 4.6, 4.7
- **Prompt strategy:** straight-implementation.
- **Risk flags:** UNCERTAIN-SCOPE

### Run 4.3: Default-look lint

- **Summary:** Build a lint pass over generated scripts that flags default-looking code: round-number positions, centered or symmetric layouts, stock/linear easing, unmodified primitive meshes.
- **Scope:** validator.
- **Files/Modules:** `validators/default_lint.py` (new: AST-based rules, each with an ID and message); `tests/test_default_lint.py` (new: one positive and one negative fixture per rule); `docs/coding-standards.md` (extend STD-005 with a pointer to the lint rule IDs).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §System concept (coding habits row).
- **Traces to:** `docs/project-definition.md` §System concept ("a lint pass flags default-looking code"); STD-005.
- **Dependencies:** 4.1
- **Integration points:** called by 4.2 and 4.4's stages on generated scripts.
- **Acceptance criteria:**
  - [ ] Each rule fires on its positive fixture and not its negative one.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 4.2, 4.4, 4.5, 4.6, 4.7
- **Prompt strategy:** TDD.
- **Risk flags:** none

### Run 4.4: Stage 6 — animation and motion styles

- **Summary:** Write the animation skill that adds keyframe scripts per shot, plus two contrasting motion styles and their easing/timing modules.
- **Scope:** pipeline stage skill; `blender/lib/motion/`; `styles/motion/`.
- **Files/Modules:** `skills/animation/SKILL.md` (new); `blender/lib/motion/easing.py` (new: custom curves from style params, never stock); `styles/motion/<id-a>/style.yaml`, `styles/motion/<id-b>/style.yaml` (new); `tests/test_motion.py` (new, `@pytest.mark.blender`: each motion param moves keyframe values).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Style library (motion dimension), §Pipeline stage 6.
- **Traces to:** `docs/project-definition.md` §Milestones M4; H2 (motion knobs).
- **Dependencies:** 4.1
- **Integration points:** motion style ids added to style bibles; easing reused by `blender/lib/camera/moves.py` (1.7).
- **Acceptance criteria:**
  - [ ] The two motion styles produce distinguishable keyframe curves on the same shot (numeric distance reported).
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 4.2, 4.3, 4.5, 4.6, 4.7
- **Prompt strategy:** straight-implementation.
- **Risk flags:** none

### Run 4.5: Stage 7 — lighting and final profile

- **Summary:** Add lighting from the visual style (key-to-fill ratio and setup), harden the `final` profile (Cycles on Metal), and run preview-then-final per shot through the harness.
- **Scope:** `blender/lib/lighting/`; `blender/harness/profiles.py`.
- **Files/Modules:** `blender/lib/lighting/key_fill.py` (new or extend 1.4's module); `blender/harness/profiles.py` (extend: `final` resolution/samples/denoise from ADR-0001's findings); `studio/stages/render.py` (new: preview all shots, then final); `tests/test_lighting.py` (new, `@pytest.mark.blender`: `key_fill_ratio` moves luminance ratio measurably).
- **Spec-refs touched:** `docs/adr/0001-blender-api-baseline.md` [Read]; `docs/project-definition.md` [Read] §Risks (render cost).
- **Traces to:** `docs/project-definition.md` §Milestones M4 ("Preview and final render profiles").
- **Dependencies:** 4.1
- **Integration points:** consumed by 4.8; final-profile reproducibility uses the Cycles tolerance from ADR-0001.
- **Acceptance criteria:**
  - [ ] One shot renders at `final` on the M5 Max; render time quoted; two final renders compare within tolerance.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 4.2, 4.3, 4.4, 4.6, 4.7
- **Prompt strategy:** straight-implementation.
- **Risk flags:** none

### Run 4.6: Stage 8 — assembly

- **Summary:** Assemble per-shot renders into the film with shot concatenation and simple transitions from the camera style, mux optional audio tracks (audio-ready), and finalize the production manifest.
- **Scope:** assembly.
- **Files/Modules:** `studio/stages/assemble.py` (new: ffmpeg; transitions limited to the camera style's list; output under `productions/<id>/renders/` — gitignored); `tests/test_assemble.py` (new: synthetic frames → duration and frame count match `shots.yaml`; an optional silent audio track muxes).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Scope (audio-ready, editing deferred), §Pipeline stage 8.
- **Traces to:** `docs/project-definition.md` §Milestones M4.
- **Dependencies:** 4.1
- **Integration points:** consumed by 4.8; reuses `studio/animatic.py` (1.9) where it overlaps — refactor shared concat code rather than duplicate.
- **Acceptance criteria:**
  - [ ] Assembled duration matches `shots.yaml` total ± one frame (ffprobe).
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 4.2, 4.3, 4.4, 4.5, 4.7
- **Prompt strategy:** TDD.
- **Risk flags:** none

### Run 4.7: Style library expansion and distinctness check

- **Summary:** Add the lifecycle's validate step — a fidelity and distinctness check for candidate styles — and use it to admit at least two more visual styles. Further styles run as side quests (`parent: studio-v1`).
- **Scope:** `validators/`; `styles/`.
- **Files/Modules:** `validators/style_distinctness.py` (new: renders a reference scene per style through the harness; distinctness = keyframe distance to every active style above a threshold); `styles/visual/<id-c>/style.yaml`, `styles/visual/<id-d>/style.yaml` (new, names chosen by the user at pre-flight) + their modules under `blender/lib/`; `tests/test_style_distinctness.py` (new).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Style library and lifecycle (validate step).
- **Traces to:** `docs/project-definition.md` §Milestones M4 ("a larger style-module library"); §Style library lifecycle step 3.
- **Dependencies:** 4.1
- **Integration points:** distinctness check reused by style side quests and M5.
- **Acceptance criteria:**
  - [ ] Both new styles pass fidelity (their palette validator) and distinctness against A and B.
  - [ ] A near-duplicate of style A fails distinctness.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 4.2, 4.3, 4.4, 4.5, 4.6
- **Prompt strategy:** TDD for the check; styles straight-implementation.
- **Risk flags:** none

### Run 4.8: First full short (exit gate)

- **Summary:** Wire stages 5–8 into `studio/pipeline.py`, then run one seed end to end with the user deciding at Gates A–C only, and record the evidence.
- **Scope:** integration; exit-gate evidence.
- **Files/Modules:** `studio/pipeline.py` (integrate: stages 5–8, validator/critic loop-backs, gate pauses); `tests/test_pipeline_e2e.py` (new: `random-pick` gates, preview profile, tiny duration); `sidequests/studio-v1/status/run4.8status.md` (evidence).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Milestones M4 exit gate — tick as proposed change at close.
- **Traces to:** exit gate "First full short".
- **Dependencies:** 4.2, 4.3, 4.4, 4.5, 4.6, 4.7
- **Integration points:** everything in M4.
- **Acceptance criteria:**
  - [ ] An end-to-end run with `random-pick` gates passes in the test suite.
  - [ ] A real seed runs to a finished film with human input recorded only at Gates A–C (manifest gate decisions); film path and manifest quoted.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 2 sessions — first end-to-end integration surfaces cross-stage defects, and a final render plus human gates spans more than one sitting.
- **Parallelizable with:** none (integration)
- **Prompt strategy:** TDD; e2e test with auto gates first.
- **Risk flags:** CRITICAL-PATH, UNCERTAIN-SCOPE

## Milestone 5: Experiments

**Theme:** run E1–E5, feed findings back, and accept or reject H1–H3 on the evidence.
**Testable capability:** each experiment has a config, a reproducible run command and a generated report; a results document states each hypothesis's verdict with its evidence.
**Session estimate:** 12 sessions (rating rounds add elapsed time outside sessions)
**Entry criteria:** M4 exit gate passed; Blender version pinned (`docs/plans/followups.md`); rater pool recruited.
**Exit criteria / Definition of Done:** exit gate "Results" — H1–H3 accepted or rejected with the evidence; the quest-close review passes.
**Testing strategy:** reproducibility (manifests for every experiment render); unit tests for new analysis code; pre-registration check (criteria frozen before E1 data).
**Key risks:** criteria shifting after seeing data; compute cost of E1 (20 seeds × 2 arms) and E5 (50 × 2 productions); friendly-rater bias.

### Dependency graph

```
├── Run 5.1: pin Blender + freeze criteria (ADR)          ──┐ (contract-first)
│         ↓                                                 │
├── Run 5.2: E1 — pipeline vs one-shot                     ─┤ (parallel after 5.1)
├── Run 5.3: E2 — full knob sweeps                         ─┤
├── Run 5.4: E3 — style survival + blind matching          ─┤
├── Run 5.5: E4 — gate modes                               ─┤
├── Run 5.6: E5 — catalog + house-style drift              ─┤
├── Run 5.7: feedback → anti-default/fatigue candidates    ─┘
│         ↓
├── Run 5.8: hypothesis results (exit gate)
│         ↓
└── Run 5.9: quest-close review
```

### Run 5.1: Pin Blender and freeze criteria

- **Summary:** Write the ADR pinning the Blender version, update `CLAUDE.md` and the manifest check to enforce it, and freeze E1–E5 criteria and rater instructions before any experiment data exists.
- **Scope:** ADR; doctrine; pre-registration.
- **Files/Modules:** `docs/adr/0004-pin-blender.md` (new) + `docs/adr/README.md` row; `CLAUDE.md` (modify §Blender: "pinned", per the ADR — shown diff, user confirms); `blender/harness/render.py` (extend: refuse to run on a non-pinned version unless `--allow-unpinned`, recorded in the manifest); `scripts/doctor.sh` (extend: Blender-version check from warn to fail; confirm `.python-version` still equals the pinned Blender's bundled Python); `eval/protocol/` (extend: E2–E5 protocols, frozen with a git tag or commit hash cited in each); `docs/plans/followups.md` (close the "Pin Blender version" row).
- **Spec-refs touched:** `CLAUDE.md` [Modify]; `docs/adr/0001-blender-api-baseline.md` [Read]; `docs/project-definition.md` [Read] §Open questions.
- **Traces to:** `docs/plans/followups.md` (Pin Blender before E1); `docs/project-definition.md` §Evaluation (criteria fixed before E1).
- **Dependencies:** M4 complete.
- **Integration points:** frozen protocol commit cited by every experiment report; pinned version checked by the harness.
- **Acceptance criteria:**
  - [ ] The harness refuses an unpinned Blender by default (test).
  - [ ] Each protocol names its frozen commit; the followups row is closed with the commit.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** none (contract-first)
- **Prompt strategy:** straight-implementation.
- **Risk flags:** CRITICAL-PATH

### Run 5.2: E1 — pipeline vs one-shot

- **Summary:** Run 20 seeds through both arms, build blind batches, collect ratings, and report familiarity and quality win rates and embedding spread.
- **Scope:** `eval/e1/`.
- **Files/Modules:** `eval/config/e1.yaml` (new: 20 seeds); `eval/e1/run.py` (extend: full pipeline arm via `studio/pipeline.py` with gate mode from config); `eval/reports/e1/report.md` (generated).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Evaluation E1, §Hypotheses H1.
- **Traces to:** E1; H1.
- **Dependencies:** 5.1
- **Integration points:** consumes M2's tooling; report consumed by 5.8.
- **Acceptance criteria:**
  - [ ] 40 productions with manifests; ratings imported from `eval/feedback/<round>/`; report generated against the frozen protocol.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 2 sessions — 40 productions plus a rating round; the second session imports ratings and reports.
- **Parallelizable with:** 5.3, 5.4, 5.5, 5.6, 5.7
- **Prompt strategy:** straight-implementation.
- **Risk flags:** none

### Run 5.3: E2 — full knob sweeps

- **Summary:** Extend the E2 sweep to every shipped knob (style parameters and gate-adjacent knobs as well as story knobs) and remove or wire any dead knob.
- **Scope:** `eval/e2/`; `eval/knobs.yaml`.
- **Files/Modules:** `eval/knobs.yaml` (extend: all knobs from §Control surface); `eval/e2/sweep.py` (extend: re-run from any stage via `studio/pipeline.py`); `eval/reports/e2/report.md` (generated).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Control surface — knob removal is a proposed change.
- **Traces to:** E2; H2.
- **Dependencies:** 5.1
- **Integration points:** report consumed by 5.8.
- **Acceptance criteria:**
  - [ ] Every knob classified live or removed with reason; report quotes distances and manifests.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 5.2, 5.4, 5.5, 5.6, 5.7
- **Prompt strategy:** straight-implementation.
- **Risk flags:** none

### Run 5.4: E3 — style survival and blind matching

- **Summary:** Render several style bibles, compute validator pass rates, and build a blind matching task where raters match renders to bibles.
- **Scope:** `eval/e3/`.
- **Files/Modules:** `eval/e3/run.py` (new); `eval/raters/matching.py` (new: matching batch + accuracy vs chance); `eval/reports/e3/report.md` (generated); `tests/test_matching.py` (new).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Evaluation E3, §Hypotheses H3.
- **Traces to:** E3; H3.
- **Dependencies:** 5.1
- **Integration points:** report consumed by 5.8.
- **Acceptance criteria:**
  - [ ] Validator pass rates and matching accuracy (with chance level) reported.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session (rating round is elapsed time)
- **Parallelizable with:** 5.2, 5.3, 5.5, 5.6, 5.7
- **Prompt strategy:** TDD for the matching scorer.
- **Risk flags:** none

### Run 5.5: E4 — gate modes

- **Summary:** Run the same seeds with gates set to human, auto-pick and random-pick, and compare divergence and quality by mode.
- **Scope:** `eval/e4/`.
- **Files/Modules:** `eval/config/e4.yaml` (new); `eval/e4/run.py` (new); `eval/reports/e4/report.md` (generated).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Evaluation E4.
- **Traces to:** E4 ("What does the human add?").
- **Dependencies:** 5.1
- **Integration points:** report consumed by 5.8.
- **Acceptance criteria:**
  - [ ] Spread and quality reported per gate mode; gate decisions present in every manifest.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 5.2, 5.3, 5.4, 5.6, 5.7
- **Prompt strategy:** straight-implementation.
- **Risk flags:** none

### Run 5.6: E5 — catalog and house-style drift

- **Summary:** Build the cross-production catalog (read only as negative examples by the ideation skill) and run sequential productions with catalog awareness on vs off, tracking embedding spread over time.
- **Scope:** catalog; `eval/e5/`.
- **Files/Modules:** `studio/catalog.py` (new: indexes past productions' premises, styles and keyframe embeddings); `skills/premise/SKILL.md` (extend: catalog policy — "don't repeat these" only); `eval/e5/run.py` (new); `eval/reports/e5/report.md` (generated).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §System concept (cross-production catalog), §Evaluation E5.
- **Traces to:** E5; §Risks (house-style convergence).
- **Dependencies:** 5.1
- **Integration points:** report consumed by 5.8.
- **Acceptance criteria:**
  - [ ] Catalog-on and catalog-off series run at the protocol's size (or a reduced size with the reduction recorded as a deviation); spread-over-time plotted.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 2 sessions — catalog build plus a long unattended production series; compute cost per Input Gaps.
- **Parallelizable with:** 5.2, 5.3, 5.4, 5.5, 5.7
- **Prompt strategy:** interface-first for the catalog.
- **Risk flags:** UNCERTAIN-SCOPE

### Run 5.7: Feedback into anti-defaults and fatigue candidates

- **Summary:** Write the skill that turns free-text rater answers into anti-default and fatigue candidates for human review, and grow the anti-default lists from the rounds run so far.
- **Scope:** feedback skill; `antidefaults/`.
- **Files/Modules:** `skills/feedback-triage/SKILL.md` (new: candidates only; a human confirms each); `studio/feedback.py` (new: reads `eval/feedback/<round>/` CSVs, writes a candidates file); `antidefaults/*.yaml` (extend, after confirmation); `tests/test_feedback.py` (new).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Feedback, §Style library (fatigue, retire).
- **Traces to:** `docs/project-definition.md` §Milestones M5 ("Grow anti-default lists from rater feedback").
- **Dependencies:** 5.1
- **Integration points:** grown lists consumed by stages 1–4; fatigue candidates feed style retirement (human-confirmed).
- **Acceptance criteria:**
  - [ ] A sample feedback CSV yields candidates with source rows cited; nothing lands in `antidefaults/` without a recorded confirmation.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** 5.2, 5.3, 5.4, 5.5, 5.6
- **Prompt strategy:** TDD for the CSV path; skill straight-implementation.
- **Risk flags:** none

### Run 5.8: Hypothesis results (exit gate)

- **Summary:** Synthesize E1–E5 into one results document stating each hypothesis's verdict against its pre-registered target, with links to reports and manifests, and feed findings back into skills as proposed changes.
- **Scope:** results; exit-gate evidence.
- **Files/Modules:** `eval/reports/results.md` (new); `sidequests/studio-v1/status/run5.8status.md` (evidence).
- **Spec-refs touched:** `docs/project-definition.md` [Read] §Hypotheses — target revisions are proposed changes, not edits.
- **Traces to:** exit gate "Results"; H1–H3.
- **Dependencies:** 5.2, 5.3, 5.4, 5.5, 5.6, 5.7
- **Integration points:** feeds `### Exit gate evidence` and `### Open questions surfaced`.
- **Acceptance criteria:**
  - [ ] H1, H2, H3 each marked accepted or rejected against the frozen target, citing the report and protocol commit.
  - [ ] Deviations from protocol listed.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** none
- **Prompt strategy:** straight-implementation.
- **Risk flags:** none

### Run 5.9: Quest-close review

- **Summary:** Audit the quest across five dimensions and write `sidequests/studio-v1/status/run5.9status.md` with pass / fail / triaged per dimension and a "blocks closure?" verdict at the top.
- **Scope:** quest audit.
- **Files/Modules:** `sidequests/studio-v1/status/run5.9status.md` (new); `docs/adr/` (new ADRs for project-level decisions found); `docs/plans/followups.md` (extend with durable risks).
- **Spec-refs touched:** all four [Read]; ADR drafts [Modify].
- **Traces to:** `/generate-rollout` quest-close review.
- **Dependencies:** 5.8
- **Integration points:** feeds `/sidequest close studio-v1`.
- **Acceptance criteria:**
  - [ ] **Reviews ran:** `/code-review` or `/complexity-review` covered the implementation runs; Critical/High findings fixed via `/bug-fix` or deferred with rationale; stage skills and critics reviewed in a separate subagent context.
  - [ ] **Per-run discipline:** every run has a status report; fixes went through `/bug-fix`; contract-first and TDD ordering honored where the prompt strategy called for them.
  - [ ] **Knowledge promoted:** each "Architecture Decisions" entry classified quest-local or project-level → ADR drafted; each milestone "Key risks" entry and realized risk classified quest-local or durable → `docs/plans/followups.md`.
  - [ ] **Deferred findings routed:** every deferred finding, Open Issue and `TODO:`/`FIXME:` in touched code has one disposition.
  - [ ] **Closure surface populated:** `### Proposed changes to referenced persistent specs` and `### Open questions surfaced` filled.
  - [ ] `scripts/run_tests.sh` passes
- **Session estimate:** 1 session
- **Parallelizable with:** none
- **Prompt strategy:** straight-implementation.
- **Risk flags:** none

## Spec refs

- `docs/project-definition.md` — milestone task and exit-gate boxes, ticked at close via shown diffs
- `docs/adr/0001-blender-api-baseline.md` — Blender API probe findings (written in M0)
- `docs/glossary.md` — ubiquitous language; changes travel with an ADR
- `CLAUDE.md` — studio doctrine (e.g. pinning the Blender version before E1); changes travel with an ADR
- `schemas/` — JSON Schemas for every artifact (M0–M4); changes after M1 need an ADR
- `styles/` — style specs per dimension (M1 visual and camera, M4 motion and library expansion)
- `docs/adr/` — ADRs this quest writes (0002 toolchain/layout, 0003 production manifest, 0004 Blender pin, plus any from the close review)

## Runs

<run status reports land in status/>

## Deliverable

### Exit gate evidence

### Artifacts

### Proposed changes to referenced persistent specs

### Open questions surfaced
