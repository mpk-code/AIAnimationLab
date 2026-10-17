---
id: NNNN
title: <specific decision title>
status: Proposed   # Proposed | Provisional | Accepted | Superseded | Withdrawn
date: YYYY-MM-DD
supersedes: N/A
superseded-by: N/A
---

# NNNN: <title>

## Status

<status>. If Provisional, name the **review trigger** (the event that prompts re-evaluation) and an **expiry** (date or milestone). Never leave Provisional open-ended.

## Context

2–4 sentences: what situation, hypothesis (H1–H3), milestone or constraint made this decision necessary. Reference `docs/project-definition.md` sections rather than copying them.

## Decision

One clear, specific sentence. Not "use a deterministic renderer" but "use EEVEE for preview and exact-hash reproducibility tests; Cycles on Metal for finals, compared at per-pixel tolerance 1/255".

## Alternatives considered

| Alternative | Why not chosen |
| --- | --- |
| | |

## Consequences

- What becomes easier.
- What becomes harder, and what now needs a test, validator or manifest field.
