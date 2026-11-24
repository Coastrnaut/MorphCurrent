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
- `src/morph_studio/audio_bands.py`: **visualizer-style band loudness** — independent Python reimplementation of the visualizer's music-visualizer algorithm (owner pointed to a local reference checkout, LGPL-2.1; no code copied): Hann-windowed 1024-point FFT per frame, bass/mid/treble 0–3.7/3.7–7.4/7.4–11 kHz, instant and `_att` values relative to the long-term average with frame-rate-adjusted decays (0.2/0.5 short, 0.9→0.992 long); `band_hits` (rising edges > 1.3); `render_timeline_png` (bass red, mid green, treble blue, beat ticks, bridge boundaries).
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
