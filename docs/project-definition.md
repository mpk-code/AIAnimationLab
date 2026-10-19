# Project Definition: Staged AI Animation Pipeline (Blender + Claude Code)

Oct 14, 2026 · @Michael

## Problem and purpose

The goal is to build a Claude Code production system that turns a seed idea into a short Blender-rendered animation through staged, human-steerable decisions. Its output should be measurably less generic than one-shot prompting.

A one-shot prompt specifies a handful of the hundreds of decisions a short film needs. The model fills the rest with its most probable choices: premise, palette, camera language, pacing, ending. Each default is reasonable, but stacked together they converge on the same average film, and the sameness shows after a few runs.

The project addresses this by doing what a human production does:

- Write decisions down as artifacts so nothing is silently defaulted.
- Inject constraints from outside the model.
- Put human selection at the few points where it has the most leverage.

Target output for v1 is a 15–60 second short, rendered from Python scripts run in headless Blender and refined with feedback from family and friends. The end goal is a series of 3–7 minute YouTube videos.

## Hypotheses and success criteria

The project succeeds if blind raters find pipeline output less familiar than one-shot output, with no loss in quality. Three hypotheses carry that claim:

- **H1, divergence.** Across the same seeds, pipeline films spread more widely than one-shot films and are rated less familiar.
- **H2, knob efficacy.** Every exposed knob produces a measurable change in the artifacts and the rendered frames.
- **H3, style fidelity.** Decisions written in the style bible survive into the rendered frames.

The targets below are proposals to fix before the first experiment runs, not findings.

| Criterion | Measure | Proposed target |
| --- | --- | --- |
| Divergence (H1) | Mean pairwise distance of script and keyframe embeddings across 20 seeds | Pipeline set wider than one-shot set |
| Familiarity (H1) | Blind paired rating: "which have you seen before?" | Pipeline judged less familiar in at least 70% of pairs |
| Quality floor (H1) | Blind paired rating of overall quality | Pipeline no worse than one-shot |
| Knob efficacy (H2) | Artifact diff and frame distance under a single-knob sweep | Every shipped knob moves both; dead knobs are removed |
| Style fidelity (H3) | Validator pass rate, plus raters matching renders to style bibles blind | Raters match well above chance |

## Scope

Version 1 covers the whole path from seed to rendered short, built entirely from code that Claude Code writes and runs. It excludes the kinds of work that don't reduce well to code.

**In scope**

- Stage skills from seed through final assembly, with artifact schemas for each handoff.
- A Blender style-module library covering shaders, line treatment, camera grammar and motion primitives.
- A headless render harness with preview and final profiles and contact-sheet output.
- Constraint decks, anti-default lists and per-stage validators.
- An evaluation harness: a one-shot baseline, rater protocol and diversity metrics.

**Out of scope for v1**

- Character rigging, facial performance and lip-sync.
- Photoreal rendering as a primary style.
- Image or video diffusion models. Keeping every frame code-generated makes the experiment cleaner.
- Engines other than Blender.

**Deferred**

- Sound, music and narration. v1 must be audio-ready: `beats.yaml` and `shots.yaml` carry timing in seconds plus optional narration-line and sound-cue fields, and assembly (stage 8) muxes audio tracks with ffmpeg. Adding a narration stage (script, text-to-speech, timing) later then requires no restructuring.
- Editing beyond shot concatenation and simple transitions.
- Narratives longer than 60 seconds, building toward the 3–7 minute end goal.

## System concept: Claude Code is the studio

The repository is the studio and Claude Code is its only crew. Everything that shapes how Claude Code reasons, remembers and writes code therefore shapes the finished film, so those mechanisms are design surfaces, not plumbing.

| Mechanism | How it shapes the film | Design response |
| --- | --- | --- |
| `CLAUDE.md` | Studio doctrine, read every session. Its wording biases every stage. | Keep it short and imperative: current Blender version, API conventions, global bans. Version it, and record changes in ADRs. |
| Skills | Each stage's procedure. Their phrasing, examples and option counts steer what gets generated. | Treat skills as aesthetic artifacts. Version them, A/B test them, and never ship an example a skill could copy. |
| Memory (files only) | Claude Code keeps nothing across sessions except what is on disk. Any decision left unwritten regresses to the model's default. | Every decision lands in a schema-validated artifact under the production folder. The artifacts are the film's memory. |
| Cross-production catalog | Knowing past films can prevent self-repetition. It can also teach a house style by imitation. | The catalog is read only as negative examples, as in "don't repeat these". Experiment E5 tests whether this works. |
| Reasoning defaults | Unconstrained choices pick the mode. "Be creative" is itself a mode. | Randomness comes from the harness, through seeded constraint draws. Skills generate N options and the harness or a human picks. |
| Coding habits | Code defaults become visual defaults: centered compositions, round numbers, symmetric layouts, linear or stock easing, primitive meshes. | The style-module library supplies non-default building blocks, and a lint pass flags default-looking code. |
| Context and subagents | A model grading its own output tends to approve it. | Generation and critique run in separate subagent contexts. Human raters judge the experiments. |
| Model version | A model change can shift every output. | Each production's `manifest.json` records model ID, skill versions, seeds and Blender version. Rerun the baseline after any model change. |

The working principle: **if it isn't written down, the model decides; if the model decides, it chooses the average.**

## Pipeline

The pipeline runs nine stages in three phases. A human decides at three gates: premise, style and animatic. After Gate C, everything runs mostly unattended against the render loop.

| Phase | Stage | Writes | Gate |
| --- | --- | --- | --- |
| Story | 0 Seed and constraints | `production.yaml`, deck draws | |
| Story | 1 Premise options ×N | `premise_options.md` | **Gate A:** human picks a premise, locks `premise.md` |
| Story | 2 Structure and beats | `beats.yaml` | |
| Look | 3 Style bible options ×N | `style_options/` | **Gate B:** human picks a style, locks `style_bible.json` |
| Look | 4 Shots and blocking (storyboard) | `shots.yaml`, blocking renders, animatic | **Gate C:** human approves the animatic, locks `shots.yaml` |
| Production | 5 Scene build | bpy scene scripts | |
| Production | 6 Animation | keyframe scripts | |
| Production | 7 Lighting and render | frames, preview then final | |
| Production | 8 Assembly | film, `manifest.json` | |

Validators and a separate critic check every handoff; failures loop back to the stage that produced the artifact.

Each stage reads only upstream artifacts and writes its own, so any stage can be re-run from its inputs. Gates sit where a choice changes everything downstream and is cheap to make from a set of options.

## Control surface

A knob earns its place only if a downstream stage enforces it as a parameter and a sweep test shows it moves the output. Adjectives like "moodier" are not knobs.

| Control | Example | Where it is enforced |
| --- | --- | --- |
| Production config | `production.yaml`: duration, aspect, seed, deck selections, gate mode | The harness, at every stage |
| Constraint decks | Seeded draws: structural form (palindrome, single shot, reversed), material world ("everything is paper"), borrowed cinematographer, banned emotional register | Premise and structure skills; validators check compliance |
| Anti-default lists | Banned premises, palettes, shot patterns and endings, kept per stage and growing | Generation prompts and validators |
| Divergence width | Generate 8–12 options at each gated stage | Stage skills |
| Style parameters | Palette hex values, key-to-fill ratio, line weight, average shot length, allowed camera moves | Style bible schema, Blender style modules, validators |
| Gate mode | `human`, `auto-pick` or `random-pick` | Harness. The non-human modes exist for experiments. |

The anti-default lists are a core asset. Whenever a reviewer says "I've seen this before," the thing they recognized is added to a list.

## Style library and lifecycle

Styles are versioned, first-class assets for each creative dimension. Each style moves through a lifecycle from recognized, to active, to retired. A production composes one style per dimension, and novel combinations are a main source of uniqueness.

| Dimension | What a style specifies | Used by stages |
| --- | --- | --- |
| Visual | Palette, shading, line, texture, lighting | 3, 5, 7 |
| Camera and editing | Shot grammar, lens, movement, average shot length, transitions | 4, 8 |
| Storytelling | Structural form, point of view, pacing, ending type | 1, 2 |
| Characterization | How characters are revealed, silhouette and design rules, motion personality, archetypes to avoid | 1, 2, 5, 6 |
| Motion | Easing curves, timing, exaggeration, physics feel | 6 |
| Sound (later) | Narration voice, music, sound palette | Narration, 8 |

Lifecycle:

1. **Recognize.** A critic skill finds recurring patterns across past productions and rater feedback, for example "every ending pulls back to a wide shot." Each pattern becomes either an anti-default or a candidate style.
2. **Build or acquire.** A style is authored from scratch or derived from a described movement or technique. It is written as a spec, plus Blender modules for the visual and motion dimensions.
3. **Validate.** A candidate must pass a fidelity test (it shows up in the output) and a distinctness test (it is measurably different from active styles).
4. **Active.** The style is available for draws, and the catalog tracks how often and how recently it is used.
5. **Fatigue.** A score combines usage, recency, similarity across recent productions, and raters' "seen it" flags.
6. **Retire.** Fatigued styles move to `styles/retired/`, and their signature is added to the anti-default lists. A retired style can be revived after a cooldown.

In the repository this lives at `styles/<dimension>/<style-id>/style.yaml`, which references modules in `blender/lib/`, with retired styles in `styles/retired/`. The main risk is a fatigue score built on a small sample retiring a style too early. Retirement therefore requires both a fatigue threshold and a human confirmation.

## Repository structure

The repository separates durable assets from individual productions. Durable assets are skills, schemas, decks, the style library and the harness. A production is one film's artifacts and renders. This mirrors the quest model: style modules and stage skills are features, Blender API probes are spikes, and each production is a run against them.

```
CLAUDE.md                  # studio doctrine: Blender version, API rules, global bans
docs/
  project-definition.md
  glossary.md              # ubiquitous language: beat, shot, style bible, gate...
  adr/
skills/<stage>/SKILL.md    # one skill per pipeline stage, plus critic skills
schemas/                   # premise, beats, style_bible, shots (JSON Schema)
decks/                     # constraint decks (YAML), seeded draws
antidefaults/<stage>.yaml  # banned defaults, grown from review
blender/
  lib/                     # style modules: shaders, lines, camera, motion, layout
  harness/                 # headless runner, render profiles, contact sheets
validators/                # artifact-vs-upstream and render-vs-style-bible checks
eval/                      # experiment configs, baseline one-shot, rater protocol, metrics
productions/<id>/          # artifacts, generated scripts, renders, manifest.json
tests/                     # schema, validator, style-module smoke renders
```

Renders and other large binaries go in Git LFS or are kept out of git, with manifests pointing to them.

## Glossary

These terms mean exactly this in skills, code and conversation. Changes to any of them need an ADR.

| Term | Meaning |
| --- | --- |
| Production | One film run from seed to assembled output, stored in `productions/<id>/` |
| Seed | The human-written idea that starts a production |
| Deck | A curated list of constraints. A draw is a seeded random pick from a deck. |
| Anti-default | A banned pattern for a stage, kept in `antidefaults/<stage>.yaml` |
| Beat | A story unit: one change in situation or emotion |
| Shot | One continuous camera take, the unit of staging and rendering |
| Style | A versioned spec for one creative dimension, such as visual or storytelling |
| Style bible | A production's locked set of styles plus overrides |
| Style module | Reusable Blender code in `blender/lib/` that implements part of a style |
| Gate | A point where a human, or the harness during experiments, picks from options |
| Animatic | Blocking renders cut together on shot timing |
| Manifest | A per-production record of everything needed to reproduce it |
| Validator | A rule-based check of an artifact against its upstream artifacts |
| Critic | A model-based review run in a separate subagent context |

## Artifact schemas (sketch)

These are starting field lists. Claude Code formalizes them as JSON Schema in `schemas/` during M0 and M1, and changes after that need an ADR. Times are in seconds, colors are hex, and every artifact carries `schema_version` and `production_id`.

`production.yaml` is written at stage 0 and filled in at the gates:

```yaml
production_id: p-0001
seed_text: "..."            # human-written
rng_seed: 4127
duration_s: 30
aspect: "9:16"              # or 16:9 for long-form
fps: 24
gate_mode: human            # human | auto-pick | random-pick
divergence_n: 8
draws: { structure: palindrome, material_world: paper }
styles: { visual: null, camera: null, storytelling: null, characterization: null, motion: null }
render_profile: preview     # preview | final
```

`styles/<dimension>/<style-id>/style.yaml` defines one style. This example is a visual style:

```yaml
style_id: visual/cut-paper
version: 3
status: active              # candidate | active | retired
palette: ["#1d1a2f", "#e85d3a", "#f2e8cf", "#6a8d73"]
shading: { model: toon, ramp_steps: 3 }
line: { enabled: true, weight_px: 2.5 }
lighting: { key_fill_ratio: 6 }
forbidden: [gradients, bloom]
modules: [shaders/toon_ramp, lines/ink]
```

`style_bible.json` is locked at Gate B. It lists one `style_id@version` per dimension, plus per-production overrides that validators enforce.

`shots.yaml` is locked at Gate C:

```yaml
shots:
  - id: s01
    beat: b01
    start_s: 0.0
    duration_s: 2.5
    framing: wide           # from the camera style's vocabulary
    camera_move: static
    lens_mm: 35
    action: "..."
    narration: null         # audio-ready
    sound_cues: []
```

`manifest.json` is written by the harness on every run. It records production ID, git commit, model ID, skill and style versions, Blender version, machine, seeds, per-stage wall time and token use, render time, and each gate decision (the options shown and the one picked).

## Evaluation and experiments

Five experiments test the hypotheses. Every production writes a manifest of model, skill versions, seeds, token use, wall time and render time, so the experiments can also be analyzed as trajectories.

| ID | Question | Design | Primary measure |
| --- | --- | --- | --- |
| E1 | Does the pipeline beat one-shot? (H1) | 20 seeds, each run one-shot and through the pipeline. Blind paired ratings by several raters. | Familiarity and quality win rates; embedding spread |
| E2 | Do the knobs work? (H2) | Hold everything fixed and sweep one knob across 3–5 values. | Artifact diff and keyframe distance per knob |
| E3 | Does style survive rendering? (H3) | Several style bibles, each rendered. Raters match renders to bibles blind. | Match accuracy; validator pass rate |
| E4 | What does the human add? | The same seeds with gates set to human, auto-pick or random-pick. | Divergence and quality by gate mode |
| E5 | Does the studio develop a house style? | 50 sequential productions with catalog awareness on vs off. | Embedding spread over time |

Criteria and rater instructions are fixed before E1 runs. The one-shot baseline gets the same Blender harness and style library, so the comparison isolates the pipeline itself rather than the tooling.

### Feedback from family and friends

Until the formal experiments run, family and friends are the rater pool. The same rubric is used every round so their feedback stays comparable.

1. Have you seen something like this before? (Not at all / Somewhat / Very)
2. Overall, how good is it? (1–5)
3. What, if anything, felt familiar or clichéd? (free text)
4. What moment stood out? (free text)
5. Would you watch another one in this style? (yes / no)

Each round, raters get a batch of 3–6 shorts as unlisted video links in random order, with a short form and no indication of how each was made. Responses are exported as CSV to `eval/feedback/<round>/`. A skill turns the free-text answers into anti-default and fatigue candidates for human review.

Two caveats shape how the results are read. Friends rate kindly, so compare films within a batch rather than relying on absolute scores. Raters also get used to the work over rounds, so rotate them where possible and record who rated what.

## Risks and failure modes

The largest risk is that a novel story gets flattened into generic visuals by limited Blender execution. Each failure mode below is tied to a symptom you can observe and to the specific part of the repository that fixes it.

| Failure mode | Symptom | Remediation target |
| --- | --- | --- |
| Visual flattening | Distinct scripts produce similar-looking renders | `blender/lib/`: add style modules |
| Dead knobs | A sweep moves the artifacts but not the frames | The knob: wire it into a style module, or delete it |
| Coherence drift | Renders violate the style bible: off-palette colors, banned camera moves | `validators/` |
| Blender API drift | Context errors or renamed nodes break scripts | Blender version in manifest, pin before E1, API probe spike, smoke tests |
| Constraint staleness | Outputs converge again after many runs | `decks/` rotation and `antidefaults/` growth |
| House-style convergence | E5 spread shrinks over time | Catalog policy in the ideation skill |
| Self-validation | Critic passes everything | Separate critic subagent; human raters |
| Gate fatigue | Gates rubber-stamped or skipped | Gate count and placement in `production.yaml` |
| Render cost | Iteration loop too slow | Preview profile in `blender/harness/` |
| Evaluation subjectivity | Rater disagreement swamps the effect | Rater protocol in `eval/`: more raters, fixed criteria |
| Model change mid-study | Baseline shifts | Manifest model ID; rerun E1 baseline |

## Milestones

The riskiest slice comes first. M1 proves that a written style survives into Blender before any story stage exists, and each phase must pass its gate before the next begins.

| Phase | Scope | Exit gate |
| --- | --- | --- |
| M0 Foundation | Repo, `CLAUDE.md`, glossary, headless render harness, manifest. Spike: probe the installed Blender API. | **Reproducible render:** a scripted scene renders headless, with the same output on rerun |
| M1 Vertical slice: style bible to animatic | Stages 3 and 4 with two contrasting style modules. First validators: palette, camera grammar. | **Style survives:** renders pass style-bible validators for both styles |
| M2 Baseline and evaluation harness | One-shot baseline on the same harness and library. Rater protocol and diversity metrics, fixed in advance. | **Baseline ready:** E1 protocol runs end to end on pilot seeds |
| M3 Story stages | Stages 0 to 2, constraint decks, anti-default lists. Critic subagent for premise and beats. | **Knobs proven:** every story knob moves the output in a sweep (E2) |
| M4 Full production | Stages 5 to 8 and a larger style-module library. Preview and final render profiles. | **First full short:** seed to finished film with human input only at gates |
| M5 Experiments | Run E1 to E5 and feed findings back into skills. Grow anti-default lists from rater feedback. | **Results:** H1 to H3 accepted or rejected with the evidence |

In quest terms, M0–M5 are the milestones of one quest. Blender API probes are spikes, and new style modules are side quests that can run in parallel from M1 onward.

### M0: first milestone

M0 is done when a headless render reproduces reliably and every later stage has a place to write. No production stages are built in M0.

Tasks:

- [ ] Create the repo skeleton from the structure above. Commit this document as `docs/project-definition.md`, and have `CLAUDE.md` name it as the source of truth.
- [ ] Write `CLAUDE.md` v0, covering:
  - the Blender version in use
  - prefer `bpy.data` over `bpy.ops`
  - render only through the harness
  - doctrine changes need an ADR
- [ ] Run an API probe spike: a script reporting Blender version, render engines and GPU device, and confirming a scene builds in background mode. Record findings in `docs/adr/0001-blender-api-baseline.md`.
- [ ] Build the render harness: `render.py --scene <script> --profile preview|final --out <dir>`.
- [ ] Write a deliberately plain test scene: a few objects, one light, a camera move, 48 frames.
- [ ] Add a manifest writer and contact-sheet output (every Nth frame on one PNG).
- [ ] Add a smoke test in `tests/` that runs the preview render.

Acceptance:

- [ ] Two runs of the test scene on the same machine with the same seed match. Use exact hashes of the decoded frame pixels for EEVEE, and a small per-pixel tolerance for Cycles on GPU, which is not guaranteed bit-identical.
- [ ] The manifest records model ID, Blender version, machine, git commit, seeds and timings.
- [ ] The smoke test passes on both Macs in a few minutes.

## Open questions

- [ ] Project name.
- [ ] When to pin Blender. For now, use the latest installed version and record it in each manifest. Pin before E1 so experiment runs are comparable.
- [ ] Render hardware: an M5 Max and an M1, both using Metal GPU for Cycles and EEVEE. Proposal: the M5 Max renders finals and every experiment set, and the M1 handles development and previews. Record the machine in each manifest.
- [ ] Does narration lead or follow picture? If voice timing drives shot lengths, the narration stage belongs between beats and shots, not after render. Can E1 be silent?
- [ ] Who are the raters, and how many? Do interns count, or do raters need to be outside the project?
- [ ] Where do style modules come from: written from scratch, adapted from open-source node setups, or both?
- [ ] Diffusion-generated textures are deferred: out for v1, to be revisited if code-generated visuals plateau. The concern is attribution, not repeatability: a diffusion model's own look could mask whether the pipeline itself creates variety.
