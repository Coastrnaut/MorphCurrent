# MorphCurrent

Turn a short YAML storyboard into a continuous morphing video, generated entirely on your own machine with [ComfyUI](https://github.com/Comfy-Org/ComfyUI).

MorphCurrent generates a still image for each storyboard concept, editing each one from the previous image so composition and lighting carry over. It then renders a [Wan 2.2](https://docs.comfy.org/tutorials/video/wan/wan2_2) first/last-frame video between every pair and joins the clips at their shared frames into one movie. There are no crossfades: every transition is a generated physical transformation.

```text
orchid (text-to-image) ──edit──▶ butterfly ──edit──▶ phoenix
        └──── Wan 2.2 bridge ────┘    └──── Wan 2.2 bridge ────┘
                         ▼ seam-verified join ▼
              final/<storyboard>_<timestamp>_<plan>.mp4
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

:: or review in a local page (loopback only; never renders): http://127.0.0.1:8765/
.venv\Scripts\python.exe -m morph_studio.cli review-ui
```

Results land in `outputs\runs\run-<id>\` (manifest, contact sheet and the movie, e.g. `final\organic-machines_20261124-153637Z_ba2d9dbe.mp4`). `render --status <run dir>` shows progress at any time. `camera-check` tests camera moves and framing against the anchors, `continuity` locates shape/colour breaks in a clip, `audio-features` + `sync-plan` time anchors to the music, `interpolate` / `warp-apply` produce delivery frame rates and music-driven retiming, `finish` makes geometric HD masters, `sync-report` / `animatic` / `captions` / `click-track` verify and preview the film's music sync, `titles-check` / `titles-render` / `act-boundaries` add safe-area-checked titles to a copy of the movie and propose act starts on music sections, `film-review-status` / `film-review` / `film-review-approve-act` / `film-rerender-queue` / `film-act-sheet` / `film-compare` (and `review-ui --film` for keyboard act pages) review the film's batches, `film-produce <acts|all>` renders every batch of the film in order (one GPU job at a time, resumable), `film-assemble` / `film-deliver` / `film-provenance` / `film-gates` assemble, deliver and account for the finished film, `history-ingest` / `prod-budget` / `prod-approve` / `prod-batch` / `prod-status` plan and track the film's GPU batches, `lineage` / `lineage-drift` / `lineage-propose` / `lineage-shared` track and control reference-edit drift, `look-check` / `look-drift` / `look-test` enforce and measure the film's visual language, `accuracy-checklist` / `accuracy-review` / `accuracy-impact` / `accuracy-status` manage the owner's per-anchor accuracy sign-off, `film-storyboard` / `film-report` build and dry-run the full-song film storyboard, `concepts-check` / `concepts-list` validate and list the film's 96 anchor subjects, `deliver --preset ...` writes verified 16:9 / 9:16 / square / licensed-audio / 1440p / 24 fps deliverables, `release-check` shows what still blocks a release, `experiment-plan` / `experiment-run` / `experiment-rate` / `experiment-report` compare settings on one bridge within a GPU budget, `project-export` / `project-inspect` / `project-import` package a project for backup or a second machine (media opt-in, nothing unsafe written), `registry` shows every workflow's capabilities and readiness (`registry-diff` / `registry-select --approve` / `registry-rollback` for safe upgrades), `run-compare A B` checks a replay byte-for-byte, `audit` checks sources and licences, and `run-backup` / `run-restore` archive a run with checksums.

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
- [docs/SPECKIT_FEATURE_LEDGER.md](docs/SPECKIT_FEATURE_LEDGER.md) — existing F01–F10 evidence, planned F11–F30 functionality and the F31–F40 full-song engineering film track
- [docs/CLAUDE_DESKTOP_ONESHOT.md](docs/CLAUDE_DESKTOP_ONESHOT.md) — **paste the entire file contents** into Claude Desktop Code for the next implementation wave

## Status

**F01–F10 working and reproduced:** MC-RUN-001 generated three Qwen anchors, two 832×480 Wan morphs and a reviewed **129-frame** movie. MC-RUN-002 selectively regenerated the phoenix and second bridge. MC-RUN-003 computed all five GPU stages in a fresh output root and reproduced their image/video outputs byte-identically. The current CLI names finished MP4s `<storyboard>_<UTC timestamp>_<plan8>.mp4`. Latest audited GitHub CI passed, with **222 offline tests reported by its commit**. **F11–F13 have real offline implementation slices** (performance reporting and Wan model hashes, anchor geometry and physical choreography); **F14–F30 remain planned:** GPU benchmarking, continuity, intermediate anchors, actual licensed music alignment, quality calibration, local UI, long-form workflows, private style packs, creative-brief storyboards, camera/motion repair, interpolation/upscaling, model capability upgrades, portable archives, bounded experiments and multi-format delivery. **F31–F40** are planned film-production features for an electrical/compute engineering story that runs the full length of its song and is synchronized to it (anchors on musical events, acts on sections, playback warped by the music's energy — see docs/MUSIC_SYNC.md; ~6 min, ~80 beat-locked bridges for the licensed Mozart track), with an 8–12-bridge pilot before any full GPU batch. See [the ledger](docs/SPECKIT_FEATURE_LEDGER.md) and [progress log](docs/PROGRESS.md).

## License

[MIT](LICENSE). Model weights are not included and carry their own licenses.
