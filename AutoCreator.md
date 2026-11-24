# AutoCreator — MorphCurrent autonomous image→morph engineering program

**Canonical spec-driven backlog:** [`docs/SPECKIT_FEATURE_LEDGER.md`](docs/SPECKIT_FEATURE_LEDGER.md).  
**End-to-end architecture and acceptance:** [`docs/FULL_PIPELINE_DESIGN.md`](docs/FULL_PIPELINE_DESIGN.md).  
**Claude Desktop Code instruction (paste-only):** [`docs/CLAUDE_DESKTOP_ONESHOT.md`](docs/CLAUDE_DESKTOP_ONESHOT.md).  
**Measured project status:** [`PROGRESS.md`](PROGRESS.md).

## Product mission

Build a **fully local Deforum-style visual metamorphosis engine** that does not require manually supplied first or last images. The end-user supplies a YAML storyboard describing ordered concepts. MorphCurrent generates first image A from a ComfyUI text-to-image model, generates B from A using a real ComfyUI reference-edit model (and C from B, etc.), generates Wan 2.2 first/last-frame video clips for A→B and B→C, detects quality/seam issues and exports a joined movie with optional beat-synchronized licensed audio. Local Windows 11, RTX A6000 48 GiB, standalone ComfyUI and a Python-only controller; no server deployment or remote media APIs.

**A winning result looks like a physically continuous morph**, not a slideshow or xfade. Each generated anchor should retain a compatible perspective, size, light direction, palette and camera, and the shared anchor must be byte-identical across adjacent clips. Video-only output works with no music.

## Snapshot: source-derived current capability (2026-11-24)

At GitHub main `2deb3863a89f37cc99be77867edda10df88b9878`:

- A real, locally validated API-format Wan 2.2 I2V/FLF2V graph and pinned semantic binding profile are committed.
- The `bridge` CLI can submit **one manually supplied image pair**, safely resume, download and verify. The first MorphCurrent-dispatched 65-frame video MC-FLF2V-003 is recorded as verified, with decoded-frame equality against manual video MC-FLF2V-002. Peak VRAM **not measured**; visual human approval not recorded.
- Windows-native Python helper scripts and Spec Kit Python scripts/Claude skills are installed, with code and tests. `PROGRESS.md` is the real measured ledger.
- **Missing work:** real anchor T2I and edit API workflow exports/models, generated-anchor scheduling, full YAML image+bridge DAG, multi-stage recovery, QA/selection, seam joining, optional audio and single command. Preserve the existing bridge and prior evidence.

This file is a future work specification, not evidence that new functionality has already been deployed. Read latest HEAD each session; do not rely solely on this snapshot.

## Execution strategy: ten sequenced Spec Kit features

The **exact ten** logical features, dependencies, detailed implementation contract, failure cases, gating evidence and status table are in [`docs/SPECKIT_FEATURE_LEDGER.md`](docs/SPECKIT_FEATURE_LEDGER.md). Claude must implement them using the actual **installed** Spec Kit skills and Python script backend, one real spec and tested feature at a time:

| Stage | Feature | User-facing capability |
|---|---|---|
| **Foundation** | F01: safe baseline and provenance | Protect owner GPU work, discover installed ComfyUI and existing code truth |
| **Image inference** | F02: image model and workflow onboarding | Verify real local T2I and image edit API exports/profile bindings |
| | F03: generate first anchor | Automatic T2I endpoint A without supplying a manual image |
| | F04: generate related next anchors | Reference-edit A→B→C with consistent geometry/style, explicit fallback |
| **Composition** | F05: full storyboard DAG | YAML → generated A,B,C dependencies → planned bridges; deterministic IDs |
| | F06: generated anchors into Wan | Feed real generated A/B images to existing working FP8 Wan FLF2V bridge |
| **Trust and quality** | F07: durable state and measurements | Atomic root manifest, crash-safe resume, model hashes and optional nvidia-smi trace |
| | F08: visual quality / candidate selection | Detect artifacts, compare seeds/prompts and selectively rerender segments |
| **Movie** | F09: seam, FFmpeg, optional music | Accurate shared B seam, 129 frames for two 65-frame bridges, optional beat sync |
| **Delivery** | F10: one-command integrated acceptance | Native Windows YAML-to-images-to-video CLI with dry-run, approve/resume and report |

### Feature acceptance gates

1. **SPEC:** real `specs/NNN-slug/spec.md` tied to Fxx + requirements, negative tests, and dependencies.
2. **DESIGN:** plan/research/data model/contracts/quickstart as needed; validate against constitution and actual ComfyUI API node choices; no made-up workflows.
3. **IMPLEMENT:** code, tests, safe defaults, README/CLI documentation, backward-compatible `bridge` behavior.
4. **OFFLINE-PASS:** real Windows/CI pytest outcomes and mocked REST failures, checked graph hashes and immutable output rules.
5. **GPU-VERIFIED:** only after explicit owner-approved bounded local inference, actual image/MP4 verified by checksum/ffprobe and machine/precision recorded. If model or queue prevents the run, mark BLOCKED, not COMPLETE.
6. **CREATIVE QA:** observe contact sheet and endpoint continuity; automated similarity metrics are not artistic proof.
7. **DONE/COMMIT:** update `PROGRESS.md` plus feature ledger mapping Fxx ↔ actual Spec Kit path ↔ commit SHA ↔ evidence and next action; no undocumented regressions.

Actual spec numbers can differ from F01–F10 if `specs/` prefixes are occupied; use the installed `create_new_feature.py --help` and preserve its returned folder. Do not pre-create ten empty templates or reinitialize an already valid Python Spec Kit environment.

## Model/workflow strategy

**Video:** preserve the existing `workflows/03_wan22_flf2v.json` and `configs/profiles/wan22_flf2v.binding.json`; known FP8 I2V high/low model pair, Wan 2.1 VAE, UMT5 text encoder. Runtime model existence and hashes should be read from local ComfyUI, not guessed from filenames. Check ComfyUI node names against live `/object_info` before dispatch.

**Still images:** T2I model and image-edit model are **not yet verified as installed**. FLUX or Qwen Image is a candidate model family, not a required magical default. Evaluate license, source, local RTX A6000 memory and ComfyUI nodes, gain owner consent for any large download, then export validated `workflows/01_anchor_t2i.json` and `02_anchor_edit.json`. If an edit workflow cannot be installed, a clearly labeled, consciously selected independent T2I approach can generate B with shared style; strict reference-edit acceptance remains BLOCKED until the real graph works.

**Memory:** 48 GiB means independent anchor and Wan stages should typically run sequentially; two full-FP16 14B experts exceed capacity together. GPU queue should be read-only while owner tests are running; no reset, auto-download, unapproved GPU job or silent `--highvram`. Measure actual per-process utilization and peak sampling; `/system_stats` snapshot alone is insufficient.

## Main end-to-end demonstration

Baseline recipe: `configs/sequences/organic-machines.yaml`, with orchid A (T2I), butterfly B (edit A), mechanical phoenix C (edit B). Generate, persist and hash all three images. Render A→B and B→C at 65 frames/16 FPS each (or explicitly recorded experimental overrides); hand the same exact B bytes to both bridges. Inspect real shared endpoints, dedupe only proven repeats, join to 129 unique frames and check rational timestamps/video nominal duration. Optional licensed local music may be added but is never needed to produce video. At each stage create a reviewable job manifest, contact sheet and safe retry route.

Keep the MC-FLF2V-001 through 003 clip evidence and refined continuity prompt in `docs/RENDER_BASELINE_001.md`; it is an experimental **candidate** not evidence of success for new auto-image generation. Verified initial video bridge is **not** a full pipeline acceptance.

## Windows/Python + Spec Kit invariants

- Native Windows 11 only; `python --version` (3.11+) and `.venv\Scripts\python.exe` in controller; separate ComfyUI Portable `python_embeded\python.exe` for CUDA.
- Only Python scripts, not PowerShell `.ps1`, WSL, Linux VMs/containers, Bash or mandatory `py.exe`.
- Verify installed Spec Kit: `python scripts/windows/speckit.py --status` and `--verify`; reinit only if broken after reviewing backed-up repair. Current `.specify/integration.json` uses `script=py`, CLI-integration version 1.2.4. Do not replace/erase generated skills or existing Spec Kit project with a new template.
- Each feature: execute *actual installed* Spec Kit specify, clarify when needed, plan, tasks, analyze, implement. Use one active spec at a time; keep specs, plans, tasks in Git, then update PROGRESS + ledger and make a reviewed commit.
- Offline verification: `python -m pytest -m "not integration and not gpu"`. Live read-only `/object_info` integration only if safe. Expensive GPU tests require explicit owner approval, short bounded run and idle queue. Never assert local A6000 usage from Windows CI.
- Reuse `comfy_client.py`, `workflow_adapter.py`, `bridge.py`, `schema.py`, `timeline.py`, `media.py` and `stitcher.py` rather than clone them. Preserve programmatic image upload security, resume and targeted cancellation.

## Agent instructions, owners and stop conditions

For a Claude Desktop Code session, **copy the entire contents** of [`docs/CLAUDE_DESKTOP_ONESHOT.md`](docs/CLAUDE_DESKTOP_ONESHOT.md) into the message box. That document is deliberately only the pasteable one-shot, without headers/footers or text to trim.

The agent may autonomously plan, spec, implement, test and commit safe offline increments. **Stop and request owner action** for a missing local image model/graph, install/license permission, new GPU-intensive test, potentially destructive changes, audio copyright, or unclear user creative acceptance. If an active GPU smoke test is underway, inspect queue read-only and continue offline without altering runtime. On any context/time/tool limit, make a truthful progress entry with actual HEAD, failing test, incomplete Fxx, blockers and exact restart commands; do not promise background work.
