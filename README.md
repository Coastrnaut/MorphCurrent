# MorphCurrent

Turn a short YAML storyboard into a continuous morphing video, generated entirely on your own machine with [ComfyUI](https://github.com/Comfy-Org/ComfyUI).

MorphCurrent generates a still image for each storyboard concept, editing each one from the previous image so composition and lighting carry over. It then renders a [Wan 2.2](https://docs.comfy.org/tutorials/video/wan/wan2_2) first/last-frame video between every pair and joins the clips at their shared frames into one movie. There are no crossfades: every transition is a generated physical transformation.

```text
orchid (text-to-image) ──edit──▶ butterfly ──edit──▶ phoenix
        └──── Wan 2.2 bridge ────┘    └──── Wan 2.2 bridge ────┘
                         ▼ seam-verified join ▼
                              final movie.mp4
```

## Features

- **Local only.** Talks to ComfyUI on `127.0.0.1`; cloud API nodes are rejected.
- **Real reference editing.** Each anchor is generated from the exact bytes of its parent; adjacent clips share the identical frame.
- **Safe GPU use.** Dry runs touch nothing; GPU jobs need `--confirm-gpu`, run one at a time and never stack on a busy queue.
- **Resumable.** Every stage is content-addressed; re-running a command after a crash or restart never repeats finished inference.
- **Verified output.** Workflows are hash-pinned and checked against ComfyUI's `/object_info`; images, clips and seams are checked before anything is joined.
- **Human in the loop.** Heuristic QA flags cuts, freezes and flashes; you approve each bridge before the final join.

## Requirements

- Windows 11, NVIDIA GPU (developed on an RTX A6000, 48 GB)
- Python 3.11+ and FFmpeg/ffprobe on `PATH`
- [ComfyUI Portable](https://github.com/Comfy-Org/ComfyUI/releases/latest/download/ComfyUI_windows_portable_nvidia.7z) with the Wan 2.2 and Qwen-Image models listed in [docs/MODELS.md](docs/MODELS.md)

## Quick start

```cmd
git clone https://github.com/Coastrnaut/MorphCurrent.git
cd MorphCurrent
python scripts\windows\initialize.py
```

Start ComfyUI ([docs/COMFYUI_SETUP.md](docs/COMFYUI_SETUP.md)), then:

```cmd
:: check the environment (read-only)
.venv\Scripts\python.exe -m morph_studio.cli baseline

:: show the plan; no network, no writes
.venv\Scripts\python.exe -m morph_studio.cli render configs\sequences\organic-machines.yaml --dry-run

:: render anchors and bridges on the GPU, then stop for review
.venv\Scripts\python.exe -m morph_studio.cli render configs\sequences\organic-machines.yaml --confirm-gpu

:: approve each bridge, then run the same render command again to join the movie
.venv\Scripts\python.exe -m morph_studio.cli review outputs\runs\run-<id> bridge:orchid->butterfly approved
```

Results land in `outputs\runs\run-<id>\` (manifest, contact sheet, `final\movie.mp4`). `render --status <run dir>` shows progress at any time.

## Storyboard

```yaml
anchors:
  - id: orchid
    prompt: A luminous glass orchid with translucent blue petals...
    generation: text_to_image
  - id: butterfly
    prompt: A metallic butterfly with translucent wing panels...
    generation: reference_edit
    reference: orchid
transitions:
  - from: orchid
    to: butterfly
    duration_beats: 8
    prompt: Glass petals lift into articulated wings...
```

See [`configs/sequences/organic-machines.yaml`](configs/sequences/organic-machines.yaml) for a full example (style, render size, seeds, timing, optional audio).

## Other commands

| Command | Purpose |
|---|---|
| `dag` | Print the task plan for a storyboard |
| `anchor` / `bridge` | Generate a single image or a single bridge clip |
| `qa` | Heuristic check of a clip (cuts, freezes, flashes, endpoints) |
| `workflow-inspect` / `workflow-check` | Validate a ComfyUI API export or binding profile |
| `models-hash` | Record SHA-256 of the model files in use (opt-in) |

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — how the pipeline, jobs and seams work
- [docs/MODELS.md](docs/MODELS.md) — installed models, workflows and how to re-export them
- [docs/COMFYUI_SETUP.md](docs/COMFYUI_SETUP.md) — installing and starting ComfyUI
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) — dev setup, tests, Spec Kit
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) and [docs/PROGRESS.md](docs/PROGRESS.md) — render results and project log

## Status

All ten planned features are implemented and covered by offline tests. The Wan bridge has been verified on the GPU; the first full storyboard render with generated anchors is in progress. See [docs/PROGRESS.md](docs/PROGRESS.md).

## License

[MIT](LICENSE). Model weights are not included and carry their own licenses.
