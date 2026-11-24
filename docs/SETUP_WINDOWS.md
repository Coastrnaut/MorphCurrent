# Windows 11 native-only setup (Python automation)

This short checklist is intentionally secondary to [WINDOWS_DEVELOPMENT.md](WINDOWS_DEVELOPMENT.md).

There is **no** WSL, Linux installation, GPU passthrough, Docker Linux backend or PowerShell scripting in MorphCurrent's supported development workflow.

1. Verify `python --version` (>= 3.11); the `py` launcher is optional. Install Git for Windows, Python 3.11+, Windows FFmpeg/FFprobe, current RTX A6000 Windows driver and native Windows ComfyUI (Portable NVIDIA or dedicated Python environment).
2. Clone repository to `C:\GIT\\MorphCurrent` and open folder in **Claude Desktop > Code**.
3. In Windows Terminal or Command Prompt, run `python scripts/windows/initialize.py`.
4. Run `python scripts/windows/speckit.py --status`, install/upgrade official Spec Kit CLI if absent or outdated, then `python scripts/windows/speckit.py --init` to create or repair the existing Claude integration using `--script py`. Verify with `python scripts/windows/speckit.py --verify`; the helper moves the unused PowerShell fallback to ignored backup.
5. Use [COMFYUI_PORTABLE_WINDOWS.md](COMFYUI_PORTABLE_WINDOWS.md) for the [official RTX Portable archive](https://github.com/Comfy-Org/ComfyUI/releases/latest/download/ComfyUI_windows_portable_nvidia.7z), extracting under `C:\AI\ComfyUI_windows_portable` with `ComfyUI\main.py` and `python_embeded\python.exe` directly inside. Run `python scripts/windows/launch_comfyui.py --install-root C:\AI\ComfyUI_windows_portable` only if ComfyUI isn't already running; then `python scripts/windows/check.py --check-comfy`.
6. For Wan 2.2 I2V/FLF2V, the user reports placing `wan_2.1_vae.safetensors` at `C:\AI\ComfyUI_windows_portable\ComfyUI\models\vae\wan_2.1_vae.safetensors`. Select it in ComfyUI's **Load VAE** node. Verify PyTorch CUDA availability from **ComfyUI's own Python**. Export real API-format workflows and validate node IDs.
7. For **Wan 2.2 I2V/FLF2V 14B**, put the FP8 UMT5 encoder at `C:\AI\ComfyUI_windows_portable\ComfyUI\models\text_encoders\umt5_xxl_fp8_e4m3fn_scaled.safetensors`, the high-noise I2V diffusion expert at `C:\AI\ComfyUI_windows_portable\ComfyUI\models\diffusion_models\wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors`, and the low-noise I2V diffusion expert at `C:\AI\ComfyUI_windows_portable\ComfyUI\models\diffusion_models\wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors`. Select **Load CLIP** (`wan` if applicable) and the matching high-/low-noise **Load Diffusion Model** nodes. Both filenames must start with `wan2.2_i2v_`, **not** `wan2.2_t2v_`. These are expected paths, not independently verified installations.
8. Paste `docs/CLAUDE_DESKTOP_ONESHOT.md` into Claude Desktop Code.

These scripts never install model weights/drivers automatically or force `--highvram`. Run only one initial GPU job at a time and record actual benchmarks.

## Adding ComfyUI anchor image generation (planned; no model installed by this guide)

Wan FP8 I2V 14B video weights, Wan VAE and UMT5 do **not** imply a compatible text-to-image or image-edit model is installed. The remaining automatic first/last-frame workflow requires two additional **real** ComfyUI API exports: `workflows/01_anchor_t2i.json` and `workflows/02_anchor_edit.json`. Review [ANCHOR_MODEL_ONBOARDING.md](ANCHOR_MODEL_ONBOARDING.md) for selection, model licensing, manual installation approval, safe export, node/profile validation and explicit fallback behavior.

The complete engineering backlog is the [ten-feature Spec Kit ledger](SPECKIT_FEATURE_LEDGER.md). During an ongoing GPU smoke run, only read-only model/queue checks and offline Python/spec work are safe; do **not** launch new inference, restart ComfyUI or install image models.
