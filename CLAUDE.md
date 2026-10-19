# CLAUDE.md — studio doctrine (v0)

**AIAnimationLab** is a Claude Code production system that turns a seed idea into a short Blender-rendered animation through staged, human-gated decisions. The repository is the studio; Claude Code is its only crew. Wording here biases every stage, so this file stays short and imperative. **Changes to this file need an ADR** (`docs/adr/`).

## Source of truth

Reference documents in this order:

1. The **active quest's rollout** (`sidequests/<slug>/<slug>-rollout.md`) — run order and acceptance criteria for the work in front of you.
2. `docs/project-definition.md` — purpose, hypotheses, scope, pipeline, milestones M0–M5 and their exit gates.
3. `docs/adr/` — decisions that amend or refine the project definition. A later ADR wins over the project definition where they conflict.
4. `docs/glossary.md` — the ubiquitous language. Use these terms exactly; changes need an ADR.
5. `docs/coding-standards.md` (`STD-###`) — read before writing code.
6. `docs/test-strategy.md` — testing approach.

Deferred items with revisit triggers live in `docs/plans/followups.md`.

## Blender

- Bootstrap a machine with `make setup`, a worktree with `make worktree-init`; check it with `make doctor`. `make` only bootstraps; `just` runs tasks.
- Blender **5.2.2 LTS** (`/Applications/Blender.app/Contents/MacOS/Blender`). Not yet pinned; record the version in every manifest. Pin before E1.
- Prefer `bpy.data` over `bpy.ops`. `bpy.ops` depends on UI context and breaks in background mode.
- **Render only through the harness** (`blender/harness/render.py --scene <script> --profile preview|final --out <dir>`). Never call render operators ad hoc.
- Every render writes a `manifest.json`: model ID, Blender version, machine, git commit, seeds, timings.

## Global bans

- No image or video diffusion models. Every frame is code-generated.
- No silent defaults: every creative decision lands in a written, schema-validated artifact. If it isn't written down, the model decides; if the model decides, it chooses the average.
- A model never grades its own output. Generation and critique run in separate subagent contexts.
- Never commit renders or other large binaries outside Git LFS; manifests point to them.

## Two kinds of skills

- `.claude/skills/` — **dev-process skills** for building the studio (quests, runs, bug-fix, review, commit). Ported from docketScore.
- `skills/<stage>/SKILL.md` — **pipeline stage skills** that make films. These are aesthetic artifacts: version them, A/B test them, and never ship an example a skill could copy.

## Working style

- **Surface uncertainty before coding.** State assumptions; if several interpretations exist, present them; if unclear, ask.
- **Stop on conflicting guardrails** — report with 2–3 resolution options. **Stop on missing decisions** — propose the smallest choice set.
- **Match existing style.** Every changed line traces to the request. Mention unrelated dead code; don't delete it. Remove orphans your change creates.
- **Make tasks verifiable:** "fix the bug" → a failing test that reproduces it, then make it pass.
- **Never promise a future check without a live mechanism** (a background task, `/loop`, or a scheduled task).

## Tests

`scripts/run_tests.sh` is the canonical runner (lanes in order: doctor → `uv lock --check` → ruff/mypy → unit → blender); `just ci` is its alias, never a second gate. Don't construct ad-hoc pytest command lines for gate decisions. Render smoke tests run the preview profile through the harness.

## Shell

The default shell is zsh: it does not word-split unquoted `$(...)`. Iterate files with `while IFS= read -r f; do ... "$f"; done`, never an unquoted `for f in $(...)`.
