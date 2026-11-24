# Models and workflows

All models run inside the local ComfyUI Portable install (`C:\AI\ComfyUI_windows_portable\ComfyUI\models\…`). Nothing is downloaded by MorphCurrent code. Image models were chosen from ComfyUI's own installed templates and run on core ComfyUI 0.46.0 nodes (no custom nodes).

## Installed models

| Stage | Folder | File | SHA-256 |
|---|---|---|---|
| Video (Wan 2.2 I2V FLF2V) | `diffusion_models` | `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` | `6122e79d55e0f235698d11d657f3b196c5273c830da00b2b013c5a048d5e6a42` |
| | `diffusion_models` | `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` | `5471a457b6ac404202a5fbe6c11595a3d5641fc766b00f38763f72303fffc21e` |
| | `text_encoders` | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | `c3355d30191f1f066b26d93fba017ae9809dce6c627dda5f6a66eaa651204f68` |
| | `vae` | `wan_2.1_vae.safetensors` | `2fc39d31359a4b0a64f55876d8ff7fa8d780956ae2cb13463b0223e15148976b` |
| Anchor T2I (Qwen-Image) | `diffusion_models` | `qwen_image_fp8_e4m3fn.safetensors` | `98763a127701eb6fb59096f7742cb3aa7d64ed510b9f4e882d8351f8176e3ce3` |
| Anchor edit (Qwen-Image-Edit-2509) | `diffusion_models` | `qwen_image_edit_2509_fp8_e4m3fn.safetensors` | `318568f61951ab9da21100c7b896e3c1da67f0d2efad6421545e022cfaa2b2b4` |
| Both Qwen stages | `text_encoders` | `qwen_2.5_vl_7b_fp8_scaled.safetensors` | `cb5636d852a0ea6a9075ab1bef496c0db7aef13c02350571e388aea959c5c0b4` |
| | `vae` | `qwen_image_vae.safetensors` | `a70580f0213e67967ee9c95f05bb400e8fb08307e017a924bf3441223e023d1f` |
| Template-referenced, unused (turbo off) | `loras` | `Qwen-Image-Lightning-8steps-V1.0.safetensors` | `07b5a999881437f63124979844ba1949ce2438f65b6220628a196a7d30a4fff9` |
| | `loras` | `Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors` | `2a32ce938ec71db2b49a817b4844ae86995569518dea56ee0ddc209cbe8e1377` |

Qwen hashes were computed while downloading and match the values Hugging Face publishes. Sources: `huggingface.co/Comfy-Org/Qwen-Image`, `Comfy-Org/Qwen-Image-Edit`, `lightx2v/Qwen-Image-Lightning`; Apache-2.0 per their Hugging Face metadata (owner to verify on the model cards). Wan hashes were measured locally on 2026-11-24 with `models-hash --confirm-io` (owner-approved, idle queue).

ComfyUI's *Setup required* panel shows sizes in GiB (19.03 GiB = 20.43 GB). If it lists installed files as missing, press ↻ or reload the tab; `GET /models/<folder>` is authoritative.

## Workflows

| Export | Template it came from | Profile | Notes |
|---|---|---|---|
| `workflows/01_anchor_t2i.json` | **Qwen-Image: Text to Image** | `configs/profiles/anchor_t2i.binding.json` | `enable_turbo_mode` false (20 steps, CFG 4) |
| `workflows/02_anchor_edit.json` | **Qwen Image Edit 2509** | `configs/profiles/anchor_edit.binding.json` | `FluxKontextImageScale` bypassed so the edit keeps the parent's size; turbo false |
| `workflows/03_wan22_flf2v.json` | Wan 2.2 14B first/last frame | `configs/profiles/wan22_flf2v.binding.json` | FP8 high/low-noise experts, 10/10 step split |

Use those exact template titles (Workflow → Browse Templates → Image); other Qwen variants ("2512", "2.1", "Edit 2511", LoRA/ControlNet templates) need different weights.

## Re-exporting a workflow

1. Render once in the ComfyUI UI and check the output (size, look).
2. **Workflow → Export (API)** over the file in `workflows/`.
3. `python -m morph_studio.cli workflow-inspect workflows\<file>.json` — must be `ok: true`, no cloud nodes, all models installed.
4. Update the profile's node IDs and `workflow_sha256` from the new export, then `python -m morph_studio.cli workflow-check --profile configs\profiles\<profile>.json`.

## Approval log

| Date | What | Approved by | Scope |
|---|---|---|---|
| 2026-11-24 | Qwen-Image + Qwen-Image-Edit-2509 fp8 (4 files, 50.5 GB) | owner, in chat | download only, SHA-256 verified |
| 2026-11-24 | Qwen Lightning LoRAs (2 files, 2.55 GB) | owner, in chat | download only, SHA-256 verified |
| 2026-11-24 | Local GPU renders to complete project tasks | owner, in chat | standing; idle queue, one job at a time |
