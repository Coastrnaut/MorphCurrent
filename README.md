# MorphCurrent

**Local-first, open-weights AI video metamorphosis and music-synchronized prompt travel.**

MorphCurrent is a Python orchestration project for making continuous Deforum-like journeys with modern image and video models. The core idea is to generate **structurally compatible anchor images**, bridge each pair using **Wan 2.2 14B first/last-frame video conditioning** inside local ComfyUI, quality-check the results, then join them with FFmpeg. Claude Desktop Code develops and operates the repository; the actual rendering is local.

> **Status: engineering starter, not a finished video renderer.** The Python client, storyboard validator, timing compiler and tests form an initial foundation. Actual anchor/image-model workflow exports and a verified Wan FLF2V API-format graph must be supplied from your own installed ComfyUI before GPU rendering. No models or videos are bundled, and no A6000 test is claimed.

## Target hardware and stack

- NVIDIA RTX A6000, 48 GiB VRAM; Windows 11, native Python or WSL2, local ComfyUI at `http://127.0.0.1:8188`.
- Python >=3.11, Pydantic v2, PyYAML, httpx, websockets, FFmpeg / FFprobe, pytest.
- Anchor models: user-installed FLUX family or Qwen Image/Edit; video: user-installed Wan 2.2 A14B I2V high/low-noise experts with `WanFirstLastFrameToVideo` conditioning.
- Claude Desktop **Code** manages specs, implementation, benchmark experiments and commits. The app's reasoning is not offline; model inference/video assets can remain local.

**Important memory caveat:** two 14B experts in FP16 alone require roughly 52 GiB of raw weight space, before the VAE, text encoder and activations. Do not assume `--highvram` can pin both in a 48 GiB card. Benchmark FP8 scaled, staged loading, and selective offload; measure peak reserved/allocated VRAM. Never silently change precision.

## Quick start

1. Clone this repository and open its folder in **Claude Desktop > Code**.
2. Read `CLAUDE.md`, `AutoCreator.md` and `docs/CLAUDE_DESKTOP_ONESHOT.md`; paste the latter's one-shot prompt in Claude Desktop Code.
3. Install Python 3.11+, FFmpeg and a local ComfyUI. Install the required ComfyUI models/nodes manually from their original sources; verify licenses and checksum.
4. Create a virtual environment and install:

   ~~~bash
   python -m venv .venv
   python -m pip install -e ".[dev]"
   python -m pytest
   python -m morph_studio.cli validate configs/sequences/organic-machines.yaml
   python -m morph_studio.cli plan configs/sequences/organic-machines.yaml
   python -m morph_studio.cli health --url http://127.0.0.1:8188
   ~~~

5. In ComfyUI, open a *working local* anchor workflow and the official Wan 2.2 FLF2V workflow; **Save (API Format)** to `workflows/01_anchor_t2i.json`, `workflows/02_anchor_edit.json`, and `workflows/03_wan22_flf2v.json`. These files are deliberately **not fabricated** in this starter. Add a mapping JSON per workflow in `configs/profiles/` from semantic roles to real node IDs and input fields. Inspect `/object_info` to check node availability.
6. Implement the next milestone in `AutoCreator.md` through Claude Code. Do not claim a successful end-to-end run until the generated media have been viewed and verified on your A6000.

## Repo navigation

- `docs/ARCHITECTURE.md`: contracts, render DAG, caching, memory, beat timing, stitching and failure recovery.
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
2. First anchor and last anchor are explicit; no hidden prompt drift.
3. Reference edit next anchor when available; measure composition/shape compatibility.
4. Three bridge strategies: direct morph, camera passage, intermediate anchors.
5. Use 4n+1 conditioned frame counts; beat sync uses **(frame_count - 1) / fps** between the two anchor timestamps.
6. Deduplicate *true* repeated boundary frames, never remove endpoints blindly; quality-check optical motion at joins.
7. Hash model/checkpoint identity, workflow, inputs, settings and dependencies to deduplicate work.
8. Never commit weights, input music under restrictive rights, generated video, tokens, private endpoints, or large intermediates.
9. Do not claim quantitative VRAM/speed/quality results without measurement.
10. Preserve a fully local render option; do not send images or audio to a remote service by default.

## External authoritative references

- ComfyUI API example: https://github.com/Comfy-Org/ComfyUI/blob/master/script_examples/websockets_api_example.py
- ComfyUI server routes: https://docs.comfy.org/development/comfyui-server/comms_routes
- Official Wan 2.2 ComfyUI tutorial: https://docs.comfy.org/tutorials/video/wan/wan2_2
- Claude Code settings: https://code.claude.com/docs/en/settings
- GitHub Spec Kit: https://github.com/github/spec-kit

**License:** see `LICENSE`; repository code licensing does not convey rights to model weights, custom nodes, or music.
