---
name: unit-test-review
description: >
  Audit the studio's Python test suite (schema, validator, harness, style-module and render smoke
  tests) for quality, intent coverage and traceability to acceptance criteria, weighing each smell
  by whether it would let a real defect ship green; emits a scorecard, traceability matrix, and
  severity-ranked findings. Use for "review the tests", "audit the test suite", "are our tests
  actually testing anything", "would these tests catch a real bug", "find weak / tautological /
  over-mocked tests", or /unit-test-review.
---

# Unit Test Review

**Purpose:** Review the Python test suite under `tests/` for structural quality, traceability to intended behavior, and intent coverage, then emit a structured, parseable report. Examples use pytest idioms (fixtures, `parametrize`, `monkeypatch`, `tmp_path`).

**Organizing principle:** The worst test smell is a test that passes when the code is broken. Every finding is weighed by one question — *does this smell degrade the suite's ability to detect a real defect, or its ability to be understood?* Cosmetics without that impact are low priority.

---

## Scope

You are reviewing tests, not writing them. Produce findings with targeted, minimal remediation. Include a patch sketch only if asked.

**Optional scoping arg** — a scope (changed files, one module such as `validators/` or `blender/harness/`, a run's footprint) limits review to tests whose subject falls inside it; record what was excluded. No scope → whole suite.

---

## Inputs (load the raw sources, not summaries)

Required:
- The test files (raw source).
- The code under test.

Strongly preferred — whatever defines *intended* behavior:
- The active quest rollout's acceptance criteria (e.g. M0: "two runs of the test scene with the same seed match"; "the manifest records model ID, Blender version, machine, git commit, seeds and timings").
- `docs/project-definition.md` (§Pipeline, §Artifact schemas, §Milestones exit gates), the JSON Schemas in `schemas/`, and relevant `docs/adr/`.
- `docs/test-strategy.md` for the intended test levels.
- Docstrings and type signatures of the public API under test.

If no documented intent exists, infer it from public signatures, docstrings and error contracts, and mark every traceability finding `INFERRED` rather than `SPEC`.

---

## Method — triangulate three edges

Establish intent first, then read each edge. A finding is real only when two corners disagree.

- **E1 — Tests ↔ Intent.** Does each documented behavior (acceptance criterion, schema rule, validator rule, manifest field) have a test expressing its *contract* — pre/postconditions, invariants, error behavior?
- **E2 — Tests ↔ Code.** Do the tests exercise real behavior, or mirror the implementation / assert against mocks / assert nothing? Mentally mutate the code — flip a comparison, drop a branch, drop a manifest field, stop passing the seed — and ask whether any test fails.
- **E3 — Intent ↔ Code.** Behaviors in code with no intent behind them, or intended behaviors with no implementation. Tests inherit the code's blind spots; this edge catches what they can't.

---

## Detection checklist

Each item has a stable ID, a cue, and what "good" looks like. Flag only when it undermines defect detection or comprehension.

### Structure & hygiene (STR)
| ID | Smell | Cue | Good looks like |
|----|-------|-----|-----------------|
| STR-01 | Uninformative name | `test_1`, `test_works` | `test_palette_validator_rejects_off_bible_hex` — unit + scenario + expected |
| STR-02 | No Arrange-Act-Assert | setup, action, asserts interleaved | clear AAA blocks; one action |
| STR-03 | Eager test | several unrelated asserts, multiple acts | one behavior per test |
| STR-04 | Logic in the test | `if`/`for`/`try` in the body | straight-line; parametrize instead of loop |
| STR-05 | Obscure / excessive setup | large fixtures unrelated to the assertion | minimal setup; SUT visible at a glance |
| STR-06 | Magic values | unexplained literals | named constants / self-evident values |
| STR-07 | Comments compensating for naming | prose explaining what a name should show | expressive name; comment only for *why* |

### Assertions (ASR)
| ID | Smell | Cue | Good looks like |
|----|-------|-----|-----------------|
| ASR-01 | No assertion | runs code, asserts nothing (or only "no exception"; a render smoke test that only checks exit code) | asserts the observable outcome (frames exist, count, manifest fields) |
| ASR-02 | Weak assertion | `assert result is not None` where an exact check is possible | precise equality / contract check |
| ASR-03 | Assertion roulette | many bare asserts; failure unattributable | one behavior, or parametrize with clear ids |
| ASR-04 | Tautology | expected value computed with the SUT's own logic (e.g. hashing frames with the same helper under test and comparing to itself) | expected value stated independently |
| ASR-05 | Testing implementation detail | private state, call order, log strings the contract doesn't promise | public contract |
| ASR-06 | Over-specification | full-manifest equality when one field matters; breaks on timing values | assert only what's guaranteed |
| ASR-07 | Rubber-stamped golden | golden frame hashes / contact sheets / schema snapshots regenerated wholesale and accepted unread | small, reviewed goldens; regeneration is a deliberate, reviewed act |

### Isolation & determinism (ISO)
| ID | Smell | Cue | Good looks like |
|----|-------|-----|-----------------|
| ISO-01 | Order dependency / shared state | relies on run order or shared globals; one Blender session reused across tests that mutate `bpy.data` | independent tests; fresh scene/fixture |
| ISO-02 | Non-determinism | real clock, unseeded RNG, unrecorded seeds, Cycles GPU frames compared by exact hash | injected clock, seeded RNG; EEVEE exact hashes, Cycles per-pixel tolerance |
| ISO-03 | Environment leakage | depends on env vars, CWD, a specific Mac, GPU presence, Blender path | explicitly set/patched; machine-specific tests marked and skipped with reason |
| ISO-04 | Pollution / no teardown | writes renders into `productions/` or the repo | `tmp_path`; context-scoped patches |

### Test doubles (MOK)
| ID | Smell | Cue | Good looks like |
|----|-------|-----|-----------------|
| MOK-01 | Over-mocking | `bpy` mocked so thoroughly only the mocks run | mock at real seams; exercise real Blender in a smoke tier |
| MOK-02 | Mocking the SUT / what you don't own | patching the harness under test, or `bpy` internals fragile to Blender upgrades | real SUT; wrap `bpy` behind an own seam |
| MOK-03 | Contract drift | a `bpy` fake's shape diverges from the real API; nothing guards the gap (API drift goes unnoticed) | a real-Blender contract/smoke test keeps the fake honest |
| MOK-04 | Interaction test where outcome matters | asserts call sequence instead of resulting state/output | assert the outcome |
| MOK-05 | Unverified critical side-effect | the manifest writer / frame writer is mocked but never verified | verify the important interaction happened |

### Intent & traceability (INT)
| ID | Smell | Cue | Good looks like |
|----|-------|-----|-----------------|
| INT-01 | No intent link | test not traceable to an acceptance criterion, schema/validator rule, or public behavior | maps to a criterion or named behavior |
| INT-02 | Uncovered behavior | acceptance criterion or schema rule with no test | every behavior has a test |
| INT-03 | Intent mismatch | name/docstring claims one behavior; asserts check another | name, docstring, asserts agree |
| INT-04 | Spec contradiction / drift | test encodes behavior that conflicts with the current schema, project definition or an ADR | test reflects current intent (escalate if ambiguous) |
| INT-05 | Contract gaps | validator tested only on passing artifacts; schema only on a valid example | pass, fail and error behavior all covered |
| INT-06 | Testing the framework | verifying `jsonschema`, pytest or Blender behavior rather than own logic | test your logic, trust the platform |

### Case coverage (COV)
| ID | Smell | Cue | Good looks like |
|----|-------|-----|-----------------|
| COV-01 | Happy-path only | no error paths (bad `--profile`, missing scene script, invalid artifact) | error paths asserted, type and message |
| COV-02 | Missing boundaries | no zero/one-frame, empty palette, `null` optional fields, duration edges | boundaries parametrized |
| COV-03 | Missing negative cases | validators never fed a violating artifact | invalid inputs rejected as specified |
| COV-04 | Coverage theater | high line coverage but mutations survive | assertions a real defect would break |
| COV-05 | Mis-prioritized effort | trivial helpers heavily tested; reproducibility, manifest and validators thin | depth tracks risk |

### Maintenance & design (MNT)
| ID | Smell | Cue | Good looks like |
|----|-------|-----|-----------------|
| MNT-01 | Duplication | copy-pasted bodies varying only in data | `parametrize` / shared fixtures |
| MNT-02 | Fragility | breaks on unrelated refactors | survives behavior-preserving refactors |
| MNT-03 | Untracked skip/xfail | `skip`/`xfail` with no reason or issue link | reason + `issue #<n>`, or delete |
| MNT-04 | Second-class test code | dead fixtures, style below production | production standard |
| MNT-05 | Misclassified level | a "unit" test that launches Blender or renders | unit tests fast and `bpy`-free; render tests marked as smoke/integration |

---

## Severity rubric

Rank by damage to defect detection and trust:

- **Critical** — false confidence: green means nothing. (`ASR-01`, `ASR-04`, `MOK-01`, `MOK-05`, `INT-04`, `COV-04`.)
- **High** — a real behavior is unprotected or the suite is unreliable. (`INT-02`, `INT-05`, `COV-01/02/03`, `ISO-02`, `MOK-03`.)
- **Medium** — erodes trust and maintainability. (`ASR-03/05/06`, `STR-03/04`, `MOK-04`, `MNT-01/02`, `ISO-01/03/04`.)
- **Low** — hygiene and readability. (`STR-01/05/06/07`, `ASR-02/07`, `INT-01/06`, `MNT-03/04/05`, `COV-05`.)

Escalate one level when the affected code guards a milestone exit gate or experiment validity — render reproducibility, the manifest, schemas, validators, seeded draws. A broken one there corrupts every downstream production or experiment.

---

## False-positive discipline

Do not flag by pattern-match:
- A single assertion is good when the test verifies one behavior.
- Faking `bpy` at a genuine seam so pure logic runs under plain pytest is correct design, not `MOK-01` — provided a real-Blender smoke test exists.
- `parametrize` sometimes reads worse than two explicit tests.
- Golden hashes are fine when small, reviewed, and tied to a determinism contract.

Every finding cites concrete evidence (`file::test_name`, line, short paraphrase). No vague findings.

---

## Output format

Emit exactly these sections, in order.

### 1. Scorecard
```
E1 Tests ↔ Intent:  <strong|adequate|weak|absent> — <why>
E2 Tests ↔ Code:    <band> — <why>
E3 Intent ↔ Code:   <band> — <why>
Top risk: <the single finding most likely to let a real defect ship>
```

### 2. Traceability matrix
| Behavior / criterion | Source (SPEC/INFERRED) | Test(s) | Status |
|---|---|---|---|
| ... | ... | `file::test` | covered / partial / uncovered / contradicted |

### 3. Findings
One block per finding, ordered by severity:
```
### [SEVERITY] <SMELL-ID> — <short title>
- Location: <file::test_name> (line N)  [or "SUITE"]
- Evidence: <paraphrase or ≤1-line snippet>
- Why it matters: <impact on defect detection or comprehension>
- Intent link: <criterion / schema / ADR path | INFERRED | NONE>
- Remediation: <smallest change that fixes it>
```

### 4. Footprint & escalation
- **Reviewed:** <files/modules in scope>
- **Excluded:** <what and why>
- **Escalations:** items needing the user's decision (ambiguous or contradictory intent, a missing acceptance criterion, a deviation to confirm). Only these carry between runs.

---

## Guardrails
- Review, don't rewrite. Patch only on request.
- Never invent a requirement to justify a finding — mark inference `INFERRED`.
- Judge unit tests and render smoke tests each at their own level.
- When intent is ambiguous, escalate rather than guess which side is the bug.
- A defect this work finds and leaves unfixed is filed afterwards with the `defect-filing` skill (this skill writes only its report) and named `issue #<n>` in the record that leaves it.
