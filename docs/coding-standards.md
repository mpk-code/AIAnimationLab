# Coding Standards

AIAnimationLab **project-specific** coding conventions — rules a reviewer must be able to cite by `STD-###`, not just intuit. Generic engineering discipline lives in the `sw_engineer` skill; working style lives in `CLAUDE.md`. This file references those and does not copy them.

Not auto-loaded. `/run-process` reads it before writing code, `/bug-fix` checks conformance against it, and `/code-review` cites it by ID.

## The standards

### STD-001 — Reference the source of truth; don't duplicate authority

A literal is a defect when it duplicates a value defined canonically elsewhere: schema keys (`schemas/`), glossary enums (gate modes, render profiles), style parameters (`styles/.../style.yaml`), paths the harness owns. Reference the source. Genuine test fixture inputs are fine as literals.

### STD-002 — `bpy.data` over `bpy.ops`

Build and modify scenes through `bpy.data` and object/datablock APIs. `bpy.ops` depends on UI context and fails or behaves differently in background mode. Where an operator is unavoidable, isolate it in one function with a comment saying why, and cover it with a background-mode test.

### STD-003 — Render only through the harness

No code outside `blender/harness/` calls render operators or sets output paths. Scene scripts build scenes; the harness renders them, applies the profile, and writes the manifest.

### STD-004 — All randomness is seeded and recorded

Every random choice takes an explicit seed derived from the production's `rng_seed`. No module-level `random` calls, no time-based seeds. The seed in use appears in the manifest.

### STD-005 — No default-looking values in style or scene code

Code defaults become visual defaults: centered compositions, round numbers, symmetric layouts, linear or stock easing, primitive meshes. Creative parameters come from the style bible or a style module, never from a literal chosen in the scene script. A value that must be a literal carries a comment saying where it came from.

### STD-006 — Artifacts are schema-validated at every handoff

Every stage artifact carries `schema_version` and `production_id` and is validated against `schemas/` on write and on read. Times are seconds (float), colors are hex strings.

### STD-007 — A comment earns its place by what a reader would get wrong without it

Applies to every comment and docstring. `/doc-review` and `/code-review` audit against it.

A comment explains how code fits the architecture and *why* a non-obvious decision was made. It never restates what the code already says, and it must never mislead.

**Six gates, in order. The first failure decides.**

| # | Gate | If it fails |
|---|---|---|
| G1 | Is it correct for the code as it stands today? | Fix it — first decide whether the *code* or the *comment* is wrong. Never merely reword. |
| G2 | Does it duplicate an authority elsewhere (STD-001)? | Reference the authority instead. |
| G3 | If deleted, would a competent reader reach a wrong conclusion? | No → delete. This is the keep test. |
| G4 | Is it recoverable from the code in one read? | Yes → delete. |
| G5 | Does its truth depend on a file it does not control? | Point at that file; never restate its state. |
| G6 | Does it read clearly on one pass — literal words, one word per meaning, the point before its support? | Rewrite with the same facts. G6 never justifies a deletion. |

Glossary terms, ADR and `STD-###` IDs, and symbol names are precision, not decoration — G6 never "simplifies" them.

**By level:**

- **Module / class:** its place in the architecture in 1–2 lines, and the rule for what belongs here versus elsewhere. Omit for obvious modules. Never inventory methods or attributes.
- **Method:** the name and arguments should say what it does; if they don't, rename first. Document only warnings (preconditions, side effects, not-thread-safe, not background-mode-safe) and why it exists if that is not obvious.
- **Statement:** a non-obvious ordering constraint and its consequence; a workaround with its provenance (Blender bug, issue, commit); a guard whose removal is a real defect; a `type: ignore` with why it is sound. Section banners are a smell — extract methods instead.

**Repo rules:**

1. **A recorded decision is never cut for length.** A comment pointing to an ADR or a user decision records an argument that survives nowhere else.
2. **Cite symbols, not `path:line`** — in source and in documents. Line numbers drift silently. Where there is no symbol, quote enough text to identify the target.
3. **A guarantee claim names its mechanism.** "Cannot drift", "by construction" and "always deterministic" must say what prevents the failure: *by construction* (types, a single-sourced value), *by gate* (a named test or validator — which vanishes silently if the test is deleted, so name it), or *by convention* (nothing — say so plainly). Watch for one claim that spans two strengths.

**Why:** in an agent-edited codebase, a model tends to follow the prose when comment and code disagree, so a false comment misleads more than a missing one. G1 outranks every brevity argument.
