---
id: 0001
title: Blender 5.2.2 API baseline and render determinism policy
status: Accepted
date: 2026-10-19
supersedes: N/A
superseded-by: N/A
---

# 0001: Blender 5.2.2 API baseline and render determinism policy

## Status

Accepted 2026-10-19 after the M1 Laptop probe and the harness-level reproducibility tests (studio-v1 Run 0.7). It was Provisional from Run 0.3 until the second Mac was probed.

## Context

M0's exit gate is a reproducible render (`docs/project-definition.md` §M0 Acceptance): EEVEE is compared by exact frame hash and Cycles on GPU by a small per-pixel tolerance. The harness (Run 0.4) and the reproducibility tests (Run 0.7) need the engine identifiers, the Metal device setup and the tolerance value before they're written. §Risks lists "Blender API drift" and gives an API probe spike as one of its mitigations. This ADR records what the probe measured on Blender 5.2.2 LTS.

## Decision

On Blender 5.2.2 LTS on Apple Silicon:
- **EEVEE** (`BLENDER_EEVEE`) is the exact-hash reproducibility engine. Two renders match when the sha256 of their decoded RGBA pixel buffers match. PNG file bytes are not compared.
- **Cycles** (`CYCLES`) is set to `scene.cycles.device = "GPU"` with Cycles add-on preference `compute_device_type = "METAL"`, denoise off, a fixed `seed` and `use_animated_seed = False`. Two renders match when every 8-bit channel differs by at most 1/255.

## Evidence

The probe ran on the **M5 Max Laptop** (Apple M5 Max, arm64, 128 GB, macOS 27.0.1, 40-core GPU) at commit 86aad30. In the quoted report the `hostname` value is replaced by that machine label; the raw report recorded the OS hostname. It ran twice as separate processes:

```
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -noaudio --python-exit-code 1 \
  --python blender/probe/api_probe.py -- --out <scratch>/run<N> --report <scratch>/probe-m5max-run<N>.json
```

Both runs exited 0. Each run renders one 256×256 frame twice per engine. Within each run, and between the two runs, the decoded pixel hashes are identical:

| Engine | pixel_sha256 (all 4 renders) | max abs diff (1/255) | PNG file sha256 |
| --- | --- | --- | --- |
| `BLENDER_EEVEE` (64 TAA samples) | `d7e06ed6a6d39b4f6de4326ad1fe053f928e561fedc56564dc1f0156b6d3d892` | 0 | differs every render |
| `CYCLES` GPU/Metal (16 samples, adaptive on, denoise off, seed 0) | `f07c44023ffd1119aa8d5cbdb85f5a9a602b098716052b60f6e2f4ab1a86deba` | 0 | differs every render |

The PNG files differ because Blender writes render metadata into `tEXt` chunks, including `Date` and `RenderTime` (e.g. `RenderTime 00:00.33` vs `00:00.24`). Between the two runs' reports, `diff` shows only `file_sha256` and `wall_seconds` changing.

Other findings:
- `--factory-startup` defaults: `compute_device_type = 'METAL'`, but `scene.cycles.device = 'CPU'`. A Cycles render that doesn't set the device runs on the CPU.
- The RNA enum's static `enum_items` for `RenderSettings.engine` lists only `BLENDER_EEVEE`. The runtime set (`BLENDER_EEVEE`, `BLENDER_WORKBENCH`, `CYCLES`) is only visible from the error raised when an invalid identifier is assigned. The 5.x EEVEE identifier is `BLENDER_EEVEE`, not 4.x's `BLENDER_EEVEE_NEXT`.
- `gpu.platform.*` raises `SystemError` in background mode until a render has initialised the GPU module. After the EEVEE render it reports backend `METAL`.
- The fake-bpy-module-5.2 stubs leave two things untyped: Cycles add-on properties, and `bpy_prop_array` indexing and `len`.

Probe report, run 1 (verbatim):

```json
{
  "blender": {
    "background": true,
    "build_branch": "blender-v5.2-release",
    "build_date": "2026-09-15",
    "build_hash": "d13f752e3b9c",
    "python": "3.13.13 (main, Apr 25 2025, 12:39:20) [Clang 21.0.0 (clang-2100.0.123.102)]",
    "version": [
      5,
      2,
      2
    ],
    "version_string": "5.2.2 LTS"
  },
  "cycles": {
    "compute_device_type": "METAL",
    "compute_device_types": [
      "NONE",
      "METAL"
    ],
    "devices": [
      {
        "name": "Apple M5 Max",
        "type": "CPU",
        "use": false
      },
      {
        "name": "Apple M5 Max (GPU - 40 cores)",
        "type": "METAL",
        "use": true
      }
    ]
  },
  "determinism": {
    "BLENDER_EEVEE": {
      "differing_pixels": 0,
      "max_abs_diff_255": 0,
      "pixel_hash_equal": true,
      "runs": [
        {
          "file": "blender_eevee_1.png",
          "file_sha256": "a0b9a7ca57148ea3e167b92fabeea4b4b0d94a242ed7e50bdb0bebf53a09a21c",
          "pixel_sha256": "d7e06ed6a6d39b4f6de4326ad1fe053f928e561fedc56564dc1f0156b6d3d892",
          "wall_seconds": 0.386
        },
        {
          "file": "blender_eevee_2.png",
          "file_sha256": "bb5f1450260ade55a58a09e4ec0f648fe6ce98fe1d2b21ce0744ecf83dbd4c7c",
          "pixel_sha256": "d7e06ed6a6d39b4f6de4326ad1fe053f928e561fedc56564dc1f0156b6d3d892",
          "wall_seconds": 0.25
        }
      ],
      "settings": {
        "engine": "BLENDER_EEVEE",
        "file_format": "PNG RGBA 8-bit",
        "film_transparent": false,
        "resolution": [
          256,
          256
        ],
        "taa_render_samples": 64,
        "view_transform": "AgX"
      }
    },
    "CYCLES": {
      "differing_pixels": 0,
      "max_abs_diff_255": 0,
      "pixel_hash_equal": true,
      "runs": [
        {
          "file": "cycles_1.png",
          "file_sha256": "b635d6de2f4bdafd06fdbe9aaa1557a37da4c7c1f744cd4a84a7df3b29199734",
          "pixel_sha256": "f07c44023ffd1119aa8d5cbdb85f5a9a602b098716052b60f6e2f4ab1a86deba",
          "wall_seconds": 2.547
        },
        {
          "file": "cycles_2.png",
          "file_sha256": "60686b644312830800133f4d0c1aa7177da55d1561102cfd53699bfc2eeda2da",
          "pixel_sha256": "f07c44023ffd1119aa8d5cbdb85f5a9a602b098716052b60f6e2f4ab1a86deba",
          "wall_seconds": 0.487
        }
      ],
      "settings": {
        "device": "GPU",
        "engine": "CYCLES",
        "file_format": "PNG RGBA 8-bit",
        "film_transparent": false,
        "resolution": [
          256,
          256
        ],
        "samples": 16,
        "seed": 0,
        "use_adaptive_sampling": true,
        "use_animated_seed": false,
        "use_denoising": false,
        "view_transform": "AgX"
      }
    }
  },
  "gpu": {
    "backend": "METAL",
    "device_type": "APPLE",
    "renderer": "Metal API",
    "vendor": "Apple M5 Max",
    "version": "1.2"
  },
  "machine": {
    "arch": "arm64",
    "cpu": "Apple M5 Max",
    "git_commit": "86aad303b1e99c2263b58dde10c6bb432722b150",
    "hostname": "M5 Max Laptop",
    "macos": "27.0.1",
    "memory_bytes": 137438953472
  },
  "probe": "blender/probe/api_probe.py",
  "render_engines": [
    "BLENDER_EEVEE",
    "BLENDER_WORKBENCH",
    "CYCLES"
  ],
  "scene_build": {
    "built_with": "bpy.data only",
    "cameras": 1,
    "lights": 1,
    "meshes": 2,
    "objects": 4,
    "ok": true
  }
}
```

### M1 Laptop (Run 0.7)

The same probe ran on the **M1 Laptop** (Apple M1 Max, arm64, 64 GB, macOS 26.6.2, 32-core GPU) at commit b11b130, twice as separate processes, with the command above. Both runs exited 0. As above, the quoted report carries the machine label in `hostname`.

| Engine | pixel_sha256 (all 4 renders) | max abs diff (1/255) | PNG file sha256 |
| --- | --- | --- | --- |
| `BLENDER_EEVEE` (64 TAA samples) | `ea34063d51ad62b844e7b51aeb069c25e5be6af36e4b49f462a8af023ead4b68` | 0 | differs every render |
| `CYCLES` GPU/Metal (16 samples, adaptive on, denoise off, seed 0) | `f07c44023ffd1119aa8d5cbdb85f5a9a602b098716052b60f6e2f4ab1a86deba` | 0 | differs every render |

The engine list, Metal device setup and `bpy.data`-only scene build match the M5 Max Laptop. The Cycles probe frame is identical on both Macs. The EEVEE probe frame is identical across runs on each Mac but **differs between the two Macs** (`ea3406…` here, `d7e06e…` on the M5 Max Laptop).

Run 1 report:

```json
{
  "blender": {
    "background": true,
    "build_branch": "blender-v5.2-release",
    "build_date": "2026-09-15",
    "build_hash": "d13f752e3b9c",
    "python": "3.13.13 (main, Apr 25 2025, 12:39:20) [Clang 21.0.0 (clang-2100.0.123.102)]",
    "version": [
      5,
      2,
      2
    ],
    "version_string": "5.2.2 LTS"
  },
  "cycles": {
    "compute_device_type": "METAL",
    "compute_device_types": [
      "NONE",
      "METAL"
    ],
    "devices": [
      {
        "name": "Apple M1 Max",
        "type": "CPU",
        "use": false
      },
      {
        "name": "Apple M1 Max (GPU - 32 cores)",
        "type": "METAL",
        "use": true
      }
    ]
  },
  "determinism": {
    "BLENDER_EEVEE": {
      "differing_pixels": 0,
      "max_abs_diff_255": 0,
      "pixel_hash_equal": true,
      "runs": [
        {
          "file": "blender_eevee_1.png",
          "file_sha256": "9e7a41bc61eece38cf7cca6575e8dfdee9e0f2d9feade9af3402d0993aa0f6b4",
          "pixel_sha256": "ea34063d51ad62b844e7b51aeb069c25e5be6af36e4b49f462a8af023ead4b68",
          "wall_seconds": 1.041
        },
        {
          "file": "blender_eevee_2.png",
          "file_sha256": "886bf0f99aa63ccae0c7426d3b6c5c4b4a72decfdc897d98bc383c7269d4f108",
          "pixel_sha256": "ea34063d51ad62b844e7b51aeb069c25e5be6af36e4b49f462a8af023ead4b68",
          "wall_seconds": 0.293
        }
      ],
      "settings": {
        "engine": "BLENDER_EEVEE",
        "file_format": "PNG RGBA 8-bit",
        "film_transparent": false,
        "resolution": [
          256,
          256
        ],
        "taa_render_samples": 64,
        "view_transform": "AgX"
      }
    },
    "CYCLES": {
      "differing_pixels": 0,
      "max_abs_diff_255": 0,
      "pixel_hash_equal": true,
      "runs": [
        {
          "file": "cycles_1.png",
          "file_sha256": "3d088ad108c467b29f8b1e321d866ab11ecb1af1abf31cd5f75bc4357298bc67",
          "pixel_sha256": "f07c44023ffd1119aa8d5cbdb85f5a9a602b098716052b60f6e2f4ab1a86deba",
          "wall_seconds": 0.332
        },
        {
          "file": "cycles_2.png",
          "file_sha256": "1bc6739184e9950ff7b4d14ee9be124e419e98bf1fab8a7d71e8624ec6b7fc2f",
          "pixel_sha256": "f07c44023ffd1119aa8d5cbdb85f5a9a602b098716052b60f6e2f4ab1a86deba",
          "wall_seconds": 0.321
        }
      ],
      "settings": {
        "device": "GPU",
        "engine": "CYCLES",
        "file_format": "PNG RGBA 8-bit",
        "film_transparent": false,
        "resolution": [
          256,
          256
        ],
        "samples": 16,
        "seed": 0,
        "use_adaptive_sampling": true,
        "use_animated_seed": false,
        "use_denoising": false,
        "view_transform": "AgX"
      }
    }
  },
  "gpu": {
    "backend": "METAL",
    "device_type": "APPLE",
    "renderer": "Metal API",
    "vendor": "Apple M1 Max",
    "version": "1.2"
  },
  "machine": {
    "arch": "arm64",
    "cpu": "Apple M1 Max",
    "git_commit": "b11b130619e89d5d05fabb557a3be2737d901944",
    "hostname": "M1 Laptop",
    "macos": "26.6.2",
    "memory_bytes": 68719476736
  },
  "probe": "blender/probe/api_probe.py",
  "render_engines": [
    "BLENDER_EEVEE",
    "BLENDER_WORKBENCH",
    "CYCLES"
  ],
  "scene_build": {
    "built_with": "bpy.data only",
    "cameras": 1,
    "lights": 1,
    "meshes": 2,
    "objects": 4,
    "ok": true
  }
}
```

### Harness-level evidence (Run 0.7)

`tests/test_render_determinism.py` and `scripts/collect_machine_evidence.sh` render the 48-frame plain test scene through the harness (`blender/harness/render.py`) and compare runs with `blender/harness/compare.py`. Clean tree at b11b130 on both Macs:

| Check (same machine, seed 0) | M5 Max Laptop | M1 Laptop |
| --- | --- | --- |
| EEVEE preview, 48 frames × 2 renders | exact: 48/48 frames pixel-equal, max diff 0 | exact: 48/48 frames pixel-equal, max diff 0 |
| Cycles final (1920×1080, 256 samples, denoise off), 1 frame × 2 renders | max diff 1/255 in 61 of 2,073,600 pixels: within tolerance | max diff 1/255 in 32 of 2,073,600 pixels: within tolerance |
| EEVEE frame 1 pixel_sha256 | `1ed82d48…12d2d` | `814a99da…77e0eb` |

So the tolerance for Cycles is exercised, not hypothetical: at the final profile Cycles on Metal is not bit-identical between two same-seed renders on one machine, though it was on the 256×256 probe frame. The harness hashes 8-bit decoded RGBA (`manifest.pixel_sha256`), so its values differ from the probe's float-buffer hashes for the same image.

## Alternatives considered

| Alternative | Why not chosen |
| --- | --- |
| Exact hash for Cycles too (measured diff was 0) | The evidence is one frame, one machine and one scene. Cycles on GPU is not guaranteed bit-identical (§M0 Acceptance). Exact-hash would fail on the first scheduling-dependent difference. The 1/255 tolerance still catches any real change. |
| Hash PNG file bytes | They differ on every render because of the metadata (Date, RenderTime). Disabling the stamp metadata would also work, but it couples the test to every metadata field Blender adds in future versions. |
| Tolerance path for EEVEE as well | EEVEE was bit-identical in every render. An exact hash is the stronger test, and it is what §M0 asks for. |
| Cycles with OIDN denoise in the reproducibility test | Not measured. Denoising adds a second source of nondeterminism. Finals may still denoise; that is a profile decision for Run 0.4, outside this test. |

## Consequences

- **Spike exception to STD-002/STD-003 (time-boxed):** `blender/probe/api_probe.py` calls `bpy.ops.render.render` and sets `render.filepath` in a single function, `_render_still`, outside `blender/harness/`. It is a probe, not a production path:
  - its output goes only to the `--out` scratch directory;
  - it writes no manifest;
  - nothing else may import it.

  The exception covers re-running this probe (on the M1 Mac and on every Blender version change). It does not cover adding new render calls under `blender/probe/` once the harness exists. CLAUDE.md is unchanged.
- **The harness (Run 0.4)** must set `scene.cycles.device = "GPU"` and the Cycles preference `compute_device_type = "METAL"` explicitly, and write both into the manifest. Frame comparison hashes decoded pixels, not files.
- **The reproducibility tests (Run 0.7)** use the EEVEE pixel sha256 and the Cycles max-abs-diff ≤ 1/255 check from the Decision, through `blender/harness/compare.py`. Re-run the probe and `scripts/collect_machine_evidence.sh` on every Blender version change and on any new render machine.
- If a later machine or Blender version shows EEVEE is not bit-identical **on one machine**, the policy moves to the tolerance path for both engines, which needs an amendment to §M0 Acceptance. (Both Macs were bit-identical per machine in Run 0.7.)
- **Reproducibility is per machine.** EEVEE output for the same scene and seed differs between the M5 Max Laptop and the M1 Laptop, so a render is reproducible exactly only on the machine that made it. Comparisons must pair runs from one machine (every manifest records `machine.label`). This supports the project definition's proposal that one machine renders finals and every experiment set (§Open questions, render hardware).
