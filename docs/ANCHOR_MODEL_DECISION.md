# Anchor image model decision record (F02)

**Status:** awaiting owner decision. **No model has been downloaded** and none will be without an explicit, bounded owner approval recorded below. Anchor T2I and reference-edit GPU/export gates are **BLOCKED**.

**Measured local state (2026-11-24, `morphcurrent baseline`, read-only):** `checkpoints/` empty; `diffusion_models/` holds only the two Wan 2.2 I2V FP8 experts; `text_encoders/` only UMT5; `vae/` only the Wan 2.1 VAE. Those are video dependencies and cannot generate anchor stills.

## Candidates (source: ComfyUI templates installed locally)

All filenames, folders and source URLs below are copied from the `models` metadata of the official templates in ComfyUI Portable's installed package `comfyui_workflow_templates_json` (templates 0.11.111). They run on **core** ComfyUI 0.46.0 nodes present in live `/object_info` — no custom nodes required. Sizes are **approximate** (check before downloading). Licenses: **owner to verify** on each model card; nothing here asserts a license.

### Option A — Qwen-Image (T2I) + Qwen-Image-Edit-2509 (reference edit) · recommended starting point

Shares one text encoder and VAE between both stages; only the diffusion model differs.

| Folder (`ComfyUI\models\…`) | File | Template | Approx. size |
|---|---|---|---|
| `diffusion_models` | `qwen_image_fp8_e4m3fn.safetensors` | `image_qwen_image.json` | ~20 GB |
| `diffusion_models` | `qwen_image_edit_2509_fp8_e4m3fn.safetensors` | `image_qwen_image_edit_2509.json` | ~20 GB |
| `text_encoders` | `qwen_2.5_vl_7b_fp8_scaled.safetensors` | both | ~9 GB |
| `vae` | `qwen_image_vae.safetensors` | both | <1 GB |

Declared sources: `https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/…/split_files/{diffusion_models,text_encoders,vae}/…` and `https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/…/split_files/diffusion_models/…`. The templates also list optional Lightning LoRAs (`lightx2v/Qwen-Image-Lightning`); **not required** — skip unless the owner wants faster, lower-step renders.

Edit graph nodes (template): `LoadImage` → `FluxKontextImageScale` → `TextEncodeQwenImageEditPlus` (prompt + image + VAE) → `VAEEncode` latent → `KSampler` → `VAEDecode` → `SaveImage(Advanced)`. This is genuine reference editing: the parent anchor's pixels condition the edit.

### Option B — Qwen-Image 2.1 (one diffusion model for T2I and edit)

Templates `image_qwen_image_2_1_t2i.json` / `image_qwen_image_2_1_image_edit.json` declare `diffusion_models/qwen_image_2.1_int8_convrot.safetensors`, `text_encoders/qwen3vl_8b_int8_convrot.safetensors`, `vae/qwen_image_2.1_vae_bf16.safetensors`, plus a per-mode prompt-enhancer encoder (`qwen3.5_9b_qwen_image_2.1_pe_{t2i,i2i}.int8_convrot.safetensors`) used by a `TextGenerate` node. Fewer diffusion weights, but newer and with an LLM prompt-rewrite step that could alter storyboard prompts — needs evaluation before adoption.

### Not shortlisted now
FLUX.1 Kontext / FLUX.2 (core nodes exist) — separate license terms; can be onboarded later with the same procedure. ComfyUI **API nodes** (`QwenImageEditApi`, `Flux2ImageNode`, …) are remote services and are rejected by MorphCurrent (F01).

## VRAM plan (RTX A6000, 48 GiB)

Image stages and Wan stages run **sequentially**, never concurrently. About 35.6 GiB was held by other processes at measurement time (nvidia-smi snapshot), so free headroom may be the real constraint; ComfyUI offloads between stages in default VRAM mode. Peak VRAM: **NOT MEASURED** — F07 adds an opt-in sampler for the first approved image render.

## Owner procedure once a set is approved (manual; Claude does not download)

1. Confirm the queue is idle (`morphcurrent baseline`).
2. Download the files of the approved option from the declared sources into the listed folders under `C:\AI\ComfyUI_windows_portable\ComfyUI\models\`. Verify licenses on the model cards.
3. Refresh ComfyUI (no restart needed for new model files in most cases; if they do not appear, restart ComfyUI yourself).
4. In the ComfyUI UI open template **Qwen-Image** (Option A). Set prompt to the orchid prompt from `configs/sequences/organic-machines.yaml`, a fixed seed, 832×480 (or the target size), disable the Lightning LoRA switch unless installed. Render once. Then **Workflow → Export (API)** and save as `C:\GIT\MorphCurrent\workflows\01_anchor_t2i.json`.
5. Open template **Qwen-Image-Edit 2509**, load the orchid image just generated, prompt the butterfly transformation, fixed seed, render once, export (API) as `workflows\02_anchor_edit.json`.
6. Run `python -m morph_studio.cli workflow-inspect workflows\01_anchor_t2i.json` (and `02_…`): must report `ok: true`, no cloud nodes, all models installed. Then a session writes `configs/profiles/anchor_t2i.binding.json` / `anchor_edit.binding.json` from the real node IDs and validates with `workflow-check`.

## Approval log

| Date | Option | Approved by | Scope (files, size, GPU renders) |
|---|---|---|---|
| — | — | — | *none yet* |
