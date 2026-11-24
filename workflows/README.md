# MorphCurrent — ComfyUI API workflow inventory

## Actual status from GitHub main (baseline 2026-11-24)

| Workflow | Status | Binding | Responsibility |
|---|---|---|---|
| `03_wan22_flf2v.json` | **REAL, committed and locally schema-validated** | `configs/profiles/wan22_flf2v.binding.json` (hash pinned) | Wan 2.2 14B I2V FLF2V bridge (user and MorphCurrent-dispatched GPU runs already documented) |
| `01_anchor_t2i.json` | **MISSING** until verified ComfyUI text-to-image model and a successful export | `configs/profiles/<actual-t2i>.binding.json` (future) | Automatic first anchor A |
| `02_anchor_edit.json` | **MISSING** until verified image editing model and a successful export | `configs/profiles/<actual-edit>.binding.json` (future) | Reference-edit B from A, C from B |

Do not claim Wan 2.2 video-model installation supplies a general text-to-image anchor model. Candidate model families FLUX/Qwen Image are not confirmed installed in ComfyUI on this machine. Follow [`docs/ANCHOR_MODEL_ONBOARDING.md`](../docs/ANCHOR_MODEL_ONBOARDING.md) and Spec Kit feature F02 in [`docs/SPECKIT_FEATURE_LEDGER.md`](../docs/SPECKIT_FEATURE_LEDGER.md).

## Required API export procedure

1. Inspect the real local ComfyUI `/object_info` and installed checkpoint list read-only. If a smoke render is running, don't install models, restart ComfyUI or queue new jobs.
2. With owner approval, choose/license/install a T2I image model and a reference-edit model compatible with this exact native Windows + RTX A6000 environment. Run the graph manually and verify image output **before exporting**.
3. In ComfyUI export **Save (API Format)**, not the editor's UI-graph JSON; save sanitized outputs as `workflows/01_anchor_t2i.json` and `workflows/02_anchor_edit.json`. Ensure graph contains actual working class IDs, inputs, links and output node(s).
4. Build separate semantic profiles in `configs/profiles/` using real node IDs. Bind prompt, negative, seed, dimensions, model choice, input reference image for editing, and image output. Pin the graph SHA and validate against local `/object_info` and fixtures.
5. Preserve the already working `03_wan22_flf2v.json` + profile. Don't rewrite the sampler split or swap T2V weights for I2V experts.
6. Before commit, inspect new exports for secrets, personal output paths and environment-specific metadata; never commit weights or media. Add mocked contract tests; local GPU image generation is a separate owner-approved acceptance gate.

The approved runtime is only **native Windows 11** ComfyUI on `127.0.0.1:8188`, independent from controller `.venv`; Python-only Spec Kit tooling. The ordinary editor's visual graph JSON is not a queueable API graph. If model/edit capability is absent, mark F02 BLOCKED with a precise manual installation step, and continue safe offline tasks rather than inventing nodes.
