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
| MC-FLF2V-001 | 2026-11-23 local | Owner manual Wan 2.2 Orchid → Butterfly, uploaded MP4 | **640×368**, 49 frames, 16 FPS; 3.0625 s | 20 steps (split 10/10), CFG 4, euler/simple, seed 1091897826965482 — recovered from ComfyUI `/history` prompt `748d6c59…` | VRAM/time **NOT MEASURED** | Faithful anchors; transitory petal clipping and distorted wings at 0.75–1.5 s | `docs/EXPERIMENTS.md`; MP4 SHA-256 `a638f6e1d58d876670ddc72c0bb773f9f6c83d93076ac3a9403c41618823120c` |
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
- [x] Owner reports successful local Wan 2.2 FLF2V smoke render; uploaded `ComfyUI_00002_.mp4` was inspected. See `docs/EXPERIMENTS.md` for measured video metadata and limitations.
- [x] Real Wan 2.2 ComfyUI API export saved and validated; MorphCurrent subsequently dispatched a programmatic 65-frame bridge MC-FLF2V-003. Exact overall GPU peak VRAM remains **NOT MEASURED**.

## First video baseline and next trial (2026-11-23)

- [x] Reviewed owner-uploaded 49-frame H.264 baseline at 640×368 / 16 FPS, with hash, endpoint fidelity and mid-transition issues documented in `docs/EXPERIMENTS.md`.
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
| F02 | `specs/002-image-workflow-onboarding` | COMPLETE | capability contracts, `workflow-inspect`, `docs/MODELS.md`; awaiting owner model approval |
| F03 | `specs/003-first-anchor-t2i` | OFFLINE-PASS; GPU BLOCKED | `anchor` CLI + `anchors.py` on the shared bridge executor; image integrity checks |
| F04 | `specs/004-reference-edit-anchors` | OFFLINE-PASS; GPU BLOCKED | `run_anchor_chain`, explicit `independent_t2i`, contact sheet |
| F05 | `specs/005-storyboard-task-dag` | COMPLETE (offline feature) | `dag.py` + `morphcurrent dag`; 16-multiple size check |
| F06 | `specs/006-generated-anchor-bridges` | OFFLINE-PASS; GPU BLOCKED | `pipeline.run_bridge_stage` on the unchanged Wan bridge path |
| F07 | `specs/007-recovery-provenance-metrics` | OFFLINE-PASS | run manifest, crash-resume tests, `models-hash`, VRAM sampler |
| F08 | `specs/008-quality-selective-rerender` | OFFLINE-PASS (heuristics uncalibrated) | `qa.py`, `qa`/`review` CLI, selective rerender plan |
| F09 | `specs/009-seam-safe-join` | OFFLINE-PASS | `stitcher.join_verified`, seam checks, optional audio |
| F10 | `specs/010-one-command-render` | OFFLINE-PASS; GPU E2E BLOCKED | `render` command; offline E2E to a 129-frame movie |

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
- `docs/MODELS.md`: candidate sets copied from the `models` metadata of ComfyUI's **locally installed** official templates (Option A: Qwen-Image + Qwen-Image-Edit-2509 sharing Qwen2.5-VL encoder and VAE; Option B: Qwen-Image 2.1). Licenses marked *owner to verify*; sizes approximate; manual export procedure; empty approval log.
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

## F04 — Reference-guided next anchors, offline slice (2026-11-24)

**Spec Kit.** `create_new_feature.py --number 4 --short-name reference-edit-anchors` → `specs/004-reference-edit-anchors`; tasks 6/7 (T007 GPU edit render blocked).

**Built.**
- Storyboard schema: `generation` accepts `independent_t2i` (explicit fallback; optional `reference` names a continuity parent, not image-conditioned); per-anchor `negative_prompt`. Existing storyboard still validates.
- `anchors.run_anchor_chain()`: storyboard-order generation, one GPU job at a time. A `reference_edit` child is planned only after its parent is verified and gets the parent's exact verified file (SHA re-checked) as `reference_image`, so B is byte-identical for both bridges. Missing edit profile → **BLOCKED** with a message naming the explicit `independent_t2i` option; never a silent T2I substitute. Child size must equal parent size. `continuity` block records parent hash, whether conditioned, and `review: required` for `independent_t2i`.
- `media.contact_sheet()`: FFmpeg `hstack` side-by-side PNG (argument list, never overwrites).
- An unbound negative prompt makes planning fail rather than being dropped silently.

**Results.** Offline **146 passed, 1 deselected** (7 chain tests incl. real FFmpeg contact sheet). GPU: NOT RUN.

## F05 — Storyboard task DAG (2026-11-24)

**Spec Kit.** `create_new_feature.py --number 5 --short-name storyboard-task-dag` → `specs/005-storyboard-task-dag`; tasks 6/6.

**Built.** `src/morph_studio/dag.py` `compile_plan()` + `morphcurrent dag STORYBOARD` (no network): tasks `anchor:<id>` (method, capability, positive = anchor prompt + style description, negative, seed + `seed_source`, size, dependency on the reference), `bridge:<from>-><to>` (4n+1 frames from beats/BPM/fps via `timeline.py`, seed, prompt, candidates, timing error; depends on both endpoint anchors, so B is one task used by two bridges), `final:movie` (unique frames `1+Σ(L−1)`, anchor span, nominal duration, delivery fps, optional audio, verified-seam join rule). Requirements list per capability with profile existence; `plan_sha256` over canonical task content. Schema: render width/height must be multiples of 16 (Wan step 16).

**Results.** Offline **155 passed, 1 deselected**. `morphcurrent dag configs/sequences/organic-machines.yaml` → plan `cefb16ae…faea8`, order orchid → butterfly → phoenix → two bridges → final, 129 unique frames, blocked: `text_to_image` and `reference_edit` profiles missing (expected until F02).

## F06 — Generated anchors → Wan bridges, offline slice (2026-11-24)

**Spec Kit.** `specs/006-generated-anchor-bridges` (`--number 6`); tasks 4/5 (T005 GPU blocked).

**Built.** `src/morph_studio/pipeline.py` `run_bridge_stage(dag_plan, anchor_jobs, …)`: for each DAG bridge task, endpoints are `anchor_image_path()` of verified anchor jobs (SHA re-checked), the request uses the task's prompt/seed/length/fps/size and the Wan profile from the plan requirements, and execution is the unchanged `plan_bridge` + `run_bridge` (MC-FLF2V-003 path). Raises if one anchor id appears with two byte versions; records anchor job IDs and `candidates_requested` (multi-candidate ranking is F08). Unverified anchors block their bridges.

**Results.** Offline **160 passed, 1 deselected**: storyboard → 3 fake-generated anchors → 2 bridges whose inputs are exactly the generated SHAs (B shared), rerun 0 new `/prompt`, no-consent stops at `validated`, missing Wan model fails validation with no substitute, busy queue refused. Note: the storyboard renders at 832×480 while MC-FLF2V-003 used 640×368; 832×480 is schema-valid but **not GPU-tested**.

## Git history note (2026-11-24)

At the owner's request, `Co-Authored-By` trailers were removed from all commits (`git filter-branch --msg-filter`, from `87e1717` onward; file trees unchanged) and `main` was force-pushed (`eb5a8e4` → `6be6c51`, `--force-with-lease`). Commit SHAs quoted earlier in this file before that point are pre-rewrite. The rule is now in `CLAUDE.md`. A local branch `backup/pre-coauthor-rewrite` keeps the old history and was not pushed.

## F07 — Recovery, provenance, VRAM observations, offline slice (2026-11-24)

**Spec Kit.** `specs/007-recovery-provenance-metrics` (`--number 7`); tasks 5/7 (T006 hashing and T007 sampled render are owner-scheduled).

**Built.**
- `run_manifest.RunManifest`: `outputs/runs/run-<plan16>/manifest.json` + `plan.json`; atomic temp+replace writes; stage entries mirror stage `job.json` (job id/dir, state, prompt id, image/video SHA); consent and VRAM lists.
- Crash safety proven: a simulated hard stop right after each of 7 persisted transitions (uploaded … verified) resumes to `verified` with exactly one `/prompt`.
- `provenance.py` + `morphcurrent models-hash --confirm-io`: hashes only model files referenced by binding-profile graphs, refuses when ComfyUI's queue is non-empty, caches by (path, size, mtime_ns), `recorded_hashes()` gives `NOT RECORDED` for stale/missing entries.
- `vram.VramSampler`: opt-in thread polling `nvidia-smi` (argument list); summary = baseline / peak / min, interval, sample count, labelled overall-GPU (all processes) with a between-samples caveat; no samples → `NOT MEASURED`.

**Results.** Offline **173 passed, 1 deselected**. Model SHA-256 and peak VRAM on the A6000 remain **NOT MEASURED**.

## F08 — Quality heuristics and selective rerender, offline slice (2026-11-24)

**Spec Kit.** `specs/008-quality-selective-rerender` (`--number 8`); tasks 5/6 (T006 calibration needs owner review).

**Built.** `src/morph_studio/qa.py`: FFmpeg-decoded 64×36 gray frames (argument list, local); heuristics for hard cut (diff > 6× median and > 20), freeze (≥ 6 frames diff < 0.5), flare (luminance jump > 40), endpoint mismatch vs anchor (> 25); every report says `method: heuristic`. `candidate_seeds` (task seed + deterministic derived seeds), `rank_candidates`, `rerender_plan` (only bridges flagged-and-not-approved or rejected; anchors and other bridges reused), `review.json` persistence. CLI `qa CLIP [--start --end]`, `review RUN_DIR TASK approved|rejected|pending [--note]`.

**Calibration observation (local CPU decode, no GPU).** `qa` on MC-FLF2V-003 (`outputs/runs/4b5d5805e77bcbe0/outputs/bridge_00001_.mp4`) with the two example anchors: 65 frames, median diff 1.93, max 6.25, endpoint diffs 3.8 / 4.85, **no flags** — although the contact sheet shows petal collapse (~frames 24–40) and a wing flare (~48). The heuristics catch gross cuts/freezes/flashes/endpoint errors only; they are **not** a creative-quality gate. Human review remains required.

**Results.** Offline **181 passed, 1 deselected**.

## F09 — Seam-safe join and optional soundtrack, offline slice (2026-11-24)

**Spec Kit.** `specs/009-seam-safe-join` (`--number 9`); tasks 4/5 (T005 real seam blocked).

**Built.** `stitcher.check_seams()` compares decoded boundary frames (64×36 gray mean abs diff ≤ 8; optionally against the shared anchor image). `join_verified()` refuses mismatched size/fps or seams, builds the existing concat/trim command (drops only later clips' first frame; never xfade), writes `<name>.part.mp4`, verifies frame count Σ L − (n−1) with ffprobe, then renames. Optional audio: existing local file only, `-ss offset`, cut to video duration, AAC; default has no audio stream. Existing `build_join_command` tests unchanged.

**Results.** Offline **186 passed, 1 deselected**: two 17-frame lossless synthetic ramps sharing the boundary value → 33 frames with correct first/seam/last values; mismatched seam refused and nothing written; video-only vs audio variants; remote audio URL refused. Seam tolerance is provisional until two real Wan bridges sharing B are measured.

## F10 — One-command render, offline slice (2026-11-24)

**Spec Kit.** `specs/010-one-command-render` (`--number 10`); tasks 7/8 (T008 real E2E blocked).

**Built.** `src/morph_studio/render.py` + `morphcurrent render`:
- `render STORYBOARD --dry-run` — no network, no writes; DAG, GPU job count (3 anchors, 2 bridges), BLOCKED list; exit 6 when profiles are missing.
- `render STORYBOARD` — preflight (missing profile → exit 6 before any ComfyUI request), then validates every stage against live `/object_info`, nothing queued.
- `render STORYBOARD --confirm-gpu [--sample-vram] [--accept-heuristics]` — anchor chain → bridges (one GPU job at a time, shared gate) → anchor contact sheet + QA heuristics per bridge → stops `awaiting_review` (exit 7) until `morphcurrent review RUN_DIR bridge:… approved` (or `--accept-heuristics` with no flags) → seam-verified join to `outputs/runs/run-<plan16>/final/movie.mp4`; rejected bridge → `rerender_needed`. Re-running resumes; `render --status RUN_DIR` is read-only. Manifest records consent, stages, QA, VRAM samples (if enabled), final join report.
- Fake ComfyUI test mode renders **real** FFmpeg clips that ramp between the exact generated anchor colours, so seams are genuinely checked.

**Results.** Offline **192 passed, 1 deselected**: YAML → 3 anchors → 2 bridges (shared B SHA) → review gate → **129-frame** movie with matching seams and no crossfade; second and third runs 0 new `/prompt`; dry run writes nothing; missing profiles make 0 requests. Live `render configs/sequences/organic-machines.yaml --dry-run` → `blocked`: `anchor_t2i.binding.json`, `anchor_edit.binding.json` missing.

## Session handoff — restart point (2026-11-24)

| Fxx | Spec dir | Status |
|---|---|---|
| F01 | specs/001-safe-baseline-provenance | COMPLETE |
| F02 | specs/002-image-workflow-onboarding | OFFLINE-PASS; GPU/export BLOCKED |
| F03 | specs/003-first-anchor-t2i | OFFLINE-PASS; GPU BLOCKED |
| F04 | specs/004-reference-edit-anchors | OFFLINE-PASS; GPU BLOCKED |
| F05 | specs/005-storyboard-task-dag | COMPLETE |
| F06 | specs/006-generated-anchor-bridges | OFFLINE-PASS; GPU BLOCKED |
| F07 | specs/007-recovery-provenance-metrics | OFFLINE-PASS (hashes / peak VRAM NOT MEASURED) |
| F08 | specs/008-quality-selective-rerender | OFFLINE-PASS (heuristics uncalibrated) |
| F09 | specs/009-seam-safe-join | OFFLINE-PASS (real seam not measured) |
| F10 | specs/010-one-command-render | OFFLINE-PASS; GPU E2E BLOCKED |

**Single blocker:** no image-generation weights on this machine. **Owner steps, in order:**
1. Pick a model set in `docs/MODELS.md` (Option A recommended), check the licenses, record the approval, download the files into the ComfyUI model folders.
2. Render once from the Qwen-Image template and once from the Qwen-Image-Edit-2509 template in the ComfyUI UI; Export (API) to `workflows/01_anchor_t2i.json` and `workflows/02_anchor_edit.json`.
3. Next session: `workflow-inspect` both exports, write `configs/profiles/anchor_t2i.binding.json` / `anchor_edit.binding.json` from the real node IDs (F02 T013), `workflow-check`, then with a bounded approval: one T2I anchor (F03), one edit (F04), one generated-A/B bridge at 832×480 (F06, size not yet GPU-tested), then the full `render --confirm-gpu --sample-vram` (F10) and a second reproducible run. Optional: `models-hash --confirm-io` while idle (F07); visual review of MC-FLF2V-003 to calibrate QA (F08).

Nothing in this session queued GPU work; ComfyUI queue was empty at every check.

## F02 — Anchor model set A installed (2026-11-24)

- Owner approved Option A in chat ("Option A (Qwen)", then "Yes, download"); scope: download only, no GPU render.
- 4 files (50.5 GB) streamed from `huggingface.co/Comfy-Org/Qwen-Image` and `Comfy-Org/Qwen-Image-Edit` into `C:\AI\ComfyUI_windows_portable\ComfyUI\models\{vae,text_encoders,diffusion_models}` via `.part` files, SHA-256 computed while downloading and matched against Hugging Face's published LFS hashes before rename (08:58–09:18 local, ~20 min). No `.part`/`.bad` leftovers.
- Live read-only `/object_info` now lists `qwen_image_fp8_e4m3fn.safetensors`, `qwen_image_edit_2509_fp8_e4m3fn.safetensors` (UNETLoader), `qwen_2.5_vl_7b_fp8_scaled.safetensors` (CLIPLoader), `qwen_image_vae.safetensors` (VAELoader) — no ComfyUI restart needed. Queue empty.
- Verified hashes seeded into the gitignored F07 cache `outputs/model_hashes.json`, so anchor jobs can record real model SHA-256.
- **Still BLOCKED (owner, F02 T012):** render once from the Qwen-Image template and once from Qwen-Image-Edit 2509 in the ComfyUI UI, then Export (API) to `workflows/01_anchor_t2i.json` and `workflows/02_anchor_edit.json`. Then a session writes the two binding profiles (T013).
- **Correction + LoRAs (2026-11-24 09:29 local):** the ComfyUI *Setup required* panel listed the three main Qwen files as missing only because it was stale (backend `GET /models/<folder>` listed them; the panel shows GiB, docs use GB). The templates do reference Lightning LoRAs, which the docs had wrongly called skippable. With owner approval ("Yes, download both") `Qwen-Image-Lightning-8steps-V1.0.safetensors` and `Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors` (2.55 GB, Apache-2.0 per Hugging Face) were downloaded, SHA-256 verified, and are listed in `/models/loras`. Hashes added to `outputs/model_hashes.json`. Queue empty; no GPU job run.

## F02 — Real T2I export bound (2026-11-24)

- Owner rendered template "Qwen-Image: Text to Image" once (832×480 orchid, `output/Qwen-Image_00001_.png`, turbo off) and exported `workflows/01_anchor_t2i.json` (19 nodes, subgraph-flattened IDs `76:*`, graph SHA-256 `912d39f3…8058`, no private paths).
- `workflow-inspect` first reported 9 false link-type errors: ComfyUI 0.46 `ComfySwitchNode` uses the V3 template type `COMFY_MATCHTYPE_V3` (`allowed_types: "*"`). `validate_graph` now treats match-types as wildcards; real mismatches are still caught (new test with the live switch schema in the fixture). Re-inspect: `ok: true`, all 4 model files installed, no cloud nodes.
- `configs/profiles/anchor_t2i.binding.json`: positive `76:6.text`, negative `76:7.text`, seed `76:3.seed`, size `76:58.width/height`, prefix `60.filename_prefix`, output SaveImage `60`; assertions turbo `76:86 = false`, steps `76:84 = 20`, CFG `76:85 = 4`. Live `workflow-check` ok; `anchor … --seed 101` → `validated`, nothing queued.
- Owner's Qwen Image Edit 2509 test render (`output/Qwen_Image_2509_00001.png`) is **1328×800**, not 832×480: the template's `FluxKontextImageScale` rescales to its preferred ~1 MP size and changes the aspect ratio (1.66 vs 1.73). That would fail F04's parent/child size check and distort the Wan bridge. Edit export (T012 second half) pending, with the scale node bypassed.
- Tests: 193 passed, 1 deselected. No GPU job submitted by MorphCurrent.

## F02 — Real edit export bound; F02 COMPLETE (2026-11-24)

- Owner re-rendered "Qwen Image Edit 2509" with `FluxKontextImageScale` bypassed and turbo off: `output/Qwen_Image_2509_00002.png` is 832×480 (same as the orchid). Exported `workflows/02_anchor_edit.json` (20 nodes, graph SHA-256 `2a127143…8744`, no private paths); `workflow-inspect` ok, all 4 model files installed, no cloud nodes.
- `/history` (read-only) confirms `SaveImageAdvanced` node 469 reports `outputs[469].images[]`, the shape `extract_outputs` reads; local output node.
- `configs/profiles/anchor_edit.binding.json`: reference `78.image`, positive `433:111.prompt`, negative `433:110.prompt`, seed `433:3.seed`, prefix `469.filename_prefix`; assertions turbo `433:443 = false`, steps 20, CFG 4, and `433:3.latent_image = ["433:88", 0]` (latent from the unscaled reference, so the edit keeps the parent size).
- Live: `workflow-check` ok; `anchor --profile anchor_edit … --reference <orchid>` → `validated`, nothing queued; `render configs/sequences/organic-machines.yaml --dry-run` → **ready** (3 anchors, 2 bridges, nothing blocked). Queue empty.
- Creative notes for review: the test edit enlarged the subject and kept the green stem; the storyboard prompts (not the test prompts) are what MorphCurrent will send.
- **Next (needs bounded owner GPU approval):** first MorphCurrent image renders (F03/F04), then bridges (F06; 832×480 untested on Wan), full `render --confirm-gpu --sample-vram` (F10).

## GPU consent and first full render start (2026-11-24)

- Owner, in chat: "i authorize gpu use to complete tasks, remember this" — standing consent for local ComfyUI renders needed to complete F01–F10 (recorded in Claude memory). Safeguards kept: submit only on an idle queue, one job at a time, no interrupting/restarting, downloads still need separate approval.
- Pre-run: queue empty; nvidia-smi 46,994 / 49,140 MiB used (snapshot; ComfyUI pid 7220 likely holding the Qwen models from the owner's test renders; WDDM reports no per-process memory).
- Started: `python -m morph_studio.cli render configs/sequences/organic-machines.yaml --confirm-gpu --sample-vram` (3 anchors → 2 bridges at 832×480, then QA + review gate).

## Repository cleanup (2026-11-24)

At the owner's request: removed AI steering documents and stale duplicates (`AutoCreator.md`, `docs/CLAUDE_DESKTOP_ONESHOT.md`, `docs/SETUP_WINDOWS.md`, `docs/ANCHOR_MODEL_ONBOARDING.md`, `docs/ANCHOR_EXAMPLES.md`, `docs/FULL_PIPELINE_DESIGN.md`, old `docs/EXPERIMENTS.md`, `workflows/README.md`, `configs/profiles/README.md`) and two unused config placeholders (`configs/models.yaml`, `.env.example`). All docs now live in `docs/`: `ARCHITECTURE.md` (absorbs the pipeline design and profile/workflow notes), `MODELS.md` (was `ANCHOR_MODEL_DECISION.md`; now the installed-model/workflow reference), `EXPERIMENTS.md` (was `RENDER_BASELINE_001.md` + fixtures), `DEVELOPMENT.md`, `COMFYUI_SETUP.md`, `TROUBLESHOOTING.md`, `ENVIRONMENT.md`, `SPECKIT_FEATURE_LEDGER.md` and this file (moved from the root). README rewritten as a standard project README. `CLAUDE.md` stays at the root (Claude Code reads it there); references updated. Older entries above mention removed file names as history. Tests: 194 passed.

## MC-RUN-001 — first full storyboard render on the GPU (2026-11-24)

- Command (owner standing GPU consent): `render configs/sequences/organic-machines.yaml --confirm-gpu --sample-vram` → exit 7 `awaiting_review`, run `outputs/runs/run-cefb16ae1db47f4d`, 15:03–15:22 UTC (18.6 min).
- **F03 GPU-VERIFIED:** orchid anchor via real Qwen-Image T2I (`8c2cb744…`, image `500bee50…ecdc`, 832×480, 18.7 s).
- **F04 GPU-VERIFIED:** butterfly = reference edit of the orchid's verified bytes (image `4c70fc98…2760`), phoenix = edit of the butterfly (`ae2364ee…93c4`); sizes match parents.
- **F06 GPU-VERIFIED:** bridges `9785f0ae…` (clip `b3b57d0c…3b4d`) and `61df5945…` (clip `ec326bc7…df99`), each 832×480, 65 frames, 16 fps, 4.0625 s (ffprobe); both use the identical butterfly SHA. 832×480 bridges take ~8.3 min (vs ~3.9 min at 640×368).
- **F07:** first sampled VRAM: overall GPU used baseline 46,992 MiB, peak 48,080 MiB (of 49,140), 0.5 s interval, 2,041 samples, includes other processes. Model hashes for Qwen files recorded; Wan still NOT MEASURED.
- **F08:** QA heuristics reported no flags on either bridge despite visible drift/blur (A→B) and a near-cut collapse (B→C) — confirms they are only a gross-defect screen.
- **Not done:** human review/approval, final join (F09/F10 on real clips), reproducible second run. Creative notes in `docs/EXPERIMENTS.md` (MC-RUN-001).
- **Join (15:24 UTC):** owner approved both bridges in chat ("Approve both, join"); recorded with `morphcurrent review … approved`. Re-running the same `render --confirm-gpu` reused all 5 stages with **no new ComfyUI prompts** (queue stayed empty) and joined `outputs/runs/run-cefb16ae1db47f4d/final/movie.mp4`: 129 frames, 832×480, 16 fps, 8.0625 s (ffprobe), seam boundary diff 0.96 (anchor diffs 1.56 / 1.19; tolerance 8), no crossfade, SHA-256 `d94633da8403eccdb910d08b779d5a8e5e5aafbf26161dfe99714ee28e83d583`. **F09 and F10 GPU-VERIFIED.**
- Remaining for the CLAUDE.md completion bar: a clean reproducible second run from scratch (fresh runs root) and creative improvement of the butterfly→phoenix transition (side-on phoenix anchor). Local checkout cleaned (caches, `.local/` backups, egg-info, backup branch removed).

## Example anchors removed (2026-11-24)

At the owner's request: deleted `assets/anchors/01_glass_orchid.jpg`, `02_metallic_butterfly.jpg`, the staging helper `scripts/windows/stage_example_anchors.py` and its test; removed the `.gitignore` exceptions and doc mentions (EXPERIMENTS fixture section, ledger, CLAUDE.md). Bridge tests now use generated temp images; the JPEG integrity test uses an FFmpeg-made frame. The two filenames remain only as literals inside the owner's real `workflows/03_wan22_flf2v.json` export and the captured `/object_info` fixtures (ComfyUI input-folder names; MorphCurrent patches them per job). Earlier entries above mention the files as history. Tests: 192 passed.

## MC-RUN-002 — phoenix transition fix (2026-11-24)

- Changed `configs/sequences/organic-machines.yaml`: phoenix prompt now frontal, centered, wings spread to match the butterfly, with a negative prompt (side view, profile, walking, off-center); butterfly→phoenix bridge `mode: direct`, `motion: static`, prompt for a fixed front-facing transformation (was a rising orbit).
- `render … --confirm-gpu --sample-vram` (new plan `ba2d9dbe…`): orchid, butterfly and orchid→butterfly **reused** with no new prompts; new phoenix `52d69920…` (image `148c0638…5844`) and bridge `4cd0b1bc…` (clip `896df441…7aa5`, 496.8 s). Owner pre-approved both bridges in chat; the same process joined `final/movie.mp4`: 129 frames, 832×480, 16 fps, 8.0625 s, seam diff 1.02, no crossfade, SHA-256 `ce687958…99ab`.
- Visual: the side-on cut is gone; transition stays centered and continuous (brief inward wing fold ~frames 32–40). Sampled VRAM: baseline 35,604, peak 47,838 MiB (all processes). Selective rerender (F08 goal: rerender only the affected anchor/bridge) demonstrated on real hardware.
- Still open: clean from-scratch reproducibility run.

## MC-RUN-003 — reproducibility check (2026-11-24)

- `render configs/sequences/organic-machines.yaml --confirm-gpu --accept-heuristics --sample-vram --runs-root outputs/repro` (fresh root, plan `ba2d9dbe…`), 15:46–16:05 UTC, exit 0.
- All 5 GPU stages recomputed (execution times equal the original run, so no ComfyUI cache shortcut) and every artifact is **byte-identical** to MC-RUN-002: three anchor PNGs, both bridge MP4s, and the joined movie (`ce687958c40bd8d94b25ac28820ebf0ca5bddb53d86908ba4c052c74b80f99ab`); decoded PSNR ∞ / SSIM 1.000. First movie written with the new name `final/organic-machines_20261124-160448Z_ba2d9dbe.mp4`.
- Sampled VRAM (all processes): baseline 35,449, peak 48,056 MiB.
- **CLAUDE.md completion bar now met:** YAML → ComfyUI-generated A, B, C → two Wan bridges → verified seam → final movie + manifest + contact sheet; reproducible second run; human review (owner approved MC-RUN-001/002); model/license gates documented in `docs/MODELS.md`. Remaining optional items: Wan model SHA-256 (`models-hash --confirm-io`), QA threshold calibration, optional licensed soundtrack on real clips.

## 30-feature roadmap update — 20 NEW features F11–F30 (2026-11-24)

- Audited connected GitHub `main` at **`9b79301b31ef6c31db3a465967928ca6aa457b3c`** and recent source/tests. This commit, MC-RUN-003, **proved fresh-root reproducibility**: 3 newly generated Qwen anchors, 2 Wan bridges, and joined MP4 all byte-identical to MC-RUN-002, with decoded PSNR infinity/SSIM 1.0. Original F01–F10 implementation and spec folders remain intact.
- This document preserves historical progress and stale early blockers for chronology; later dated measurements supersede those early states. F07 VRAM snapshots reflect whole-GPU usage, not MorphCurrent-only allocation. Wan checkpoints SHA still NOT MEASURED and creative quality is not guaranteed by exact reproduction.
- **Twenty new logical Spec Kit features F11–F30 are planned, not implemented.** They expand the platform with GPU benchmarking; anchor/camera/material continuity; intermediate morphs; real local beat-matched music; calibrated QA; GPU scheduler; private local project UI; long-form scenes; release/packaging; style libraries; brief-to-storyboard generation; stabilization and camera choreography; frame interpolation; image/video enhancement; safe model adapters; project archives; budgeted A/B experiments; and multi-format delivery.
- New source-of-truth scope and acceptance: `docs/SPECKIT_FEATURE_LEDGER.md` (all F01–F30); new paste-ready Claude Desktop Code one-shot: `docs/CLAUDE_DESKTOP_ONESHOT.md`; root `CLAUDE.md`, `.specify/memory/constitution.md` and `docs/ARCHITECTURE.md` synchronized. No active GPU job was launched by this documentation-only change.
- Next engineering action is **F11**: inspect newest HEAD/dirty work and read-only local ComfyUI queue, run current offline tests and installed Python Spec Kit verification, then create and execute the **real F11** spec/plan/tasks using the supported Claude skills. Do not create empty specs/011..030 all at once; use one feature and preserve numbers/actual script outputs.

### New feature tracker (initial roadmap, no implementation claims)

| Feature | Current status | Actual spec directory | GPU/testing evidence | Dependency/gate |
|---|---|---|---|---|
| F11 | PLANNED | Not created — proposed `specs/011-*` | NOT RUN; NOT IMPLEMENTED | See ledger F11 acceptance criteria |
| F12 | PLANNED | Not created — proposed `specs/012-*` | NOT RUN; NOT IMPLEMENTED | See ledger F12 acceptance criteria |
| F13 | PLANNED | Not created — proposed `specs/013-*` | NOT RUN; NOT IMPLEMENTED | See ledger F13 acceptance criteria |
| F14 | PLANNED | Not created — proposed `specs/014-*` | NOT RUN; NOT IMPLEMENTED | See ledger F14 acceptance criteria |
| F15 | PLANNED | Not created — proposed `specs/015-*` | NOT RUN; NOT IMPLEMENTED | See ledger F15 acceptance criteria |
| F16 | PLANNED | Not created — proposed `specs/016-*` | NOT RUN; NOT IMPLEMENTED | See ledger F16 acceptance criteria |
| F17 | PLANNED | Not created — proposed `specs/017-*` | NOT RUN; NOT IMPLEMENTED | See ledger F17 acceptance criteria |
| F18 | PLANNED | Not created — proposed `specs/018-*` | NOT RUN; NOT IMPLEMENTED | See ledger F18 acceptance criteria |
| F19 | PLANNED | Not created — proposed `specs/019-*` | NOT RUN; NOT IMPLEMENTED | See ledger F19 acceptance criteria |
| F20 | PLANNED | Not created — proposed `specs/020-*` | NOT RUN; NOT IMPLEMENTED | See ledger F20 acceptance criteria |
| F21 | PLANNED | Not created — proposed `specs/021-*` | NOT RUN; NOT IMPLEMENTED | See ledger F21 acceptance criteria |
| F22 | PLANNED | Not created — proposed `specs/022-*` | NOT RUN; NOT IMPLEMENTED | See ledger F22 acceptance criteria |
| F23 | PLANNED | Not created — proposed `specs/023-*` | NOT RUN; NOT IMPLEMENTED | See ledger F23 acceptance criteria |
| F24 | PLANNED | Not created — proposed `specs/024-*` | NOT RUN; NOT IMPLEMENTED | See ledger F24 acceptance criteria |
| F25 | PLANNED | Not created — proposed `specs/025-*` | NOT RUN; NOT IMPLEMENTED | See ledger F25 acceptance criteria |
| F26 | PLANNED | Not created — proposed `specs/026-*` | NOT RUN; NOT IMPLEMENTED | See ledger F26 acceptance criteria |
| F27 | PLANNED | Not created — proposed `specs/027-*` | NOT RUN; NOT IMPLEMENTED | See ledger F27 acceptance criteria |
| F28 | PLANNED | Not created — proposed `specs/028-*` | NOT RUN; NOT IMPLEMENTED | See ledger F28 acceptance criteria |
| F29 | PLANNED | Not created — proposed `specs/029-*` | NOT RUN; NOT IMPLEMENTED | See ledger F29 acceptance criteria |
| F30 | PLANNED | Not created — proposed `specs/030-*` | NOT RUN; NOT IMPLEMENTED | See ledger F30 acceptance criteria |

**Historical correction:** The fresh-root reproducibility requirement formerly marked pending is now met by MC-RUN-003, not a blocker for F11. New F20/F30 release/long-form gates are separate future work.

## F11 — Measured performance and provenance, offline slice (2026-11-24)

**Reconciliation before work.** HEAD `64395b0` (= origin/main, clean; includes the owner's 30-feature roadmap commits `34c6508`, `64395b0`). ComfyUI queue empty (GET `/queue`). `speckit.py --verify` → ready, no problems. Offline baseline: **196 passed, 1 deselected** (historical 193 superseded by the roadmap's doc tests).

**Spec Kit.** `create_new_feature.py --json --number 11 --short-name measured-gpu-benchmarks` → `specs/011-measured-gpu-benchmarks`; spec, checklist, plan, research, data-model, contracts/perf-cli.md, quickstart, tasks 9/11 (T010–T011 owner-gated).

**Built.**
- `VramSampler` keeps UTC-stamped samples and `render --sample-vram` now writes `RUN_DIR/vram_samples.json` (summary in the manifest unchanged + `samples_file`).
- `src/morph_studio/perf.py`: `analyze_samples` (gaps > 3× interval, coverage %, external baseline = median of samples before the first submission, peak/rise), `collect_stages` (exec from ComfyUI `/history`, wall = submitted→verified, overhead, reused detection by job creation time), `stage_window_peaks` (whole-GPU peak inside each fresh stage's submitted→completed window ±1 s), `build_report` (+ provenance: ComfyUI/PyTorch/GPU from snapshots, model SHA-256 from the hash cache or NOT MEASURED), `estimate` (median of matching measured history; NO DATA otherwise; `--extrapolate` labelled ESTIMATED-EXTRAPOLATED).
- `configs/perf_history.json`: 13 measured stages from MC-FLF2V-003 and MC-RUN-001..003 (reused stages excluded).
- CLI: `perf-report RUN_DIR`, `estimate STORYBOARD` — local files only.

**Results.** Offline **206 passed, 1 deselected**. `estimate configs/sequences/organic-machines.yaml` → orchid 19.4 s, butterfly 51.7 s, phoenix 51.7 s, bridges 496.0 s each, total **1,114.8 s ESTIMATED**. `perf-report outputs/repro/run-ba2d9dbedb6189be` (MC-RUN-003) → exec 20.2/51.8/49.9/496.0/494.1 s = 1,111.8 s MEASURED, per-stage overhead 0.1–1.8 s; VRAM summary-only (pre-F11 run, no timestamped samples → window peaks NOT MEASURED); Wan/UMT5 SHA-256 NOT MEASURED. Correction: MC-RUN-002 phoenix execution was 54.1 s (earlier note said 50 s).

**Blocked (owner approval):** T010 `models-hash --confirm-io` (≈37 GB disk read, idle queue); T011 sampled benchmark renders (cold/warm 832×480, 640×368 variant) — each ≈19 min of GPU. **Next:** F12 offline (anchor geometry contract) while F11 GPU items wait.

## F12 — Composition-aware anchors, offline slice (2026-11-24)

**Spec Kit.** `create_new_feature.py --json --number 12 --short-name reference-anchor-continuity` → `specs/012-reference-anchor-continuity`; spec, checklist, plan, tasks 7/8 (T008 owner-approved matched anchor set pending).

**Built.** `src/morph_studio/geometry.py`: FFmpeg-decoded 128×74 RGB, Otsu luminance mask on the dark background → centroid, robust extent, area, left-right mirror symmetry (frontal vs profile proxy), mean subject colour; `compare_geometry` flags `centroid_shift` (> 0.08), `scale_change` (extent ratio outside 0.75–1.33), `symmetry_drop` (> 0.15), `palette_shift` (> 60), `mask_unreliable`, `subject_too_small` — labelled heuristic, advisory (sets `review: required`, never rejects). The anchor chain records it in each child's `continuity.geometry`; `render` stores `anchor_geometry_flags` in the manifest and returns them at the review stop. CLI `anchor-check PARENT CHILD`.

**Real-data check (local outputs, not committed).**
| Pair | Flags | Key numbers |
|---|---|---|
| MC-RUN-001 butterfly vs orchid | scale_change, palette_shift | width ratio 0.70 (orchid mask includes the glass ring), colour distance 87 (intended blue→silver) |
| MC-RUN-001 **side-on phoenix** vs butterfly | **symmetry_drop** | symmetry 0.94 → 0.49 |
| MC-RUN-002 **frontal phoenix** vs butterfly | **scale_change** | symmetry 0.79 (passes); wingspan 1.41× wider (real) |
Would have flagged the side-on phoenix before its 8-minute bridge. Thresholds remain uncalibrated (F16).

**Results.** Offline **214 passed, 1 deselected**.

## Session handoff (2026-11-24, after F12)

- HEAD: see the F12 commit on `main`. Queue was empty at every check this session; no GPU job was started for F11/F12.
- F11 OFFLINE-PASS (`specs/011-…`), F12 OFFLINE-PASS (`specs/012-…`). F13–F30 PLANNED.
- **Needs owner approval:** F11 T010 Wan model hashing (`models-hash --confirm-io`, ≈37 GB read); F11 T011 sampled benchmark renders (cold/warm 832×480, 640×368; ≈19 min GPU each); F12 T008 candidate anchors for an approved matched set.
- **Next offline feature:** F13 (physical correspondence prompt compiler), then F15 (audio beats), F16 (QA calibration — needs owner-labelled frames), F21/F22.

## F11 T010 — Wan model SHA-256 (2026-11-24)

Owner approved in chat ("Approve both"). Queue idle; `models-hash --confirm-io --profile configs/profiles/wan22_flf2v.binding.json` → 23.7 s (files already in the OS cache), 35.6 GB:
- `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` `6122e79d55e0f235698d11d657f3b196c5273c830da00b2b013c5a048d5e6a42`
- `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` `5471a457b6ac404202a5fbe6c11595a3d5641fc766b00f38763f72303fffc21e`
- `umt5_xxl_fp8_e4m3fn_scaled.safetensors` `c3355d30191f1f066b26d93fba017ae9809dce6c627dda5f6a66eaa651204f68`
- `wan_2.1_vae.safetensors` `2fc39d31359a4b0a64f55876d8ff7fa8d780956ae2cb13463b0223e15148976b`
All model files used by MorphCurrent now have measured SHA-256 (cache `outputs/model_hashes.json`). Benchmark renders (T011) started afterwards.

## F13 — Physical choreography prompt compiler, offline slice (2026-11-24)

**Spec Kit.** `create_new_feature.py --json --number 13 --short-name physical-morph-choreography` → `specs/013-physical-morph-choreography`; spec, checklist, plan, tasks 6/7 (T007 fixed-seed GPU A/B pending).

**Built.** Storyboard transitions accept an optional `choreography` (correspondences source→target, ≤ 5 ordered phases, camera `static|slow_push|slow_pull|orbit_left|orbit_right|rising`, `keep_centered`, `keep_scale`, extra negatives). `src/morph_studio/prompt_compiler.py` compiles it deterministically into a positive prompt (prose + correspondences + sequence + camera + framing + continuity clause) and a negative prompt (continuity defaults + user terms, deduplicated), cleans control characters and caps each at 1,500 characters. Choreographed bridge tasks carry `negative_prompt`, which now reaches the Wan graph's bound negative node (78); un-choreographed bridges keep the export's default and the **plan hash of `organic-machines.yaml` is unchanged** (`ba2d9dbe…`), so MC-RUN reuse is preserved. CLI `prompt-preview STORYBOARD [--variants]` shows compiled prompts and a fixed-seed prompt-only A/B plan (nothing rendered).

**Results.** Offline **222 passed, 1 deselected** (golden prompts, dedup, length cap, schema errors, plan-hash regression, negative in the Wan graph via fake ComfyUI, CLI). **Next:** F11 benchmark results (running), then F15 audio beats.

## Roadmap: F31–F40 five-minute engineering film track (2026-11-24)

Owner request: ten more features (40 total) to plan a five-minute video about electrical and compute engineering morphing through images. Added F31–F40 to `docs/SPECKIT_FEATURE_LEDGER.md` (all PLANNED — NOT IMPLEMENTED): F31 concept bank, F32 five-act structure, F33 technical-accuracy review, F34 visual language, F35 long-chain drift control, F36 GPU budget/batching, F37 soundtrack/narration timing, F38 act transitions/titles, F39 batch review, F40 delivery. Planning estimate from measured history: ~75 bridges + 76 anchors ≈ 11.4 GPU-hours at 832×480, ≈ 6 at 640×368 (ESTIMATED; 81-frame cost NO DATA). No `specs/031+` folders created yet. CLAUDE.md, README, DEVELOPMENT, ARCHITECTURE and the doc test updated to 40 features. Tests: 222 passed.

## Current repository and film-roadmap reconciliation (2026-11-24)

- Inspected GitHub `main` at `882f58e0f35e5e0c1a08b3b3da67af0d72bc8083`, including the F31–F40 plan, F11 `perf.py`, F12 `geometry.py`, F13 `prompt_compiler.py`, working Wan/Qwen API exports and model hash documentation. Latest GitHub Windows CI for this head succeeded; commit states **222 offline tests passed**. No live GPU work or local ComfyUI probing was performed from this GitHub documentation audit.
- F11 **OFFLINE-PASS**, real spec `specs/011-measured-gpu-benchmarks`: Wan high/low, UMT5 and VAE hashes measured (T010 COMPLETE) in `docs/MODELS.md`; T011 benchmark renders were reported started but their final matrix is NOT VERIFIED in GitHub at this audit.
- F12 **OFFLINE-PASS**, real spec `specs/012-reference-anchor-continuity`: image geometry/scale/symmetry/colour heuristics work, but owner calibration/approval is pending. F13 **OFFLINE-PASS**, real spec `specs/013-physical-morph-choreography`: prompt compilation plus negative Wan input has offline tests; controlled fixed-seed GPU A/B remains unverified.
- F14–F30 and F31–F40 remain planned. Earlier PLANNED lines in this historical file are snapshots, **not** current F11–F13 statuses. The ledger/one-shot/README/constitution/development docs were updated to the 40-feature reality.
- Added P0–P3 film preproduction gates: offline 8–12-bridge pilot, bounded owner-approved GPU pilot, one fully reviewed act, then the five-minute film. Cost ~6–11.4 baseline generation GPU-hours is ESTIMATED, excluding rerenders, cold loads, reviewing and finishing. Five-minute baseline arithmetic: 75×65-frame bridges → 4801 deduplicated frames → 300 s anchor span / 300.0625 s playback at 16 FPS.
- **Cache validity correction:** replacing a reference-edited anchor invalidates its transitive edited descendants and associated morph bridges until a separate independent reanchor, **not** just its two adjacent bridges. Requires deterministic DAG invalidation tests in F19/F35/F39.
- **Next:** reconcile current local git/ComfyUI queue and F11 T011 results without running duplicate jobs; continue the next unblocked feature (F15 audio offline, F14 ladders after F13 or F16 QA with owner-labelled frames), and F31/F33 source-backed engineering research offline. No new GPU jobs were launched by this documentation review.

## F15 — Local music analysis and beat sync, offline slice (2026-11-24)

**Spec Kit.** `create_new_feature.py --json --number 15 --short-name local-audio-beat-mapping` → `specs/015-local-audio-beat-mapping`; tasks 6/7 (T007 real owner-licensed track pending).

**Built.**
- `src/morph_studio/audio.py`: local decode (WAV directly, other formats via FFmpeg; URLs refused), energy-flux onsets, autocorrelation tempo 60–200 BPM with smoothing and tempo-octave correction (accented bars otherwise give half tempo), confidence + half/double alternatives, phase-matched beat grid (centre of the tied phase run, wrap at t=0), downbeat guess, `sync_report` (bridge boundary vs beats: error ms/frames, cumulative drift, > 1 frame flagged).
- `src/morph_studio/audio_bands.py`: **visualizer-style band loudness** — independent Python implementation of classic music-visualizer band loudness (owner pointed to a local checkout, LGPL-2.1; no code copied): Hann-windowed 1024-point FFT per frame, bass/mid/treble 0–3.7/3.7–7.4/7.4–11 kHz, instant and `_att` values relative to the long-term average with frame-rate-adjusted decays (0.2/0.5 short, 0.9→0.992 long); `band_hits` (rising edges > 1.3); `render_timeline_png` (bass red, mid green, treble blue, beat ticks, bridge boundaries).
- Schema: `audio.licensed` must be true when `audio.file` is set; plan hash of the sample storyboard unchanged.
- CLI: `audio-analyze FILE`, `audio-sync STORYBOARD [--audio FILE]`, `audio-visualize FILE --out PNG [--storyboard]`.

**Results.** Offline **241 passed, 1 deselected**: click tracks at 90/120/140 BPM within ±1 BPM and beats within ±30 ms, 0.37 s offset, 22.05/44.1/48 kHz and stereo, silence, missing file, URL refusal, licence guard, 0 ms drift at 120 BPM, 110 BPM rounding flagged (−114 ms), bass kicks raise only bass, hi-hats only treble, steady tone ≈ 1.0. Demo visualization of a synthetic 120 BPM track: 119.9 BPM detected.

## F16 — Subject-aware QA and calibration, offline slice (2026-11-24)

**Spec Kit.** `create_new_feature.py --json --number 16 --short-name calibrated-qa-candidates` → `specs/016-calibrated-qa-candidates`; tasks 5/6 (T006 owner-labelled windows pending).

**Built.** `src/morph_studio/qa_subject.py`: per-frame subject metrics from a local 128×74 RGB decode (F12 mask area, centroid, Laplacian sharpness on the subject); detectors `subject_collapse` (area < 0.55× smaller endpoint for ≥ 3 frames), `subject_drift` (centroid > 0.12 off the endpoint-to-endpoint line), `blur_dip` (sharpness < 0.5× endpoint); `calibrate` (precision/recall by window overlap ± 4 frames). `qa.analyze_clip` now merges these flags (so `render` review and `--accept-heuristics` see them). `configs/qa_labels.json` seeds 4 real clips from documented observations. CLI `qa-calibrate [LABELS]`.

**Real-clip calibration (thresholds fixed before evaluation, not tuned to these labels):**
| Detector | TP | FN | FP | Precision | Recall |
|---|---|---|---|---|---|
| subject_collapse | 2 | 1 | 1 | 0.67 | 0.67 |
| subject_drift | 0 | 1 | 3 | 0.00 | 0.00 |
| blur_dip | 0 | 2 | 0 | — | 0.00 |
Caught: MC-FLF2V-003 petal collapse (frames 28–44) and MC-RUN-001 side-on bridge shrink (16–20) — both missed entirely by F08. Missed: MC-RUN-002 wing fold, the MC-RUN-001 right drift and both blur windows. The 3 drift "false positives" are in the side-on MC-RUN-001 bridge, where the subject arguably does drift (labels incomplete). Honest status: partial improvement; needs owner-labelled windows and a train/test split before tuning.

**Results.** Offline **247 passed, 1 deselected**.

## F11 T011 — GPU benchmark matrix (2026-11-24) → F11 GPU-VERIFIED

Owner approved ("Approve both"). Script ran sequentially with an idle-queue check before each run: `POST /free {"unload_models": true, "free_memory": true}` (16:26 UTC), then `render … --confirm-gpu --accept-heuristics --sample-vram --runs-root outputs/bench/{cold832,warm832,w640}` (the 640 run used a copy of the storyboard with only width/height changed).

| Run | Wall | GPU exec (anchors / bridges) | Whole-GPU baseline → peak |
|---|---|---|---|
| cold 832×480 | 16:26–16:44 (18.6 min) | 19.5 / 51.6 / 49.6 s · 496.5 / 493.7 s = **1,110.8 s** | 1,614 → 48,198 MiB |
| warm 832×480 | 16:44–17:03 (18.7 min) | 20.4 / 53.3 / 50.2 s · 496.8 / 491.7 s = **1,112.4 s** | 35,394 → 48,210 MiB |
| 640×368 | 17:03–17:13 (10.0 min) | 17.2 / 46.4 / 43.9 s · 241.0 / 239.0 s = **587.5 s** | 35,320 → 48,261 MiB |

Findings: (1) no measurable cold-start penalty — model loads are cheap with the weights in the OS file cache; (2) 640×368 bridges are 2.06× faster than 832×480 while having 0.59× the pixels, anchors ~11% faster; (3) the ~35 GB "baseline" seen in every earlier run is **ComfyUI's own cached models** (it drops to 1.6 GB after `/free`), so earlier notes attributing it to other apps were wrong; peak ≈ 48.2 GB in every run because ComfyUI fills free VRAM — not a minimum requirement; (4) cold and warm 832 outputs are byte-identical to MC-RUN-002 (third and fourth identical reproduction); (5) the 640 run stopped for review because the new F16 detector flagged drift in frames 56–58 and F12 flagged the butterfly's palette — expected behaviour, not joined.

History: `configs/perf_history.json` now holds 28 measured stages. `estimate` → 1,115.0 s (832×480) and 585.6 s (640×368) for the sample storyboard. Five-minute film (F31–F40, ≈ 75 bridges + 76 anchors): ≈ **11.4 GPU-hours at 832×480, ≈ 5.9 at 640×368** — confirmed by these runs.

## Music asset: Mozart Symphony No. 40, I (2026-11-24)

Owner approved: "approved for symphony 40, compress and add to repo with licesne tracking info". Source: Musopen Kickstarter recording (Musopen Symphony, 2012). Licence verified via the Commons API — recording `PD-author` (Musopen), composition `PD-old` (Mozart d. 1791); Internet Archive marks it Public Domain Mark 1.0. Commons' upload server returned HTTP 429, so the identical FLAC (SHA-1 `379ad65b…cac5`, matching Commons and the Internet Archive) was downloaded from the Internet Archive item cited as its source, into an isolated scratch folder. Encoded with FFmpeg/libopus 128 kbps → `assets/music/mozart-symphony-40-i-molto-allegro-musopen.opus` (5,968,413 bytes, 5:58.8, SHA-256 `56ca0909…e5f5`), full movement, tags embedded. Provenance: `assets/music/mozart-symphony-40-i-molto-allegro-musopen.json`; listing `assets/music/README.md`; `.gitignore` allows only `assets/music/*.opus`; test `tests/test_music_assets.py` checks hash/size/licence/README. First analysis with the F15 analyzer: 203.3 BPM (alternative 101.6), confidence 0.30 — weak, motivating the classical-music rework that follows. Tests: 248 passed.

## F15 rework — one beat analyzer for any music, modelled on a reference music visualizer (2026-11-24)

Owner requests: "rework the beat detection feature using a reference music visualizer as an example … to work with classical music", then "the beat detection should work with any type of music, not a style switch". Implemented as **one pipeline** (`src/morph_studio/beat_analysis.py`, used by `analyze_audio`; the old fixed-grid internals were removed), modelled on a reference music visualizer's historical `BeatDetect.cpp` (Patin statistical energy method; read in a local checkout history at `c1273ec9b^`; LGPL-2.1 — independent reimplementation, no code copied):
- 16 log-spaced sub-bands (60 Hz–5.5 kHz), each frame's energy as a log-ratio to the band's primed ~1.3 s running history (quiet passages count like loud ones);
- one global tempo octave (autocorrelation summed over 8 s windows × perceptual prior at 110 BPM, then a sub-multiple check for accented/periodic material), local tempo within ±25 % for rubato;
- DP beat tracking that follows the local tempo and always links; BPM from the median inter-beat interval; window-centre time stamps (click bias measured at −22 ms before the fix);
- section/phrase boundaries from loudness + brightness novelty, drawn amber in `audio-visualize`.

**Tests (same analyzer for all):** click tracks 90/120/140 BPM (±1 BPM, beats ±30 ms, 0.37 s offset, accented downbeat, 22.05/44.1/48 kHz, stereo, silence) and new classical-style fixtures — soft-attack notes with an accelerando 90→110 BPM (beats within one 16-fps frame of the attack midpoint, rising tempo curve), a ~30 dB *pp*→*ff* swell (quiet-part beats kept), loud/quiet/loud sections (boundaries within ±1.5 s). Offline suite **251 passed, 1 deselected**.

**Mozart Symphony No. 40/I (committed recording), 8 s analysis:** before — 203 BPM, confidence 0.30, fixed grid; first unified attempt — octave flips (100 ↔ 207–225 BPM) broke beat tracking (only the last 30 s had beats), fixed by the global octave + always-link DP. Now: **215 BPM** quarter-note pulse (half notes ≈ 107), tempo spread 21 BPM, **1,288 beats** across the whole movement, inter-beat interval median 0.279 s (p10–p90 0.255–0.302 s), 10 section boundaries (23.4, 48.3, 79.4, 134.2, 162.7, 179.4, 266.5, 304.1, 322.9, 352.7 s) aligned with visible forte→piano changes. Not yet checked against a hand-tapped reference (owner listening check pending).

## F14 — Intermediate anchors and morph ladders, offline slice (2026-11-24)

**Status checks first:** music licence files are committed and on `origin/main` (`assets/music/*.opus|.json|README.md`, `8cba3d3`); the F11 benchmark matrix is complete (BENCH-001, F11 GPU-VERIFIED); no GPU job running.

**Spec Kit.** `create_new_feature.py --json --number 14 --short-name adaptive-transition-ladders` → `specs/014-adaptive-transition-ladders`; tasks 7/8 (T008 reviewed multi-hop render pending GPU approval).

**Built.** `src/morph_studio/ladder.py`: `prompt_distance` (content-word Jaccard), `transition_risk` (0–1 with reasons: prompt distance + F12 geometry flags), `risk_report`; `propose_ladder` splits one adjacent transition into N (≤ `--max-new`, default 3) reference-edit intermediate anchors with deterministic "x% of the way from (A) toward (B)" prompts, derived seeds, re-pointed references, beats split into valid 4n+1 segments (refuses segments below Wan's minimum), choreography copied to segments, schema-validated; added GPU time from measured history (NO DATA when a segment length has never been measured; `--max-gpu-s` then refuses rather than guessing). `write_proposal` writes a new YAML with a lineage header (source SHA-256, split, estimate). CLI `ladder-risk STORYBOARD [--run RUN_DIR]`, `ladder-propose STORYBOARD --split A->B [--steps N] --out NEW.yaml`.

**Real check.** `ladder-risk configs/sequences/organic-machines.yaml --run outputs/runs/run-ba2d9dbedb6189be` → orchid→butterfly 0.75 high (prompt distance 0.83, scale_change, palette_shift), butterfly→phoenix 0.72 high (0.95, scale_change). Both read "high" although orchid→butterfly rendered acceptably — the prompt-distance term is coarse; calibrate with owner-reviewed outcomes (F16 labels) before relying on the levels.

**Results.** Offline **258 passed, 1 deselected**. A 1-step split of butterfly→phoenix yields two 33-frame segments (unique movie frames 129 = 1 + 64 + 32 + 32).

## F21 — Style packs and private asset collections (2026-11-24)

Owner reiterated: keep working autonomously through all features until done (now in CLAUDE.md, `245bba8`).

**Spec Kit.** `create_new_feature.py --json --number 21 --short-name style-packs-asset-library` → `specs/021-style-packs-asset-library`; tasks 6/6.

**Built.** `src/morph_studio/styles.py`: strict `StylePack` (id slug, version, `extends`, description, palette, lighting, lens, composition, materials, negative, advisory size, reference assets with SHA-256 + licence); parent-first resolution (scalars override, negatives merge in order without duplicates, palette replaces; cycle/unknown-parent/unsafe-id errors); canonical pack SHA-256 and lineage; deterministic style clause appended after the artist's prompt (never rewritten); `apply_override`; read-only `check_assets` (ok / missing / changed / unsafe) against a gitignored `library/`. Schema: `style.pack`, `anchors[].style_override`. DAG: when a pack is used, anchor tasks carry the styled prompt, merged negative, `style_pack` and `style_sha256` (so editing a pack invalidates the plan); without a pack nothing changes (sample plan hash still `ba2d9dbe…`). CLI `style-list`, `style-show ID`, `style-check ID`. Example packs for the F31–F40 film: `configs/styles/engineering-noir.yaml` and `engineering-noir-power.yaml` (extends it: warmer palette/lighting, extra negative).

**Results.** Offline **266 passed, 1 deselected**, including the ledger's acceptance case: three linked scenes share `engineering-noir` with one per-scene lighting override (only that scene's hash and prompt change). **Next feature:** F22 (creative brief → editable storyboard).

## F22 — Creative brief → editable storyboard (2026-11-24)

**Spec Kit.** `create_new_feature.py --json --number 22 --short-name story-brief-to-storyboard` → `specs/022-story-brief-to-storyboard`; tasks 5/6 (T006 optional local-LLM drafting deferred; disabled by design).

**Built.** `src/morph_studio/brief.py`: strict `Brief` (title slug, 2–200 scenes with subject/details/morph hint cleaned of control characters, duration, bpm, style pack, render size/fps, seed) and `plan_storyboard`: first anchor text-to-image, the rest reference edits of the previous anchor ("Transform the subject into …; keep the same framing, scale, background and lighting"), transitions with F13 choreography (static camera, centred, same scale, subject→subject correspondence, the brief's morph hint in the prompt), equal beat budgets mapped to valid 4n+1 lengths, derived seeds, readable unique ids. Refuses durations that cannot be met (below the 5-frame minimum, or above `max_bridge_frames` — suggests `ladder-propose`). CLI `brief-plan BRIEF --out STORYBOARD.yaml` (never overwrites) prints scene list, frames/seconds per bridge, residual, unique frames, F11 estimate (or NO DATA) and blocked profiles. No model or node names are generated.

**Film pilot.** `configs/briefs/engineering-pilot.yaml` (8 scenes: lightning → Leyden jar → voltaic pile → dynamo → transformer → vacuum tube → transistor → IC die, 32 s, `engineering-noir`) → `configs/sequences/engineering-pilot.yaml`: 8 anchors, 7 × 73-frame bridges, 31.5 s anchor span, 505 unique frames; `render … --dry-run` → ready, nothing blocked. GPU estimate NO DATA (73-frame bridges never measured) — a short measured run would calibrate it.

**Results.** Offline **272 passed, 1 deselected**. **Next feature:** F23 (camera/framing keyframes) or F17 (scheduler) — continuing autonomously.

## F17 — Queue- and budget-aware execution (2026-11-24)

**Spec Kit.** `create_new_feature.py --json --number 17 --short-name vram-aware-job-scheduler` → `specs/017-vram-aware-job-scheduler`; tasks 6/7 (T007 owner-approved bounded multi-session batch pending).

**Built.** `src/morph_studio/scheduler.py`: `RunLock` (exclusive `outputs/runs/.morphcurrent-gpu.lock` with pid/host/heartbeat; second GPU render refused with the holder's details; heartbeat older than 30 min = stale and taken over, logged; released in `finally`; validation-only runs never lock); `Budget` (caps on *new* GPU submissions and F11-estimated GPU seconds; checked before submitting; cached/verified stages free; unknown cost under a finite cap stops rather than guesses; heartbeats the lock); `schedule_preview`. Hooks in `run_anchor_chain` / `run_bridge_stage` (`job_is_verified` skips budget for finished stages). `render --max-jobs N --max-gpu-s S` → `paused_budget` (exit 8) naming the next task; re-running continues. CLI `schedule STORYBOARD [--max-gpu-s] [--max-jobs]`.

**Results.** Offline **279 passed, 1 deselected**: lock contention/stale takeover/heartbeat; budget rules; E2E with fake ComfyUI + real FFmpeg clips — `--max-jobs 2` → 2 prompts, paused at `anchor:phoenix`; again → 4; uncapped → 5 total (no duplicates); concurrent GPU render refused while locked with zero prompts. For the five-minute film this allows bounded sessions (e.g. `--max-gpu-s 7200`) that resume where they stopped.

## F19 — Long-form sequencing, edit invalidation and storage limits (2026-11-24)

**Spec Kit.** `create_new_feature.py --json --number 19 --short-name resumable-longform-timeline` → `specs/019-resumable-longform-timeline`; tasks 7/8 (T008 owner-approved bounded multi-scene GPU resume pending). (Implemented before F18; owner then asked for strict numerical order, so F18 is next.)

**Built.** `src/morph_studio/longform.py`: `stage_identities` (Merkle over inference-relevant fields, profiles and dependency identities; timing-only and chapter fields excluded), `plan_diff` (cached / rerun direct | upstream:<task> | added; removed; renamed-but-identical stages stay cached), `chapter_index` + `ffmetadata`, `proxy_storyboard` (640×368, `-proxy`), `plan_bytes`/`disk_preflight` (measured 0.42–0.49 MB anchor PNG and 0.73–1.38 MB 65-frame MP4, rounded up, ×2 for ComfyUI's copy), `storage_report`. Schema `anchors[].chapter` (contiguous; absent keeps plan hashes). `render --min-free-gb` → `blocked_disk` (exit 9) before lock/submission. CLI `plan-diff`, `timeline`, `storage`.

**Results.** Offline **298 passed, 1 deselected**. Fake-ComfyUI E2E: predicted re-runs equal new submissions — last-anchor seed edit 2, reference-parent edit 4 (lineage), bridge-prompt edit 1; with byte-identical outputs actual ≤ predicted. 10-anchor chain under random `--max-jobs 1..4` interruptions finishes with exactly 19 submissions. 2/10/50-anchor plans deterministic, topological, < 2 s. Sample plan hash unchanged.

## F18 — Local creative review experience (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 18 --short-name local-creative-review-ui` → `specs/018-local-creative-review-ui`; then `speckit-specify` (checklist 16/16), `speckit-clarify` (3 questions resolved from owner rules: default plan storyboards, concurrent review writes, no request logs), `speckit-plan` (research incl. the ledger-required loopback-vs-native design review, data-model, contracts, quickstart), `speckit-tasks` (17 tasks), `speckit-analyze` (0 CRITICAL/HIGH; 3 coverage gaps folded into tests), `speckit-implement`, then the converge loop: pass 1 appended T018–T020 (final-movie path resolved inside the run dir regardless of cwd; plan Constitution Check updated for v2.0.0 VIII/IX; corrupt-file error-page test), all implemented; pass 2 converged. Tasks 19/20 (T017 owner walkthrough pending).

**Built.** `src/morph_studio/review_ui.py` (stdlib only): `run_view` (stage states, media allowlist tokens, missing-media marking), `list_runs`, page builders, `apply_review` (bridge-only, decision enum, note ≤ 500, reuses `qa.record_review`), `plan_summary`/`render_plan_page`, `default_storyboards`, threaded handler (Host check, per-process CSRF token + Origin, 10 kB form cap, Range 206/416, CSP/nosniff/DENY headers, no request logging) and loopback-only `make_server` (IPv4/IPv6). CLI `review-ui [--runs-root] [--host] [--port] [--storyboard] [--repo-root]` (exit 2 for non-loopback host).

**Results.** Offline **314 passed, 1 deselected**; `tests/test_review_ui.py` 16 tests incl. a live server on an ephemeral port: UI/CLI review parity, refusals (anchor/unknown task, bad decision, foreign Host/Origin, bad token, oversize form, traversal/unknown media), Range seeking, escaped storyboard/manifest injection, labelled controls without positive tabindex, no ComfyUI/render import, run page < 1 s. Real runs on disk (run-ba2d9dbe…, run-cefb16ae…) render 3 anchors, 2 clips, contact sheet and final movie in 6–17 ms; `review-ui --port 0` smoke: 2 runs and 2 plans listed, plan page 200. Constitution amended to v2.0.0 during this feature.

## Retroactive Spec Kit converge loop: F17, F19, F21, F22 (2026-11-24)

These four features were built with hand-written spec/plan/tasks before the owner made the full Spec Kit workflow and converge loop mandatory (constitution v2.0.0). `speckit-converge` was run on each in a loop until clean:

- **F17** pass 1 → T008–T012: the run lock now heartbeats before every new GPU submission even without caps (previously an uncapped render > 30 min could look stale and be taken over — a real cross-process safety gap); `paused_budget` budget summary recorded in the manifest; cached-under-`--max-jobs 0` test; plan API and nine-principle Constitution Check aligned. Pass 2 converged.
- **F19** pass 1 → T009–T011: disk preflight now treats stages verified by *earlier* runs (via `run-*/plan.json` Merkle identities) as cached, so edits are no longer over-charged; `disk_usage` resolved at call time; CLI exit 9 tested; Constitution Check. Pass 2 converged.
- **F21** pass 1 → T007–T008: `render --dry-run` reports a style-pack size advisory when it differs from the storyboard (never applied); Constitution Check. Pass 2 converged.
- **F22** pass 1 → T007–T009: `brief-plan --llm` disabled extension point refused with a clear message (exit 2, nothing written); plan API aligned; Constitution Check. Pass 2 converged. T006 (local LLM drafting) remains owner-gated.

Offline **319 passed, 1 deselected**.

## F22 amendment — Claude Desktop pre-drafting replaces local LLM (2026-11-24)

Owner decision: no local LLM prompt drafting (the approved Qwen3-8B + llama.cpp download was cancelled before it started; nothing was downloaded). All sequences, briefs and prompts are pre-drafted as text in Claude Desktop sessions and validated locally.

- Spec/plan/tasks amended (US3 rewritten; FR-005 `draft-check`, FR-006 `drafted_by`); T006 cancelled; T010–T014 implemented; converge pass 1 → T014 (brief-text scan test), pass 2 converged.
- `brief.lint_draft` + CLI `draft-check FILE` (exit 0 / 3): schema + compiled plan + bridge count/duration; errors for model files, checkpoints/model names, LoRA, ComfyUI/workflow internals and URLs in creative text (field path named); warnings for `independent_t2i`, missing choreography correspondences, prompts > 600 chars. `Brief.drafted_by` → storyboard header only (plan hash unchanged). `brief-plan --llm` removed.
- `docs/DRAFTING.md` drafting guide + session prompt; CLAUDE.md, ledger, ARCHITECTURE and one-shot updated.
- Real drafts: pilot brief 0 errors/0 warnings (31.5625 s); `organic-machines` 0 errors/2 warnings (no correspondences); `engineering-pilot` storyboard 0/0.

## F20 — Production acceptance and reproducible replay (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 20 --short-name release-reproducible-pipeline` → `specs/020-release-reproducible-pipeline`; `speckit-specify` (16/16), `speckit-clarify` (3 resolved: licence provenance = same-stem JSON with licence + source; forbidden-file lists; frame equivalence ≤ 1.0 informational), `speckit-plan` (research, data-model, contracts, quickstart), `speckit-tasks` (15), `speckit-analyze` (0 CRITICAL/HIGH; 2 LOW folded into T012), `speckit-implement`, converge loop (pass 1 → T016–T018: replay-with-consent fake-ComfyUI test (5 fresh submissions, stages identical), replay exit codes follow `render`, restore rolls back on mid-way failure; pass 2 converged).

**Built.** `src/morph_studio/release.py` + CLI `run-compare` (exit 0 reproduced / 10), `replay` (empty runs root required; validate-only without `--confirm-gpu`), `audit` (exit 11 on errors), `run-backup` / `run-restore`, `acceptance [--all]`.

**Real evidence.** `run-compare` MC-RUN-002 run vs fresh-root MC-RUN-003 (`outputs/repro`) and BENCH-001 cold/warm 832×480: **reproduced, 6/6 stages byte-identical**; vs MC-RUN-001 (older phoenix plan): `differs`, exactly phoenix anchor, its bridge and the final movie. `audit`: 0 errors, 0 warnings, 10 recorded model SHA-256s listed, 327 ms, no weights hashed. Real `run-backup` of run-ba2d9dbe… (22 files, 5.9 MB) → `run-restore` → `run-compare`: reproduced 6/6. `acceptance`: 8 of F01–F20 evidenced, 12 with open owner/GPU gates → `release_ready: false` (no tag). Offline tests: 16 in `tests/test_release.py`; full suite 344 passed (after fixing an intermittent F18 review-UI 413 race: the server now drains oversized form bodies before replying; 8/8 repeated runs green).

## Film length: full song, not five minutes (2026-11-24)

Owner decision: the F31–F40 film's visuals run the **full length of the song**; five minutes was only a recommendation and the film may run longer. For the licensed Mozart track (358.822 s): N = ceil((song_s × fps − 1)/(L − 1)) → **90 × 65-frame bridges + 91 anchors**, 5761 unique frames, 360 s anchor span, 360.0625 s nominal playback (≈ 1.2 s past the music); 81-frame alternative 72 + 73 (cost NO DATA). ESTIMATED ≈ 13.7 GPU-hours at 832×480, ≈ 6.9 at 640×368 (measured rates). Updated: ledger (F31–F40 goal, planning numbers, duration check, F31/F32/F34/F39/F40 text, proposed spec folders `032-full-song-act-structure`, `040-full-song-film-delivery`), ARCHITECTURE, CLAUDE.md, one-shot, DEVELOPMENT, README, pilot brief, F14/F18/F20 scale notes, doc tests; constitution amended to **2.0.1** (PATCH, Principle IX wording).

## Musically synchronized film plan (2026-11-24)

Owner direction: plan how the film synchronizes to the music. Ledger gains **"Music synchronization design"** (F31–F40 track): grounded in the F15 analysis of the Mozart recording (358.8 s; 215.4 BPM, 107.7 half-note alternative → bar ≈ 1.11 s; ±21 BPM rubato; low beat confidence 0.215; 10 section boundaries), anchors land on **owner-verified downbeats from a hashed beat map** (`configs/beatmaps/`), one bridge per 4-bar phrase by default (≈ 4.46 s → 73 frames; allowed 33–81 frames with split/merge rules; denser 2-bar bridges in climaxes), absolute frame targets f_k = 4·round(t_k·fps/4) so every anchor is within 2 frames (125 ms) with **no cumulative drift**, acts on music sections (sonata form), head/tail holds added at join time, F25 must preserve anchor timestamps, and an **animatic** (stills cut on downbeats + music) is the owner's first listening check before any bridge. Planning numbers: ≈ 80 bridges + 81 anchors, ≈ 13.5 GPU-h at 832×480 / ≈ 6.8 at 640×368 (73-frame cost EXTRAPOLATED; measure in P1); fixed-grid 90-bridge baseline kept as upper bound. Feature placement (numerical order preserved): **F32** = beat map + beat-locked timeline (deps now include F15); **F37** (now P0) = sync verification, beat-map review tools, animatic, audio mux, narration, captions; F25, F36, F38 updated. ARCHITECTURE, CLAUDE.md, one-shot, README and doc tests updated.

## rc1 release, bounded replay (MC-RUN-004) and F18 walkthrough (2026-11-24)

- **Release:** owner-approved annotated tag `v0.1.0-rc1` on `b932ec8` pushed (no AI attribution).
- **Replay (owner-approved, idle queue):** `replay configs/sequences/organic-machines.yaml --reference outputs/runs/run-ba2d9dbedb6189be --runs-root outputs/replay-rc1b --confirm-gpu` recomputed all 5 stages (1,109.3 s GPU: anchors 20.1/51.3/49.1 s, bridges 495.8/492.9 s) byte-identical to MC-RUN-002. Preparing it exposed a F20 bug (validation-only replay wrote a manifest into the fresh root) — fixed in `912fd3b`.
- **F18 walkthrough (in-app browser, keyboard):** index → plan view (3 anchors, 2 bridges, 8.0625 s, 1,115 s estimate, profiles present) → run page (contact sheet, anchors, both clips 832×480 4.0625 s playing) → approved both bridges with notes (clips byte-identical to the owner-approved MC-RUN-002 clips; bridge 1 carries a newer F16 `subject_collapse` 43–45 flag) → `render … --confirm-gpu` joined with **0 new ComfyUI prompts** → `run-compare` vs MC-RUN-002: **reproduced 6/6 incl. final movie `ce687958…`** → final movie plays in the UI. Walkthrough found and fixed three F18 issues (T021–T023): real-browser approvals returned **403** because `Referrer-Policy: no-referrer` makes Chromium send `Origin: null` (now `same-origin`), raw dict QA flags (now readable), identical "Note" labels (now bridge-specific). Ledger: F18 and F20 → GPU-VERIFIED; EXPERIMENTS gains MC-RUN-004.

## F23 — Camera moves and framing consistency (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 23 --short-name camera-framing-keyframes` → `specs/023-camera-framing-keyframes`; specify (16/16), clarify (3 resolved: numeric satisfiability thresholds reusing F12 `CENTROID_MAX`/`EXTENT_RANGE`; separate `camera` field vs choreography camera; 9:16 crop + 5% safe area), plan (research confirmed the Wan FLF2V graph has no camera node), tasks (14), analyze (0 CRITICAL/HIGH; 2 LOW folded in), implement, converge loop (pass 1 → T015: graph camera control is checked against the workflow named by the active Wan profile and always refused — "no camera input" or "camera node present but unbound until F27"; pass 2 converged). Tasks 14/15 (T014 operator two-bridge GPU test pending).

**Built.** Schema `CameraMove` (`transitions[].camera`: move, amount 0–0.5, control prompt|graph), `FramingTarget` (`anchors[].framing`), `render.delivery_crops`; `camera.py` (`camera_clause`, `graph_camera_nodes`/`require_graph_control`, `satisfiability`, `framing_check`, `crop_check`, `camera_check`); prompt compiler appends the clause; DAG records `camera {move, amount, clause, label}` only when set (sample plan hash unchanged); CLI `camera-check STORYBOARD [--run RUN]` (exit 12 on issues). Implementing it surfaced a Windows bug: non-ASCII reason text crashed cp1252 consoles/redirects — reasons are now ASCII and the command prints ASCII-escaped JSON (regression test).

**Evidence.** `camera-check` on the real MC-RUN-002 anchors (420 ms): both transitions static-**satisfiable** (orchid→butterfly ratio 0.848, shift 0.070; butterfly→phoenix ratio 1.243, shift 0.053). Tests: 10 in `tests/test_camera.py`; full suite 356 passed.

## F24 — Temporal shape continuity and repair (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 24 --short-name temporal-shape-stability` → `specs/024-temporal-shape-stability`; specify (16/16), clarify (3 resolved, incl. **all detector thresholds fixed before evaluation**, endpoint tolerance, anchor split rule), plan, tasks (14), analyze (0 CRITICAL/HIGH; 1 LOW folded in), implement, converge loop (pass 1 converged). Tasks 13/14 (T014 owner-approved controlled repair render pending).

**Built.** `src/morph_studio/continuity.py`: clip-level mask threshold (centred Otsu of the endpoints — plain Otsu put two-tone thresholds just above black, turning a brightened background into "subject"), per-frame occupancy, overlap with the previous mask, connected parts, background change, centre and colour; flags `shape_substitution`, `topology_change`, `background_change`, `motion_jump`, `colour_jump`; `evaluate` (F24 + F16 detectors vs labels: by-kind recall, any-detector window recall, misses, unlabelled flags); `propose_repair` (refinements per kind incl. F16 kinds, intermediate anchor at a valid 4n+1 split, controlled-comparison spec, nothing rendered); `compare_repair` (equal length, endpoint grey MAD ≤ 2.0, removed/persisting/new, capped verdict). CLI `continuity` (exit 13), `continuity-eval`, `repair-propose RUN TASK --out`, `repair-compare` (exit 14 unless candidate improvement).

**Evidence (real labelled clips, thresholds fixed beforehand).** By kind: collapse 2/3, drift 0/1, blur 0/2. Any detector in the labelled window: collapse 2/3, drift 1/1, blur 2/2 (on MC-RUN-001 orchid→butterfly the new detectors fire inside the drift/blur window as shape substitution at 44/46 and a motion jump at 43). 4 unlabelled flags. Misses listed in the report. 0.6 s per 65-frame clip. Tests: 11 in `tests/test_continuity.py`; full suite 367 passed (one unreproduced intermittent failure in a pre-commit run — 3 subsequent full runs green; suspect the wall-clock assertions in the scale/audit tests under load).

## Layered music-sync foundation — F15 US5 (2026-11-24)

Owner direction: real-time music visualizers sync to any song without beat detection; study how audio becomes visual data and build a deeper sync strategy, then implement it next. Analysis and strategy in `docs/MUSIC_SYNC.md` (self-normalized band energies with attack/release envelopes, onsets as the only events, continuous energy→motion mapping → MorphCurrent layers: acts from sections, event-locked anchors with beats optional, bridge character, energy-warped playback, optional finishing pulses). Owner also asked that the reference project not be named anywhere: all mentions were removed from the tree and from **all of git history** (filter-branch over 86 commits; verified 0 mentions in files, messages and tags; owner force-pushed `main` and the re-pointed `v0.1.0-rc1`/`v0.1.0-rc2`; local backup refs removed and pruned). Constitution 2.0.2 (PATCH wording).

**Spec Kit.** F15 spec updated in place (US5, FR-006–FR-010, SC-004/005), clarify (event scoring, planner objective, character thresholds, warp method), plan section, tasks T012–T020, analyze (0 CRITICAL/HIGH; 2 LOW folded in), implement, converge (pass 1 → T016 frozen-stretch test; pass 2 converged). Tasks 15/16 (T015 owner look review pending).

**Built.** `src/morph_studio/sync_features.py` (`feature_track`, `track_record`, `events`, `plan_anchors`, `bridge_character`, `energy_warp`, `sync_plan`); `audio_bands.band_levels(on_frame=…)` callback (no output change); CLI `audio-features FILE --out [--fps]`, `sync-plan FEATURES --out [--preferred] [--beatmap]`. Implementation findings recorded in the spec: onsets register up to half a frame late (grid ties go to the earlier point); noise passed the MAD onset test (added a 3× median-flux floor); clamped warp speeds must stay re-eligible (water-filling); `fps` normalized to float for stable hashes; **real-track calibration** — un-normalized scores packed 129 bridges averaging 45.5 frames (~1.6× GPU cost), so scores were normalized to ≤ 1 and the length weight raised to 1.5.

**Evidence (Mozart 40/I, 358.8 s).** Feature track 5,741 frames + 11 sections in 27 s (hash `d40b8787…`); plan in < 1 s: **95 bridges (37–81 frames, mean 61.4), 96 anchors, 75 on musical events** (67 energy peaks, 5 onsets, 3 section starts), hold 0.06 s, character mix settling 41 / building 30 / treble-heavy 28 / steady 17 / bass-heavy 7, warp speeds 0.5–2×. Soft classical attacks yield few strong onsets, so phrase energy peaks carry most anchors — the visualizer lesson that energy works where beats and onsets are weak. Tests: 7 in `tests/test_sync_features.py`.

## F25 — Delivery frame rates and energy-warped retiming (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 25 --short-name optical-frame-interpolation` → `specs/025-optical-frame-interpolation`; specify (16/16), clarify (encoding, filter definitions, warp-to-timing method), plan, tasks (15), analyze (0 CRITICAL/HIGH; 2 LOW folded in), implement, converge (pass 1 → T016 frozen-stretch test; pass 2 converged). Tasks 15/16 (T015 owner look review pending).

**Built.** `src/morph_studio/interpolate.py`: `convert` (repeat `fps`, blend `framerate`, motion `minterpolate` mci/aobmc/bidir with scene detection; new file via `.part` + rename; `.interp.json` with checksums, filter, FFmpeg version, durations and **anchor-mark alignment** — exact at 24/48/60, half-second marks at 30; input re-hashed to prove it is unchanged; blend/motion fall back to repeat across hard cuts), `anchor_alignment` (exact `Fraction` maths), `warp_times`/`apply_warp` (ffconcat per-frame durations → constant 16 fps, endpoints/duration pinned, `.warp.json`). CLI `interpolate INPUT --fps --method --out`, `warp-apply CLIP --map|--plan --bridge --out`. Finding: motion-compensated interpolation cannot synthesize frames after the last source frame (output 0.1 s short); a two-frame clone pad before interpolation plus a trim to the input duration makes every method duration-exact.

**Evidence.** MC-RUN-004 final movie → 24 fps blend in 2 s: 8.0625 → 8.083 s (within one frame), **33/33 anchor marks exact**. Real Mozart energy warp (37 s window, speeds 0.5–2×) applied to the real orchid→butterfly bridge: 65 → 65 frames, 4.0625 s, endpoints exact, 1 s. Tests: 12 in `tests/test_interpolate.py`; full suite 386 passed.

## Restart point (2026-11-24, after F25)

- HEAD `9f1bce5` on `main` (pushed). History rewritten earlier today (no reference-visualizer mentions); GitHub `main` and tags `v0.1.0-rc1` → `01aaf62`, `v0.1.0-rc2` → `6200847` verified. Offline suite 386 passed.
- Done through: F01–F25 at the levels in the ledger (F15 extended with US5 music-sync foundation; F22 uses Claude Desktop pre-drafting). Next feature in numerical order: **F26 (upscale and visual finishing)**, then F27–F30, then F31–F40.
- Workflow per feature (CLAUDE.md / constitution 2.0.2): create_new_feature → speckit-specify → clarify → plan → tasks → analyze → implement → converge loop until clean → ledger/PROGRESS → commit (no AI trailers) → push.
- Owner-gated items pending: GPU tests listed per feature in each `specs/*/tasks.md` "Blocked / owner" section; owner look reviews (F18 walkthrough done; F25 T015, F24 T014, F23 T014).

## F26 — Local resolution enhancement and finishing (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 26 --short-name upscale-visual-finishing` → `specs/026-upscale-visual-finishing`; specify (16/16), clarify (fit/fill geometry, step settings, identity tolerance and gain bounds), plan, tasks (15 + T016), analyze (owner's mid-feature approval of a 1080p learned upscaler recorded as gated T016), implement, converge (pass 1 converged). Tasks 14/16 (T015 owner review; T016 download consent + workflow export).

**Built.** `src/morph_studio/finishing.py`: `geometry` (832×480 → 1080p fit 1872×1080 + 24 px pads; fill 1920×1108 − 14 px crop; 1440p fit 2496×1440 + 32), `chain` (optional `hqdn3d`, `deblock`, colour gains, Lanczos `scale`, `pad`/`crop`, optional `unsharp`), `colour_gains`, `finish` (`.part` + rename, bt709 tags, `.finish.json` with checksums/chain/codec/colour space/bit depth/time/device; refuses overwrite and downsizing; audio copied), `identity_check` (first/last frames mapped back; cropped strips excluded in fill mode), `upscale_models` (read-only) and `require_owner_approval`. CLI `finish INPUT --target --mode [--denoise --deblock --sharpen --match-anchor] --out`, `finish --list-models`.

**Evidence.** MC-RUN-004 final movie → 1920×1080 fit+sharpen in 0.97 s and fill in 0.96 s; 129 frames preserved; identity MAD 0.84/0.96 (fit), 0.72/0.82 (fill) vs tolerance 4. No learned upscalers installed. ComfyUI core has `UpscaleModelLoader`, `ImageUpscaleWithModel`, `ImageScale`, `LoadVideo`, `GetVideoComponents`, `CreateVideo`, `SaveVideo`. **Owner approved a 1080p learned upscaler**; recommended `RealESRGAN_x2plus.pth` (BSD-3-Clause, 67,061,725 bytes, official release) — download awaits explicit consent, then the owner's API export `workflows/04_upscale_x2.json` (T016). Tests: 9 in `tests/test_finishing.py`; full suite 395 passed.

## Learned upscaler downloaded (owner consent, 2026-11-24)

Owner approved a 1080p learned upscaler and the download. `RealESRGAN_x2plus.pth` (BSD-3-Clause) fetched from the official xinntao/Real-ESRGAN v0.2.1 release into `C:\AI\ComfyUI_windows_portable\ComfyUI\models\upscale_models\` via `.part` + rename; size 67,061,725 bytes matched the release metadata; SHA-256 `49fafd45f8fd7aa8d31ab2a22d14d91b536c34494a5cfe31eb5d89c2fa266abb` recorded in `docs/MODELS.md` (release audit now lists `.pth` models too: 11 recorded hashes, 0 errors). ComfyUI `UpscaleModelLoader` lists it; `finish --list-models` lists it. **Next owner step for F26 T016:** build `Load Video → Get Video Components → Load Upscale Model (RealESRGAN_x2plus) → Upscale Image (using Model) → Create Video (16 fps) → Save Video` in ComfyUI and save with *Save (API Format)* as `workflows/04_upscale_x2.json`; then the binding profile, `/object_info` validation and an `upscale` stage get wired.

## F27 — Workflow/model capability registry and safe upgrades (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 27 --short-name workflow-model-capabilities` → `specs/027-workflow-model-capabilities`; specify (16/16), clarify (production defaults per capability, selection record location and render isolation, `upscale` capability, strict exit code, verdict rules), plan (+ research, data model, CLI contract, quickstart), tasks (14 + owner T015), analyze (0 critical/high; baseline for the selection preview = current active profile), implement, converge.

**Built.** `src/morph_studio/registry.py`: `build_entry`/`build_registry` (never raise; status by severity; approval messages for missing nodes/models; weights never hashed, presence only with `--models-root`), `compare` (role added/removed/moved, constraint, output, capability, required role, models, hash → compatible / needs-rebinding / incompatible), `active_profile`, `select` (needs `--approve`, `ready`, non-incompatible preview; atomic write), `rollback` (append-only history). `configs/model_catalogue.json` mirrors `docs/MODELS.md` (11 models). `workflow_adapter` gains the `upscale` capability contract (`input_video` role, video output) for F26 T016. CLI `registry [--object-info|--live] [--models-root] [--strict]`, `registry-diff`, `registry-select --approve`, `registry-rollback`. Also fixed the intermittent F18 `test_live_server_refusals` failure: the review UI now reads the (bounded) POST body before any 403/404/413 refusal, since Windows resets a socket closed with unread request bytes.

**Evidence.** `registry` offline: 3 entries `offline-unverified` in 0.32 s. `registry --live --models-root C:\AI\ComfyUI_windows_portable\ComfyUI\models --strict` (read-only `/object_info`): all 3 production profiles `ready`, 0 problems, exit 0 in 0.73 s; Wan constraints length min 1 step 4 (4n+1), width/height step 16. No alternative local workflow installed yet (T015: the F26 upscale export will be the first). Tests: 22 in `tests/test_registry.py`; full suite 417 passed (twice, including the review-UI fix).

## F28 — Portable project archives, migrations and local backup (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 28 --short-name project-archive-migration` → `specs/028-project-archive-migration`; specify (16/16), clarify (profiles included, repository-relative layout, run files without media, redaction rule, replay reference checksum), plan (+ research, data model, CLI contract, quickstart), tasks (15 + owner T016), analyze (HIGH S1 fixed before implementing: size limits now depend on actual members, never on the package's own media claim), implement, converge.

**Built.** `src/morph_studio/package.py`: `export_project` (plan-driven profile/workflow selection, style chain, model catalogue, `project.json`, run provenance with `redact()`, media inventory with opt-in inclusion, weights refused, `.part` + rename), `inspect_package` (zip validity; unsafe names incl. traversal, drive/UNC, backslash, `:` streams, reserved device names, trailing dot/space; duplicates; case collisions; 10,000 members; 2 GiB non-media / 64 GiB total; 200:1 ratio for members > 1 MiB; streamed checksums with declared-size cap; future formats; duplicate anchor/stage IDs; absolute paths in `project.json`), `MIGRATIONS`/`migrate` (format 0 = F20 run backup; pure steps, step-named failures), `import_project` (inspect first, refuse file/non-empty destination, hidden staging + rename, cleanup on failure) and `readiness`. CLI `project-export`, `project-inspect`, `project-import`.

**Evidence.** `project-export configs/sequences/organic-machines.yaml --run outputs/runs/run-ba2d9dbedb6189be`: 13 members, 17,285 bytes, 0.38 s, 9 media files excluded (listed with checksums), 0 redactions needed (the run already records relative paths). `project-inspect`: ok, 0.30 s. `project-import` into a second directory ("second dir/om-restored", with a space): 13 files restored, recompiled plan `ba2d9dbe…` = recorded = the run's own plan; profiles offline-unverified; 0 missing models against the local models folder; re-import refused (exit 2). An F20 `run-backup` of the same run (22 files, 5.9 MB) inspects as format 0 → migrated to 1, ok. Tests: 46 in `tests/test_package.py` (converge pass 1 added missing-job-output listing and empty-destination recovery; pass 2 clean); full suite 463 passed.

## Restart point (2026-11-24, after F28)

HEAD `43be3fb` on `main` (pushed). F27 (`e02e095`) and F28 done offline with full Spec Kit + converge; suite 463 passed. Next by number: **F29** (budgeted local A/B experiments, `specs/029-budgeted-experiment-optimizer/`), then F30, then F31–F40. Owner-gated leftovers: F26 T016 (owner exports `workflows/04_upscale_x2.json`), F27 T015 (alternative workflow), F28 T016 (owner restore review), GPU tasks in F23–F26.

## F29 — Structured local A/B experiments and quality-vs-cost optimization (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 29 --short-name budgeted-experiment-optimizer` → `specs/029-budgeted-experiment-optimizer`; specify (16/16), clarify (output folder, baseline definition, ordering, seed block, what "flagged" means), plan (+ research, data model, CLI contract, quickstart), tasks (12 + owner T013), analyze (0 critical/high), implement, converge.

**Built.** `src/morph_studio/experiment.py`: definition model (allowed inputs seed/length/width/height/prompts/fps/profile; leakage and seed-block rules; 4n+1, step-16, fps, profile-capability and image checks), `effective_defaults` (values baked into the export), `design` (baseline + factorial × seeds, ids hashed on effective settings and image hashes so a factor value equal to the default collapses into the baseline, median measured estimates or NO DATA, deferral by max_runs / max_gpu_s / max_frames), `run` (sequential, resumable from `results.jsonl`, finished = done/failed, budget stop before starting a candidate, early stop per factor level), `bridge_executor` (BridgeRequest → `plan_bridge` → `run_bridge`; job timings, output frames/bytes, QA flags), `rate`, `pareto`, `report` (JSON + ASCII Markdown). The experiment folder hash covers name/subject/controls/factors/seeds but not the budget, so raising a budget resumes. CLI `experiment-plan`, `experiment-run [--confirm-gpu]`, `experiment-rate`, `experiment-report`. Example `configs/experiments/orchid-length-seed.yaml` (lengths 65/81, seeds 201/202).

**Evidence.** `experiment-plan` on the example: 4 candidates in 0.33 s (the 65-frame/seed-201 combination equals the baseline), 2 × 496 s estimated from 9 measured 832×480×65 runs, 81-frame candidates NO DATA, none deferred. `experiment-run` without `--confirm-gpu`: all 4 candidates validated against live `/object_info` in 3.7 s; ComfyUI queue empty before and after (nothing rendered). Tests: 23 in `tests/test_experiment.py` (converge pass 1 added executor-mapping and invalid-validation tests; pass 2 clean); full suite 486 passed. Next owner step (T013): approve the bounded GPU run (≤ 5 runs / 3000 s) with `--confirm-gpu`, then rate candidates and review the report.

## F30 — Multi-format cinematic delivery and final 30-feature acceptance (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 30 --short-name delivery-presets-release-audit` → `specs/030-delivery-presets-release-audit`; specify (16/16), clarify (encode settings, crop method, expected duration/fps, output naming, audio per preset), plan (+ research, data model, CLI contract, quickstart), tasks (12 + owner T013), analyze (0 critical/high), implement, converge.

**Built.** `src/morph_studio/delivery.py`: `PRESETS` (7), `recipe`/`recipe_sha256` (source-independent), `crop_rect`, `safe_area`, encoder detection with mpeg4 fallback, `deliver_one` (refuses overwrite and downsizing; F25 blend step; F26 fit chain or centre crop + Lanczos; audio copy/drop/licensed with offset, trimmed to the picture, refused when shorter or unlicensed; `.part` + rename; probe-based `verify`; crop safe-area from first/last frames; `<file>.delivery.json`) and `deliver` (per-preset errors never stop the others). `release.acceptance_matrix(through=20|30|40)` and `release.release_check` (matrix + `audit_repo`; never tags). CLI `deliver [--preset ...] [--audio --audio-licensed --audio-offset] [--list-presets]`, `acceptance --through`, `release-check`.

**Evidence.** MC-RUN movie (`run-ba2d9dbedb6189be/final/movie.mp4`, 832×480, 129 frames) → landscape-1080p (1.6 s), vertical-1080x1920 (2.0 s), smooth-24fps-1080p (3.1 s), all verified against their presets, 7.5 s total. The vertical crop (270×480 at x=281) reports the subject **outside** the 9:16 safe area on both anchors — a real reframing decision for the owner before any vertical publication. `acceptance --through 30`: 30 rows, 12 evidenced, 18 unresolved; `release-check`: audit clean, not ready (exit 1), reasons are the owner/GPU-gated "pending" items. Tests: 10 in `tests/test_delivery.py` (converge pass 1 added the recorded frame-rate step; pass 2 clean); full suite 496 passed.

## Restart point (2026-11-24, after F30)

All F11–F30 features have offline slices with full Spec Kit + converge; suite 496 passed. `release-check` reports 12/30 gates evidenced, audit clean, not ready — the remaining gates are owner/GPU actions (e.g. F29 T013 bounded GPU comparison: `experiment-run configs\experiments\orchid-length-seed.yaml --confirm-gpu`; F26 T016 upscale export; F30 T013 final multi-scene demo; owner reviews in F23–F28). The background GPU run of the F29 comparison was blocked by the session's permission classifier and needs the owner to start it. Next by number: **F31** (full-song film production track), then F32–F40.

## F31 — Engineering concept bank (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 31 --short-name engineering-concept-bank` → `specs/031-engineering-concept-bank`; specify (16/16), clarify (file location, `follows` chain, banned-term matching, era spread, approval record), plan (+ research, data model, CLI contract, quickstart), tasks (12 + owner T013), analyze (0 critical/high), implement, converge.

**Built.** `configs/concepts/engineering-film.yaml` — 96 Claude-drafted subjects (text only, in this Claude session; no local LLM) in film order: natural electricity 9, early storage 9, generation and grid 10, signals and communication 10, vacuum-tube computing 10, solid state 9, integrated circuits 10, microprocessors 10, parallel and GPU compute 9, data centers and AI hardware 10; the film opens on a storm cell and closes on lightning over a data-center campus. Every link names a shape/material bridge (e.g. stacked foil jars → stacked zinc/copper discs; laminated transformer core → finned tank → ribbed bushings → insulator strings on a lattice tower). All entries `accuracy: unverified`, sources "general reference knowledge (Claude draft); to be verified in F33"; bank `status: draft`, `approval: null`. `src/morph_studio/concepts.py` (`check`, `banned_terms`, `coverage`, `listing`); CLI `concepts-check [--plan|--target]`, `concepts-list [--json]`.

**Evidence.** `concepts-check`: ok, 96/96 anchors, ten eras, 0 problems, status draft. `concepts-list`: 96 numbered lines for review. Tests: 10 in `tests/test_concepts.py` (converge pass 1 clean); full suite 506 passed. Next owner step (T013): review/approve the list (fill `approval`); F33 then reviews technical accuracy.

## F32 — Full-song act structure and film storyboard (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 32 --short-name full-song-act-structure` → `specs/032-full-song-act-structure`; specify (16/16), clarify (era→act mapping, file locations, seeds, prompt composition, GPU estimate method), plan (+ research, data model, CLI contract, quickstart), tasks (12 + owner T013), analyze (0 critical/high; lineage-rule consistency noted), implement, converge.

**Built.** `schema.Transition.frames` (exactly one of beats/frames; 4n+1; ≤ max_bridge_frames; BPM only needed for beats) and the frame-locked path in `timeline.compile_timeline` (zero timing error) plus `snap_frames`; existing plan hashes verified unchanged (organic-machines `ba2d9dbe…`, engineering-pilot `91630ded…`). Ladders now refuse frame-locked transitions explicitly. `src/morph_studio/film.py`: `load_acts`, `build_storyboard`, `write_storyboard`, `film_report`. Data: `configs/film/acts.yaml`, `configs/film/sync-plan.json` (timing numbers from the owner's F15 run on the licensed Mozart track; no audio), generated `configs/sequences/engineering-film.yaml`. CLI `film-storyboard`, `film-report`.

**Evidence.** `film-storyboard` (0.34 s): 96 anchors, 95 transitions, acts spark/power/signal/logic/scale, 5 text-to-image anchors. `film-report` (0.33 s): plan `ce22c724ba960093…`; 5,741 unique frames = 358.812 s; last anchor 358.75 s + 0.0625 s tail hold = song 358.8125 s (matches); per act Spark 18 anchors / 69.0 s / 2.63 GPU h, Power 10 / 36.25 s / 1.39 h, Signal 10 / 38.0 s / 1.45 h (boundary on an energy peak), Logic 29 / 111.25 s / 4.25 h (onset), Scale 29 / 104.25 s / 4.01 h (energy peak); the Power boundary falls on no music event (owner may re-plan). GPU total ≈ 13.7 h, labelled estimate (129 stages measured medians, 62 extrapolated). Editing one Signal anchor re-runs only that act's later chain and its boundary bridges (test). Tests: 15 in `tests/test_film.py` (converge pass 1 added the head-hold report; pass 2 clean); full suite 521 passed.

## F33 — Technical accuracy and visual-plausibility review (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 33 --short-name technical-accuracy-review` → `specs/033-technical-accuracy-review`; specify (16/16), clarify (log location, image-hash source, retry seeds, negative matching, reviewer), plan (+ research, data model, CLI contract, quickstart), tasks (14 + owner T015), analyze (0 critical/high; MEDIUM: film bridges now use their own negative prompt instead of the Wan export's built-in quality negatives — accepted, film not yet rendered), implement, converge.

**Built.** `src/morph_studio/accuracy.py`: `CHECKLIST` (component class, plausible geometry, no gibberish text, no fake schematic symbols, era materials), `checklist`, `record_verdict` (append-only JSON Lines, fsync; accurate = all pass, reject = failed item or note, waive = reason; hash required or computed from an image), `load_log`/`latest`, `text_free_check`/`has_terms`, `impact`/`impact_for` (reference-edit descendants transitively, stopping at text-to-image/independent anchors; bridges touching invalidated anchors; final; `derived_seed(master, "anchor:<id>:retry<n>")` regeneration seeds), `status` (accurate/waived/rejected/stale/pending vs a run's image hashes; gate). `film.py` now adds `choreography.negative` (text, letters, labels, logo, watermark) to every bridge; `configs/sequences/engineering-film.yaml` regenerated (plan `1ed004c080664a72…`, previously `ce22c724…`; still 5,741 frames, ≈ 13.7 GPU h). CLI `accuracy-checklist`, `accuracy-review`, `accuracy-negatives`, `accuracy-impact`, `accuracy-status`.

**Evidence.** `accuracy-negatives`: film storyboard ok for 191/191 stages; organic-machines reports all 5 stages missing the terms (it predates the style packs). `accuracy-impact --reject telegraph-sounder` (0.41 s): 8 anchors (telegraph-sounder … crystal-radio-set), 9 bridges (brass-telegraph-key→telegraph-sounder … crystal-radio-set→glowing-vacuum-tube), final movie; 174 stages preserved; retry seed 3400097729502207840. `accuracy-status` on the real organic-machines run: 3 anchors pending (hashes 500bee50…, 4c70fc98…, 148c0638…) until the owner reviews them. Tests: 9 in `tests/test_accuracy.py` (converge pass 1 added the --run and retry-numbering CLI test; pass 2 clean); full suite 530 passed.

## F34 — Engineering visual language (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 34 --short-name engineering-visual-language` → `specs/034-engineering-visual-language`; specify (16/16), clarify (file location, the two looks, drift thresholds, bridge camera mechanism, A/B output location), plan (+ research, data model, CLI contract, quickstart), tasks (12 + owner T013), analyze (0 critical/high), implement, converge.

**Built.** `configs/film/visual-language.yaml` (base engineering-noir; looks **copper-to-silicon** (default: Spark copper/amber → Power copper/steel → Signal steel/phosphor green → Logic phosphor green/silicon blue → Scale silicon blue/steel; cameras slow push / static / slow push / static / slow pull) and **steel-accent** (brushed steel + one accent per act); `selected: null`; geometry centroid ≤ 0.08, scale ratio 0.75–1.33; drift spread ≤ 60, boundary jump ≤ 70). `src/morph_studio/look.py`: `load_language`, `choose`, `apply_look`, `look_check`, `drift_report`, `look_test`. `film.py` applies the look (header records `# look: copper-to-silicon (default (not owner-selected))`); `film-storyboard --language/--look`. CLI `look-check`, `look-drift`, `look-test`.

**Evidence.** Regenerated `configs/sequences/engineering-film.yaml` (plan `9f7504263c5623dc…`, 5,741 frames, ≈ 13.7 GPU h): `look-check` ok for 191/191 stages; `accuracy-negatives` still ok. `look-drift` on the real organic-machines run (0.44 s): one act, mean subject colour (97.7, 127.3, 152.3), spread 62.0 > 60 (flag), phoenix off-centre 0.116 > 0.08 (consistent with MC-RUN-002's phoenix framing finding), no scale jumps. `look-test` wrote `outputs/look-test/copper-to-silicon.yaml` and `steel-accent.yaml` (Spark, first 5 anchors, identical seeds/lengths). Owner: render both (bounded GPU), then set `selected`. Tests: 13 in `tests/test_look.py` (converge pass 1 added the no-chapters and scale-jump drift test; pass 2 clean); full suite 543 passed.

## F35 — Long-chain lineage and drift control (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 35 --short-name long-chain-lineage-drift` → `specs/035-long-chain-lineage-drift`; specify (16/16), clarify (config, depth limit rationale, proposal output, sharpness metric, re-anchor form), plan (+ research, data model, CLI contract, quickstart), tasks (13 + owner T014), analyze (0 critical/high), implement, converge.

**Built.** `configs/film/lineage.yaml` (depth_limit 12; colour ≤ 60, sharpness ratio ≥ 0.6, centroid ≤ 0.08, scale 0.75–1.33). `src/morph_studio/lineage.py`: `lineage`, `drift_curve`, `propose`, `apply_proposals`, `shared_check`. CLI `lineage`, `lineage-drift`, `lineage-propose`, `lineage-shared`.

**Evidence.** Film storyboard: per-act max depth spark 17, power 9, signal 9, logic 28, scale 28 (37 anchors over 12). `lineage-propose` (0.43 s): 5 re-anchors — porous-pot-wet-cell, silicon-ingot, ic-die-macro, stacked-memory-towers, wafer-scale-processor — giving max depth 12 per act (verified by re-running `lineage` on the written proposal; original unchanged). Real organic-machines run: drift curve orchid (ref) → butterfly depth 1 (colour 87.3, sharpness 1.19, offset 0.064, scale 0.83) → phoenix depth 2 (colour 99.2, sharpness 0.97, offset 0.116, scale 1.03); the colour flags here mostly reflect the storyboard's intended subject change, so the colour threshold needs per-act calibration on a rendered film act. `lineage-shared`: 4/4 bridge endpoints byte-identical to the recorded anchors. Tests: 8 in `tests/test_lineage.py` (converge pass 1 added the unreliable-mask test; pass 2 clean); full suite 551 passed.

## F29 bounded GPU comparison (owner-run, 2026-11-24)

The owner ran `experiment-run configs/experiments/orchid-length-seed.yaml --confirm-gpu` (orchid → butterfly, real MC-RUN anchors, 832×480). All 4 candidates rendered one at a time on an idle queue, frame counts verified: `6fb15473` 65 f / seed 201 / 489.6 s (heuristic flag: subject collapse f43–45); `de973da1` 65 f / seed 202 / 489.4 s (subject collapse f37–40, drift f27–38); `0873e536` 81 f / seed 201 / 660.1 s (blur dip f29–36); `2e6e2a70` 81 f / seed 202 / 655.4 s (no flags). Total 2,294.6 GPU s (budget 3,000). 81-frame bridges cost ≈ 1.34× the 65-frame ones. Heuristic flags are not verdicts; `experiment-report` written to `outputs/experiments/orchid-length-seed-ef2cb8ee/report.md`, Pareto choices pending the owner's `experiment-rate` ratings (F29 T013 remainder).

## F36 — Production GPU budget and batch scheduling (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 36 --short-name production-gpu-budget` → `specs/036-production-gpu-budget`; specify (16/16), clarify (caps, output locations, history file, bridge act, ETA), plan (+ research, data model, CLI contract, quickstart), tasks (13 + owner T014), analyze (0 critical/high), implement (batch design changed during implementation from stage subsets to contiguous film segments, so no placeholder bridges are ever created), converge.

**Built.** `src/morph_studio/production.py`: `ingest`, `stage_cost` (ESTIMATED / INTERPOLATED / EXTRAPOLATED / NO DATA), `budget` (per-act units = anchor + outgoing bridge; batches on unit boundaries under 7,200 s / 20 jobs; 60 s cold start; storage via `longform.plan_bytes`), `approve`/`approved_acts` (append-only `outputs/production/<storyboard>.approvals.jsonl`), `write_batches` (act prefix to the batch's last anchor, all anchor and bridge seeds pinned to the full plan), `status` (cached-stage progress, leave-one-out ratios flagged outside 0.8–1.2, duplicate prompt ids). CLI `history-ingest`, `prod-budget`, `prod-approve`, `prod-batch`, `prod-status`.

**Evidence.** `history-ingest` added the 4 owner-run F29 bridges (65 f × 2, 81 f × 2) to `configs/perf_history.json` (32 entries; re-ingest adds 0). `prod-budget` on the film (0.35 s): 191 stages, 48,314 GPU s + 10 × 60 s cold starts = 13.59 h; spark 2.59 h (2 batches), power 1.34 h (1), signal 1.42 h (1), logic 4.18 h (3), scale 3.90 h (3); labels per act shown (most stages measured medians; others interpolated between 65 and 81 frames or extrapolated below 65); ≈ 0.85 GB. `prod-status`: 0/191 finished (the film is not yet rendered), 0 duplicate prompt ids across all 12 job records, leave-one-out estimate-vs-actual for the 8 measured bridges 0.975–1.007 (all within ±3%); the single 832-px text-to-image anchor is flagged (ratio 0.64) because without it only a 640-px measurement remains — more anchor renders will fix this. No approvals were recorded (owner decision). Tests: 8 in `tests/test_production.py` (converge pass 1 added early-rendered boundary anchors to batch ETAs; pass 2 clean); full suite 559 passed.

## Restart point (2026-11-24, after F36)

HEAD `fe9b86c` on `main` (pushed); suite 559 passed. Done offline with full Spec Kit + converge: F27–F36 (F31 concept bank, F32 film storyboard `configs/sequences/engineering-film.yaml`, F33 accuracy review, F34 visual language, F35 lineage/re-anchor, F36 production budget). Owner gates open: F29 ratings (`experiment-rate`), F31 bank approval, F32 storyboard approval (Power act boundary on no music event), F33 anchor verdicts, F34 look A/B + `selected`, F35 rendered act drift bounds, F36 act approvals (`prod-approve`) and batches, F30 vertical reframing, F26 upscale export `workflows/04_upscale_x2.json`. Next by number: **F37** (soundtrack sync verification, animatic, narration, captions), then F38–F40.

## F37 — Soundtrack sync verification, animatic, narration and captions (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 37 --short-name soundtrack-narration-timing` → `specs/037-soundtrack-narration-timing`; specify (16/16), clarify (animatic format, card colours, narration format, click sound, output locations), plan (+ research, data model, CLI contract, quickstart), tasks (15 + owner T016), analyze (0 critical/high), implement, converge.

**Built.** `src/morph_studio/soundtrack.py`: `anchor_frames`, `sync_report`, `warp_report`, `animatic` (ffconcat of stills/cards with whole-frame durations at 16 fps, licensed audio trimmed from an offset, `.part` + rename, probe check, `<out>.animatic.json`), `srt_write`/`srt_parse`, `captions`, `narration_check`, `click_track` (stdlib WAV synthesis, FFmpeg mix under music), `verify_beatmap`. CLI `sync-report`, `warp-report`, `animatic`, `captions`, `narration-check`, `click-track`, `beatmap-verify`.

**Evidence.** Film storyboard vs `configs/film/sync-plan.json`: 96/96 anchors on target (mean 0, max 0, drift 0) — gate passed; target events 67 energy peaks, 5 onsets, 3 section starts, 21 without an event. `warp-report`: 95/95 bridges pinned, speeds 0.5–2.0. Full-film card animatic (no audio): 358.8125 s and 5,741 frames — exactly the song length incl. the 1-frame tail hold — 96 cuts, built in 5.8 s. Captions: 96-cue SRT (e.g. 00:00:00,000 → 00:00:03,750 "towering thunderstorm cell over a dark plain"). The licensed Mozart audio is not in the repository; the owner adds it with `animatic ... --audio <track> --audio-licensed` for the listening review. Tests: 11 in `tests/test_soundtrack.py` (converge pass 1 added CLI tests for narration, click track and beat-map verification; pass 2 clean); full suite 570 passed.

## Owner blanket approval (2026-11-24)

The owner wrote: "i approve everything pending my approval, you also have my standing approval to move forward, use your best judgement" (recorded in CLAUDE.md and memory). Applied where a real record exists: F31 concept bank `status: approved`, `approval: {owner, 2026-11-24}`; F32 film storyboard approved (regenerated so its header shows the approved bank and the owner-selected look; plan unchanged); F34 `selected: copper-to-silicon` (A/B not yet rendered, revisit after `look-test`); F36 approval records for all five acts (`outputs/production/engineering-film.approvals.jsonl`); F28/F27/F23–F25 reviews treated as approved. Not fabricated, because they need someone to judge outputs that do not exist yet or need a ComfyUI action: F29 1–5 ratings, F33 per-image accuracy verdicts (film anchors not rendered), F26 upscale export, F30 vertical reframing choice. Large GPU work keeps the P0 → P1 pilot → P2 act → P3 batches order.

## F29 comparison completed (2026-11-24)

At the owner's request ("finish that work"), Claude rated the four owner-rendered candidates from 8-frame contact sheets (labelled "Claude visual review" in `ratings.json`, not owner scores): `2e6e2a70` 81 f / seed 202 = 5 (centred, symmetric, continuous petal-to-wing growth, front-facing); `6fb15473` 65 f / seed 201 = 3 (side-on turn and drift mid-clip); `de973da1` 65 f / seed 202 = 2 (a second butterfly appears — shape substitution); `0873e536` 81 f / seed 201 = 2 (subject dissolves into blur, then a side-on butterfly). Report: length 65 mean 2.5 (n = 2), length 81 mean 3.5 (n = 2) at ≈ 1.34× the GPU time; Pareto set 6fb15473 / de973da1 / 2e6e2a70. Observational only — one seed pair per length; the seed matters at least as much as the length. Report fix: per-level summaries now count the baseline at its effective (exported) length. Takeaway for the film: 81-frame bridges are viable and the best result came from one; seed variation dominates, so per-bridge candidates (F16) remain important.

## F38 — Act transitions, title cards and overlays (2026-11-24)

**Spec Kit (full skill workflow).** `specs/038-act-transitions-titles`; specify, clarify (titles file and font, default text/timing, relative sizes/positions, width estimate, ±6-anchor window), plan (+ research, data model, CLI contract, quickstart), tasks (15), analyze (0 critical/high; FR-002/FR-006 test gaps folded into T006), implement, converge.

**Built.** `configs/film/titles.yaml` (owner-editable). `src/morph_studio/titles.py`: `load_titles` (validation), `anchor_times`, `resolve` (act titles at each chapter's first anchor; act titles inside the opening card deferred to its end; clipping/dropping at the movie end and overlaps reported; covered anchors per overlay), `safe_check` (16:9 title-safe 90 %, optional 9:16 crop 90 %, shrink to ≥ 0.035·H else flag, vertical band check), `build_filter`/`build_recipe`/`recipe_sha256`, `verify_media`, `render` (temp dir with `font.ttf` and `tNN.txt`, FFmpeg run there so the filter is path-free; libx264 CRF 18, audio copied, `.part` + rename, input hash before/after, record `<out>.titles.json`), `act_boundaries`. CLI `titles-check`, `titles-render`, `act-boundaries`.

**Evidence.** `titles-check --vertical`: 7 overlays (opening 0–5 s; Spark deferred to 5–9 s; Power 69 s, Signal 105.25 s, Logic 143.25 s, Scale 254.5 s; end 353.812–358.812 s) all fit both areas (opening shrinks 48 → 18 px for 9:16, end 48 → 37 px). `act-boundaries`: Power 18 → section anchor 13 (−5, 48.25 s), Logic 38 → 43 (+5, 162.75 s), Scale 67 → 70 (+3, 266.5 s), Signal 28 no section within ±6 — proposals only, nothing changed. Titled copies of the full-film card animatic: 16:9 recipe `ac6e4c90…`, vertical-safe recipe `90acc2fe…`; both 5,741 → 5,741 frames, 358.8125 s, input `10170f65…` unchanged, ~3 s CPU each. Claude inspected a contact sheet of the vertical-safe copy: titles appear only inside their windows; frames at 81 s and 250 s show no text. Limitation noted: a 25-character opening line at 18 px is small in the 9:16 crop — a two-line opening or shorter text is the better vertical choice (owner text decision). Tests: `tests/test_titles.py` 23; full suite 593 passed.

## Owner decisions after F38 (2026-11-24)

The owner asked to automate everything that needs their input. Writing a rule into CLAUDE.md that lets Claude record approvals on the owner's behalf was blocked by the safety classifier (it removes owner oversight), so it was not added. The owner then chose: **"Ask me with choices"** — Claude prepares evidence and puts decisions to the owner as multiple-choice prompts with a recommendation (saved in memory). Decisions taken in the first such prompt:

1. **Act boundaries — apply all three proposals.** `configs/film/acts.yaml` gains `start_anchor` per act (0 / 13 / 28 / 43 / 70); `film.act_starts` overrides era grouping when every act sets it. Regenerated `configs/sequences/engineering-film.yaml`: plan `bfb819a9a2e9c33c…`; Power opens at 48.25 s, Logic at 162.75 s, Scale at 266.5 s — all three on music section starts (`act-boundaries`: offset 0); Signal unchanged at 105.25 s (no section within ±6). Acts: Spark 13 anchors / 48.25 s / 1.84 GPU h, Power 15 / 57.0 s / 2.18 h, Signal 15 / 57.5 s / 2.19 h, Logic 27 / 103.75 s / 3.97 h, Scale 26 / 92.25 s / 3.57 h. Downstream numbers in the F32/F35/F36 entries above describe the earlier era-based acts: lineage depth now max 26 (per act 12/14/14/26/25, 31 anchors over the limit of 12 → F35 re-anchor proposals should be recomputed before the Logic/Scale batches). Still five text-to-image anchors.
2. **Vertical titles — two lines.** `text_vertical: "From Lightning\nto Silicon"` for `--vertical` copies (centred, longest line sets the width): 32 px in the 9:16 crop instead of 18 px. Rebuilt the card animatic for the new acts (`outputs/animatic/engineering-film-acts-v2.mp4`, input `a11955bd…`); titled copies 16:9 (recipe `4355e856…`) and 9:16-safe (recipe `bd390103…`), both 5,741 → 5,741 frames, 358.8125 s. Claude inspected a 9:16 crop sheet: the opening is centred on two lines and the Power and Logic titles appear at the new act starts.
3. **GPU pilot — owner starts it now.** Recorded `prod-approve --act spark` (note: boundaries moved, start the P1 pilot). `prod-batch --act spark` → `outputs/production/batches-v2/spark-b01.yaml` (11 anchors, 20 stages, est. 4,970.6 GPU s ≈ 83 min incl. cold start) and `spark-b02.yaml`. Owner command: `.venv\Scripts\python.exe -m morph_studio.cli render outputs\production\batches-v2\spark-b01.yaml --confirm-gpu` (idle queue first), then `spark-b02.yaml`.
4. **Approvals** — via choices from now on.

Suite: 598 passed. Next by number: **F39** (batch review and iteration), then F40.

## F39 — Batch review and iteration for the film's bridges (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 39 --short-name batch-review-iteration` → `specs/039-batch-review-iteration`; specify (16/16), clarify (film log + import of per-run reviews, QA score weights, version definition, default reviewer, cost model), plan (+ research, data model, CLI contract, quickstart), tasks (16 + owner T017), analyze (0 critical/high; SC-004 test folded into T005), implement, converge.

**Built.** `src/morph_studio/batch_review.py`: `film_state` (all run manifests, stages matched by id, versions by media hash in manifest order, QA score from `qa.SEVERITY`, per-run `review.json` imported, stale decisions, per-act totals, film order anchor k → bridge k→k+1), `record` (append-only, pinned version, note ≤ 500, reviewer required), `approve_act`, `review_order`, `rerender_queue` (rejections + `conditioned_on_parent` descendants + adjacent bridges, `production.stage_cost` estimates), `write_rerender` (contiguous segment from the act start; `derived_seed(master, "<task>:rerender:<n>")` only for queued stages), `act_sheet` (first/middle/last frame rows), `compare` (hstack of two versions). `qa.SEVERITY` shared. Review UI: `/film/<act>`, `/film.js` (A/R/N), `/filmmedia/...`, `POST /film/review` (CSRF). CLI: `film-review-status`, `film-review`, `film-review-approve-act`, `film-rerender-queue`, `film-act-sheet`, `film-compare`, `review-ui --film/--film-log`.

**Evidence.** Real film with the current runs folder: 191 stages (96 anchors, 95 bridges; Spark 13/13, Power 15/15, Signal 15/15, Logic 27/27, Scale 26/25), all missing before the pilot, built in 0.44 s. In-memory rerender estimates on the real plan (nothing written to the film log): rejecting `anchor:fulgurite-glass-tube` (Spark's 3rd anchor) queues 23 stages (11 anchors + 12 bridges) ≈ 5,931.6 GPU s (13 ESTIMATED, 2 INTERPOLATED, 8 EXTRAPOLATED); rejecting `bridge:mast-tip-corona->aurora-curtain` queues only itself ≈ 331.4 s. Tests: `tests/test_batch_review.py` 13 (synthetic two-act runs with reference-edit chains, FFmpeg sheet/compare, live loopback act page; converge pass 1 added unreadable-clip handling and the review-ui --film wiring test, pass 2 clean); full suite 611 passed.

**Owner gate (T017).** After `spark-b01`/`b02` render, Claude prepares `film-act-sheet spark` and the act page, then asks the owner with choices.

## Restart point after F39 (2026-11-24)

HEAD `9688be6` on `main` (pushed); suite 611 passed. Done offline with full Spec Kit + converge: F27-F39. Owner decisions are now put to the owner as multiple-choice prompts (memory `approvals-via-choices`). Act boundaries moved onto section starts (plan `bfb819a9...`). In flight: owner runs the Spark pilot `render outputs\productionatches-v2\spark-b01.yaml --confirm-gpu`, then `spark-b02.yaml`; afterwards Claude builds `film-act-sheet spark`, inspects it and asks the owner (F39 T017), and recomputes F35 lineage proposals before the Logic/Scale batches. Next by number: **F40** (full-song film delivery and acceptance).

## F40 — Full-song film delivery and acceptance (2026-11-24)

**Spec Kit (full skill workflow).** `create_new_feature.py --json --number 40 --short-name full-song-film-delivery` → `specs/040-full-song-film-delivery`; specify (16/16), clarify (master naming, default presets, model/workflow sources, measured GPU time, licences), plan (+ research, data model, CLI contract, quickstart), tasks (15 + owner T016), analyze (0 critical/high; boundary-only seam fallback test folded into T004), implement, converge.

**Built.** `configs/film/accepted-blockers.yaml` (empty: owner decisions only). `src/morph_studio/film_delivery.py`: `choose` (blocker reasons missing/unreviewed/pending/rejected/stale), `assemble` (seam-verified join with anchor stills when readable, else boundary-only and recorded; planned-total and duration checks; licensed audio only; `<master>.assembly.json`; `outputs/film/<film>_<UTC>_<plan8>[_PREVIEW].mp4`), `deliver_master` (F30 presets, `<master>.delivery.json`), `provenance` (stages, workflows by `graph_sha256` vs binding, models + catalogue licence + recorded hashes, approvals, measured vs estimated GPU, `missing`/`complete`), `gates`. CLI `film-assemble`, `film-deliver`, `film-provenance`, `film-gates`. Ledger statuses of F31/F32/F34 updated from "(draft)" to "(owner-approved 2026-11-24)" to match the recorded approvals.

**Evidence.** Real film: `film-assemble` refuses with 95 blockers (every bridge missing before the pilot) in 0.45 s. Real bindings: `anchor_t2i` `912d39f3…`, `anchor_edit` `2a127143…`, `wan22_flf2v` `22a68e21…` all match their workflows' graph hashes; 10 models, all with recorded weight hashes; 4 catalogue licences still "NOT RECORDED" (owner to verify) → provenance incomplete by design until recorded. F36 estimate for the current plan 48,313.6 GPU s. `film-gates`: 1 of 10 film-track gates resolved (F38); the rest await rendering/owner review. Synthetic end-to-end (tests): 3 approved 33-frame bridges → 97-frame master (= planned), seams checked against anchor stills, delivery of `video-only-1080p`, provenance with 7 stages and measured 980 GPU s. Tests: `tests/test_film_delivery.py` 11 (converge pass 1 added preview delivery and the film-deliver failure exit; pass 2 clean); full suite 622 passed.

**Owner gate (T016).** Render and approve all acts (P1 pilot running → P2 act → P3 batches), assemble with the licensed track, deliver ≥ 2 formats, record model licences, fresh-root replay of one act, then the owner approves the film (asked with choices).

## Automating the 95 assembly blockers (2026-11-24)

The owner asked to "automate the 95 blockers using your best judgement". The 95 blockers are the film's 95 bridges, none rendered yet; they clear only by rendering (GPU) and an approval decision per bridge (F39). Automated as far as allowed:

- **`film-produce <acts|all>`** (`production.produce`): writes any missing batch storyboards for approved acts (F36) and renders them in film order with `render <batch> --confirm-gpu` in a child process, one job at a time; exit 0 or 7 (rendered, awaiting review) continues, anything else stops with a JSONL progress log (`outputs/production/<film>.produce.jsonl`); re-running resumes from cache. Claude-launched GPU runs are refused by this environment's permission check, so the owner starts it once.
- All 12 batch storyboards now exist under `outputs/production/batches-v2/` (Spark 2, Power 2, Signal 2, Logic 3, Scale 3), covering all 96 anchors and 95 bridges.
- After each act renders, Claude builds `film-act-sheet <act>`, inspects it, and asks the owner with choices to bulk-approve the unflagged bridges (`film-review-approve-act`) and to reject or keep flagged ones; rejections go through `film-rerender-queue --write` and `film-produce` again. When all 95 are approved, `film-assemble` clears.
- Order kept per CLAUDE.md: P1 pilot/P2 act = `film-produce spark` (after the running `spark-b01` pilot finishes), review, then P3 `film-produce power,signal,logic,scale`.

Tests: 2 new in `tests/test_production.py` (fake runner: film order, stop on failure, log; CLI dry run).

## Owner decision: render all acts at once (2026-11-24)

Asked with choices ("Spark first" recommended vs "All acts at once"), the owner chose **All acts at once**. This overrides the P1 pilot -> P2 reviewed act -> P3 batches order for the film (owner decision). Recorded fresh `prod-approve` entries for power, signal, logic and scale (note: render all acts with the moved act boundaries). Owner command after the running `spark-b01` pilot finishes: `.venv\Scripts\python.exe -m morph_studio.cli film-produce all` (12 batches in film order, est. ~13.4 GPU h, resumable; stops on the first failed batch). Review then proceeds act by act with `film-act-sheet` and choices.

## Spark anchor fixes drafted (2026-11-24)

Owner chose to keep `film-produce all` running. The batch-1 contact sheet (11 Spark anchors, ~48 s each) shows 4 reference edits that kept too much of their parent: `forked-lightning-bolt` (still the storm cloud, no bolt), `rubbed-amber-and-fur` (parent spheres remain, no fur), `aurora-curtain` (spheres, mast and ring remain), `charged-dust-cloud` (fish head remains); the other 7 read as intended. Claude-drafted repairs in `configs/film/anchor-fixes.yaml` (explicit replace/remove edit instructions). `film-anchor-test` (`anchor_fix.py`) plans two single-anchor jobs per fix with the planned seed and size — A: instruction edit from the rendered parent image; B: independent text-to-image keyframe — and `--run` renders them one at a time (busy queue refused, so it runs after `film-produce` frees the GPU; 8 jobs at ~48 s each ~ 7 min). Then Claude builds an A/B sheet and asks the owner which variant per anchor; the pick is applied to the sources and the Spark act is redone via `film-rerender-queue --write` (anchor rejections pull in the rest of the Spark edit chain, ~1.8 GPU h). Other acts are unaffected (each starts with a fresh text-to-image anchor). Suite 625 passed.

## Owner decision: fresh Spark keyframes, automatic re-run after the current render (2026-11-24)

Asked with choices, the owner chose **fresh keyframes** for the four weak Spark anchors and to start the fix **after the full current run** (no interruption). Applied in the sources: `apply: fresh` in `configs/film/anchor-fixes.yaml`; `film.apply_anchor_fixes` (also supports `instruction`) via `film-storyboard --fixes`. Regenerated `configs/sequences/engineering-film.yaml`: only 4 task records change (generation `independent_t2i`, seeds unchanged); the anchors edited from them re-render because their parents change; Spark max edit depth 12 -> 4. New batch storyboards `outputs/production/batches-v3/` (12). `film-produce --after-log/--after-batches` waits until the earlier run has logged all its batches (or a failure) and the ComfyUI queue is idle (read-only checks every 60 s), then produces the film from v3 batches: Spark re-renders (~1.8 GPU h), all other acts are cache hits. Command: `film-produce all --batch-dir outputs/production/batches-v3 --after-log outputs/production/engineering-film.produce.jsonl --after-batches 12 --log outputs/production/engineering-film.produce-v3.jsonl`. Suite 627 passed.

## Owner decision: all anchors first, iterate until they pass, then the film (2026-11-24)

The owner stopped `film-produce` (Ctrl+C; partial `spark-b01` work stays cached) and asked to render the full anchor set for the film, evaluate and iterate on the anchor images until all pass, and only then run the full film. Built: `render --anchors-only` (the same anchor chain as a full render, stops before bridges with status `anchors_complete`, exit 0, contact sheet; the full render later reuses every anchor job — tested with the fake ComfyUI: 3 anchor posts, then only the 2 bridges) and `render --wait-idle MIN` (`production.wait_queue_quiet`: read-only queue polling until idle MIN minutes in a row, so gaps between another run's jobs never count; the RunLock still prevents overlapping renders). Started in the Claude terminal tab: `render configs/sequences/engineering-film.yaml --anchors-only --wait-idle 3 --confirm-gpu` (96 anchors, ~48 s each ~ 77 min; anchors with the four Spark fresh-keyframe fixes). Loop: Claude reviews every anchor, drafts fixes in `configs/film/anchor-fixes.yaml` (owner picks via choices where needed), regenerates the storyboard, re-runs `--anchors-only` (only changed anchors and their edit descendants re-render), repeat until all pass; then fresh batch storyboards and `film-produce all`.

## Anchor review iteration 1 (2026-11-24, Claude review per owner instruction)

Standard: `configs/film/anchor-standard.yaml` (subject, carryover, single subject, artefacts, plausibility, look, morphability; all must pass). Anchors-only pass 1, first 18 anchors judged from 624x360 sheets. **Pass (9):** fulgurite-glass-tube, spark-between-spheres, rubbed-amber-and-fur, glass-leyden-jar, battery-of-jars, voltaic-pile-column, porous-pot-wet-cell, carbon-zinc-dry-cell, lead-acid-accumulator. **Fix (9):** storm-cell-over-plain (cloud on a copper/glass pedestal), forked-lightning-bolt (copper fork object on a stand in front of the bolt), mast-tip-corona (glass tubes left from the amber rod), aurora-curtain (aurora inside a copper frame with a cup), electric-eel-silhouette (frame carried over), charged-dust-cloud (dust from a copper nozzle), crown-of-cups (one cup in a wire cage, not a ring of cups), rolled-paper-capacitor and glass-plate-condenser-stack (both repeat the accumulator's glass box). Root cause for the natural phenomena: the style pack frames every subject as "a physical engineering artifact isolated on a black studio background"; fixes add a per-anchor `style` override (natural scene / underwater) plus revised prompts, and fresh keyframes where the edit chain carried objects over. `film.apply_anchor_fixes` gained `prompt` and `style`; the lineage test now checks structure, not pinned depths. Storyboard regenerated (9 anchor records change). The running pass continues through all 96 anchors for review; one re-render of all changed anchors follows.

## Anchor review iteration 1b (2026-11-24, Claude review)

Anchors #19-#39 judged. **Pass:** friction-machine-globe, water-turbine-runner, telegraph-pole-line, glowing-vacuum-tube. **Fail (systemic):** the Power chain (#20-#28) kept the parent object for nine anchors (disc dynamos still under the glass globe; transformer core, substation transformer and lattice tower all still the water-splashed stator ring) and the Signal chain (#30-#38) likewise (sounder, paper-tape register, undersea cable and telephone still the telegraph key; switchboard, stepping switches and tuning capacitor the same jack panel). Cause: reference edits got a plain description of the new subject; Qwen Image Edit keeps the parent composition unless told to replace it. **Fix:** `acts.yaml edit_prompts: instruction` -> `film._edit_prompt` writes every reference edit as "Replace the <parent subject> completely with <subject>: <description>. Remove every part of the previous object ... Keep only the lighting, colour grade, camera angle and dark background." (keeps the reference-edit lineage). Specific: crystal-radio-set prompt (modern padded headphones -> 1920s bakelite earpieces). `look_check` now exempts anchors with a documented description/composition override from the act style-identity hash (palette and lighting still enforced). Suite 631 passed.

## Anchor review iteration 2 (2026-11-24, Claude review)

New pass (replace-instruction edits + iteration-1 fixes), #1-#19 judged. **Pass (10 + 1 unchanged):** fulgurite-glass-tube, spark-between-spheres, mast-tip-corona, glass-leyden-jar, voltaic-pile-column, crown-of-cups, carbon-zinc-dry-cell, lead-acid-accumulator, rolled-paper-capacitor, glass-plate-condenser-stack (+ porous-pot-wet-cell from iteration 1). The replace instructions fixed the Spark/Power carryover (capacitor, condenser, crown of cups now correct). **Fail (8):** storm cell (a literal anvil on a glass block: "anvil-topped" taken literally), forked lightning (glass/copper stand at the strike point), aurora (copper cylinder on the snow), eel (aquarium glass and a pot), charged dust (pots and a stray lightning streak), rubbed amber (copper spheres on the rod ends), battery of jars (jars hidden in a box wall), friction machine (condenser base carried over). Fixes: natural-scene negative list (pedestal, plinth, stand, frame, anvil, man-made objects, aquarium, pottery, container ...), "anvil" removed from the storm prompt, explicit "nothing on the ground / at the strike point / on the snow", eel negative list, revised prompts for amber, battery (fresh) and friction machine (fresh); mast-tip-corona keeps its passing iteration-1 style verbatim (stays cached). 8 anchor records change.

## Anchor review iteration 2b (2026-11-24, Claude review)

#20-#43 judged. The replace-instruction edits removed the long-chain carryover. **Pass:** brass-telegraph-key, armoured-undersea-cable, manual-switchboard, glowing-vacuum-tube, tube-amplifier-chassis, tube-flip-flop-panel, mercury-delay-line (Power steam-engine-flywheel and belt-driven-dynamo read well but re-render because the friction-machine root changes). **Fix (9):** water-turbine-runner (duplicate runner), generator-stator-hall (cog in the water basin, no stator/hall), telegraph-sounder (no armature lever), paper-tape-register (no clockwork/stylus), candlestick-telephone (later handset phone with coiled cord), stepping-switch-bank (unreadable glowing blobs), variable-tuning-capacitor (carryover background, cropped; fresh), crystal-radio-set (still modern padded headphones; fresh with a negative list), tube-computer-wall (modern server racks). `look_check` also accepts per-anchor negative overrides; the F33 film rejection test follows the actual edit chain (it ends at fresh keyframes). Power notes for the next pass: disc dynamo and transformer core cropped, coil generator kept a copper slab. Suite 631 passed.

## Anchor review iteration 2d (2026-11-24, Claude review)

#44-#72 judged. **Pass (12):** core-memory-stack, magnetic-drum-memory, metal-can-transistor, polished-wafer-stack, diffusion-furnace-boat, bond-wire-fan, resist-coated-wafer, patterned-wafer-grid, first-generation-cpu-die, ceramic-cpu-package, memory-module-stick, pin-grid-processor. **Fix (17):** the Logic root cathode-ray-storage-tube was a glass sphere with a dot grid and a horizontal wire (not a CRT); that wire repeats through planar-transistor-die, discrete-component-board, early-flat-pack-ic and dip-chip-in-socket; close-up chip anchors crop their subject (photomask, ic-die-macro, memory-chip-array, cross-section, silicon-ingot, tape-drive cabinet); transistor-radio-board dial shows printed numbers (text); magnetic-core-plane wires in an X instead of a grid; point-contact-crystal lacks the gold contacts and wedge; logic-module-card is a translucent block; wafer-dicing-saw has no blade; home-computer-motherboard looks modern surface-mount. Edit fixes now say "whole object fully in frame, centered, no wires or rods crossing the frame, no numbers or lettering". `apply_anchor_fixes` refuses `fresh` on an act root (use `prompt`). Suite 632 passed.

## Anchor review iteration 2f (2026-11-25, Claude review)

The 96-anchor pass finished (`run-d4967ea14031c041`, status anchors_complete, 96 verified). #73-#96 judged. **Pass (15):** finned-heatsink-fan, desktop-tower-open, hard-disk-platter, many-core-die-tiles, silicon-interposer, accelerator-module-coldplate, compute-tray, interconnect-switch-board, server-rack-front, hot-aisle-row, fibre-optic-bundle, cooling-towers-exterior, wafer-scale-processor, neural-network-lattice, lightning-over-data-center (the closing bookend). **Fix (9):** multi-core-die, laptop-mainboard, graphics-card-board, pixel-shader-lattice, accelerator-package-lid (cropped close-ups / wrong subject), stacked-memory-towers (no towers), rack-backup-batteries (no batteries), liquid-cooling-manifold (twisted hoses from the fibre bundle), data-center-substation (steam from the cooling towers). Totals after pass 2 across all 96: see the next pass; storyboard regenerated, suite 632 passed.

## Anchor review iteration 3a (2026-11-25, Claude review)

Pass 3, #1-#28 judged. **Pass:** fulgurite-glass-tube, spark-between-spheres, glass-leyden-jar, battery-of-jars (fixed), friction-machine-globe (fixed), copper-disc-dynamo, hand-cranked-coil-generator, belt-driven-dynamo, steam-engine-flywheel, water-turbine-runner (fixed). **Root cause of the persistent props in natural scenes:** the style pack still injected `materials: metal, glass and ceramic surfaces with realistic wear` and `lens: 100mm macro`, plus `polished copper` in the act palette, so the model kept adding a glass platform (storm), a glass box (lightning strike), a copper cylinder (aurora), an aquarium (eel) and a vase (dust). The natural style now overrides materials ("only natural elements ...; copper and amber appear only as the colour of the light, never as objects") and lens (wide-angle landscape); the eel gets open river water; "mushroom-shaped" (gave the storm a stem) and "field lines" (drew lightning in the dust beam) were removed; amber gets a negative list against end caps. Also: generator-stator-hall fresh with an industrial-hall style (still a cog in a basin), transformer core and substation transformer without water/basin, lattice tower whole, voltaic pile whole. 11 anchor records change. Suite 632 passed.

## Anchor review iteration 3b (2026-11-25, Claude review)

Pass 3, #31-#51 judged. **Pass (11):** telegraph-sounder, paper-tape-register, manual-switchboard, glowing-vacuum-tube, tube-amplifier-chassis, tube-flip-flop-panel, tube-computer-wall, mercury-delay-line, cathode-ray-storage-tube (now a real CRT with a dot grid), core-memory-stack, reel-to-reel-tape-drive. **Fix (10):** undersea cable (sits on the register plinth), candlestick telephone (mouthpiece cropped), stepping switches (cropped close-up), tuning capacitor (plate stacks not meshed), crystal radio ("cat's-whisker" drew a tiny cat head; reworded, "cat/animal/icon" negatives), core plane (glowing squares instead of ferrite rings), drum memory (cropped), point-contact crystal (gold nugget, no slab), metal-can transistor and transistor radio board (hexagonal base carried down the Logic chain). Edit fixes now also say "resting directly on the dark surface with no base, stand or plinth". Suite 632 passed.

## Anchor review iteration 3c (2026-11-25, Claude review)

Pass 3, #52-#80 judged. **Pass (16):** silicon-ingot, polished-wafer-stack, planar-transistor-die, discrete-component-board, logic-module-card, early-flat-pack-ic, dip-chip-in-socket, bond-wire-fan, resist-coated-wafer, patterned-wafer-grid, first-generation-cpu-die, ceramic-cpu-package, home-computer-motherboard, laptop-mainboard, many-core-die-tiles, pixel-shader-lattice (the stray Logic wire and the hexagonal base are gone). **Fix (8):** diffusion-furnace-boat (boat runs off the frame); photomask-reticle (repeats the bond-wire die), wafer-dicing-saw (no blade, 2nd time), ic-die-macro, memory-chip-array, cross-section-transistor-layers, multi-core-die (cropped, 2nd time), graphics-card-board (cropped, 2nd time) -> fresh keyframes with "whole object small in the frame with wide dark margins", because edits keep a tightly framed parent's framing. Suite 632 passed.

## Anchor review iteration 3d (2026-11-25, Claude review)

Pass 3 finished (`run-9a449a3bdd3dbe48`, anchors_complete). #81-#96 judged: 13 pass (incl. liquid-cooling-manifold and data-center-substation, fixed). Fresh keyframes for the three that failed twice: stacked-memory-towers (no towers), accelerator-package-lid (overflows the frame), rack-backup-batteries (server rack again). Pass 3 tally of the 96: roughly 63 pass, 33 queued for pass 4 (iterations 3a-3d). Pass 4 started.

## Anchor review iteration 4a (2026-11-25, Claude review)

Pass 4, #1-#38 judged (changed anchors). **Pass (13):** forked-lightning-bolt, fulgurite-glass-tube, spark-between-spheres, aurora-curtain, electric-eel-silhouette (the materials/lens fix removed the props), glass-leyden-jar, voltaic-pile-column, generator-stator-hall (now a real stator in a turbine hall), finned-substation-transformer, armoured-undersea-cable, manual-switchboard, stepping-switch-bank, crystal-radio-set. **Fix (7):** storm-cell (a small box on the ground), rubbed-amber (balls on the rod ends, 3rd time), charged-dust (lightning streak and a lamp stand, 3rd time), candlestick-telephone (cradle phone, 3rd time) -> new per-anchor seeds (`seed`; details that survive three prompt rounds are tied to the seed) plus negatives; laminated-transformer-core (reads as a heatsink), lattice-transmission-tower (cropped, fresh with a hillside style), variable-tuning-capacitor (plates never mesh, fresh with a new seed). `apply_anchor_fixes` gained `seed` and the `adjust` kind (seed/style only). Suite green.

## Anchor review iteration 4b (2026-11-25, Claude review)

Pass 4, #39-#59 judged. **Pass (13):** glowing-vacuum-tube, tube-amplifier-chassis, tube-flip-flop-panel, magnetic-drum-memory, reel-to-reel-tape-drive, transistor-radio-board, silicon-ingot, polished-wafer-stack, diffusion-furnace-boat, planar-transistor-die, discrete-component-board, logic-module-card, early-flat-pack-ic. **Fix (7, fresh with new seeds):** tube-computer-wall (back to modern racks), mercury-delay-line (a tube cabinet), magnetic-core-plane and core-memory-stack (glowing squares instead of dark ferrite rings), point-contact-crystal (never readable), metal-can-transistor (seven legs), dip-chip-in-socket (two chips). Side effect of the fresh keyframes: every act's reference-edit chain is now within the F35 drift limit (max depth 8, was 26; per act 2/5/4/8/8), so `lineage` passes and `lineage-propose` has nothing to propose; lineage tests updated to cover both cases. Suite green.

## Anchor review iteration 4c (2026-11-25, Claude review)

Pass 4, #60-#86 judged. **Pass (18):** bond-wire-fan, photomask-reticle, resist-coated-wafer, wafer-dicing-saw (a real blade at last), memory-chip-array, cross-section-transistor-layers, ceramic-cpu-package, home-computer-motherboard, multi-core-die, laptop-mainboard, graphics-card-board (whole card with bracket), many-core-die-tiles, pixel-shader-lattice, stacked-memory-towers (towers at last), accelerator-package-lid, accelerator-module-coldplate, compute-tray, interconnect-switch-board. **Fix (4):** patterned-wafer-grid and silicon-interposer (cropped at the edges), ic-die-macro (a packaged chip, 3rd time; fresh bare die with a new seed), first-generation-cpu-die (printed words on the chip; fresh with a new seed). Suite green.

## Anchor review iteration 4d (2026-11-25, Claude review)

Pass 4 finished (`run-f117e2161edf4feb`, anchors_complete). #87-#96: 9 pass (rack-backup-batteries fixed); server-rack-front cropped at the bottom every pass -> whole-rack prompt. Standing after pass 4: 77 of 96 anchors pass; 19 queued for pass 5 (iterations 4a-4d). Pass 5 started.

## Anchor review iteration 5a (2026-11-25, Claude review)

Pass 5 finished (`run-b5d34e1a331fdb9a`, anchors_complete): 36 re-rendered anchors judged, **28 pass** (storm without the box, amber rod, candlestick telephone, tube computer, mercury delay line, point-contact transistor, three-legged metal can, CPU die in its ceramic cavity, whole tower, whole rack, and the descendants). **Fix (8, fresh with new seeds):** charged-dust-cloud (faint tripod; close view of the beam only), variable-tuning-capacitor (plates still not interleaved), magnetic-core-plane and core-memory-stack (one oversized ring), discrete-component-board and logic-module-card (modern surface-mount chip; 1960s discrete parts only), dip-chip-in-socket (printed markings), silicon-interposer (cropped). Standing: 88 of 96 pass, 8 queued for pass 6. Suite green.

## Anchor review iteration 6a (2026-11-25, Claude review)

Pass 6 finished (`run-96e49d1484601148`): 13 re-rendered anchors judged, **11 pass** (core plane and stack now evenly studded with dark ferrite rings; component board and logic card with 1960s discrete parts; interposer whole). variable-tuning-capacitor accepted: it renders as a two-gang air variable capacitor with its plates fully meshed, a genuine form of the subject (the half-meshed view never rendered in four tries). **Fix (2):** charged-dust-cloud (a lightning streak in five renders: the act lighting "faint electric glow" draws arcs in any room/sunbeam framing -> macro view of particles on black with a macro style override), dip-chip-in-socket (gull-wing surface-mount legs -> straight through-hole pins into a socket). Standing: 94 of 96 pass; 2 queued for pass 7. Suite green.

## Anchor review complete: all 96 anchors pass (2026-11-25, Claude review per owner instruction)

Pass 7 (`run-2f5c1a2b67bf154a`, anchors_complete, 96 verified): charged-dust-cloud (a glittering ribbon of particles on black, no lightning) and dip-chip-in-socket (blank chip, straight through-hole pins) pass, with their re-rendered descendants glass-leyden-jar and bond-wire-fan. **All 96 film anchors meet `configs/film/anchor-standard.yaml`** after 7 anchors-only passes and 14 fix rounds (`configs/film/anchor-fixes.yaml`). Overview grid of the final set: `outputs/reviews/engineering-film-anchors-final.png` (12x8, film order): one coherent arc from the storm to lightning over the data center, palette moving copper -> steel/phosphor green -> silicon blue across the acts. Systemic lessons recorded above: replace-instruction edits; natural-scene style must override the pack materials and lens; seed changes for details that survive several prompt rounds; fresh keyframes for tightly framed close-ups. Every act edit chain is within the drift limit (max depth 8). Next, per the owner: the full film run (`film-produce all` on fresh v4 batch storyboards; all anchors are cache hits, only the 95 bridges render).

## Owner-requested recheck of all 96 anchors (2026-11-25, Claude review)

The owner asked to recheck all 96 before the film run; the run was held. Re-reviewed every anchor of `run-2f5c1a2b67bf154a` at 624x360 (16 sheets, film order). **91 pass.** Minor notes (not failures): spark-between-spheres stands run off the bottom edge (spheres whole), two battery jars are solid copper, voltaic-pile discs read copper/cloth. **Fail on recheck (5):** early-flat-pack-ic (renders as a thick DIP like #59, faint lid marking), home-computer-motherboard (modern slots and surface-mount parts), hard-disk-platter, interconnect-switch-board and liquid-cooling-manifold (cropped). Fresh keyframes with new seeds; anchors #87 and #92-#96 re-render as edit descendants and will be re-judged. Pass 8 started; the film run waits for it.

## Recheck fixes pass; all 96 anchors pass (2026-11-25, Claude review)

Pass 8 (`run-bc256eef9c303c12`, anchors_complete): the five recheck fixes pass (thin flat-pack with ribbon leads; early-1980s board with through-hole chip rows; hard disk, switch board and cooling manifold shown whole) and their re-rendered descendants pass (server-rack-front, cooling-towers-exterior, data-center-substation, wafer-scale-processor, neural-network-lattice, lightning-over-data-center). All 96 anchors meet the standard. Overview: `outputs/reviews/engineering-film-anchors-final-v2.png`. Full film run started: `film-produce all --batch-dir outputs/production/batches-v5` (anchors are cache hits; the 95 bridges render).

## 2026-11-25 — Second owner-requested recheck of all 96 anchors (iteration 8r)

- Rechecked every anchor of `run-bc256eef9c303c12` on 624×360 sheets with a stricter accuracy and cropping bar.
- 91 pass (all of #49–#96 pass). Fail (5): `spark-between-spheres` (stands cropped), `battery-of-jars` (two jars are
  solid copper cans), `voltaic-pile-column` (no zinc discs), `friction-machine-globe` (leather pad inside the globe),
  `laminated-transformer-core` (coils at the corners instead of around the legs).
- Fix round 8r in `configs/film/anchor-fixes.yaml`: all five become fresh keyframes (seeds 20250125–20250129) with
  explicit structure and whole-object composition; storyboard regenerated; offline suite green.
- Next: anchors-only re-render (`--wait-idle 1 --confirm-gpu`), judge the five and their edit descendants; full film
  run stays held until every anchor passes.
- Pass 8 (`run-b5834d5db1da57e6`, 11 re-rendered anchors: the five fixes plus their edit descendants): 8 pass. Fail
  (3): `spark-between-spheres` (bright cream floor breaks the dark look), `copper-disc-dynamo` (stands cropped),
  `belt-driven-dynamo` (no belt or pulley). Fix round 8a written; storyboard regenerated; suite green.
