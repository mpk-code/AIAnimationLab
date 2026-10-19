# Run 0.2: Test runner, Python project and harness contract — status

**Quest:** studio-v1 (feature)  **Date:** 2026-10-19  **Status:** COMPLETE
**Spec trace:**
- `sidequests/studio-v1/studio-v1-rollout.md:117` (Run 0.2 spec; Files/Modules `:121`; acceptance criteria `:126-132`).
- `sidequests/studio-v1/studio-v1-rollout.md:40` (Input Gaps: host-side package layout).
- `sidequests/studio-v1/studio-v1-rollout.md:79` (M0 testing strategy).
- `docs/project-definition.md:138` §Repository structure.
- `CLAUDE.md:18` §Blender, `CLAUDE.md:46` §Tests.
- `docs/test-strategy.md:15` §Rules (blender marker `:18`).
- `docs/coding-standards.md:9` STD-001, `:13` STD-002, `:17` STD-003.
- `docs/adr/0000-template.md`.
- `sidequests/studio-v1/status/run0.1status.md` (carry-forward contract; proposed §Blender wording).

User decisions 2026-10-19 (relayed by the parent at plan approval):
- uv config only in `uv.toml`;
- just single-lane recipes call `scripts/run_tests.sh <lane>`;
- `fake-bpy-module-5.2==20260730`;
- no shellcheck lane (followup row);
- the CLAUDE.md diff is confirmed and applied.

## Acceptance Criteria Checklist
- [x] `scripts/run_tests.sh` exits 0 on the empty suite and exits non-zero when a deliberately failing test or a ruff violation is added (checked, then removed); `just ci` gives the same exit code and output. Evidence: blocks 1–3 below. The only difference between the `just ci` output and the bare run is a pytest timing figure.
- [x] The gate fails in the environment lane when `.python-version` disagrees with Blender's bundled Python, and in the locks lane when `pyproject.toml` gains a dependency without `uv lock`. Each case was checked and then reverted, and each fails before any later lane runs. Evidence: blocks 4–5.
- [x] A `@pytest.mark.blender` test is collected when `BLENDER_BIN` resolves, and is reported as skipped with a reason when it doesn't. Evidence: block 6 and the final run.
- [x] The pin test fails when `uv.toml`'s `required-version` differs from the Makefile (checked, then reverted). Evidence: block 7. uv itself also refuses to run, so in the bare gate the environment lane is what fires first (see Open Issues).
- [x] ADR-0002 is `Proposed` and states the toolchain, layout and scene-script contract one bullet each. It contains a little more than one sentence per bullet: the gate is its own bullet, and the `sys.path` rule is attached to the contract bullet. The index row is in "Shared-file edits" below, for the parent to apply.
- [x] `scripts/run_tests.sh` passes. Evidence: final block, run bare in the real tree with Run 0.3's `blender/probe/api_probe.py` present (mypy checked 3 source files).

### Evidence

**Where each check ran.** Mutations 1–7 ran in a scratchpad copy of the tree, made with `rsync` that excluded `.git`, `.venv`, caches and `blender/probe/`. That way they could not disturb Run 0.3, which was working in the same tree. Every Run 0.2 file in the copy was confirmed byte-identical to the real tree (`cmp`: pyproject.toml, uv.lock, uv.toml, justfile, CLAUDE.md, scripts/run_tests.sh, scripts/doctor.sh, tests/conftest.py, tests/test_toolchain_pins.py, the ADR and .python-version all reported "same"). The final gate ran bare in the real tree.

Block 1: bare gate (copy) and `just ci` (copy):

```
$ bash scripts/run_tests.sh; echo exit=$?
=== lane: environment
==> pinned toolchain (.toolchain/)
  ok    uv 0.12.24
  ok    just 1.53.0
  ok    Python 3.13.13 (uv-managed: /Users/mpkirby/.local/share/uv/python/cpython-3.13.13-macos-aarch64-none/bin/python3.13)
==> Blender (/Applications/Blender.app)
  ok    Blender 5.2.2
  ok    Blender's bundled Python 3.13.13 = .python-version
==> outside tools (Brewfile)
  ok    ffmpeg: ffmpeg version 9.0.2 Copyright (c) 2000-2026 the FFmpeg developers
  ok    shellcheck: 0.11.0
doctor: all checks pass.
=== lane: environment — ok
=== lane: locks
Resolved 25 packages in 4ms
=== lane: locks — ok
=== lane: static
All checks passed!
17 files already formatted
Success: no issues found in 2 source files
=== lane: static — ok
=== lane: unit
...
collected 5 items / 1 deselected / 4 selected
tests/test_toolchain_pins.py ....                                        [100%]
======================= 4 passed, 1 deselected in 0.02s ========================
=== lane: unit — ok
=== lane: blender
...
collected 5 items / 4 deselected / 1 selected
tests/test_toolchain_pins.py .                                           [100%]
======================= 1 passed, 4 deselected in 1.01s ========================
=== lane: blender — ok
=== run_tests.sh: all lanes ok (environment locks static unit blender)
exit=0
$ just ci > c1_just.txt; echo exit=$?   # then: diff c1_bare.txt c1_just.txt
44c44
< ======================= 1 passed, 4 deselected in 1.01s ========================
---
> ======================= 1 passed, 4 deselected in 0.73s ========================
```

Block 2: deliberately failing test (`tests/test_tmp_fail.py`: `assert len("ab") == 3`), then removed. A first attempt with `assert 1 == 2` was rejected earlier, in the static lane, by mypy's `comparison-overlap`; that also counts as non-zero, but the check was redone so that the unit lane is the one that fails.

```
exit=1
=== lane: environment — ok
=== lane: locks — ok
=== lane: static — ok
=== lane: unit
E       AssertionError: assert 2 == 3
E        +  where 2 = len('ab')
=== lane: unit — FAILED; later lanes not run
```

Block 3: ruff violation (`tests/tmp_lint.py`: `import os`), then removed:

```
=== lane: static
F401 [*] `os` imported but unused
Found 1 error.
=== lane: static — FAILED; later lanes not run
exit=1
```

Block 4: `.python-version` set to 3.13.12, then restored to 3.13.13:

```
=== lane: environment
  FAIL  no uv-managed Python 3.13.12 (.python-version) found. Fix: make worktree-init, which installs exactly .python-version; if the Blender bundled-Python check below also FAILs, correct .python-version first.
  FAIL  Blender's bundled Python is 3.13.13, but .python-version is 3.13.12. Host Python must equal it. Fix: set .python-version to 3.13.13 and run make worktree-init (Python and Blender pins move together).
doctor: something needs action (FAIL lines above).
=== lane: environment — FAILED; later lanes not run
exit=1
```

Block 5: `"rich>=13"` added to `dependencies` without `uv lock`, then reverted:

```
17:    "rich>=13",
=== lane: environment — ok
=== lane: locks
error: The lockfile at `uv.lock` needs to be updated, but `--check` was provided.
=== lane: locks — FAILED; later lanes not run
exit=1
$ cmp uv.lock lock.bak && echo "uv.lock untouched"
uv.lock untouched
```

Block 6: `BLENDER_BIN=/nonexistent/Blender`. With the default path, the same test is collected and passes (block 1, and below).

```
exit=0
=== lane: blender
!!! SKIPPED: blender lane — BLENDER_BIN is not executable: /nonexistent/Blender
!!! Blender-dependent tests did NOT run; this gate says nothing about them.
SKIPPED [1] tests/test_toolchain_pins.py:62: BLENDER_BIN is not executable: /nonexistent/Blender
======================= 1 skipped, 4 deselected in 0.01s =======================
=== lane: blender — ok
$ bash scripts/run_tests.sh blender
collected 5 items / 4 deselected / 1 selected
======================= 1 passed, 4 deselected in 0.54s ========================
=== run_tests.sh: all lanes ok (blender)
```

Block 7: `uv.toml` `required-version` set to `==0.12.23`, then restored to `==0.12.24`:

```
$ .venv/bin/pytest tests/test_toolchain_pins.py -q
E       AssertionError: assert '==0.12.23' == '==0.12.24'
1 failed, 4 passed in 0.54s
$ .toolchain/uv/bin/uv lock --check
error: Required uv version `==0.12.23` does not match the running version `0.12.24`. Update `uv` by running `uv self update 0.12.23`.
$ bash scripts/run_tests.sh   # same edit
=== lane: environment
  FAIL  no uv-managed Python 3.13.13 (.python-version) found. Fix: make worktree-init, ...
=== lane: environment — FAILED; later lanes not run
exit=1
```

Single-lane recipes and shellcheck (real tree):

```
$ just test | tail -1;  just lint | tail -1;  just typecheck | tail -1
=== run_tests.sh: all lanes ok (unit)
=== run_tests.sh: all lanes ok (ruff)
=== run_tests.sh: all lanes ok (mypy)
$ shellcheck scripts/*.sh; echo shellcheck=$?
shellcheck=0
```

Final run: the bare gate in the real tree, with `blender/probe/api_probe.py` (Run 0.3) present:

```
$ scripts/run_tests.sh; echo exit=$?
=== lane: environment
  ok    uv 0.12.24
  ok    just 1.53.0
  ok    Python 3.13.13 (uv-managed: /Users/mpkirby/.local/share/uv/python/cpython-3.13.13-macos-aarch64-none/bin/python3.13)
  ok    Blender 5.2.2
  ok    Blender's bundled Python 3.13.13 = .python-version
  ok    ffmpeg: ffmpeg version 9.0.2 Copyright (c) 2000-2026 the FFmpeg developers
  ok    shellcheck: 0.11.0
doctor: all checks pass.
=== lane: environment — ok
=== lane: locks
Resolved 25 packages in 3ms
=== lane: locks — ok
=== lane: static
All checks passed!
18 files already formatted
Success: no issues found in 3 source files
=== lane: static — ok
=== lane: unit
collected 5 items / 1 deselected / 4 selected
tests/test_toolchain_pins.py ....                                        [100%]
======================= 4 passed, 1 deselected in 0.01s ========================
=== lane: unit — ok
=== lane: blender
collected 5 items / 4 deselected / 1 selected
tests/test_toolchain_pins.py .                                           [100%]
======================= 1 passed, 4 deselected in 0.53s ========================
=== lane: blender — ok
=== run_tests.sh: all lanes ok (environment locks static unit blender)
exit=0
```

(The pytest session headers are trimmed in the blocks above. Everything else is verbatim.)

## What Changed
- `pyproject.toml`: new. A virtual project. Holds `requires-python = "==3.13.*"`, the deps (jsonschema, numpy, pillow, pyyaml) and a dev group (pytest, ruff, mypy, types-*, `fake-bpy-module-5.2==20260730`), with floors at the locked versions. Configures pytest (`blender` marker, `--strict-markers`, `-rs`), ruff (py313, line 100, E/F/W/I/B/UP/RUF, excluding `.claude`) and mypy (strict, `files=["."]`, excluding `.claude/`, `.venv/`, `.toolchain/`). There is no `[tool.uv]` table.
- `uv.lock`: new. 25 packages.
- `uv.toml`: comment only. The old text said pyproject repeats these settings; that is now false. The values are unchanged.
- `scripts/run_tests.sh`: new. The gate. Its lanes are environment → locks → static (ruff, mypy) → unit → blender, and it stops at the first failure. An optional `<lane>` argument, or `ruff`/`mypy`, runs one lane. The blender lane skips loudly when `BLENDER_BIN` does not resolve.
- `scripts/doctor.sh`: one flag plus a comment. `uv python find` now gets `--system`. Without it, once a `.venv` exists (first created in this run), uv returns `.venv/bin/python` and doctor FAILs the managed-Python check. See Architecture Decisions.
- `tests/conftest.py`: new. Resolves `BLENDER_BIN`, provides the `blender_bin` fixture, and skips `blender` items with a reason when the binary is missing.
- `tests/test_toolchain_pins.py`: new. Five tests:
  - uv.toml `required-version` equals the Makefile's `UV_VERSION`;
  - pyproject has no `[tool.uv]`;
  - `requires-python` is the pinned minor;
  - the running interpreter equals `.python-version`;
  - (blender) Blender's bundled Python equals `.python-version`.
- `justfile`: adds `ci` (runs the gate bare), `test` (unit), `lint` (ruff) and `typecheck` (mypy), each calling `scripts/run_tests.sh`.
- `docs/adr/0002-python-toolchain-and-layout.md`: new. Proposed. Covers the toolchain, the gate, the layout, the scene-script contract and `sys.path`, and contains the CLAUDE.md diff.
- `CLAUDE.md`: §Blender gets a new first bullet (bootstrap commands); §Tests now gives the lane order and states that `just ci` is an alias. This is exactly the diff recorded in ADR-0002.

## How to Test
```
scripts/run_tests.sh                         # the gate, bare
just ci                                      # same thing
BLENDER_BIN=/nonexistent scripts/run_tests.sh   # blender lane: loud SKIPPED + pytest -rs reason
just test | just lint | just typecheck       # single lanes
```

## Architecture Decisions
- **uv config only in `uv.toml`** (user decision). Measured in the Phase 1 scratchpad probe: uv 0.12.24 ignores `[tool.uv]` in a `pyproject.toml` next to a `uv.toml` and only warns. `test_pyproject_has_no_uv_table_for_uv_to_ignore` guards this. Recorded in ADR-0002.
- **mypy scope is `files = ["."]` with excludes**, not the planned `["tests", "blender"]`. mypy exits non-zero with "There are no .py[i] files in directory 'blender'" whenever `blender/` holds no Python. That is the state of a fresh clone before Run 0.3's probe lands, since git keeps no empty directories. Seen in the copy, which excluded `blender/probe/`.
- **ruff and mypy exclude `.claude/`.** On the first gate run, ruff found 97 findings in the ported dev-process skill scripts (`.claude/skills/...`). They are not studio code (CLAUDE.md "Two kinds of skills"), so they are left as they are. Recorded in ADR-0002 Consequences.
- **The static lane has two halves, `ruff` and `mypy`**, so `just lint` and `just typecheck` differ without restating any command.
- **doctor.sh fix (`--system`)** is a one-flag change to Run 0.1 code. I made it in this run because the gate could not pass without it: the first `.venv`, created here, triggered it. It is held by the environment lane of every gate run. I did not file a separate defect; the parent may want one recorded via `/defect-filing` for audit.
- **ADR candidate:** none beyond ADR-0002.

## Open Issues
- issue #1: doctor reports "no uv-managed Python … found" when `uv.toml`'s `required-version` disagrees with the pinned uv — its `2> /dev/null` swallows uv's own clear message. The gate still fails before any later lane. Filed 2026-10-19 via `/defect-filing`; not fixed in this run.
- not a defect: doctor FAILs on any machine without `/Applications/Blender.app`, so the gate cannot pass there. The blender lane's loud-skip path is reachable only through a `BLENDER_BIN` override. This is acceptable while both Macs have Blender. Recorded in ADR-0002 Consequences.
- not a defect: the shellcheck lane was deferred (user decision). The followup row is below for the parent.
- not a defect: Run 0.3's `blender/probe/api_probe.py` failed static during this run: first ruff E501 plus one format finding and 6 mypy errors, later 2 mypy errors (`bpy_prop_array` len/Any return). It passed by the final run, presumably after Run 0.3 fixed it. I made no edits to it.

## Shared-file edits for the parent to apply

**1. `docs/adr/README.md`: replace the `| — | — | — |` row with:**
```
| [0002](0002-python-toolchain-and-layout.md) | Python toolchain, test gate, host-side package layout and scene-script contract | Proposed |
```
(Run 0.3's ADR-0001 row goes above it.)

**2. Rollout `sidequests/studio-v1/studio-v1-rollout.md`, Run 0.2:**
- Insert after the `### Run 0.2: …` heading (before `- **Summary:**`):
  ```
  - **Status:** COMPLETE 2026-10-19 — `sidequests/studio-v1/status/run0.2status.md`
  ```
- Tick all six acceptance criteria (`:127-132`), changing `- [ ]` to `- [x]`.
- Files/Modules correction. In the `pyproject.toml` + `uv.lock` clause, replace
  `` `[tool.uv] required-version` equal to the Makefile's `UV_VERSION`, ``
  with
  `` no `[tool.uv]` table (uv ignores it next to `uv.toml`, which stays the only uv config and holds `required-version` equal to the Makefile's `UV_VERSION` — Run 0.2 decision), ``
  and replace
  `` how `bpy` is typed — `fake-bpy-module` stubs or a scoped `ignore_missing_imports` ``
  with
  `` `bpy` typed by `fake-bpy-module-5.2==20260730` (Run 0.2 decision) ``.
- The Run 0.1 Integration points line (`pyproject.toml` (`requires-python`, `[tool.uv] required-version`) must equal) is now inaccurate. Suggested replacement: `` Run 0.2's `pyproject.toml` `requires-python` must admit `.python-version`, and `uv.toml`'s `required-version` must equal `UV_VERSION` ``.

**3. Carry-forward ledger: append (4 lines):**
```
- [0.2] -> 0.4,0.5,0.6 | contract | Scene script = build(seed: int) -> None + module FRAME_COUNT: int; bpy.data only, no render/output settings; in-Blender entry puts repo root on sys.path (ADR-0002).
- [0.2] -> surface | gotcha | uv ignores [tool.uv] in a pyproject next to uv.toml: uv settings live only in uv.toml; tests/test_toolchain_pins.py guards it.
- [0.2] -> 5.1 | gotcha | fake-bpy-module-5.2==20260730 (pyproject dev group) moves with the Blender pin, alongside .python-version and BLENDER_EXPECTED.
- [0.2] -> 0.7 | contract | Blender tests take @pytest.mark.blender + the blender_bin fixture (tests/conftest.py); run_tests.sh's blender lane runs them — add no new lane.
```
**Fold** the consumed 0.1 line into the folded band:
```
~ uv/Python pins: uv.toml required-version == Makefile UV_VERSION; pyproject requires-python admits .python-version — held by tests/test_toolchain_pins.py (est. 0.1, enforced 0.2)
```

**4. `docs/plans/followups.md`, Open table row:**
```
| shellcheck lane in the gate | Next run that adds or changes a `scripts/*.sh` file | Add `shellcheck scripts/*.sh` to `scripts/run_tests.sh`'s static lane and a line to ADR-0002 | `sidequests/studio-v1/status/run0.2status.md` |
```

## Carry-forward
Handed to the parent to append (see "Shared-file edits" item 3). This run did not write the ledger.

## Test Counts
`scripts/run_tests.sh`, bare, real tree: unit 4 passed / 1 deselected; blender 1 passed / 4 deselected; 0 failed, 0 skipped. ruff clean (18 files), mypy clean (3 source files). No renders. The gate's wall time is a few seconds; this is a summary, not measured.

## Confidence Report
A. Assumptions made:
- The scratchpad copy stands in for the real tree in the mutation checks. Its files were byte-identical, and blender/probe was excluded.
- Dependency floors equal the versions locked today. The exact pins live in `uv.lock`.

B. Deviations from existing patterns:
- mypy `files=["."]` instead of the planned `["tests","blender"]`.
- `.claude/` excluded from lint and type-checking.
- doctor.sh `--system` fix to Run 0.1 code.
- just recipes call lanes of the gate instead of restating commands. This differs from docketScore, where recipes are the lanes.

C. Thin context: no spec fixes the ruff rule set. E/F/W/I/B/UP/RUF is my choice; amend it in ADR-0002 if wanted.

D. Conflicts found: the rollout's `[tool.uv] required-version` in pyproject conflicts with uv's actual precedence. Resolved by user decision; the rollout fix is in item 2.

E. Complexity concentrations: none. `scripts/run_tests.sh` is 59 lines.

## Next Unblocked Run
0.4 (after 0.2; it consumes Run 0.3's engine IDs), 0.5 and 0.6 (after 0.2). 0.3 runs in parallel.
