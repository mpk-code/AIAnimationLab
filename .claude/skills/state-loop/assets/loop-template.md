---
name: <loop-name>
scope: project                   # project | sidequest:<slug>
goal: <one sentence>
opened: <YYYY-MM-DD>
owner: <git-user-name>           # defaults to the opener's git identity
status: active                   # active | complete | abandoned
last-distilled: <YYYY-MM-DD HH:MM>
turns-since-distill: 0
---

# Loop: <name>

## Goal
<one paragraph: what success looks like, why this matters now, when we'd close>

## Out of scope
- <bullet — explicit guardrails to prevent drift>

## Established Constraints
> Facts treated as load-bearing. Each cites its evidence.

- **C1.** <constraint> — *evidence:* <file:line | measurement | manifest path | doc URL>

## Current Hypotheses
> The live frontier. Confidence ≥ ~95% migrates to Constraints; ≤ ~5% migrates to Rejected.

- **H1. <one-line claim>** — confidence: <0–100% or low/medium/high> · trend: ↑/↓/→
  - *Why we believe it:* <evidence so far, or "unverified — initial hunch">
  - *What would raise confidence:* <concrete test, measurement, or reading>
  - *What would falsify it:* <the experiment that kills it>
  - *Last update:* <YYYY-MM-DD — what changed>

## Rejected Paths
> Approaches ruled out. The reason field stops the rerun.

- **R1.** <approach> — *rejected because:* <reason> — *would reopen if:* <condition>

## Human-AI Consensus
> Decisions both parties signed off on. Distinct from Constraints (facts about the world).

- **D1.** <decision> — *agreed:* <YYYY-MM-DD> — *rationale:* <why>

## Open Questions
> Known unknowns. Each must be answerable in principle.

- **Q1.** <question> — *needed for:* <hypothesis or decision> — *how to answer:* <approach>

## Pivot Log
> The narrative spine. Read this first on resume.

- **<YYYY-MM-DD HH:MM> — <one-line pivot description>**
  - *From:* <prior framing> · *To:* <new framing> · *Why:* <trigger>

## Scratch (volatile)
> Working notes since the last distillation. Wiped at every distillation. If non-empty on
> resume, the previous session ended unclean — promote anything worth keeping, discard
> the rest, do not silently absorb.

<free-form>
