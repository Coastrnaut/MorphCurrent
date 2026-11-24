# MorphCurrent

**Local-first, open-weights AI video metamorphosis and music-synchronized prompt travel.**

MorphCurrent is a Python orchestration project for making continuous Deforum-like journeys with modern image and video models. The core idea is to generate **structurally compatible anchor images**, bridge each pair using **Wan 2.2 14B first/last-frame video conditioning** inside local ComfyUI, quality-check the results, then join them with FFmpeg. Claude Desktop Code develops and operates the repository; the actual rendering is local.

> **Status: one Wan 2.2 image-pair bridge is already automated and GPU-verified, but full automatic image-to-video creation is NOT implemented.** The owner completed a successful **manual** Wan 2.2 FLF2V Orchid → Butterfly render (49 frames, 640×368, 16 FPS), documented in [the reviewed baseline](docs/RENDER_BASELINE_001.md); the actual Wan API workflow was subsequently exported and a MorphCurrent-dispatched 65-frame bridge was verified as MC-FLF2V-003. **Automatic ComfyUI text-to-image/reference-edit anchors and full movie assembly are still pending**; see [PROGRESS.md](PROGRESS.md).
>
> **Starter limitations:** The Python client, storyboard validator, timing compiler and tests form an initial foundation. The Wan FLF2V API graph and binding are present and a single programmatic bridge has rendered on the owner's GPU. **Real T2I and reference-edit anchor workflow exports are still missing**; do not assume the Wan model can generate new still-image endpoints. No model weights or videos are bundled. The owner's manual A6000 render is documented separately; automated MorphCurrent GPU execution remains unverified.

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

## Wan 2.2 14B I2V/FLF2V model file checklist (Windows Portable)

The Wan 2.1 VAE path was previously user-reported; these text-encoder and diffusion model paths are **required/recommended locations**, not verified installs:

| File | Subdirectory under `C:\AI\ComfyUI_windows_portable\ComfyUI\models` |
| --- | --- |
| `wan_2.1_vae.safetensors` | `vae` |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | `text_encoders` |
| `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` | `diffusion_models` (I2V high-noise) |
| `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` | `diffusion_models` (I2V low-noise) |

Select the two **I2V** diffusion models in the corresponding high-/low-noise loader nodes, **not** similarly named T2V models. Select UMT5 in **Load CLIP** and Wan 2.1 VAE in **Load VAE**. See [ComfyUI Portable model file checks](docs/COMFYUI_PORTABLE_WINDOWS.md) for exact Windows paths and `dir` commands. Do not commit the model files.


## Example first/last-frame images for Wan 2.2

Two generated 16:9 test anchors are tracked at [assets/anchors/](assets/anchors/): **Glass Orchid** (first frame) and **Metallic Butterfly** (last frame). Unlike the ignored output media, only these two reviewed JPEG samples are committed. On native Windows, copy them safely into ComfyUI Portable's input folder:

```cmd
cd /d C:\GIT\MorphCurrent
python scripts\windows\stage_example_anchors.py --install-root C:\AI\ComfyUI_windows_portable --dry-run
python scripts\windows\stage_example_anchors.py --install-root C:\AI\ComfyUI_windows_portable
```

Refresh the ComfyUI model/image list, select `01_glass_orchid.jpg` in the first **Load Image** node and `02_metallic_butterfly.jpg` in the last **Load Image** node. Paste the motion prompt and follow the initial 49-frame smoke test in [docs/ANCHOR_EXAMPLES.md](docs/ANCHOR_EXAMPLES.md). These are generated *images*, not evidence that Wan rendered a working video.

## Full automatic image-to-morph engineering program

The ten Spec Kit features F01–F10 are implemented and pass offline tests (with a fake ComfyUI); **real anchor image generation is BLOCKED** until the owner approves and installs a local image model set and exports two real API workflows (see [`docs/ANCHOR_MODEL_DECISION.md`](docs/ANCHOR_MODEL_DECISION.md)). The Wan bridge stage itself is GPU-verified (MC-FLF2V-003).

~~~cmd
cd /d C:\GIT\MorphCurrent
.venv\Scripts\python.exe -m morph_studio.cli baseline
.venv\Scripts\python.exe -m morph_studio.cli render configs\sequences\organic-machines.yaml --dry-run
.venv\Scripts\python.exe -m morph_studio.cli render configs\sequences\organic-machines.yaml
.venv\Scripts\python.exe -m morph_studio.cli render configs\sequences\organic-machines.yaml --confirm-gpu
.venv\Scripts\python.exe -m morph_studio.cli render --status outputsunsun-<plan16>
.venv\Scripts\python.exe -m morph_studio.cli review outputsunsun-<plan16> bridge:orchid->butterfly approved
~~~

`--dry-run` makes no network request and writes nothing (exit 6 = BLOCKED, listing missing profiles). Without `--confirm-gpu` the render only validates against live `/object_info`. With it, anchors and bridges run one GPU job at a time, then QA heuristics and an anchor contact sheet are produced and the run waits for your `review` approvals (exit 7) before the seam-verified join writes `final/movie.mp4`. Re-running the same command resumes without repeating inference. Other tools: `workflow-inspect`, `anchor`, `dag`, `qa`, `models-hash --confirm-io`.

- [Spec Kit ten-feature ledger](docs/SPECKIT_FEATURE_LEDGER.md) — authoritative statuses, requirements and acceptance gates.
- [End-to-end system architecture](docs/FULL_PIPELINE_DESIGN.md) — image→video dependencies, manifests, timing and GPU consent.
- [Anchor model/workflow onboarding](docs/ANCHOR_MODEL_ONBOARDING.md) — real T2I/edit models and verified API exports; no invented nodes.
- [Claude Desktop Code paste-only one-shot](docs/CLAUDE_DESKTOP_ONESHOT.md) — open and paste the **entire file contents**, with no start/end trimming.
- `AutoCreator.md` and `CLAUDE.md` — feature orchestration strategy and persistent agent constraints.

**Safety:** If ComfyUI is already running a GPU smoke test, do not restart it or submit more GPU jobs. Run offline planning/specification/tests only until the GPU is idle and additional bounded inference is explicitly approved.

## Repo navigation

- `docs/ARCHITECTURE.md`: contracts, render DAG, caching, memory, beat timing, stitching and failure recovery.
- `docs/WINDOWS_DEVELOPMENT.md`: Windows native only; separate environments and Python-based tooling.
- `docs/COMFYUI_PORTABLE_WINDOWS.md`: official RTX Portable download, C:\AI extraction, Wan 2.1 VAE placement, Python launcher and CUDA health checks.
- `scripts/windows/`: Python helpers for setup, ComfyUI launch, staging sample anchors, diagnostics and Spec Kit.
- `assets/anchors/`: two generated, reviewed JPEG images for the first FLF2V smoke test.
- `docs/ANCHOR_EXAMPLES.md`: positive motion prompt and first/last-frame ComfyUI test instructions.
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
