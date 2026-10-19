# Carry-forward ledger — studio-v1

> Cumulative, machine-loaded channel for routed cross-run handoffs. `/run-process` pre-flight
> prints the entries routed to the run being started; post-flight appends a run's handoffs.
> Format — one routed conclusion per line, ≤5 per run:
>
>     - [<from-run>] -> <targets> | <class> | <one-line conclusion>
>
> <targets>: comma-separated run IDs (no spaces), and/or `surface` (any run, any quest, on this
> surface) / `quest` (any later run here). <class>: contract | gotcha | deferred | decision.
> ROUTING RULE: an entry exists ONLY if addressed to a future audience — un-routed noise stays
> in the status report's Open Issues. See the run-process "Carry-forward ledger" section.

- [0.1] -> 5.1 | gotcha | .python-version must equal Blender's bundled Python (doctor FAILs otherwise): bump Blender pin, .python-version and Makefile BLENDER_EXPECTED together.
- [0.2] -> 0.4,0.5,0.6 | contract | Scene script = build(seed: int) -> None + module FRAME_COUNT: int; bpy.data only, no render/output settings; in-Blender entry puts repo root on sys.path (ADR-0002).
- [0.2] -> surface | gotcha | uv ignores [tool.uv] in a pyproject next to uv.toml: uv settings live only in uv.toml; tests/test_toolchain_pins.py guards it.
- [0.2] -> 5.1 | gotcha | fake-bpy-module-5.2==20260730 (pyproject dev group) moves with the Blender pin, alongside .python-version and BLENDER_EXPECTED.
- [0.2] -> 0.7 | contract | Blender tests take @pytest.mark.blender + the blender_bin fixture (tests/conftest.py); run_tests.sh's blender lane runs them — add no new lane.
- [0.3] -> 0.4,0.7 | contract | Engine IDs (5.2.2): BLENDER_EEVEE, BLENDER_WORKBENCH, CYCLES. Cycles GPU = prefs compute_device_type="METAL" + scene.cycles.device="GPU" (ADR-0001).
- [0.3] -> 0.4 | gotcha | Factory-startup scene.cycles.device is 'CPU' even with METAL prefs: Cycles silently renders on CPU unless the harness sets GPU and records it.
- [0.3] -> 0.4,0.7 | gotcha | PNG bytes differ every render (tEXt Date/RenderTime metadata): compare sha256 of decoded pixels (Image.pixels), never file bytes.
- [0.3] -> 0.7 | decision | EEVEE exact pixel sha256; Cycles Metal max abs diff <= 1/255, denoise off, fixed seed, no animated seed. Measured diff 0 on M5 Max (ADR-0001).
- [0.3] -> 0.7 | deferred | Rerun blender/probe/api_probe.py on the M1 Mac; quote its JSON in ADR-0001 and lift it from Provisional (expiry: M0 exit).
- [0.3] -> 0.5 | decision | Manifests name machines by a stable label, never the OS hostname (user, 2026-10-19): "M5 Max Laptop", "M5 Max Mac Studio", "M1"; pick the label mechanism in 0.5.

<!-- folded: consumed/resolved residues; pre-flight does not read past here -->
~ uv/Python pins: uv.toml required-version == Makefile UV_VERSION; pyproject requires-python admits .python-version — held by tests/test_toolchain_pins.py (est. 0.1, enforced 0.2)
