# PROGRESS — MorphCurrent

> Date: 2026-11-23. This document is a ledger, not a promise. Only mark a stage complete when its acceptance gate is demonstrated.

## Current snapshot
- [x] Repository created by owner; initial engineering scaffold committed via connected GitHub workflow (after initial setup).
- [x] Architecture and Claude Desktop engineering handoff documented.
- [x] Native Windows 11-only Python setup/launch/Spec Kit helpers and doctor CLI authored; Windows-only CI configured (check job status for results).
- [x] Offline storyboard / timing and local ComfyUI client starter included.
- [x] Wan 2.2 FLF2V API export (`workflows/03_wan22_flf2v.json`) validated against live `/object_info` and bound by `configs/profiles/wan22_flf2v.binding.json` (2026-11-23). Anchor T2I/edit exports (`01_`, `02_`) still missing.
- [ ] A6000 environment and model inventory verified.
- [x] First two-anchor FLF2V video bridge **manually** rendered by owner, uploaded, and qualitatively inspected — see `docs/RENDER_BASELINE_001.md`. Automated MorphCurrent rendering and quantitative GPU benchmarking remain unverified.
- [ ] Continuous three-anchor seam and beat sync validated.
- [ ] Benchmark tables and quality regression suite completed.

## Milestone sequence
M0 — Native Windows environment discovery, independent controller/ComfyUI Python, Python-only Spec Kit, pinned dependencies, Windows CI/offline contract tests.
M1 — Model inventory, real ComfyUI API workflows and semantic node adapters.
M2 — Reference-guided anchors with immutable artifact manifests.
M3 — Wan 2.2 FLF2V video bridge scheduling, retries, error tracking, VRAM benchmarking.
M4 — Seam inspection / FFmpeg chain, beat-aligned durations and audio mux.
M5 — Automatic transition planning, intermediate anchors, multi-candidate quality review.
M6 — Higher resolution + frame interpolation + resumable multi-song render jobs.

## Experiment ledger
| ID | Date | Change | Resolution | Steps/CFG/Seed | VRAM/time | Quality observation | Evidence |
|---|---|---|---|---|---|---|---|
| MC-FLF2V-001 | 2026-11-23 local | Owner manual Wan 2.2 Orchid → Butterfly, uploaded MP4 | **640×368**, 49 frames, 16 FPS; 3.0625 s | 20 steps (split 10/10), CFG 4, euler/simple, seed 1091897826965482 — recovered from ComfyUI `/history` prompt `748d6c59…` | VRAM/time **NOT MEASURED** | Faithful anchors; transitory petal clipping and distorted wings at 0.75–1.5 s | `docs/RENDER_BASELINE_001.md`; MP4 SHA-256 `a638f6e1d58d876670ddc72c0bb773f9f6c83d93076ac3a9403c41618823120c` |
| MC-FLF2V-002 (manual) | 2026-11-23 local | Owner manual run of the exact exported graph (refined continuity prompt) | 640×368, 65 frames, 16 FPS; 4.0625 s per `/history` metadata | 20 steps (10/10), CFG 4, euler/simple, seed 844823683741909 — `/history` prompt `160616bb…`, output `video/ComfyUI_00003_.mp4` | **NOT MEASURED** | **NOT REVIEWED** — MP4 not inspected | ComfyUI `/history`; graph differs from `03_wan22_flf2v.json` only in node 84 `noise_seed` |

## First run checklist
- Require native Windows 11, no WSL. Log NVIDIA driver, GPU VRAM, CUDA and PyTorch versions from ComfyUI's **own Python environment**.
- Log `ComfyUI --version` or Git commit, API availability, node types, models and checkpoint hashes.
- Export verified API-format anchor and Wan FLF2V workflows (do not substitute UI-format JSON).
- Record exact model license, precision, loading policy, and `--highvram` configuration.
- Run `python scripts/windows/check.py`, storyboard validation and planning CLI; use `doctor --skip-comfy` before attempting GPU health.
- Benchmark 832x480 65-frame 16fps clips before attempting 720p.
- Log all blockers rather than fabricating success.

## Windows Python launcher / Spec Kit repair hardening (2026-11-23)
- [x] Replace all repository setup commands using the optional `py.exe` launcher with `python` and make VS Code task execution use `python`.
- [x] Upgrade Python Spec Kit initialization to handle existing PowerShell-mode installs; preserve backed-up files, verify actual `.py` core scripts and Claude command references, and move generated PowerShell fallback out of the active tree.
- [ ] On the owner's Windows host, run `python --version`, `python scripts/windows/speckit.py --init`, then `python scripts/windows/speckit.py --verify` and record actual CLI version and results.
- [ ] Real local CUDA/ComfyUI inference remains untested; do not confuse Windows CI unit tests with A6000 evidence.

## Example FLF2V anchor pair generated (2026-11-23)

- [x] Two matched 16:9 Glass Orchid → Metallic Butterfly endpoint images created from original AI-generated artwork, manually composed/cropped for consistent framing and stored as small JPEG fixtures in `assets/anchors/`.
- [x] Documented the positive transformation prompt, manual ComfyUI first/last-frame loading and Python-only optional staging helper (`docs/ANCHOR_EXAMPLES.md`).
- [x] Owner reports successful local Wan 2.2 FLF2V smoke render; uploaded `ComfyUI_00002_.mp4` was inspected. See `docs/RENDER_BASELINE_001.md` for measured video metadata and limitations.
- [ ] Save and validate the real ComfyUI API-format workflow. The owner performed a **manual** GPU video render; no programmatic MorphCurrent render or measured VRAM/time is claimed.

## First video baseline and next trial (2026-11-23)

- [x] Reviewed owner-uploaded 49-frame H.264 baseline at 640×368 / 16 FPS, with hash, endpoint fidelity and mid-transition issues documented in `docs/RENDER_BASELINE_001.md`.
- [ ] MC-FLF2V-002: evaluate the new continuity-oriented positive prompt and a 65-frame trial; **not yet rendered**.
- [x] Export user-run ComfyUI FLF2V graph as `workflows/03_wan22_flf2v.json`, capture sampler/seed and actual model names, and validate `/object_info` before API integration (see M1 section below).

## M1 — Wan 2.2 FLF2V semantic binding (2026-11-23)

**Plan.** Inspect the owner's real API export, validate every node against the live ComfyUI schema, bind semantic roles to real node IDs in a versioned profile, add offline tests against a captured schema snapshot, and keep submission out of scope.

**Live environment observed** (`GET /system_stats`, read-only): ComfyUI 0.46.0, portable embedded Python 3.13.14, PyTorch 2.14.1+cu130, `--listen 127.0.0.1 --port 8188` (default VRAM mode), NVIDIA RTX A6000 with 51,526,500,352 bytes VRAM total.

**Workflow inspection (`workflows/03_wan22_flf2v.json`, 15 nodes, all `comfy-core`).**
- All 11 classes exist in live `/object_info`: CLIPLoader, CLIPTextEncode, CreateVideo, KSamplerAdvanced, LoadImage, ModelSamplingSD3, SaveVideo, UNETLoader, VAEDecode, VAELoader, WanFirstLastFrameToVideo. Every required input is present; every link points to an existing node and a type-compatible output.
- Model literals are in the installed choice lists: `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors`, `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors`, `umt5_xxl_fp8_e4m3fn_scaled.safetensors`, `wan_2.1_vae.safetensors` (FP8 experts, shift 8, 20 steps split 10/10, CFG 4, euler/simple). Checkpoint SHA-256 hashes are **not** yet recorded.
- `SaveVideo` carries the dynamic-combo sub-key `format.codec` (resolved against `COMFY_DYNAMICCOMBO_V3` options) and a UI-only `video-preview` key, which is reported as a warning.

**Bindings** (`configs/profiles/wan22_flf2v.binding.json`, pinned with canonical graph hash `22a68e21…0dc2`, `_meta` excluded):

| Role | Node.input | Class | Constraint from `/object_info` |
|---|---|---|---|
| start_image | 80.image | LoadImage | must exist in ComfyUI input folder |
| end_image | 89.image | LoadImage | must exist in ComfyUI input folder |
| positive_prompt | 90.text | CLIPTextEncode | STRING |
| negative_prompt | 78.text | CLIPTextEncode | STRING |
| width / height | 81.width / 81.height | WanFirstLastFrameToVideo | INT ≥16, step 16 |
| length (frames) | 81.length | WanFirstLastFrameToVideo | INT ≥1, step 4 (4n+1) |
| fps | 86.fps | CreateVideo | FLOAT 1–120 (container rate only) |
| seed | 84.noise_seed | KSamplerAdvanced | INT 0–2^64−1 |
| filename_prefix | 83.filename_prefix | SaveVideo | STRING |
| output | 83 | SaveVideo | `output_node: true` |

The profile's assertions fail closed if a re-export changes the assumptions behind it: 84 `add_noise=enable`, 87 `add_noise=disable` (so 87's `noise_seed` is inert and unbound), and the 10/10 step split. Steps, CFG, sampler and shift are deliberately **not** bound roles yet because the expert split is coupled to them.

**Code.** `workflow_adapter.py`: `validate_graph` (classes, required inputs, links/types, choice lists incl. model filenames, ranges, INT steps), `BindingProfile` + `validate_profile` (hash pin, node/class/input existence, literal-not-link, output node, assertions), schema-checked `patch_workflow`, `extract_outputs` for the observed `/history` SaveVideo shape. CLI: `morphcurrent workflow-check` and `workflow-patch --set role=value --out FILE` (validated, refuses overwrite, **never submits**). Both accept `--object-info FILE` for offline use.

**Commands and results.**
- `python -m morph_studio.cli workflow-check` against live ComfyUI → `ok: true`, 0 errors, 1 warning (`video-preview`).
- `python -m pytest -m "not integration and not gpu"` → 63 passed.
- `set MORPHCURRENT_COMFY_URL=http://127.0.0.1:8188` then `python -m pytest -m integration` → 1 passed (reads `/object_info` only).
- Offline fixture: `tests/fixtures/object_info_wan22_flf2v.json` (the 11 classes, captured from ComfyUI 0.46.0).

**Not done / next.**
- [x] Programmatic dispatch (upload anchors → refresh `/object_info` → patch → `/prompt` → `/history` → download) with a persistent job record — see M3 below. No MorphCurrent-submitted render exists yet; a GPU smoke run needs explicit owner approval.
- [ ] Record SHA-256 for the four model files and the ComfyUI git revision in a run manifest.
- [ ] Decide whether to expose steps/CFG/split as a coupled `sampling` role group for experiments.
- [ ] Review `ComfyUI_00003_.mp4` (MC-FLF2V-002) visually before drawing quality conclusions.

## M3 — Programmatic FLF2V bridge dispatch (2026-11-24)

**Plan.** Turn the validated binding into a resumable, single-job dispatcher: upload anchors, re-validate against refreshed `/object_info`, submit only on explicit GPU consent, follow `/history`, download, and verify the clip, persisting every step.

**What exists now** (`src/morph_studio/bridge.py`, `media.py`, client additions):
- `morphcurrent bridge --start A --end B --seed N [--prompt|--prompt-file] [--negative] [--width --height --length --fps]`. Without `--confirm-gpu` it plans, uploads and validates, then stops at `validated` with nothing queued.
- Job directory `outputs/runs/<job_id[:16]>/`, holding `job.json` (state, request, anchor SHA-256s, resolved values, model filenames, ComfyUI version/argv/VRAM snapshots, prompt ID, timings, outputs with SHA-256, verification, event log) and the exact `workflow.api.json` submitted. The job ID is a content hash of the patched graph, anchor bytes, workflow hash and code version, so an identical request reuses a verified clip with zero HTTP calls.
- Anchors upload as `mc_<sha16>.<ext>` (deduplicated by ComfyUI, never overwrites). A rename by ComfyUI fails the job.
- The `prompt_id` is a client-generated UUID saved *before* `POST /prompt` (supported by ComfyUI 0.46 `server.py`). On resume it is reconciled against `/history` and `/queue`: a lost response does not double-queue; an unreceived POST is resent with the same ID. HTTP rejections fail the job; transport errors stay resumable.
- Guards: refuses to submit while ComfyUI's queue is busy (`--allow-busy-queue` overrides). `bridge-cancel` dequeues or sends a **targeted** `/interrupt` with the prompt ID, never a global interrupt. A prompt missing from both history and queue (ComfyUI restart) fails closed; `--retry` resubmits.
- Downloads go to `.part` and are renamed without replacing. `ffprobe` checks width/height/decoded frame count/fps against the request; if ffprobe is missing the job stays `downloaded` with verification `skipped`, never `verified`.
- Peak VRAM is recorded as **NOT MEASURED** (the API exposes only `vram_free` snapshots, which are recorded).

**Commands and results.**
- `python -m pytest -m "not integration and not gpu"` → 79 passed (16 new in `tests/test_bridge.py`, against a stateful fake ComfyUI covering crash/resume, retry, lost prompt, busy queue, cancel, tamper and verification paths; `probe_video` tested on a synthetic ffmpeg clip).
- `set MORPHCURRENT_COMFY_URL=http://127.0.0.1:8188` then `python -m pytest -m integration` → 1 passed.
- Live, no GPU: `python -m morph_studio.cli bridge --start assets/anchors/01_glass_orchid.jpg --end assets/anchors/02_metallic_butterfly.jpg --seed 844823683741909 --length 65 --width 640 --height 368 --fps 16` → `validated`, job `4b5d5805e77bcbe0`, anchors uploaded as `mc_8cdb3f53b119ff78.jpg` / `mc_c7f2be088ac64194.jpg`, queue empty afterwards. Rerun reused the same job without new uploads. At validation the A6000 reported 14,177,250,198 of 51,526,500,352 bytes free (other processes holding VRAM; not investigated).

**Not done / next.**
- [ ] First MorphCurrent-submitted GPU render (`bridge ... --confirm-gpu`), pending owner approval. Expect ~3+ minutes per 65-frame 640×368 clip based on the manual runs (not measured here).
- [ ] WebSocket progress display (history polling is authoritative and sufficient for now).
- [ ] Model checkpoint SHA-256 inventory, so the job hash covers weights rather than filenames.
- [ ] Storyboard → multi-bridge scheduling using `timeline.py` frame plans.
