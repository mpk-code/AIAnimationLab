# Run 0.1: Pinned toolchain bootstrap — status

**Quest:** studio-v1 (feature)  **Date:** 2026-10-19  **Status:** COMPLETE
**Spec trace:** `sidequests/studio-v1/studio-v1-rollout.md:97` (Run 0.1 spec; acceptance criteria at `:107`; Input Gaps LFS bullet `:41`); `CLAUDE.md:18-23` §Blender ("Not yet pinned; record the version in every manifest. Pin before E1."); `CLAUDE.md:49` §Shell; `docs/project-definition.md:275` §Risks (Blender API drift row); `docs/coding-standards.md:9` STD-001 (pins read from the Makefile, not restated); `docs/plans/followups.md:11` (Pin Blender version row). User decisions 2026-10-19 (relayed at plan approval): drop git-lfs, merge installers, no shared cache, Info.plist Blender check.

## Acceptance Criteria Checklist
- [x] In a fresh worktree, `make worktree-init` leaves `.toolchain/uv/bin/uv --version` = 0.12.24, `.toolchain/just/bin/just --version` = 1.53.0, and `uv python find` resolving a uv-managed 3.13.13 (not Homebrew's 3.14) — "fresh" reproduced in place: `.toolchain/` deleted, then bootstrapped under `env -i` with `PATH=/usr/bin:/bin:/usr/sbin:/sbin` (no Homebrew, no `~/.local/bin`, so the machine uv/just could not be used). A throwaway `git worktree` was not used: it checks out HEAD, which does not hold this run's uncommitted files. 3.13.13 was not installed before this run, so `uv python install` was exercised (output in the first block). Evidence below.
- [x] A corrupted expected sha256 (in a temp copy) makes the install script refuse the download — temp copy of `Makefile`, `scripts/`, `.uv.sha256`, `.just.sha256` under the session scratchpad, first hex digit of each aarch64 line flipped; both refuse with exit 1 and leave `.toolchain/` empty; temp copy deleted afterwards.
- [x] `make doctor` exits 0 on this machine; changing `.python-version` to a value that differs from Blender's bundled Python makes it exit 1 naming the fix (checked, then reverted) — `scripts/doctor.sh` exits 1; `make doctor` reports make's own exit 2 for a failed recipe (see Confidence Report D). Reverted to 3.13.13 and re-checked: exit 0. `git status --porcelain` identical before and after the doctor runs (read-only).
- [x] `shellcheck scripts/*.sh` is clean — shellcheck 0.11.0, exit 0 (after fixing two SC2015 notes in `install_tool.sh`; the bootstrap and the corrupted-sha check were re-run after that fix, outputs below are post-fix).

### Evidence

Criterion 1 — bootstrap from a stripped PATH (`rm -rf .toolchain && env -i HOME="$HOME" PATH=/usr/bin:/bin:/usr/sbin:/sbin make worktree-init`). First run (Python not yet installed):

```
==> uv: fetching uv-aarch64-apple-darwin.tar.gz from https://github.com/astral-sh/uv/releases/download/0.12.24/
==> uv: 0.12.24 at /Users/mpkirby/projects/AIAnimationLab/.toolchain/uv/bin
==> just: fetching just-1.53.0-aarch64-apple-darwin.tar.gz from https://github.com/casey/just/releases/download/1.53.0/
==> just: 1.53.0 at /Users/mpkirby/projects/AIAnimationLab/.toolchain/just/bin
Downloading cpython-3.13.13-macos-aarch64-none (download) (23.9MiB)
 Downloaded cpython-3.13.13-macos-aarch64-none (download)
Installed Python 3.13.13 in 1.69s
 + cpython-3.13.13-macos-aarch64-none
==> no pyproject.toml yet; skipping uv sync
exit=0
```

Final run, after the SC2015 fix:

```
==> uv: fetching uv-aarch64-apple-darwin.tar.gz from https://github.com/astral-sh/uv/releases/download/0.12.24/
==> uv: 0.12.24 at /Users/mpkirby/projects/AIAnimationLab/.toolchain/uv/bin
==> just: fetching just-1.53.0-aarch64-apple-darwin.tar.gz from https://github.com/casey/just/releases/download/1.53.0/
==> just: 1.53.0 at /Users/mpkirby/projects/AIAnimationLab/.toolchain/just/bin
Python 3.13.13 is already installed
==> no pyproject.toml yet; skipping uv sync
exit=0
```

```
$ .toolchain/uv/bin/uv --version
uv 0.12.24 (5411378eb 2026-10-08 aarch64-apple-darwin)
$ .toolchain/just/bin/just --version
just 1.53.0
$ uv python find   # with the full login PATH (Homebrew python3 3.14.4 first)
/opt/homebrew/bin/python3
Python 3.14.4
/Users/mpkirby/.local/share/uv/python/cpython-3.13.13-macos-aarch64-none/bin/python3.13
$ uv python dir
/Users/mpkirby/.local/share/uv/python
```

Criterion 2:

```
$ bash scripts/install_tool.sh uv <tmp-root>   # aarch64 line 0c4346de… -> 1c4346de…
==> uv: fetching uv-aarch64-apple-darwin.tar.gz from https://github.com/astral-sh/uv/releases/download/0.12.24/
error: the release's sha256.sum lists '0c4346de7abdb49495b393b9ec809fe387aa43e586be20fecb972216c1e71732' for uv-aarch64-apple-darwin.tar.gz, not 1c4346de7abdb49495b393b9ec809fe387aa43e586be20fecb972216c1e71732 (.uv.sha256). Nothing was installed.
exit=1
$ bash scripts/install_tool.sh just <tmp-root>  # aarch64 line 27f1361f… -> 37f1361f…
==> just: fetching just-1.53.0-aarch64-apple-darwin.tar.gz from https://github.com/casey/just/releases/download/1.53.0/
error: the release's SHA256SUMS lists '27f1361f2e4fb5d733837f1a9f80f85c237e5a36c75ee14961e59141713aa4ed' for just-1.53.0-aarch64-apple-darwin.tar.gz, not 37f1361f2e4fb5d733837f1a9f80f85c237e5a36c75ee14961e59141713aa4ed (.just.sha256). Nothing was installed.
exit=1
$ ls -A <tmp-root>/.toolchain; echo entries=$(ls -A <tmp-root>/.toolchain | wc -l)
entries=0
```

x86_64-darwin lines (the rollout asks for both; the M1 Mac is aarch64 too, so these serve only an Intel Mac) checked against the published lists:

```
$ x86_64 lines vs published sums
4fa82e37cb94767661f532b001e470b67a186c7260e305bd84ddb78fd545c0b6  uv-x86_64-apple-darwin.tar.gz
bc345a26d40ae4697cb6b2f2ca04cdf1fbdc8c50eba1b40684c8bf3f98555d72  just-1.53.0-x86_64-apple-darwin.tar.gz
bc345a26d40ae4697cb6b2f2ca04cdf1fbdc8c50eba1b40684c8bf3f98555d72  just-1.53.0-x86_64-apple-darwin.tar.gz
(uv published line: 4fa82e37…c0b6  *uv-x86_64-apple-darwin.tar.gz — matches .uv.sha256)
```

Criterion 3:

```
$ make doctor; echo exit=$?
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
exit=0
```

```
$ printf "3.13.12\n" > .python-version; make doctor; echo exit=$?
==> pinned toolchain (.toolchain/)
  ok    uv 0.12.24
  ok    just 1.53.0
  FAIL  no uv-managed Python 3.13.12 (.python-version) found. Fix: make worktree-init
==> Blender (/Applications/Blender.app)
  ok    Blender 5.2.2
  FAIL  Blender's bundled Python is 3.13.13, but .python-version is 3.13.12. Host Python must equal it. Fix: set .python-version to 3.13.13 and run make worktree-init (Python and Blender pins move together).
==> outside tools (Brewfile)
  ok    ffmpeg: ffmpeg version 9.0.2 Copyright (c) 2000-2026 the FFmpeg developers
  ok    shellcheck: 0.11.0
doctor: something needs action (FAIL lines above).
make: *** [doctor] Error 1
exit=2
```

```
$ (.python-version=3.13.12) bash scripts/doctor.sh >/dev/null; echo exit=$?
exit=1
$ printf "3.13.13\n" > .python-version; make doctor >/dev/null; echo exit=$?
exit=0
$ just doctor | tail -1
doctor: all checks pass.
```

Blender warn path (`BLENDER_EXPECTED` temporarily edited to 5.2.3, then restored):

```
$ (BLENDER_EXPECTED temporarily 5.2.3) make doctor > out; echo exit=$?; grep Blender out
exit=0
==> Blender (/Applications/Blender.app)
  warn  Blender 5.2.2, but the Makefile expects 5.2.3 (BLENDER_EXPECTED).
```

Criterion 4:

```
$ shellcheck scripts/*.sh; echo exit=$?
exit=0
$ shellcheck --version | sed -n 2p
version: 0.11.0
```

## What Changed
- `.python-version` — new: `3.13.13` (Blender 5.2.2's bundled Python).
- `uv.toml` — new: `python-preference = "only-managed"`, `required-version = "==0.12.24"`.
- `.uv.sha256`, `.just.sha256` — new: aarch64- and x86_64-apple-darwin lines for the pins (copied from docketScore's files for the same versions; verified against the releases' own lists).
- `Makefile` — new: pins `UV_VERSION`, `JUST_VERSION`, `BLENDER_EXPECTED` (warn-only); `TOOL_PATH`; targets `help`, `tooling-bootstrap`, `worktree-init`, `setup`, `doctor`.
- `scripts/install_tool.sh` — new: `uv|just` installer, three-way SHA-256 check, installs into `.toolchain/<tool>/bin`.
- `scripts/check_tool_version.sh` — new: ported from docketScore.
- `scripts/doctor.sh` — new: read-only ok/warn/FAIL report.
- `Brewfile` — new: `ffmpeg`, `shellcheck`.
- `justfile` — new: PATH export (`.toolchain` first), recipes `default`, `doctor`.
- `.gitignore` — add `.toolchain/`.
- `docs/plans/followups.md` — Open row "Git LFS".
- `sidequests/studio-v1/studio-v1-rollout.md` — Run 0.1 marked COMPLETE and criteria ticked; Files/Modules updated for the merged installer and the dropped git-lfs; Input Gaps LFS bullet points at the followup.
- `sidequests/studio-v1/status/carry-forward.md` — two routed lines appended.

## How to Test
```
rm -rf .toolchain && make worktree-init      # or under env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin
.toolchain/uv/bin/uv --version; .toolchain/just/bin/just --version; .toolchain/uv/bin/uv python find
make doctor                                  # or: just doctor
shellcheck scripts/*.sh
```
`make setup` (runs `brew bundle`) was NOT run in this run, per instruction; it is verified by reading only.

## Architecture Decisions
- One installer for both tools (`scripts/install_tool.sh uv|just`) instead of docketScore's two — user decision, to meet the line budget; it is the refactor docketScore's own TODO in `install_uv.sh` asks for.
- No per-machine download cache: each worktree downloads into its own `.toolchain/` (user decision). Cost: ~20 MB and a network fetch per worktree.
- git-lfs dropped from Brewfile and doctor until the followup's trigger fires (user decision).
- Blender version read from `Contents/Info.plist` (`CFBundleShortVersionString`) rather than by launching Blender (user-accepted assumption).
- `BLENDER_EXPECTED := 5.2.2` lives in the Makefile as a warn-only expectation. ADR candidate: ADR-0004 (Run 5.1) turns it into a pin and doctor's warn into a fail.
- **Proposed doctrine change (not applied):** `CLAUDE.md` §Blender (`CLAUDE.md:18`) should name the bootstrap, e.g. "Bootstrap a machine with `make setup`, a worktree with `make worktree-init`; check with `make doctor`." It travels with ADR-0002 in Run 0.2 (rollout Run 0.2 Spec-refs touched).

## Open Issues
- not a defect: `make doctor` exits 2 (make's code for any failed recipe), while `scripts/doctor.sh` exits 1. User decision 2026-10-19: any non-zero exit means error; criterion satisfied.
- not a defect (fixed in this run): with a wrong `.python-version`, the uv-managed-Python FAIL said only `make worktree-init`, which installs the wrong pin. It now says worktree-init installs exactly `.python-version` and to correct the pin first when the Blender bundled-Python check also FAILs. Re-verified: `.python-version`=3.13.12 → both FAIL lines, `scripts/doctor.sh` exit 1; restored to 3.13.13 → exit 0; `shellcheck scripts/doctor.sh` clean.
- not a defect: line budget — Makefile + scripts are 217 lines including comments, 159 non-comment, non-blank lines (`wc -l`; `grep -hvcE '^\s*(#|$)'`), against the ≲150 target. User decision 2026-10-19: accepted as is.
- not a defect: CLAUDE.md §Blender bootstrap wording proposed above, unapplied. User agreed 2026-10-19; it lands with ADR-0002 in Run 0.2.
- not a defect: `scripts/run_tests.sh` does not exist yet (Run 0.2); post-flight used the commands in Evidence instead.

## Carry-forward
- [0.1] -> 0.2 | contract | Pins: Makefile UV_VERSION=0.12.24 (uv.toml required-version copies it), .python-version=3.13.13; pyproject must equal both. Tools: .toolchain/{uv,just}/bin first on PATH.
- [0.1] -> 5.1 | gotcha | .python-version must equal Blender's bundled Python (doctor FAILs otherwise): bump Blender pin, .python-version and Makefile BLENDER_EXPECTED together.

## Test Counts
No pytest suite yet (Run 0.2). Checks run: 4 acceptance checks, all pass; plus the Blender warn path and x86_64 checksum cross-check. No renders.

## Confidence Report
A. Assumptions made — "fresh worktree" reproduced in place (deleted `.toolchain/`, stripped PATH) rather than a new `git worktree`, because the run's files are uncommitted. The x86_64 lines are verified against the published lists but never installed (no Intel Mac).
B. Deviations from existing patterns — the rollout's Files/Modules listed `scripts/install_uv.sh` + `scripts/install_just.sh`; this run ships one merged `scripts/install_tool.sh uv|just` (user decision; rollout line updated). docketScore's per-machine read-only cache, rename race and Linux targets were dropped; `check_python_version.sh` was not ported — its managed-Python check is folded into `doctor.sh`.
C. Thin context — no spec says which outside tools M0 needs beyond ffmpeg; shellcheck is kept because criterion 4 calls it.
D. Conflicts found — git-lfs in the rollout vs "doctor exits 0 here" (resolved by the user: dropped, followup row). `make doctor` exits 2 vs criterion's "exit 1" (Open Issues).
E. Complexity concentrations — `scripts/install_tool.sh` (77 lines): the tool-specific asset name and archive layout branch on `uv` vs `just`.

## Next Unblocked Run
0.2 (depends on 0.1). 0.3 was already unblocked (no dependencies).
