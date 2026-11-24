# Anchor image model decision record (F02)

**Status:** Option A approved and installed 2026-11-24 (all four files SHA-256 verified; listed by live `/object_info`). No model has been downloaded beyond the approval log below. Anchor T2I and reference-edit GPU/export gates remain **BLOCKED** until the owner renders each template once and exports `01_anchor_t2i.json` / `02_anchor_edit.json`.

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

Declared sources: `https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/…/split_files/{diffusion_models,text_encoders,vae}/…` and `https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/…/split_files/diffusion_models/…`. **Correction (2026-11-24):** the "Qwen-Image: Text to Image" template *contains* a `LoraLoaderModelOnly` node for `loras/Qwen-Image-Lightning-8steps-V1.0.safetensors` (1,698,951,104 bytes = 1.58 GiB, SHA-256 `07b5a999881437f63124979844ba1949ce2438f65b6220628a196a7d30a4fff9`, `huggingface.co/lightx2v/Qwen-Image-Lightning`, Apache-2.0 per Hugging Face metadata), so ComfyUI's *Setup required* panel reports it missing even when the template's Lightning switch is off. Either install it (keep the switch off for full-step anchors) or remove/bypass that node before exporting; an exported graph that still references an uninstalled LoRA fails `workflow-inspect`. The Edit 2509 template likewise references `Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors`.

**Size units:** ComfyUI's panel shows GiB/MiB; tables here use decimal GB. 19.03 GiB = 20.43 GB, 8.74 GiB = 9.38 GB, 242 MiB = 254 MB — same files. If the panel still lists installed files as missing, press its refresh (↻) button or reload the browser tab; the backend (`GET /models/<folder>`) is authoritative.

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
4. In the ComfyUI UI open **Workflow → Browse Templates → Image** and choose exactly **"Qwen-Image: Text to Image"** (file `image_qwen_image.json`). Not "Qwen Image 2512", "Qwen Image 2.1" or any LoRA/ControlNet variant: those need other weights. Set prompt to the orchid prompt from `configs/sequences/organic-machines.yaml`, a fixed seed, 832×480 (or the target size), disable the Lightning LoRA switch unless installed. Render once. Then **Workflow → Export (API)** and save as `C:\GIT\MorphCurrent\workflows\01_anchor_t2i.json`.
5. Open exactly **"Qwen Image Edit 2509"** (file `image_qwen_image_edit_2509.json`; not "Qwen Image Edit", "Qwen Image Edit 2511 …" or "Image Relight"), load the orchid image just generated, prompt the butterfly transformation, fixed seed, render once, export (API) as `workflows\02_anchor_edit.json`.
6. Run `python -m morph_studio.cli workflow-inspect workflows\01_anchor_t2i.json` (and `02_…`): must report `ok: true`, no cloud nodes, all models installed. Then a session writes `configs/profiles/anchor_t2i.binding.json` / `anchor_edit.binding.json` from the real node IDs and validates with `workflow-check`.

## Approval log

| Date | Option | Approved by | Scope (files, size, GPU renders) |
|---|---|---|---|
| 2026-11-24 | A (Qwen-Image + Qwen-Image-Edit-2509, fp8) | owner, in Claude Code chat ("Option A (Qwen)", then "Yes, download") | Download only: 4 files, 50.5 GB, from `huggingface.co/Comfy-Org/Qwen-Image` and `Comfy-Org/Qwen-Image-Edit`, each verified against the SHA-256 published by Hugging Face before install. Licenses per Hugging Face metadata: Apache-2.0 (Comfy-Org/Qwen-Image, Comfy-Org/Qwen-Image-Edit, Qwen/Qwen-Image, Qwen/Qwen-Image-Edit-2509, Qwen/Qwen2.5-VL-7B-Instruct). **No GPU render approved by this entry.** |

| 2026-11-24 | Lightning LoRAs for both templates | owner, in Claude Code chat ("Yes, download both") | Download only: 2 files, 2.55 GB, from `huggingface.co/lightx2v/Qwen-Image-Lightning` (Apache-2.0 per Hugging Face metadata), SHA-256 verified before install. Installed so the templates load complete; keep the Lightning switch **off** for full-step anchors. No GPU render approved. |

Expected SHA-256 (Hugging Face LFS metadata, 2026-11-24):

| File | Bytes | SHA-256 |
|---|---|---|
| `diffusion_models/qwen_image_fp8_e4m3fn.safetensors` | 20,430,635,136 | `98763a127701eb6fb59096f7742cb3aa7d64ed510b9f4e882d8351f8176e3ce3` |
| `diffusion_models/qwen_image_edit_2509_fp8_e4m3fn.safetensors` | 20,430,698,424 | `318568f61951ab9da21100c7b896e3c1da67f0d2efad6421545e022cfaa2b2b4` |
| `text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors` | 9,384,670,680 | `cb5636d852a0ea6a9075ab1bef496c0db7aef13c02350571e388aea959c5c0b4` |
| `vae/qwen_image_vae.safetensors` | 253,806,246 | `a70580f0213e67967ee9c95f05bb400e8fb08307e017a924bf3441223e023d1f` |
| `loras/Qwen-Image-Lightning-8steps-V1.0.safetensors` | 1,698,951,104 | `07b5a999881437f63124979844ba1949ce2438f65b6220628a196a7d30a4fff9` |
| `loras/Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors` | 849,608,296 | `2a32ce938ec71db2b49a817b4844ae86995569518dea56ee0ddc209cbe8e1377` |
