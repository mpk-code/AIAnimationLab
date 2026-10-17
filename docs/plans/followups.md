# Followups — deferred items with revisit triggers

A thin index of things deliberately deferred until a trigger fires. Each row points to its source (fix plan, status report, rollout, ADR); the source carries the context. Scan the Open table at the start of any session that touches dependencies, tooling or Blender versions.

**Add a row** when a `/bug-fix` or `/run-process` flow defers an item with a specific trigger. **Close a row** by moving it to Closed with the date and the commit that took the action.

## Open

| Item | Trigger | Action | Source |
| --- | --- | --- | --- |
| Pin Blender version | Before E1 runs | Write an ADR pinning the version; record it in the manifest schema | `docs/project-definition.md` §Open questions |

## Closed

| Item | Closed | Commit |
| --- | --- | --- |
