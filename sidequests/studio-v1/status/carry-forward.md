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

- [0.1] -> 0.2 | contract | Pins: Makefile UV_VERSION=0.12.24 (uv.toml required-version copies it), .python-version=3.13.13; pyproject must equal both. Tools: .toolchain/{uv,just}/bin first on PATH.
- [0.1] -> 5.1 | gotcha | .python-version must equal Blender's bundled Python (doctor FAILs otherwise): bump Blender pin, .python-version and Makefile BLENDER_EXPECTED together.
