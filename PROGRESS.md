# PROGRESS — MorphCurrent

> Date: 2026-11-23. This document is a ledger, not a promise. Only mark a stage complete when its acceptance gate is demonstrated.

## Current snapshot
- [x] Repository created by owner; initial engineering scaffold committed via connected GitHub workflow (after initial setup).
- [x] Architecture and Claude Desktop engineering handoff documented.
- [x] Native Windows 11-only Python setup/launch/Spec Kit helpers and doctor CLI authored; Windows-only CI configured (check job status for results).
- [x] Offline storyboard / timing and local ComfyUI client starter included.
- [x] Wan 2.2 FLF2V API export (`workflows/03_wan22_flf2v.json`) validated against live `/object_info` and bound by `configs/profiles/wan22_flf2v.binding.json` (2026-11-23). Anchor T2I/edit exports (`01_`, `02_`) still missing.
- [ ] A6000 environment and model inventory verified.
- [x] First two-anchor FLF2V bridge manually rendered and inspected as MC-FLF2V-001. The **first MorphCurrent-dispatched** 65-frame bridge MC-FLF2V-003 was also GPU-verified and matched MC-FLF2V-002 decoded frames; artistic quality and peak VRAM remain unverified. See experiment ledger below.
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
| MC-FLF2V-003 | 2026-11-24 local | **First MorphCurrent-dispatched render** (`bridge --resume … --confirm-gpu`), same graph + seed as 002 | 640×368, 65 frames, 16 FPS, H.264, 4.0625 s (ffprobe) | 20 steps (10/10), CFG 4, euler/simple, seed 844823683741909; prompt_id `5f38ed34-db9d-4e6d-b11b-22726fb27ab3` | ComfyUI execution 234.0 s (history timestamps); submit→verified 3 min 55 s; peak VRAM **NOT MEASURED** (~35.7 GB already held by other processes, e.g. LM Studio, per nvidia-smi) | Decoded frames **identical** to manual 002 (PSNR ∞, SSIM 1.000 over 65 frames). Contact sheet (heuristic, owner review pending): endpoints match anchors; petals collapse to a thin vertical form ~frames 24–40, wings appear quickly with a bright flare ~frame 48 | `outputs/runs/4b5d5805e77bcbe0/` (gitignored); MP4 SHA-256 `2d145e6b563fb2b7ccf75412fae7522e3bb5446c6363eec0cac779b13647843c` |

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
- [x] Real ComfyUI video inference is demonstrated by owner manual runs and MorphCurrent dispatch MC-FLF2V-003. Peak GPU VRAM and automatic T2I/edit image generation are **NOT VERIFIED**; Windows CI remains offline only.

## Example FLF2V anchor pair generated (2026-11-23)

- [x] Two matched 16:9 Glass Orchid → Metallic Butterfly endpoint images created from original AI-generated artwork, manually composed/cropped for consistent framing and stored as small JPEG fixtures in `assets/anchors/`.
- [x] Documented the positive transformation prompt, manual ComfyUI first/last-frame loading and Python-only optional staging helper (`docs/ANCHOR_EXAMPLES.md`).
- [x] Owner reports successful local Wan 2.2 FLF2V smoke render; uploaded `ComfyUI_00002_.mp4` was inspected. See `docs/RENDER_BASELINE_001.md` for measured video metadata and limitations.
- [x] Real Wan 2.2 ComfyUI API export saved and validated; MorphCurrent subsequently dispatched a programmatic 65-frame bridge MC-FLF2V-003. Exact overall GPU peak VRAM remains **NOT MEASURED**.

## First video baseline and next trial (2026-11-23)

- [x] Reviewed owner-uploaded 49-frame H.264 baseline at 640×368 / 16 FPS, with hash, endpoint fidelity and mid-transition issues documented in `docs/RENDER_BASELINE_001.md`.
- [x] MC-FLF2V-002: owner rendered 65 frames with revised prompt, with actual node/seed captured in ComfyUI history. **Visual creative review remains NOT DONE**, notwithstanding MC-FLF2V-003's decoded-frame equality.
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
- [x] Programmatic dispatch (upload anchors → refresh `/object_info` → patch → `/prompt` → `/history` → download) with a persistent job record — see M3 below. Owner-approved MorphCurrent GPU bridge MC-FLF2V-003 completed afterward; **new** GPU runs still require explicit bounded approval.
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
- [x] First MorphCurrent-submitted GPU render — owner approved in chat on 2026-11-24 ("Yes, render it"). See MC-FLF2V-003 and the result notes below.
- [ ] WebSocket progress display (history polling is authoritative and sufficient for now).
- [ ] Model checkpoint SHA-256 inventory, so the job hash covers weights rather than filenames.
- [ ] Storyboard → multi-bridge scheduling using `timeline.py` frame plans.

### M3 result — first programmatic render (2026-11-24)
- Command: `.venv\Scripts\python.exe -m morph_studio.cli bridge --resume outputs\runs\4b5d5805e77bcbe0 --confirm-gpu --timeout 3600` → exit 0, state `verified`.
- Events: validated 04:59:37Z → submitting/submitted 05:01:15Z → completed/downloaded/verified 05:05:10Z. Prompt ID was chosen client-side and persisted before the POST, as designed.
- Determinism: decoded frames match the owner's manual `ComfyUI_00003_.mp4` exactly (ffmpeg `psnr` = inf, `ssim` = 1.000). Container bytes differ (embedded run metadata), so compare decoded frames, not file hashes.
- Finding: `/system_stats` `vram_free` stayed at 14,177,250,198 bytes before, during and after the run while `nvidia-smi` reported ~35.7 GB used; those snapshots are now labelled non-evidence in `job.json`. Real VRAM benchmarking needs an `nvidia-smi` sampler during execution (next step).
- Quality is **not** judged here; the contact-sheet notes in the ledger are heuristics for owner review.

**Next.**
- [ ] Add an opt-in `nvidia-smi` memory sampler around the render for real peak-VRAM numbers (W0/W4 benchmark gate).
- [ ] Owner review of MC-FLF2V-003 mid-transition (collapse/flare ~frames 24–48); then seed/prompt sweep via `bridge` (each run is a separate content-addressed job).

## Ten-feature automatic anchor-to-morph program — design baseline (2026-11-24)

- **Source baseline:** main commit `2deb3863a89f37cc99be77867edda10df88b9878` observed before this documentation rewrite; later execution must re-read HEAD and not overwrite newer runs.
- **Plan only:** the new [ten-feature ledger](docs/SPECKIT_FEATURE_LEDGER.md), [full pipeline design](docs/FULL_PIPELINE_DESIGN.md) and [paste-only Claude instruction](docs/CLAUDE_DESKTOP_ONESHOT.md) define F01–F10. This documentation commit **does not** implement T2I/edit image generation or a final movie.
- **Current capability boundary:** verified single-bridge Wan dispatcher and the sample external anchor pair exist. Real `workflows/01_anchor_t2i.json` and `workflows/02_anchor_edit.json` **do not** exist; no local image-generation checkpoint/terms have been confirmed in this repository.
- **Next executable milestone F01:** verify Python Spec Kit, inspect active GPU queue read-only (do not disturb owner's smoke test), record available models and tests; then F02 acquisition/validation of **real** local image workflows with owner-approved downloads as necessary.
- **F01–F10 mapping/status:** all **PLANNED**, not yet executed under this new program; use actual conflict-free Spec Kit `specs/NNN-slug` names recorded as features start. Offline-only work may proceed while the owner's GPU is busy.
- **Next visual approval:** MC-FLF2V-002/003 contact-sheet/clip quality review; peak VRAM **NOT MEASURED**; avoid conflating frame-identical reproduction with a smooth visual morph.

| Logical feature | Actual Spec Kit folder | State | Implementation evidence |
|---|---|---|---|
| F01 | `specs/001-safe-baseline-provenance` | COMPLETE (offline + live read-only) | `gates.py`, `preflight.py`, `baseline` CLI, cloud-node rejection, `docs/ENVIRONMENT.md`; 100 offline tests |
| F02 | `specs/002-image-workflow-onboarding` | OFFLINE-PASS; GPU/export BLOCKED | capability contracts, `workflow-inspect`, `docs/ANCHOR_MODEL_DECISION.md`; awaiting owner model approval |
| F03 | `specs/003-first-anchor-t2i` | OFFLINE-PASS; GPU BLOCKED | `anchor` CLI + `anchors.py` on the shared bridge executor; image integrity checks |
| F04 | Not yet created | PLANNED | Pending Spec Kit specification, code and tests |
| F05 | Not yet created | PLANNED | Pending Spec Kit specification, code and tests |
| F06 | Not yet created | PLANNED | Pending Spec Kit specification, code and tests |
| F07 | Not yet created | PLANNED | Pending Spec Kit specification, code and tests |
| F08 | Not yet created | PLANNED | Pending Spec Kit specification, code and tests |
| F09 | Not yet created | PLANNED | Pending Spec Kit specification, code and tests |
| F10 | Not yet created | PLANNED | Pending Spec Kit specification, code and tests |

## F01 — Safe baseline, GPU gate, provenance (2026-11-24)

**Session baseline (before edits).** HEAD `7c54caf` on `main`, clean, equal to `origin/main`. `python scripts/windows/speckit.py --status` and `--verify` → `ready_for_python_spec_kit: true`, no problems (not re-initialised). Offline tests: **83 passed, 1 deselected**. Live ComfyUI (GET only): queue running 0 / pending 0; last four `/history` items all `success`. No owner render was active, none was started.

**Spec Kit.** `create_new_feature.py --json --number 1 --short-name safe-baseline-provenance` → `specs/001-safe-baseline-provenance` (no branch). Artifacts: spec, checklist, plan, research, data-model, contracts/baseline-cli.md, quickstart, tasks (15/15 done). Analyze: 100 % FR coverage, 0 critical.

**Built.**
- `src/morph_studio/gates.py`: `check_gpu_gate` (explicit consent + idle queue unless overridden + no cloud nodes) and `cloud_nodes`. `bridge._submit` now uses it; its message and flags are unchanged.
- `validate_graph` rejects ComfyUI **cloud API nodes** (`api_node: true` or module `comfy_api_nodes`). Measured: 363 of 1066 installed classes are cloud (e.g. `QwenImageEditApi`), so this matters for the image-workflow work.
- `src/morph_studio/preflight.py` + `morphcurrent baseline [--skip-comfy] [--object-info] [--out] [--strict]`: read-only report (git, ComfyUI, queue, model inventory, profile validation, capability classification, nvidia-smi snapshot). `BindingProfile.capability` added (`wan_flf2v` set on the Wan profile; graph hash unchanged).
- `docs/ENVIRONMENT.md`: measured facts only; peak VRAM and checkpoint SHA-256 **NOT MEASURED**.
- Fixture `tests/fixtures/object_info_image_nodes.json`: 25 real classes captured from local ComfyUI 0.46.0 (image loaders/samplers/edit encoders + 2 cloud nodes) for the F02–F04 offline tests.

**Commands and results.**
- `.venv\Scripts\python.exe -m pytest -m "not integration and not gpu"` → **100 passed, 1 deselected**.
- `set MORPHCURRENT_COMFY_URL=http://127.0.0.1:8188` then `python -m pytest -m integration` → 1 passed.
- `python -m morph_studio.cli baseline` (live) → 0.75 s, GET only, queue unchanged; `wan_flf2v: available`, `text_to_image` / `reference_edit`: **BLOCKED** (CheckpointLoaderSimple choices empty; diffusion_models only the two Wan I2V experts; text encoder only UMT5).
- `python -m morph_studio.cli workflow-check` → `ok: true` (1 warning `video-preview`).

**Key blocker for F02–F04 GPU gates:** no image-generation weights are installed. Downloading any requires explicit owner approval (model choice, license, size).

## F02 — Image model/workflow onboarding, offline slice (2026-11-24)

**Spec Kit.** `create_new_feature.py --number 2 --short-name image-workflow-onboarding` → `specs/002-image-workflow-onboarding`. spec, checklist, plan, research, data-model, contracts/workflow-inspect.md, quickstart, tasks (10/13 done; T011–T013 owner-gated).

**Built.**
- Capability role contracts in `validate_profile`: `text_to_image` needs `positive_prompt`, `seed` + image output; `reference_edit` adds `reference_image`; `wan_flf2v` needs `start_image`, `end_image`, `positive_prompt`, `seed`, `length` + video output (Wan profile passes).
- `morphcurrent workflow-inspect EXPORT [--object-info|--offline]` (`src/morph_studio/onboarding.py`): read-only; lists nodes, cloud nodes, model literals with installed status, schema errors and *candidate* roles; rejects UI-format files with Save (API Format) guidance; writes nothing.
- `docs/ANCHOR_MODEL_DECISION.md`: candidate sets copied from the `models` metadata of ComfyUI's **locally installed** official templates (Option A: Qwen-Image + Qwen-Image-Edit-2509 sharing Qwen2.5-VL encoder and VAE; Option B: Qwen-Image 2.1). Licenses marked *owner to verify*; sizes approximate; manual export procedure; empty approval log.
- `tests/image_graphs.py`: synthetic API graphs built only from real captured classes, plus a *simulated-install* object_info, reused by later anchor tests. They are not owner exports.

**Results.** Offline **113 passed, 1 deselected**; live `workflow-check` ok. No download, no GPU job.

**BLOCKED (owner):** approve a model set → download into ComfyUI model folders → render once per template → Save (API Format) to `workflows/01_anchor_t2i.json` and `workflows/02_anchor_edit.json`. Then a session writes and live-validates the two binding profiles (T013).

## F03 — First anchor via local T2I, offline slice (2026-11-24)

**Spec Kit.** `create_new_feature.py --number 3 --short-name first-anchor-t2i` → `specs/003-first-anchor-t2i`; tasks 8/9 (T009 GPU render blocked).

**Built.**
- `bridge.advance_job()`: the bridge's crash-safe executor (upload → validate → gate → submit with persisted prompt ID → reconcile → await → `.part` download → verify) extracted and shared; `_upload` iterates the plan's roles. `run_bridge` behaviour unchanged (16/16 bridge tests untouched).
- `src/morph_studio/anchors.py`: `AnchorRequest` (explicit seed; `reference_image` iff `reference_edit`; methods `text_to_image`, `reference_edit`, `independent_t2i`), `plan_anchor` (capability must match method; content-addressed job ID over graph + reference bytes + workflow hash + version), `run_anchor`, `verify_anchor_image` (exactly one image, structurally valid, bound width/height must match), `anchor_image_path` (refuses unverified/tampered).
- `media.inspect_image`: stdlib PNG chunk/CRC walk and JPEG SOI/SOF/EOI check (no Pillow).
- CLI `anchor` (validates only without `--confirm-gpu`) and `anchor-status`.
- Tests: `tests/fake_comfy.py` (generic image+video fake ComfyUI), `tests/conftest.py` (`image_repo` fixture), `test_anchors.py` (17), `test_media_images.py` (6): success, no-consent, cache hit with zero calls, seed change, missing model on the **real** captured object_info, hash drift, wrong capability, non-image / truncated / wrong size / zero / two outputs, lost `/prompt` response without double submit, execution error + retry, tamper, busy queue, CLI.

**Results.** Offline **137 passed, 1 deselected**. GPU: NOT RUN (no T2I model/profile).
