# MorphCurrent — measured environment (F01)

**Measured:** 2026-11-24 13:30 UTC with `python -m morph_studio.cli baseline` (GET `/system_stats`, `/queue`, `/object_info` on 127.0.0.1:8188 plus one `nvidia-smi --query-gpu` reading). Nothing was queued, uploaded, interrupted or loaded. Regenerate any time with the same command; this file records one observation, not a guarantee.

## Host and ComfyUI

| Fact | Value | Method |
|---|---|---|
| Repository HEAD at measurement | `7c54caf85987f645619a592d0c5775fee0dc0809` (`main`) | `git rev-parse` |
| Controller Python | 3.12.10 (`.venv`) | `python --version` |
| ComfyUI | 0.46.0, Portable, embedded Python 3.13.14, PyTorch 2.14.1+cu130 | `/system_stats` |
| Launch flags | `--windows-standalone-build --listen 127.0.0.1 --port 8188` (loopback only, default VRAM mode) | `/system_stats` argv |
| GPU | NVIDIA RTX A6000, 51,526,500,352 bytes total (49,140 MiB per nvidia-smi) | `/system_stats`, nvidia-smi |
| GPU memory in use | 35,616 MiB — **snapshot (not peak)**, ComfyUI idle; held by other processes (see PROGRESS M3) | nvidia-smi |
| `/system_stats` vram_free | 14,177,250,198 bytes — **snapshot (not peak)**; observed static during a render in M3 | `/system_stats` |
| Peak VRAM during any render | **NOT MEASURED** (opt-in sampler is F07) | — |
| Queue at measurement | running 0, pending 0 | `/queue` |
| FFmpeg / ffprobe | 8.1.2 full build on PATH (WinGet Gyan.FFmpeg) | `which` |

## Installed model files (loader choices in `/object_info`)

| Folder | Files |
|---|---|
| checkpoints | *(none)* |
| diffusion_models | `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors`, `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors`; **added 2026-11-24 09:18 UTC (owner-approved, SHA-256 verified):** `qwen_image_fp8_e4m3fn.safetensors`, `qwen_image_edit_2509_fp8_e4m3fn.safetensors` |
| text_encoders | `umt5_xxl_fp8_e4m3fn_scaled.safetensors`; added `qwen_2.5_vl_7b_fp8_scaled.safetensors` |
| vae | `wan_2.1_vae.safetensors`, added `qwen_image_vae.safetensors` (+ built-in `taef1`, `taesdxl`, `taesd`, `pixel_space`) |
| loras | added 2026-11-24 (owner-approved, SHA-256 verified): `Qwen-Image-Lightning-8steps-V1.0.safetensors`, `Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors` |

Model checkpoint SHA-256: Qwen files verified at download against Hugging Face's published hashes (see `docs/MODELS.md`); Wan files **NOT MEASURED** (hashing multi-GB weights is deferred to an owner-scheduled F07 step). License review of the installed Wan files: **not recorded** here.

## Capabilities

| Capability | Status | Reason |
|---|---|---|
| Wan 2.2 FLF2V bridge | **available** | `configs/profiles/wan22_flf2v.binding.json` validates against live `/object_info` (1 warning: UI-only `video-preview`) |
| Anchor text-to-image | **BLOCKED** | Qwen-Image weights now installed (visible in `/object_info`); still no verified `workflows/01_anchor_t2i.json` export |
| Anchor reference edit | **BLOCKED** | Qwen-Image-Edit-2509 weights installed; no verified `workflows/02_anchor_edit.json` export yet; core *node classes* exist (`TextEncodeQwenImageEdit`, `TextEncodeQwenImageEditPlus`, `ReferenceLatent`, `FluxKontextImageScale`) but node classes are not models |

## Local-only policy

The installed ComfyUI exposes 1066 node classes, of which 363 come from `comfy_api_nodes` (344 flagged `api_node: true`), e.g. `QwenImageEditApi`, `Flux2ImageNode`. These call remote paid services. Since F01 `validate_graph` rejects any graph that contains one, and the shared GPU gate (`morph_studio.gates.check_gpu_gate`) refuses to submit it.
