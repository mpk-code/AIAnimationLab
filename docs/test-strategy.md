# Test Strategy

How AIAnimationLab is tested. The canonical runner is `scripts/run_tests.sh` (pytest + ruff + mypy; created in M0).

## Layers

| Layer | What it covers | Runs in |
| --- | --- | --- |
| Unit | Pure Python: schema validation, deck draws, validators, manifest writer, metrics | Plain Python, fast, every run |
| Blender integration | Style modules and scene scripts build correctly in background mode (`blender -b --python ...`) | Headless Blender, no render or a 1-frame render |
| Render smoke | The harness renders the plain test scene with the preview profile and writes a manifest and contact sheet | Headless Blender, minutes |
| Reproducibility | Two runs with the same seed match: exact hashes of the decoded frame pixels for EEVEE (PNG bytes carry render-time metadata — ADR-0001), small per-pixel tolerance for Cycles on GPU | Headless Blender; part of the M0 exit gate |
| Knob sweeps (E2) | Each shipped knob moves both the artifacts and the frames | Experiment harness in `eval/` |

## Rules

- A bug fix starts with a failing test that reproduces it.
- Tests that need Blender are marked (`@pytest.mark.blender`) so the unit layer runs without it.
- Smoke tests must pass on both Macs (M5 Max and M1) in a few minutes.
- Never assert on a full-resolution final render in the default lane; use the preview profile.
