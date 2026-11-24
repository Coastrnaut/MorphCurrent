# Research — F01

## R1. How to recognise ComfyUI cloud API nodes
- **Decision**: a class is cloud when its `/object_info` entry has `api_node: true` **or** `python_module` starts with `comfy_api_nodes`.
- **Rationale**: Measured on local ComfyUI 0.46.0 (2026-11-24): 1066 classes; 344 `api_node: true`; 363 classes from module `comfy_api_nodes` (both fields present on the API nodes inspected, e.g. `QwenImageEditApi`). Core local nodes such as `TextEncodeQwenImageEdit` are `api_node: false`, module `comfy_extras.nodes_qwen`.
- **Alternatives**: name suffix matching (`*Api`, `*Node`) — rejected, unreliable (`FluxKontextImageScale` is local, `Flux2ImageNode` is cloud).

## R2. What counts as "image capability available"
- **Decision**: `available` only if a binding profile for that role exists in `configs/profiles/` and validates against live `/object_info`. Otherwise `blocked`, with installed loader choices listed so the owner sees what is missing.
- **Rationale**: Constitution III: a node class existing (e.g. `ReferenceLatent`) does not mean a model is installed. Measured: `CheckpointLoaderSimple.ckpt_name` = `[]`, `UNETLoader.unet_name` = only the two Wan 2.2 I2V experts, `CLIPLoader.clip_name` = only `umt5_xxl_fp8_e4m3fn_scaled.safetensors`.
- **Alternatives**: heuristics on filenames — rejected as guessing.

## R3. GPU memory figures
- **Decision**: include `/system_stats` VRAM and optionally one `nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits` reading, both labelled `snapshot (not peak)`.
- **Rationale**: PROGRESS M3 showed `vram_free` stayed static during a render; peak sampling belongs to F07.

## R4. Shared gate placement
- **Decision**: pure function `check_gpu_gate(consent, queue, graph, object_info, allow_busy_queue)` in `gates.py`; `bridge._submit` uses it for the queue rule while keeping its exact existing error text.
- **Rationale**: Keeps bridge regression tests stable and gives anchors/pipeline one implementation.
