# MorphCurrent

**Local-first, open-weights AI video metamorphosis and music-synchronized prompt travel.**

MorphCurrent is a Python orchestration project for making continuous Deforum-like journeys with modern image and video models. The core idea is to generate **structurally compatible anchor images**, bridge each pair using **Wan 2.2 14B first/last-frame video conditioning** inside local ComfyUI, quality-check the results, then join them with FFmpeg. Claude Desktop Code develops and operates the repository; the actual rendering is local.

> **Status: engineering starter, not a finished video renderer.** The Python client, storyboard validator, timing compiler and tests form an initial foundation. Actual anchor/image-model workflow exports and a verified Wan FLF2V API-format graph must be supplied from your own installed ComfyUI before GPU rendering. No models or videos are bundled, and no A6000 test is claimed.

## Target hardware and stack

- NVIDIA RTX A6000, 48 GiB VRAM; native Windows 11 only (no WSL, GPU passthrough or Linux VM), local ComfyUI at `http://127.0.0.1:8188`.
- Python >=3.11 for the MorphCurrent controller (separate from ComfyUI Portable's bundled Python), Pydantic v2, PyYAML, httpx, websockets, FFmpeg / FFprobe, pytest.
- Anchor models: user-installed FLUX family or Qwen Image/Edit; video: user-installed Wan 2.2 A14B I2V high/low-noise experts with `WanFirstLastFrameToVideo` conditioning.
- Claude Desktop **Code** manages specs, implementation, benchmark experiments and commits. The app's reasoning is not offline; model inference/video assets can remain local.

**Important memory caveat:** two 14B experts in FP16 alone require roughly 52 GiB of raw weight space, before the VAE, text encoder and activations. Do not assume `--highvram` can pin both in a 48 GiB card. Benchmark FP8 scaled, staged loading, and selective offload; measure peak reserved/allocated VRAM. Never silently change precision.

## Quick start — native Windows Python only

1. Clone `https://github.com/Coastrnaut/MorphCurrent.git` to e.g. `C:\GIT\\MorphCurrent`, then open the folder in **Claude Desktop > Code**.
2. Verify `python --version` (3.11+). If `python` is missing, install an official native Windows Python distribution and restart Command Prompt. The `py.exe` launcher is **not required**. Install Git for Windows, FFmpeg/FFprobe for Windows, NVIDIA Windows driver and one working **native Windows ComfyUI** installation (Portable NVIDIA or manually installed CUDA PyTorch). No WSL, Docker Linux runtime, or GPU passthrough.
3. From **Windows Terminal / Command Prompt**, run Python scripts (no PowerShell scripts):

   ```text
   cd C:\GIT\\MorphCurrent
   python scripts/windows/initialize.py
   python scripts/windows/speckit.py --status
   .venv\Scripts\\python.exe -m morph_studio.cli validate configs/sequences/organic-machines.yaml
   .venv\Scripts\\python.exe -m morph_studio.cli plan configs/sequences/organic-machines.yaml
   .venv\Scripts\\python.exe -m morph_studio.cli doctor --skip-comfy
   ```

4. After verifying and installing the **current** official Spec Kit CLI, use `python scripts/windows/speckit.py --init` to install/repair the Claude integration with **`--script py`**. The helper verifies real `.specify/scripts/python/*.py` files and Claude command references, then moves Spec Kit's otherwise-generated PowerShell fallback into an ignored local backup. Re-run `--verify` afterward.
5. If you haven't installed ComfyUI yet, download the **official standard NVIDIA RTX Portable archive**: https://github.com/Comfy-Org/ComfyUI/releases/latest/download/ComfyUI_windows_portable_nvidia.7z (currently documented with Python 3.13 / PyTorch CUDA 13.0). Extract it to `C:\AI\ComfyUI_windows_portable` so `ComfyUI\main.py` and `python_embeded\python.exe` are direct children. See [ComfyUI download and launch instructions](docs/COMFYUI_PORTABLE_WINDOWS.md) for extraction and CUDA verification. If ComfyUI is **already running**, skip launching another instance. Otherwise launch via Python:

   ```text
   python scripts/windows/launch_comfyui.py --install-root C:\AI\ComfyUI_windows_portable
   .venv\Scripts\\python.exe -m morph_studio.cli doctor
   python scripts/windows/check.py --check-comfy
   ```

6. Export **real** local working ComfyUI workflows using *Save (API Format)* into `workflows/`. Map actual node IDs and verify with `/object_info`. The starter deliberately ships no invented executable FLF2V workflow.
7. Paste `docs/CLAUDE_DESKTOP_ONESHOT.md` into Claude Desktop Code and develop against the roadmap. The existing Python foundation does **not** yet render real video.

If Spec Kit was initialized earlier with PowerShell, the same `--init` command repairs it safely, with an explicit backup under `.local/spec-kit-backups/`. See `--status` and `--repair` for diagnostic/forced regeneration options.

**Windows-only guide:** [docs/WINDOWS_DEVELOPMENT.md](docs/WINDOWS_DEVELOPMENT.md). **Python-based setup scripts:** [scripts/windows/](scripts/windows/). Controller Python and ComfyUI's Python must remain isolated. `--highvram` is optional, not a substitute for VRAM capacity.

## Repo navigation

- `docs/ARCHITECTURE.md`: contracts, render DAG, caching, memory, beat timing, stitching and failure recovery.
- `docs/WINDOWS_DEVELOPMENT.md`: Windows native only; separate environments and Python-based tooling.
- `docs/COMFYUI_PORTABLE_WINDOWS.md`: official RTX Portable download, C:\AI extraction, Wan 2.1 VAE placement, Python launcher and CUDA health checks.
- `scripts/windows/`: Python helpers for setup, ComfyUI launch, diagnostics and Spec Kit.
- `AutoCreator.md`: staged engineering roadmap and acceptance gates.
- `docs/CLAUDE_DESKTOP_ONESHOT.md`: full copy/paste one-shot for Claude Desktop Code.
- `CLAUDE.md`: permanent repository rules for the coding agent.
- `PROGRESS.md`: factual milestone/experiment log; update after each session.
- `src/morph_studio`: Python foundation (validation, planning, ComfyUI API client).
- `configs/sequences`: creative, reproducible storyboard definitions.
- `configs/profiles`: workflow bindings and model/precision policy.
- `.claude/skills`: local skills for common engineering work.
- `tests`: offline tests, plus later gated integration/hardware tests.

## Design principles

1. A *continuous morphological transformation*, not a slideshow or generic dissolve.
2. Windows 11 native is the sole supported runtime. First anchor and last anchor are explicit; no hidden prompt drift.
3. Reference edit next anchor when available; measure composition/shape compatibility.
4. Three bridge strategies: direct morph, camera passage, intermediate anchors.
5. Use 4n+1 conditioned frame counts; beat sync uses **(frame_count - 1) / fps** between the two anchor timestamps.
6. Deduplicate *true* repeated boundary frames, never remove endpoints blindly; quality-check optical motion at joins.
7. Hash model/checkpoint identity, workflow, inputs, settings and dependencies to deduplicate work.
8. Never commit weights, input music under restrictive rights, generated video, tokens, private endpoints, or large intermediates.
9. Windows-only CI validates offline tests; it does not certify ComfyUI/GPU rendering. Do not claim VRAM/speed/quality results without measurement.
10. Preserve a fully local render option; do not send images or audio to a remote service by default.

## External authoritative references

- ComfyUI API example: https://github.com/Comfy-Org/ComfyUI/blob/master/script_examples/websockets_api_example.py
- ComfyUI server routes: https://docs.comfy.org/development/comfyui-server/comms_routes
- Official ComfyUI Portable Windows install: https://docs.comfy.org/installation/comfyui_portable_windows
- Official RTX NVIDIA Portable archive: https://github.com/Comfy-Org/ComfyUI/releases/latest/download/ComfyUI_windows_portable_nvidia.7z
- Official Wan 2.2 ComfyUI tutorial: https://docs.comfy.org/tutorials/video/wan/wan2_2
- Claude Code settings: https://code.claude.com/docs/en/settings
- GitHub Spec Kit: https://github.com/github/spec-kit

**License:** see `LICENSE`; repository code licensing does not convey rights to model weights, custom nodes, or music.
