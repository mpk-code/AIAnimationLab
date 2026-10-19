# Followups — deferred items with revisit triggers

A thin index of things deliberately deferred until a trigger fires. Each row points to its source (fix plan, status report, rollout, ADR); the source carries the context. Scan the Open table at the start of any session that touches dependencies, tooling or Blender versions.

**Add a row** when a `/bug-fix` or `/run-process` flow defers an item with a specific trigger. **Close a row** by moving it to Closed with the date and the commit that took the action.

## Open

| Item | Trigger | Action | Source |
| --- | --- | --- | --- |
| Pin Blender version | Before E1 runs | Write an ADR pinning the version; record it in the manifest schema | `docs/project-definition.md` §Open questions |
| Git LFS | First binary we want committed (golden reference frames, .blend assets, finished films, review contact sheets) | Install git-lfs, add `.gitattributes`, add to `Brewfile` + `scripts/doctor.sh` | `sidequests/studio-v1/status/run0.1status.md` |
| shellcheck lane in the gate | Next run that adds or changes a `scripts/*.sh` file | Add `shellcheck scripts/*.sh` to `scripts/run_tests.sh`'s static lane and a line to ADR-0002 | `sidequests/studio-v1/status/run0.2status.md` |
| JS package manager: pnpm, never npm | First JavaScript/Node dependency (any `package.json`) | Use pnpm only: pin node in `.toolchain/`, pin pnpm via `package.json` `packageManager` + corepack, commit `pnpm-lock.yaml`, add to `make worktree-init` / `make doctor`, record in an ADR; never `npm install` or `package-lock.json` | User decision 2026-10-19 (docketScore npm/pnpm confusion) |

## Closed

| Item | Closed | Commit |
| --- | --- | --- |
