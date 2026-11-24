# Research — F02

## R1. Which local model families can ComfyUI 0.46.0 run without custom nodes?
- **Decision**: shortlist Qwen-Image family; it is supported by core nodes present in live `/object_info` (`TextEncodeQwenImageEdit`, `TextEncodeQwenImageEditPlus`, `TextEncodeQwenImage21`, `ModelSamplingAuraFlow`, `EmptySD3LatentImage`, `FluxKontextImageScale`) and ships official templates in the installed `comfyui_workflow_templates_json` package.
- **Evidence (read 2026-11-24, local files)**: `image_qwen_image.json`, `image_qwen_image_edit_2509.json`, `image_qwen_image_edit_2511.json`, `image_qwen_image_2_1_t2i.json`, `image_qwen_image_2_1_image_edit.json` — model filenames, folders and source URLs taken from their `models` metadata (see docs/MODELS.md).
- **Alternatives**: FLUX.1 Kontext / FLUX.2 (core nodes exist) — not shortlisted first because the owner must accept a separate license and no local template metadata was examined; can be added later via the same procedure.

## R2. Shared components reduce VRAM/disk
- Qwen-Image T2I and Qwen-Image-Edit-2509 share `qwen_2.5_vl_7b_fp8_scaled.safetensors` and `qwen_image_vae.safetensors`; only the diffusion model differs. Qwen-Image 2.1 templates use one diffusion model for both T2I and edit.
- Sequential scheduling (image stage, then Wan stage) remains mandatory on 48 GiB; peak VRAM NOT MEASURED.

## R3. Role contracts
- **Decision**: contracts keyed by `capability`; only enforced when a profile declares it (Wan profile now declares `wan_flf2v` and satisfies its contract).

## R4. Role candidates in inspect
- **Decision**: heuristic *hints* by class/input (`text`/`prompt` STRING on text-encoder classes → prompt candidate; `seed`/`noise_seed` INT → seed; `LoadImage.image` → reference/start image; output nodes with IMAGE input → image output; width/height INT on latent nodes → size). Printed as `candidate`; the profile author confirms by reading the graph (constitution III forbids code guessing node IDs into executable profiles).
