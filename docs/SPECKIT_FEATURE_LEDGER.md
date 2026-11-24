# MorphCurrent — 40-feature GitHub Spec Kit engineering ledger

**Scope:** F01–F10 are working pipeline milestones; **F11–F30 comprise twenty additional features, of which F11–F13 have offline implementation slices**, evolving MorphCurrent from a working short YAML-to-video pipeline into a long-form, musically synchronized, quality-controlled local creative system; **F31–F40 are a production track for a full-song electrical & compute engineering film** (picture runs the whole soundtrack; may exceed five minutes) built on those capabilities.

**Grounded audit:** GitHub `main` at `882f58e0f35e5e0c1a08b3b3da67af0d72bc8083`, 2026-11-24; associated Windows CI successful, commit reports 222 offline tests. Future Claude sessions must fetch current HEAD and respect concurrent owner edits; never assume this SHA is latest after today.

## Current technical reality (not goals)

- Three **real** ComfyUI API-format exports exist and are bound to actual node IDs: `workflows/01_anchor_t2i.json` (Qwen-Image T2I), `workflows/02_anchor_edit.json` (Qwen Image Edit 2509), `workflows/03_wan22_flf2v.json` (Wan 2.2 I2V FP8 high/low experts). Versioned profile JSONs at `configs/profiles/` and live schema fixtures exist; keep them stable.
- Python implementation already includes `anchors.py`, `bridge.py`, `dag.py`, `render.py`, `qa.py`, `stitcher.py`, `provenance.py`, `vram.py` and supporting schemas, tests, command-line UX and Windows CI. The latest audited commit reports **222 passing offline tests**. Recheck locally rather than blindly repeating that result.
- `MC-RUN-001` generated orchid→butterfly→phoenix using Qwen image generation/reference editing, completed two 832×480/65-frame/16-fps Wan bridges, and joined a verified **129-frame** H.264 movie after owner review. Original bridge quality was weak in parts despite no QA flags. See `docs/EXPERIMENTS.md` and the end of `docs/PROGRESS.md`.
- `MC-RUN-002` selectively regenerated the **phoenix** from a more front-facing prompt and reran only the butterfly→phoenix bridge; the orchid, butterfly and earlier bridge were reused. Result was joined without a hard cut, though a mid-bridge wing fold remains. MC-RUN-003 then recomputed all five GPU stages from a fresh output root; all three anchors, both bridges, and the final 129-frame movie were byte-identical to MC-RUN-002 (decoded PSNR ∞ and SSIM 1.000). This proves reproducibility under those recorded conditions, not artistic perfection or general determinism across different driver/model versions. The current final output name is `<storyboard>_<UTC timestamp>_<plan8>.mp4`; manifest tracks the actual path.
- GPU memory observations come from an opt-in **whole-GPU** `nvidia-smi` sampler, not per-model or per-process allocations. **Wan high/low-noise, UMT5, VAE and Qwen model hashes are now measured** (owner-approved F11 T010; see `docs/MODELS.md`). Longer-form music alignment and calibrated quality review are not yet demonstrated. A clean **from-scratch** reproduction was verified in MC-RUN-003; new features require their own acceptance evidence.
- **F11–F13 current state:** `specs/011-measured-gpu-benchmarks`, `012-reference-anchor-continuity`, `013-physical-morph-choreography` and their implementation modules (`perf.py`, `geometry.py`, `prompt_compiler.py`) exist. F11's Wan model hashing is complete; the completed T011 benchmark matrix is not documented at this audited HEAD. F12 needs owner-calibrated creative acceptance; F13 needs a fixed-seed GPU A/B comparison. No new speculative model IDs or empty spec directories are needed.
- **Operational truth:** `docs/PROGRESS.md` is an append-only historical record, so older entries contain stale `BLOCKED` states. Its *latest dated entries* and real code/tests control current factual status. Do not rewrite old evidence as if it never happened.

## Definition of end-state for F11–F30

From a local storyboard (and optionally an owner-licensed audio file), the user can generate and refine compatible anchor images, physically meaningful morph bridges, and multi-minute synchronized movies. Local tools present previews and correction controls; every result is resumable, content-addressed, measurable, and approved according to a transparent quality policy. No externally hosted image/video inference, advertisements, remote workflow server, or automatic model downloads. A working 8-second demo is a baseline, **not** proof of this end state.

## F01–F10 — preserved and current verified status

| Logical ID | Existing Spec Kit directory | Audit status | Evidence / limitation |
|---|---|---|---|
| F01 | `specs/001-safe-baseline-provenance/` | **COMPLETE** | Read-only safety/preflight, existing Wan bridge |
| F02 | `specs/002-image-workflow-onboarding/` | **COMPLETE** | Installed Qwen Image/Edit workflows, pinned binding profiles |
| F03 | `specs/003-first-anchor-t2i/` | **GPU-VERIFIED** | Qwen T2I anchor generated in MC-RUN-001 |
| F04 | `specs/004-reference-edit-anchors/` | **GPU-VERIFIED** | Qwen edits generated butterfly and phoenix |
| F05 | `specs/005-storyboard-task-dag/` | **COMPLETE (offline)** | Deterministic storyboard DAG and 4n+1 timing |
| F06 | `specs/006-generated-anchor-bridges/` | **GPU-VERIFIED** | Two 832x480 Wan FLF2V bridges with byte-identical shared anchor |
| F07 | `specs/007-recovery-provenance-metrics/` | **PARTIAL — OFFLINE-PASS** | Crash-resume and sampled overall GPU VRAM; Wan model hashes / isolated VRAM not complete |
| F08 | `specs/008-quality-selective-rerender/` | **PARTIAL — GPU-EXERCISED** | Selective phoenix rerender proven in MC-RUN-002; QA missed some real artistic defects |
| F09 | `specs/009-seam-safe-join/` | **GPU-VERIFIED** | 129-frame real seam-verified join, optional audio mode not evidenced |
| F10 | `specs/010-one-command-render/` | **GPU-VERIFIED + REPRODUCED** | MC-RUN-003 from-scratch run produced byte-identical anchors, both bridges and final MP4 |

These original ten scope definitions and existing specification directories are preserved below. Do not recreate `specs/001-...` through `specs/010-...`, reset their completed evidence, or claim that the presence of `tasks.md` alone proves successful GPU validation.

## Existing F01–F10 feature specifications (preserved)

### F01 — Preserve successful Wan bridge; establish GPU-safe, factual baseline

**Purpose.** Reconcile the current code and experiment log, protect in-progress jobs, and create a redacted reproducibility/health report.

**Build:** Verify current `git status`, HEAD, `python scripts/windows/speckit.py --status` + `--verify`, existing 15-node Wan export and hash-pinned profile, CLI tests and real `/history` evidence. Detect active ComfyUI `/queue` read-only. Document model hashes still missing and VRAM snapshots that are not true peak readings. Define clear consent checks and queued-job exclusion for future multi-stage execution.

**Acceptance:** Existing `bridge --confirm-gpu`, resume, targeted cancel and verified-output tests still pass; no new jobs queued, reset/reinstall, model hashing of huge weights or GPU interruption while another run is active. Record baseline test count, commit SHA and blockers. Create a redacted `docs/ENVIRONMENT.md` only with actual measured details.

### F02 — Onboard real local T2I and reference-edit workflows

**Purpose.** Supply the *missing* image-generation capability without inventing node IDs, models or installed dependencies.

**Build:** Read-only inventory of ComfyUI checkpoints, text encoders, available edit nodes, `/object_info`, model license/VRAM constraints and real user installation. Select one compatible local T2I workflow (candidate families: FLUX/Qwen Image) and one image-to-image/reference-edit workflow, subject to actual model availability, licensing and owner approval. Export **only working** ComfyUI graphs in API format as `workflows/01_anchor_t2i.json` and `workflows/02_anchor_edit.json`; create separate versioned semantic binding profiles with image output/seed/prompt/dimensions/reference roles and schema fixtures. Explicitly request owner approval for absent weights/custom nodes; never download automatically.

**Acceptance:** Each real graph passes class/input/model-choice validation against installed `/object_info`, bindings pin actual graph SHA, outputs are image types and no path/secret leaks. When no compatible edit model is installed, record GPU gate **BLOCKED**, with a separate opt-in independent T2I fallback design—not a forged reference-edit export.

### F03 — Generate the first anchor automatically from storyboard text

**Purpose.** Produce the first image without manually uploading a source anchor.

**Build:** Implement typed local `AnchorRequest`, real T2I graph semantic patch and execution; safely submit, monitor history, download/verify PNG/JPEG dimensions, record model/version, seed, prompt, graph/hash, image SHA and output manifest. Reuse ComfyUI client and stage-journal primitives. Validate ComfyUI output image naming and failure states. Provide dry-run and `anchor generate` or equivalent CLI.

**Acceptance:** Offline fake ComfyUI tests cover success, model missing, invalid graph, wrong output shape, lost response, empty output, checksum mismatch. One bounded owner-approved local GPU image render yields verifiable anchor A; if model is absent, leave GPU gate blocked and mocks passing.

### F04 — Generate a compatible last anchor from the first (and B→C)

**Purpose.** Make an *actual* reference-guided A→B (and B→C) possible with shared camera, color and geometry.

**Build:** Implement `reference_edit` input image upload, reference-strength/crop/style fields only where verified in real graph, target concept prompt and deterministic seed. Reuse parent-anchor bytes as reference. Record provenance parent image SHA and `generation_method`. Provide explicit alternative `independent_t2i` with common composition/style constraints; ask before switching from storyboard-declared reference edit. Generate contact-sheet compatibility preview and allow user-approved image selection.

**Acceptance:** Offline A→B→C tests verify image outputs, no broken references/future cycles, B byte identity shared by both bridges, stable dimensions and immutable images. Reference-edit **GPU-VERIFIED** requires actual model/graph and owner-approved render; fallback is separately labeled and never silently substituted.

### F05 — Compile a full image-and-video storyboard DAG

**Purpose.** Make `configs/sequences/organic-machines.yaml` the single creative entry point.

**Build:** Plan anchor tasks by topological dependency, then `bridge(A,B)` and `bridge(B,C)` tasks using anchor hashes. Extend strict schema only as needed for negative prompts, image generation mode, style lock, seed, reference linkage, per-bridge `4n+1` length, delivery FPS and optional audio. Validate no missing refs, duplicate IDs, circular dependencies, mismatched dimensions or unsupported beat targets; preserve rational timing and existing CLI validation/planner compatibility.

**Acceptance:** No-GPU dry run shows 3 generated anchors + 2 dependent bridge tasks + final output; B is generated only once and shared; deterministic plan hashes; invalid inputs fail before any ComfyUI write operation.

### F06 — Wire generated images into proven Wan 2.2 bridges

**Purpose.** Automatically turn A and B images into a morph video, while preserving the already working manual-pair `bridge` CLI.

**Build:** Reuse validated `03_wan22_flf2v.json`, high-noise/low-noise FP8 expert binding, `bridge.py` idempotent upload, queue guard, resume and ffprobe checks. Supply generated image file paths, semantic prompts/seeds, `L=4n+1`, fps, safe namespace. Run GPU serially; keep pre-existing user queue undisturbed. Ensure an absent model/error cannot trigger fallback to unrelated T2V checkpoint.

**Acceptance:** Mock end-to-end T2I→edit→Wan consumes generated image SHA values, not hand-supplied images; bridge output verified for frame count/dimensions/fps; one owner-approved live generated-A/B bridge tests actual GPU path after dependencies exist. No duplicate `/prompt` on identical resume.

### F07 — Crash-safe multi-stage recovery, model provenance and VRAM observations

**Purpose.** No repeated costly inference after interruption; no fake memory statistics.

**Build:** Root job journal with per-stage immutable hashes, declared dependency models and SHA256 of checkpoint weights, exact workflow versions, real prompt IDs, atomic `.part` file commits, resume and selective retry. Use an **opt-in** `nvidia-smi` time-series during future owner-approved GPU runs, recording measured interval/coverage and distinguishing resident overall GPU use from per-process allocation; do not hash giant models while the current smoke job is active. Reconcile unknown state against queue/history, never global cancel.

**Acceptance:** Mock hard crash after each state transition, missing history, network loss, tampered image and changed model hash; verified stages reused without new GPU submission. If peak VRAM is not sampled, metric remains `NOT MEASURED`.

### F08 — Quality assessment, candidate ranking and selective rerender

**Purpose.** Address mid-morph subject collapse/flaring without destroying good anchor or bridge results.

**Build:** Local frame sampling/contact sheets, endpoint match, temporal sudden-cut/flash/freeze detection, clipping/framing and blur checks. Score as **heuristics**, preserve all candidate seeds/parameters; require human creative approval for subjective quality. Use historical MC-FLF2V-001/003 defects and the revised prompt from `docs/EXPERIMENTS.md` as hypotheses. Rerender only the failed bridge with bounded candidates and explicit GPU approval.

**Acceptance:** Synthetic tests detect hard cuts, freezes, endpoint mismatch and sudden flare; smooth sequence doesn't falsely report a cut; reselect/retry B→C never re-renders verified A or A→B. No assertion that SSIM or PSNR alone proves visual morph quality.

### F09 — Seam-safe MP4 and optional music/beat sync

**Purpose.** Produce an actual Orchid→Butterfly→Phoenix continuous movie rather than disconnected MP4 files.

**Build:** Inspect actual boundary decoded frames; drop duplicates only when verified B matches, otherwise block/repair; normalize PTS, fps, pixel format, audio time base and codecs with native FFmpeg argument arrays (`shell=False`). Two 65-frame segments at 16 fps produce 129 unique frames only if B endpoints match: anchor timestamp span 8.0s vs file playback duration 129/16 = 8.0625s. Add optional owner-supplied licensed audio, BPM/downbeat offset and explicit time reconciliation; no music required for default MP4.

**Acceptance:** Synthetic golden 2-bridge frames prove expected 129 frames, correct endpoints, reproducible codec/timebase and no xfade; mismatched B is flagged instead of blindly trimming. Video-only and music-enabled output both tested separately.

### F10 — One-command native Windows end-to-end product

**Purpose.** From creative text YAML to generated stills, bridge clips, contact sheets, manifest and joined MP4 with one CLI command.

**Build:** Add `morphcurrent render <storyboard> --dry-run`, explicit GPU-authorized execution flag, `--resume`, read-only `--status`, bounded jobs and appropriate offline developer UX. Preserve existing `bridge` CLI. Keep all artifacts in gitignored `outputs/runs/<id>/`, provide user guidance on installing/approving T2I/edit models and downloading/output inspection. Document setup for native Windows, no WSL/PowerShell/Docker cloud inference.

**Acceptance:** With real T2I/edit workflows installed and a separately approved bounded GPU run, YAML alone produces A/B/C images, two verified Wan bridges and final MP4, without manually preparing endpoints or ComfyUI node edits. Repeated run reuses verified stages; missing image model yields precise BLOCKED preflight, not a fake completed video. Offline CI and end-to-end local GPU evidence remain distinct.

## F11–F30 — 20-feature expansion wave

| ID | Proposed Spec Kit folder (verify numbering before creation) | Dependencies | Priority | Initial status |
|---|---|---|---|---|
| **F11** | `specs/011-measured-gpu-benchmarks/` (created) | F07, F10 | P0 | **GPU-VERIFIED** — `perf-report`, `estimate`, timestamped whole-GPU samples; Wan model hashes verified; benchmark matrix (cold/warm 832×480, 640×368) completed 2026-11-24 — see PROGRESS F11 T011 |
| **F12** | `specs/012-reference-anchor-continuity/` (created) | F04, F08 | P0 | **OFFLINE-PASS** — geometry heuristics recorded per child anchor, `anchor-check`; matched three-anchor owner approval pending |
| **F13** | `specs/013-physical-morph-choreography/` (created) | F12, F08 | P0 | **OFFLINE-PASS** — `choreography` → compiled bridge prompts/negatives, `prompt-preview --variants`; fixed-seed GPU A/B pending |
| **F14** | `specs/014-adaptive-transition-ladders/` (created) | F12, F13, F05 | P1 | **OFFLINE-PASS** — `ladder-risk` (prompt distance + F12 geometry), `ladder-propose` (intermediate reference-edit anchors, 4n+1 splits, GPU budget); reviewed multi-hop render pending |
| **F15** | `specs/015-local-audio-beat-mapping/` (created) | F05, F09 | P0 | **OFFLINE-PASS** — tempo/beats/downbeat, visualizer-style bass/mid/treb bands, licence guard, drift report, timeline PNG; real licensed track pending; **US5 layered sync foundation**: `audio-features` (per-frame relative bands + envelopes, flux, onsets, brightness, sections; hashed) and `sync-plan` (event-locked anchors on onsets/energy peaks/sections, beats optional; bridge character; energy-warp maps) — Mozart: 95 bridges, mean 61.4 frames, 75/96 anchors on events |
| **F16** | `specs/016-calibrated-qa-candidates/` (created) | F12, F13, F08 | P0 | **OFFLINE-PASS (partial)** — subject collapse/drift/blur detectors + `qa-calibrate`; collapse recall 2/3 on real clips, drift/blur 0; owner labels pending |
| **F17** | `specs/017-vram-aware-job-scheduler/` (created) | F11, F07, F14 | P1 | **OFFLINE-PASS** — cross-process GPU run lock (heartbeat/stale takeover), `render --max-jobs/--max-gpu-s` pause/resume with no duplicate submissions (exit 8), `schedule` preview; bounded multi-session GPU batch pending |
| **F18** | `specs/018-local-creative-review-ui/` (created) | F08, F15, F16 | P1 | **GPU-VERIFIED** — `review-ui` strictly-loopback local page; owner-requested walkthrough 2026-11-24 on the MC-RUN-004 replay: index, plan view, run page, clips and final movie playing, keyboard-only approve of both bridges recorded in `review.json`, join via CLI; walkthrough fixed a real-browser 403 (Referrer-Policy), raw QA flag text and ambiguous note labels |
| **F19** | `specs/019-resumable-longform-timeline/` (created) | F14, F15, F17 | P1 | **OFFLINE-PASS** — `plan-diff` edit invalidation (Merkle stage identity; lineage rule; prediction = actual submissions in fake-ComfyUI E2E), optional contiguous chapters + `timeline` index/FFmpeg chapters/640×368 proxy, storage report and render disk preflight (exit 9), 2/10/50-anchor and random-restart tests; owner-approved multi-scene GPU resume pending |
| **F20** | `specs/020-release-reproducible-pipeline/` (created) | F11–F19 | P0 final | **GPU-VERIFIED** — `run-compare`, `replay`, `audit`, `run-backup`/`run-restore`, `acceptance`; owner-approved bounded replay MC-RUN-004 reproduced MC-RUN-002 6/6 byte-identical (incl. final movie); `v0.1.0-rc1` tagged with owner approval |
| **F21** | `specs/021-style-packs-asset-library/` (created) | F12, F18 | P1 | **OFFLINE-PASS** — versioned style packs with inheritance, per-scene overrides, pack SHA-256 in plan identity, private-library asset checks; `engineering-noir` packs for the film |
| **F22** | `specs/022-story-brief-to-storyboard/` (created) | F14, F18, F21 | P1 | **OFFLINE-PASS** — `brief-plan`: deterministic brief → schema-valid storyboard with choreography, style pack, 4n+1 timing and preview; 8-scene engineering pilot generated; Claude Desktop pre-drafting + `draft-check` (model/node/URL text rejected) — no local LLM |
| **F23** | `specs/023-camera-framing-keyframes/` (created) | F12, F13, F14 | P1 | **OFFLINE-PASS** — `transitions[].camera` (10 moves + amount) compiled to a deterministic clause labelled *prompt-only approximation* (installed Wan FLF2V has no camera input; `control: graph` refused), endpoint satisfiability from F12 anchor geometry, per-anchor framing targets and 16:9/9:16 safe-area crops, `camera-check`; real organic-machines anchors static-satisfiable; operator two-bridge GPU test pending |
| **F24** | `specs/024-temporal-shape-stability/` (created) | F13, F16, F23 | P0 quality | **OFFLINE-PASS** — `continuity` (shape substitution, topology, background, motion and colour jumps on a clip-level mask; thresholds fixed before evaluation), `continuity-eval` on labelled real clips (by kind collapse 2/3, drift 0/1, blur 0/2; any-detector-in-window 2/3, 1/1, 2/2; 4 unlabelled flags), `repair-propose` (refinements + intermediate anchor, nothing rendered), `repair-compare` (endpoint check, capped verdict); owner-approved controlled repair render pending |
| **F25** | `specs/025-optical-frame-interpolation/` (created) | F09, F15, F24 | P1 | **OFFLINE-PASS** — `interpolate` (16→24/30/48/60 fps; repeat/blend/motion; new file + provenance sidecar; duration-exact via clone-pad + trim; anchor-mark alignment report; blend refused across hard cuts) and `warp-apply` (energy-warp retiming with pinned endpoints and unchanged duration); real: MC-RUN-004 movie → 24 fps, 33/33 anchors exact; Mozart warp on a real bridge, endpoints exact; owner look review pending |
| **F26** | `specs/026-upscale-visual-finishing/` (created) | F11, F24, F25 | P1 | **OFFLINE-PASS** — `finish` geometric 1080p/1440p (Lanczos; fit+pad or fill+crop; optional denoise/deblock/sharpen; per-channel colour match to an anchor; new file + record; identity check of first/last frames); real MC-RUN-004 movie → 1920×1080 in ~1 s, identity MAD 0.72–0.96 (≤ 4); owner approved a 1080p learned upscaler — RealESRGAN_x2plus download consent + exported ComfyUI workflow pending (T016) |
| **F27** | `specs/027-workflow-model-capabilities/` (created) | F02, F11, F17 | P1 | **OFFLINE-PASS** — `registry` (per profile: capability, workflow checksum, roles, output kind, node classes, models by role with licence/hash from `configs/model_catalogue.json`, object_info constraints incl. Wan 4n+1; status ready / offline-unverified / stale-hash / missing-node / missing-model / contract-error / cloud-node), `registry-diff` (compatible / needs-rebinding / incompatible), owner-approved `registry-select` with append-only history and `registry-rollback`; production profiles stay defaults; `upscale` capability contract added; live read-only check: all 3 production profiles `ready`; alternative owner-installed workflow pending (T015) |
| **F28** | `specs/028-project-archive-migration/` (created) | F07, F19, F21 | P1 | **OFFLINE-PASS** — `project-export` (storyboard, style chain, profiles + workflow exports, model catalogue, `project.json` with plan checksum, registry statuses and model/licence report; optional run provenance with local paths redacted; media/music only with owner authorization; weights always refused; checksum list), `project-inspect` (checksums, unsafe/reserved/ADS/case-colliding names, duplicates, member/size/ratio limits, future formats, duplicate IDs, absolute paths; nothing written), format-0 migration of F20 run backups with rollback, `project-import` (staged, never overwrites) + replay readiness; real organic-machines run re-plans to the same plan checksum in a second directory; owner restore review pending (T016) |
| **F29** | `specs/029-budgeted-experiment-optimizer/` (created) | F11, F16, F17, F24 | P1 | **OFFLINE-PASS** — `experiment-plan` (one-bridge definition; factors limited to bound Wan inputs with 4n+1 / step-16 checks; leakage refused; baseline + factorial × seed block in fixed order; content-hashed candidates deduped on effective values; measured-history estimates or NO DATA; over-budget candidates deferred), `experiment-run` (one candidate at a time via `run_bridge`, validate-only without `--confirm-gpu`, append-only results, resume, run/GPU budget stop, early stop per level), `experiment-rate`, `experiment-report` (per-level means, length mismatches, Pareto over rating/GPU s/size, observational caveat); real orchid→butterfly plan (4 candidates, 992 s known) validated live with nothing queued; bounded GPU comparison + owner review pending (T013) |
| **F30** | `specs/030-delivery-presets-release-audit/` (created) | F18–F29 | P0 final | **OFFLINE-PASS** — `deliver` with 7 versioned presets (16:9 1080p, 9:16 1080×1920, 1:1 1080, video-only, licensed-audio, 1440p, smooth 24 fps; recipe checksums; probe-verified size/fps/codec/audio/duration; mpeg4 fallback recorded; crop safe-area report from first/last frames), `acceptance --through 30|40`, `release-check` (matrix + audit; never tags); real MC-RUN movie delivered landscape/vertical/smooth in 7.5 s, all verified, vertical crop flags the subject outside the 9:16 safe area; release-check: 12/30 evidenced, audit clean, not ready; final owner-approved multi-scene demo pending (T013) |

`specs/011-*` through `specs/013-*` are already real feature directories. F14–F40 remain proposed; create one spec at a time with installed Python Spec Kit and preserve the existing directory/feature mapping.

### F11 — Reproducible A6000 performance and model provenance

**Purpose:** Turn whole-GPU snapshots into interpretable repeatable cost/performance evidence without harming existing workloads.

**Build:** Provide opt-in measured stage timers, correct whole-GPU VRAM coverage and other-process baseline, owner-approved idle-queue Wan checkpoint SHA-256 inventory, driver/torch/ComfyUI provenance, GPU memory pressure detection and conservative cost estimates. Benchmark warm vs cold cache, Qwen T2I, Qwen edit, Wan 640x368 vs 832x480, safe model offload; never imply whole-GPU usage is MorphCurrent-only.

**Tests / evidence:** Mock nv-smi samples including missing intervals and concurrent external process; numerical report and no fake per-process peaks; real A6000 samples only when owner authorizes a bounded run; regression with MC-RUN-001/002 historical data.

**Acceptance gate:** Report explicitly distinguishes MEASURED / ESTIMATED / NOT MEASURED; no unapproved model hashing or disruptive jobs.

**Status (2026-11-24):** F11 OFFLINE-PASS, with T010 verified: the Wan expert, UMT5 and VAE files were SHA-256 hashed under owner consent and recorded in `docs/MODELS.md`. T011 benchmark renders were subsequently started according to historical `docs/PROGRESS.md`; the audited GitHub HEAD has **no completed matrix results yet**. Inspect the local GPU queue/history and latest commits before rerunning anything.

### F12 — Composition-aware anchor generation and reference-edit QA

**Purpose:** Stop the subject-scale, profile and camera-direction drift that caused the original side-on phoenix and right-moving butterfly.

**Build:** Add anchor geometry contract: subject centroid, bounding extent, silhouette orientation, key color/material palette, background/camera continuity, explicit frontal/rear/side view constraints. Provide compositional targets and negative prompts per anchor, optional local reference image guidance if real nodes support it, image-to-image candidate comparison and immutable approvals. Do not claim pixel heuristics alone know wing anatomy.

**Tests / evidence:** Synthetic anchor shifts/crops/background changes, real generated B/C evaluation, unchanged parent SHA and lossless shared boundary, mismatch and manual approval paths; record improvements against MC-RUN-001/002.

**Acceptance gate:** Owner-approved matched three-anchor set without accidental layout/scale shifts; no undisclosed independent-T2I fallback.

**Status (2026-11-24):** OFFLINE-PASS in `specs/012-reference-anchor-continuity` — see docs/PROGRESS.md F12 entry.

### F13 — Physical correspondence and prompt orchestration

**Purpose:** Improve mid-morph collapse, flare and sudden subject replacement via structured transformation plans rather than generic prose.

**Build:** Represent physical correspondences (petals→wings→feathers, stem→torso/tail), material continuity, permitted camera motion, negative constraints, and temporal beats. Compile readable positive/negative prompt variants from user-authored templates and validated role maps; preserve seed/control comparisons; avoid claims that a text prompt can guarantee motion. Provide preview of proposed changes and reversible variants.

**Tests / evidence:** Golden prompt-format/escaping fixtures, fixed-seed prompt-only A/B experiments, manual review of collapsed midframes; do not conflate sampler/length changes with prompt effects.

**Acceptance gate:** At least one user-approved candidate demonstrably better on defined defects, or report an honest negative result.

**Status (2026-11-24):** OFFLINE-PASS in `specs/013-physical-morph-choreography` — see docs/PROGRESS.md F13 entry.

### F14 — Intermediate anchors and variable-length morph routing

**Purpose:** Handle distant subject concepts that one Wan bridge cannot morph smoothly.

**Build:** Predict continuity risk using explicit interpretable heuristics and user controls; split A→D into A→B→C→D if requested; generate intermediate images through existing T2I/edit graphs, preserve ancestor hashes, define beat budgets and 4n+1 for each segment; prevent combinatorial explosion with max anchors/GPU budget and proposal approval.

**Tests / evidence:** DAG branching/length math, shared-asset hashes, retry only affected subchain, variable 49/65/81 length joins, impossible beat targets and max-budget failures.

**Acceptance gate:** At least one reviewed multi-hop project with correct endpoints, no duplicate/untracked prompts, and verified seam math after approval.

### F15 — Music analysis, beats and frame-accurate sync

**Purpose:** Go beyond manual 120 BPM and align transitions to real user-provided soundtrack structure.

**Build:** Add offline audio import, licensed-local-file guard, BPM/onset/downbeat detection with confidence, **a visualizer-style audio feature track** (per-video-frame relative bass/mid/treb with attack/release envelopes, vol, spectral flux, onset strength, brightness; sections) and an **event-locked anchor planner** that works without reliable beats (see `docs/MUSIC_SYNC.md`), half/double-tempo safeguards, audio section markers, human correction, variable bridge beat budgets, 4n+1 rounding/retime with explicit drift report and FFmpeg mux. Work without audio remains supported; never fetch music, upload it or silently retime copyrighted tracks.

**Tests / evidence:** Synthetic click tracks and silence, 90/120/140 BPM, time offsets, transitions on beats with bounded error, sample-rate and stereo mono cases, negative or missing files, no-audio end-to-end.

**Acceptance gate:** User-approved licensed sample produces measured beat alignment and verified no silent drift; manual override always possible.

### F16 — Quality calibration and bounded candidate search

**Purpose:** Correct the false-negative QA behavior seen in MC-FLF2V-003 and MC-RUN-001.

**Build:** Gather local owner-reviewed representative frame windows, derive labels for subject collapse/off-screen motion, flare, abrupt shape substitution, focus/blur and endpoint mismatch; evaluate heuristics/optical flow with precision-recall rather than a single magic scalar. Generate bounded seed/prompt candidates, rank with uncertainty, request human selection; preserve every trial and price/VRAM budget.

**Tests / evidence:** Synthetic hard cut/flash/freeze plus real labelled negative/positive windows, threshold calibration without train/test leakage, rerender-selection safety; no automatic acceptance when QA is uncertain.

**Acceptance gate:** Show improved measured defect recall on held-out owner-labelled clips without unacceptable false positives; preserve human override.

### F17 — Queue and memory-aware local execution planner

**Purpose:** Run longer projects efficiently without oversubscribing 48 GiB or trampling other desktop workloads.

**Build:** Single-GPU bounded scheduler, read-only queue and per-stage resource preflight, stage grouping by model only when DAG permits, optional unload/offload strategy as owner-approved experiment, pause/resume without global interrupt, lock/concurrency policies across multiple MorphCurrent instances, GPU job budget/time ceilings. No speculative multi-GPU code required.

**Tests / evidence:** Competing queue jobs, concurrent controllers, OOM backoff, crash during reservation, idempotent resume, timeout, no reordering that violates anchor dependencies.

**Acceptance gate:** Owner-approved mixed anchor/bridge batch completes with no duplicate submissions or interruption of unrelated ComfyUI jobs.

### F18 — Interactive local review, timeline and preview experience

**Purpose:** Make the pipeline usable without hand-editing YAML and manually locating every MP4.

**Build:** Select native local Python GUI (or strictly loopback UI after explicit design review) with storyboard editor, anchor/contact-sheet previews, transition timeline, positive/negative prompt editor, model availability, GPU budget, per-stage state, candidate comparisons and approve/reject actions wired to manifest. No hosted server, logins, tracking, subscriptions or cloud media upload. CLI remains authoritative and functional.

**Tests / evidence:** Local UI/CLI parity, malformed/storyboard injection, failed run/resume, missing media, stale previews, disabled GPU action by default, accessibility keyboard controls.

**Acceptance gate:** Operator can plan, inspect and approve an Orchid→Butterfly→Phoenix project locally without opening ComfyUI graph; no involuntary rendering.

### F19 — Long-form sequencing, chapter controls and resource limits

**Purpose:** Scale from the validated 8-second demonstration to many scenes and multi-minute songs.

**Build:** Storyboard sections/chapters, arbitrary N anchors and dynamic link planning, beat-level segment lengths, automatic checkpoint and cache reuse, scene reorder/insert/delete invalidation rules, preview/proxy mode, disk quota and storage accounting, resumable partial render, out-of-order artifact verification and final index/manifest; no blind giant GPU batches.

**Tests / evidence:** Two/ten/fifty anchors, randomized DAG restarts, shared anchor reuse, scene edits invalidating only dependent stages, missing disk and interrupted concat, frame/PTS/duration integrity.

**Acceptance gate:** Owner-approved bounded multi-scene video with successful resume and no unnecessary re-inference; no requirement to run GPU for every test.

### F20 — Production acceptance, reproducible replay and Windows delivery

**Purpose:** Turn technical experiments into a maintainable, trustworthy native Windows local creative product.

**Build:** Fresh-output-root replay (not just warm-cache resume), source/license/hash audit, recorded deterministic conditions and known nondeterminism, complete acceptance matrix for T2I→edit→Wan→QA→join→music, CLI and optional UI help, file migration, installer or wheel packaging options, release guide, CI/Windows smoke harness, backup/restore and user-facing errors. Never bundle weights or model licenses implicitly.

**Tests / evidence:** Clean room controller install on Windows, offline 193+ regression baseline, real bounded fresh run with approved models, reproducible output comparisons (decoded frames vs byte hashes, with documented variance), no unauthorized network calls, user review of final longform sample.

**Acceptance gate:** Every F01–F20 required acceptance gate is evidenced or explicitly listed as an unresolved blocker; release tagged only after owner approval.

### F21 — Local style packs, prompt presets and asset collections

**Purpose:** Allow repeated shots to share a deliberate visual language without copying fragile prompt text between storyboards.

**Build:** Develop versioned user-owned style packs covering palette, materials, lens/camera, composition, lighting, negative prompts, aspect ratios and reference-image identity. Provide local collection browsing/search, provenance and licensing notes, stable IDs and an explicit style inheritance/override contract; import only user-approved local assets. Resolve style/preset hashes into existing storyboard and artifact DAG identities; never auto-publish media or include private assets in Git.

**Tests / evidence:** Mock library creation, reference relocation, stale/missing assets, safe path resolution, controlled style overrides, deterministic hash invalidation and preview/CLI parity; confirm no silent rewriting of existing artist prompts.

**Acceptance gate:** Three linked scenes share a reproducible style pack and retain user-controlled per-scene overrides; all assets remain local and private.

### F22 — Creative brief to editable storyboard and shot planner

**Purpose:** Take the user from one creative idea to a real editable multi-scene YAML plan before any GPU rendering.

**Build:** Parse a natural-language brief into explicit concepts, anchor progression, physical morph correspondences, beat/length budget, camera/storyboard constraints and candidate prompt text. Default deterministic rule/template compiler. Creative drafting (briefs, storyboards, prompts) is done in Claude Desktop sessions as text only and checked locally (`draft-check`); no local LLM is used (owner decision 2026-11-24) and no user media is uploaded. Always validate schema, display the generated plan, expose edits and require approval before running.

**Tests / evidence:** Golden creative briefs, ambiguity/error reporting, hallucinated model/node prevention, deterministic templating, unsafe filename injection, plan-version history and no GPU side effects.

**Acceptance gate:** A human can create and edit an eight-scene plan from a single brief and a dry-run reports all generated tasks correctly without queued inference.

### F23 — Camera trajectories and spatial consistency constraints

**Purpose:** Control camera motion intentionally rather than relying on vague movement words that cause object drift and mismatched endpoints.

**Build:** Introduce shot-level camera locks, safe pan/zoom/orbit targets, framing grids, subject center/size targets and optional keyframe trajectories. Use only motion controls demonstrably supported by the installed ComfyUI workflow; otherwise compile a labelled prompt-only approximation and expose its limits. Preserve shared anchor views, lens/perspective consistency and temporal budgets; provide previews and diagnostics.

**Tests / evidence:** Static-to-moving shot transitions, out-of-bounds keyframes, 16:9/9:16 aspect constraints, unsatisfiable endpoint views, deterministic prompt mapping, and explicit failure on absent graph controls.

**Acceptance gate:** Operator-approved test shows stable camera/subject geometry for at least two linked bridge clips, with measured bounds and no invented node parameters.

### F24 — Temporal shape/material continuity and repair

**Purpose:** Reduce the specific wing collapse, disappearing petals, mid-shot flares and sudden visual substitutions documented in earlier runs.

**Build:** Develop interpretable frame-wise shape occupancy, appearance flow, background persistence, subject topology proxies and motion-path diagnostics. Propose material-continuity prompt refinements or local intermediate-anchor corrective renders for owner review; avoid fake dissolves or claims that optical flow proves physical identity. Version repair provenance and compare the same endpoints/seeds/steps under controlled interventions.

**Tests / evidence:** Labelled MC-RUN-001/002 failure windows and held-out synthetic deformations, tolerance for genuine motion, repair affecting only failed bridge, seam/endpoint stability, no apparent success based solely on automated QA score.

**Acceptance gate:** At least one independently reviewed improvement in a known collapse/flare failure, with controlled comparison and no degradation of first/last frames.

### F25 — Locally computed motion interpolation and delivery frame rates

**Purpose:** Deliver smoother motion at 24/30/60 fps without confusing added interpolated frames with original Wan inference frames.

**Build:** **Energy-warped retiming** (playback progress inside a bridge follows the music's cumulative energy from the F15 feature track; anchor frames pinned to their times; speed clamped 0.5×–2×), plus postprocessing profiles for FFmpeg-native and optionally verified local optical-flow/model-based interpolation, with explicit cadence mapping, PTS preservation, anchor/seam protection (anchor frames sit on 4-frame multiples at 16 fps and must keep their timestamps so music sync survives 16→24/30/48 fps conversion) and fallback on motion failures. Interpolation runs only on produced/approved clips or verified assembled movies, and its algorithm/version and artifacts are hashed separately from original inference. Keep 16 fps originals lossless/immutable.

**Tests / evidence:** Synthetic moving object, hard scene cut and shared-boundary tests, odd frame counts and rational 16→24/30/60 rates, interpolation around seam and frozen-frame handling, ffprobe timing and audio sync.

**Acceptance gate:** User-approved interpolated output maintains seam integrity and accurate real-time duration; original 16 fps movie is unchanged.

### F26 — Local resolution enhancement and finishing pipeline

**Purpose:** Turn initial 832×480 renders into higher-quality output while respecting local memory/time limits and avoiding invented detail.

**Build:** Add opt-in local upscaling, denoise, deblock, sharpen and color/palette-match stages; use native FFmpeg where adequate and only verified owner-installed GPU models when approved. Separate geometric resampling from hallucination-prone generative enhancement; support tile budgeting and staged CPU/GPU selection. Record codec, color space, bit depth and VRAM estimates.

**Tests / evidence:** Synthetic fine-texture/edge cases, color/alpha transfer, tile seams, CPU fallback, OOM simulation, before/after perceptual and endpoint comparisons, transparent quality limitations.

**Acceptance gate:** At least one reviewed high-resolution delivery with measured memory/time and no altered approved anchor identity or temporal artifacts.

### F27 — Multi-workflow local model capability registry and safe upgrades

**Purpose:** Support future local image/video models without embedding hard-coded Qwen/Wan node IDs throughout product logic.

**Build:** Registry of actual locally installed model capabilities, image/video formats, input roles, frame constraints, required VAE/text encoders, verified licenses and ComfyUI graph/profile SHA. Add versioned semantic adapter migration/compatibility preview and a rollback path; require user approval for any download, custom node or changed model graph. Preserve production Qwen/Wan defaults and offline operation.

**Tests / evidence:** Two mocked versioned profiles, missing node/model, changed input constraints, incompatible output, stale hash, migration/backout, no cloud-node acceptance, no unapproved model installs.

**Acceptance gate:** One explicitly owner-installed alternative local workflow can be inspected, bound and exercised safely without breaking or silently replacing current Wan and Qwen profiles; if none, offline registry remains OFFLINE-PASS.

### F28 — Portable project archives, manifest migrations and local backup

**Purpose:** Allow safe sharing/backing up a creative project without losing its reproducibility or leaking private media by default.

**Build:** Design portable project-package schema with storyboard, style references, versioned profile metadata, chosen outputs and hashes, selective media inclusion, explicit license/missing-model report, migration checks and restore into a sandboxed local directory. Protect against zip-slip, excessive archive expansion, path traversal, foreign absolute paths, duplicate IDs and future schema versions. Never bundle model weights or user music unless owner explicitly authorizes eligible media.

**Tests / evidence:** Round-trip archive and replay-plan checks, Windows path cases, bad hash and corrupt bundle, zip-slip and archive bomb thresholds, absent models, migration rollback, optional private-media exclusion.

**Acceptance gate:** Export/import of a multi-bridge project preserves its editing and provenance context and restores safely on a second Windows directory without unsafe writes or inference.

### F29 — Structured local A/B experiments and quality-vs-cost optimization

**Purpose:** Explore settings systematically rather than guessing seed, prompts, lengths, expert schedules or resolution adjustments.

**Build:** Typed experiment matrix with fixed controls, variable factors, GPU-time/frame budget, run count limits, seed blocks, candidate hashes and early-stop rules. Compare Pareto frontiers for owner-rated quality, runtime, VRAM and artifact size; preserve all original approved outputs, no automated global queue saturation and no silent model-parameter changes outside real node contracts.

**Tests / evidence:** Factorial design generation, reproducibility and cache reuse, budget exhaustion, baseline/control leakage, mismatched output lengths, Pareto ordering, interrupt/resume and test-double scheduler enforcement.

**Acceptance gate:** One owner-approved bounded comparison yields a human-readable causal experiment report with explicit variables, measured timings, review notes and Pareto choices (not false scientific certainty).

### F30 — Multi-format cinematic delivery and final 30-feature acceptance

**Purpose:** Make a complete trustworthy creative workflow for personal local use across formats and project lengths, beyond the first eight-second demonstration.

**Build:** Define local export presets for landscape 16:9, vertical 9:16, square, video-only, licensed-audio video, high-resolution and smooth-FPS products. Preserve safe areas and reframing, color profiles, subtitle/metadata policy where owner-provided, container/codec capabilities and deterministic versioned export recipe. Audit installation, CLI/UI, local-only privacy, model licensing, archive restore, long-form checkpointing, QA review, frame/PTS/audio sync and release documentation. No ads/remote inference.

**Tests / evidence:** Cross-format ffprobe golden fixtures, vertical crop subject bounds, codec failure/fallback, licensed music continuity, frame interpolation/finishing interoperability, fresh-root and archived-project replay, Windows CI and owner-reviewed GPU demo with noninvented evidence.

**Acceptance gate:** Final owner-approved demonstration of a multi-scene local project with optional synced audio and at least two delivery presets; each required F01–F30 gate has real evidence or an explicit unresolved blocker. Never declare release complete solely from tests.

## F31–F40 — Production track: full-song electrical & compute engineering film

**Goal:** plan and produce a local morph film that runs for the **full length of the song** (≈ 6 min for the licensed Mozart track; may exceed five minutes) that travels through the history and inner workings of electrical and compute engineering — for example lightning → Leyden jar → voltaic pile → dynamo → power grid and transformer → telegraph key and waveforms → vacuum tube → transistor → integrated-circuit die → microprocessor → GPU → data-center rack → AI accelerator — as one continuous chain of physical metamorphoses. F31–F40 *use* F11–F30 capabilities (long-form timeline, music sync, style packs, QA, scheduling, finishing) and add what this specific production needs. All start **PLANNED — NOT IMPLEMENTED**.

**Planning numbers (owner decision 2026-11-24: the picture runs for the full length of the chosen song; five minutes was only a recommendation and the film may run longer).** The licensed track `assets/music/mozart-symphony-40-i-molto-allegro-musopen.opus` is **358.822 s**. Bridge count N = ceil((song_s × fps − 1)/(L − 1)); at 16 fps with 65-frame bridges (4 s anchor span) that is **90 bridges + 91 anchors**. ESTIMATED from measured history in `configs/perf_history.json` (F11 benchmarks 2026-11-24: bridge ≈ 496 s and edited anchor ≈ 50 s at 832×480; bridge ≈ 240 s and anchor ≈ 36 s at 640×368): ≈ **13.7 GPU-hours** at 832×480 or ≈ **6.9 GPU-hours** at 640×368. 81-frame (5 s) bridges would cut the count to 72 (+73 anchors), but their cost is NO DATA until measured. If the soundtrack changes, recompute from its measured duration. Every batch needs explicit bounded owner approval.

### Music synchronization design (planned; owner direction 2026-11-24)

**Layered, visualizer-informed strategy (owner direction 2026-11-24; full analysis in [`docs/MUSIC_SYNC.md`](MUSIC_SYNC.md)).** A real-time music visualizer syncs to *any* song without beat tracking: self-normalized band energies (bass/mid/treb relative to their own long-term average, with attack/release envelopes), onsets as the only events, and a continuous mapping from energy to motion. MorphCurrent adopts the same principle within Wan's constraints: one hashed **audio feature track** per song drives (1) acts from sections, (2) **event-locked anchor timing** — onsets, section starts and energy peaks, with downbeats only as an optional refinement when the beat map is owner-verified or confident, (3) per-bridge prompt character from band energy, (4) **energy-warped playback** inside each bridge (progress follows cumulative energy, anchors pinned, 0.5×–2× speed via F25 interpolation) and (5) optional finishing pulses. The numbered rules below remain valid where they concern frame math, holds, interpolation and verification; where they say "downbeat", read "chosen musical event".

The film is **musically synchronized**: picture structure follows the music's structure, and every
anchor (the moment the frame *is* a concept image) lands on a musical event. Grounded in the F15
analysis of the licensed track (`assets/music/mozart-symphony-40-i-molto-allegro-musopen.opus`):
duration 358.8 s; detected pulse 215.4 BPM with a 107.7 BPM alternative — consistent with the half-note
beat of this cut-time (2/2) *Molto allegro*, i.e. a bar ≈ 1.11 s; tempo spread ±21 BPM (live orchestral
rubato) and **low beat confidence (0.215)**; 10 section-novelty boundaries (23.4, 48.3, 79.4, 134.2,
162.7, 179.4 s, …). Consequences: a constant-BPM grid would drift audibly, and the automatic beats must
be checked by ear before anything is rendered.

1. **Sync hierarchy.** Music section → film act; phrase (normally 4 bars) → one bridge; downbeat → anchor
   landing; individual beats inside a bridge are *not* controllable (Wan generates continuous motion) and
   are not promised.
2. **Beat map (single source of timing).** `configs/beatmaps/<track>.json`: audio SHA-256, beat times,
   downbeats with bar numbers, phrase starts, sections (sonata form: exposition / development /
   recapitulation / coda as identified by ear), tempo curve, analyzer version and an `owner_verified`
   flag. Built from `audio-analyze` output plus owner corrections (moving or adding downbeats, fixing
   the half-/double-tempo choice, confirming whether the exposition repeat is played). Its hash joins
   the plan identity, so a corrected beat map invalidates exactly the bridges whose lengths change.
3. **Beat-locked timeline.** Anchors target absolute downbeat times t_k. Frame index
   f_k = 4·round(t_k·fps/4) (Wan lengths are 4n+1, so anchors sit on a 4-frame = 0.25 s grid at 16 fps);
   bridge length L_k = f_k − f_(k−1) + 1. Because targets are absolute, the error is bounded per anchor
   (|f_k/fps − t_k| ≤ 2 frames = 125 ms) and never accumulates. Bridge lengths must stay within
   **33–81 frames (2–5 s)**; a phrase that is too long is split at an inner downbeat, one that is too
   short is merged with its neighbour.
4. **Density follows the music.** Default one bridge per 4-bar phrase (≈ 4.46 s → 73 frames). F15
   band energy and onset density may choose 2-bar bridges (≈ 2.2 s → 37 frames) in climaxes and 8-bar
   spans split into two bridges in quiet passages; act boundaries (F38) sit on section starts.
5. **Head and tail holds.** Silence or a pickup before the first chosen downbeat is covered by holding
   the first anchor (or an F38 title card); after the last anchor the final frame holds until the audio
   ends. Holds are added at join time as still frames (no GPU) and never touch seam verification.
6. **Frame-rate conversion keeps sync.** Anchors fall on multiples of 4 frames at 16 fps, which map to
   exact frames at 24, 30 (approx.) and 48 fps; F25 interpolation must preserve presentation timestamps
   and anchor frames.
7. **Animatic before bridges.** A cheap preview — anchor stills (or placeholder cards) cut exactly at
   their beat-map times, muxed with the music — is the owner's first listening check of the sync. It
   needs only anchor images (or none), not Wan bridges.
8. **Verification.** A sync report lists every anchor's target downbeat, actual frame time and error;
   acceptance: max |error| ≤ 2 frames (125 ms) at 16 fps, mean ≤ 1 frame, zero cumulative drift, audio
   offset recorded in the manifest, plus an owner listening review of the animatic and of each act.
9. **Constant-tempo music** (electronic, click-tracked) keeps working with today's `audio.bpm` +
   `duration_beats` mode; the beat-map mode is for performed music like this recording.

**Planning numbers (beat-locked):** with one bridge per 4-bar phrase the Mozart track needs **≈ 80
bridges (mostly 73 frames) + ≈ 81 anchors**, exact count from the verified beat map. 73-frame bridge
cost is **NO DATA** (EXTRAPOLATED linearly from the measured 65-frame 496 s: ≈ 558 s at 832×480,
≈ 270 s at 640×368) → ≈ 13.5 GPU-hours at 832×480 or ≈ 6.8 at 640×368. Measure a 73-frame bridge in
the P1 pilot before trusting this. The fixed-grid baseline below (90 × 65-frame bridges) remains the
upper-bound comparison.

| ID | Proposed Spec Kit folder (verify numbering before creation) | Dependencies | Priority | Initial status |
|---|---|---|---|---|
| **F31** | `specs/031-engineering-concept-bank/` (created) | F12, F21 | P0 | **OFFLINE-PASS (draft)** — Claude-drafted `configs/concepts/engineering-film.yaml`: 96 subjects (one per anchor of the current Mozart sync plan) across ten eras (9–10 each), lightning → … → AI hardware → lightning, each with description, shapes, materials, scale, morph-affinity note, accuracy note, honest sources, `accuracy: unverified`; `concepts-check` (schema, unique ids, era order/coverage, single `follows` chain, link notes, brand/logo/person terms, count vs sync plan, approval rules) and `concepts-list`; owner approval pending (T013), accuracy review is F33 |
| **F32** | `specs/032-full-song-act-structure/` (created) | F15, F19, F22, F31 | P0 | **OFFLINE-PASS (draft)** — frame-locked transitions (`frames`, 4n+1, zero drift; beat storyboards and plan hashes unchanged; `snap_frames`), five acts (`configs/film/acts.yaml`: Spark/Power/Signal/Logic/Scale, fresh text-to-image per act), `film-storyboard` → `configs/sequences/engineering-film.yaml` (96 anchors, 95 bridges from `configs/film/sync-plan.json`), `film-report` dry run: 5,741 frames = 358.81 s = song length incl. 1-frame tail hold, ≈ 13.7 GPU h estimated (129 measured-median stages, 62 extrapolated); owner storyboard approval pending (T013) |
| **F33** | `specs/033-technical-accuracy-review/` (created) | F31, F16 | P0 | **OFFLINE-PASS** — `accuracy-checklist` (5 items + concept context), `accuracy-review` (owner verdicts accurate/reject/waive tied to image SHA-256 in an append-only log; stale on re-render), `accuracy-negatives` (film storyboard: all 191 stages carry text/letters/labels/logo/watermark after adding bridge negatives; organic-machines lacks them on all 5), `accuracy-impact` (transitive reference-edit subgraph + touching bridges + final; rejecting a Signal anchor re-renders 8 anchors / 9 bridges and preserves 174 stages; new derived seeds), `accuracy-status` (gate); owner verdicts for every film anchor pending (T015) |
| **F34** | `specs/034-engineering-visual-language/` (created) | F21, F12, F23 | P1 | **OFFLINE-PASS (draft)** — `configs/film/visual-language.yaml` (engineering-noir base; looks copper-to-silicon (default) and steel-accent with per-act palette/lighting/camera; adjacent acts share a colour; geometry + drift thresholds); film storyboard regenerated with the default look (`look-check` ok for 191 stages; text-free check still ok); `look-drift` on the real organic-machines anchors flags colour spread 62 > 60 and the phoenix 0.116 off-centre; `look-test` A/B storyboards written; owner A/B render + look selection pending (T013) |
| **F35** | `specs/035-long-chain-lineage-drift/` (created) | F12, F14, F19 | P0 | **OFFLINE-PASS** — `lineage` (root/depth/chain; film per-act max 17/9/9/28/28 vs limit 12 in `configs/film/lineage.yaml`), `lineage-propose` (5 explicit independent re-anchors → max depth 12, written to a new file with exact invalidation), `lineage-drift` (colour/sharpness/centring/scale vs act reference; real organic-machines curve over depths 0–2), `lineage-shared` (real run: 4/4 bridge endpoints byte-identical); full rendered act with approved drift bounds pending (T014) |
| **F36** | `specs/036-production-gpu-budget/` (proposed) | F11, F17, F19 | P0 | **PLANNED — NOT IMPLEMENTED** |
| **F37** | `specs/037-soundtrack-narration-timing/` (proposed) | F15, F32 | P0 | **PLANNED — NOT IMPLEMENTED** |
| **F38** | `specs/038-act-transitions-titles/` (proposed) | F14, F32, F37 | P1 | **PLANNED — NOT IMPLEMENTED** |
| **F39** | `specs/039-batch-review-iteration/` (proposed) | F16, F18, F36 | P0 | **PLANNED — NOT IMPLEMENTED** |
| **F40** | `specs/040-full-song-film-delivery/` (proposed) | F25, F26, F30, F31–F39 | P0 final | **PLANNED — NOT IMPLEMENTED** |

### Required preproduction gates for the full-song film

**P0 — Offline continuity pilot:** assemble a sourced, technically reviewed sequence of **8–12 adjacent bridges** (32–48 seconds of anchor span at 65 frames/16 fps), preferably crossing an era or chapter boundary. Produce a validated dry-run plan, correspondences, visual style, source/uncertainty notes and measured-input GPU estimate. No render is authorized by planning.

**P1 — Bounded GPU pilot:** with fresh owner-scoped consent and an idle queue, render only that passage. Record full-stage wall time, whole-GPU VRAM (not per-process memory), reference-edit depth/drift, disk consumption, bridge/anchor continuity, QA false negatives and human creative/technical review. Stop and revise before attempting a full act if quality or budget gates fail.

**P2 — One complete act:** verify explicit lineage reanchors, transitive cache invalidation, seam checks, bulk review, optional licensed music/narration and reproducibility. Replacing a reference-edited anchor can invalidate **all transitively dependent edited descendants and their bridge videos** until an independently generated reanchor cuts the lineage; it is never automatically limited to two adjacent bridges.

**P3 — Whole-film delivery:** only after owner approval of P0–P2, schedule bounded, resumable act batches, followed by approved finishing/audio and two export formats. Preserve original 16 fps masters and recorded provenance. No automatic six-hour-plus GPU batch.

**Duration/cost check:** the picture must cover the whole 358.822 s song. With 90 adjacent 65-frame bridges the exact deduplicated count is `1 + 90×(65−1) = 5761` frames: 360 seconds between the first and last anchor timestamps and a nominal `5761/16 = 360.0625 s` container duration, i.e. the picture runs ≈ 1.2 s past the music (allowed; the final anchor may hold or the audio may end first). Ninety-one unique anchor concepts are an **illustrative plan**, not an artistic quota; approved act titles, pauses, different bridge lengths or a shorter list change the count. The published ~6.9–13.7 GPU-hour range is a **base generation estimate**, not a wall-clock guarantee: price in quality rerenders, reanchors, startup/load, review, storage, joining, interpolation, upscaling and audio separately. 81-frame bridge cost remains unknown until measured.

**Factual storytelling rule:** historical electricity/computing components must have sourced component/era descriptions, an owner review and uncertainty notes; physically impossible transitions can be marked **artistic metamorphoses**, not literal engineering history. Never invent authoritative component labels or citations in model-generated pixels. Use postproduction captions with checked facts.

**Engineering order:** finish/reconcile F11 benchmark evidence without repeating ongoing jobs, run F13 controlled prompt tests only if consented, implement F15 beat mapping and F16 calibrated QA, and research F31/F33 concepts offline. Delay F36/F40 full GPU scheduling until the pilot gates pass.
### F31 — Engineering concept bank and anchor subject research

**Purpose:** A vetted, ordered library of ~76 visual subjects spanning electricity and computing, each a good morph partner for its neighbours.

**Build:** Concept entries (id, era, subject, physical description, dominant shapes and materials, scale, suggested neighbours, morph-affinity notes such as coil windings ↔ transformer laminations, accuracy notes, sources consulted). Eras: natural electricity, early storage, generation and grid, signals and communication, vacuum-tube computing, solid state, integrated circuits, microprocessors, parallel/GPU compute, data centers and AI hardware. No brand names, logos, trademarked product designs or real people's likenesses in prompts; generic, physically plausible depictions only.

**Tests / evidence:** Schema validation, unique ids, every concept reachable in the chain, banned-term check (brands/logos), neighbour shape/material notes present; owner review of the list.

**Acceptance gate:** Owner-approved concept bank of ≥ 91 entries (one per anchor for the full song) in era order with neighbour notes; no unverified technical claims presented as fact.

### F32 — Full-song act structure, beat map and beat-locked storyboard

**Purpose:** Turn the concept bank into a musically synchronized, multi-act storyboard the existing pipeline can render.

**Build:** The **beat map** (owner-verified downbeats, bars, phrases and sonata-form sections; hashed into plan identity) and the **beat-locked timeline** (anchors on absolute downbeat frames f_k = 4·round(t_k·fps/4), bridge lengths L_k = f_k − f_(k−1) + 1 within 33–81 frames, no cumulative drift; schema: `audio.beatmap` + per-transition `bars`/`to_bar`, alongside the existing constant-BPM mode). Acts follow the music's sections (exposition, development, recapitulation, coda; ≈ five acts over the whole song), for example *Spark* (natural and early electricity), *Power* (generation and grid), *Signal* (communication and waveforms), *Logic* (tubes, transistors, ICs), *Scale* (CPUs, GPUs, data centers, AI). Per act: anchors, second/beat budgets, Wan `4n+1` lengths, transition choreography (F13), act-boundary handling (F38). Anchor times come from the F15 event-locked planner (beat map an optional refinement). Compile to chapter storyboards (F19) with deterministic plan hashes and a duration report (unique frames = 1 + Σ(L−1)).

**Tests / evidence:** every anchor within 2 frames (125 ms) of its target downbeat with zero cumulative drift on a synthetic rubato beat map; bridges within 33–81 frames (split/merge rules); beat-map edit invalidates only bridges whose lengths change; picture plus head/tail holds covers the full song; per-act and total frame math; deterministic hashes; editing one act invalidates only that act; full-film dry run without GPU.

**Acceptance gate:** Owner-approved storyboard whose dry run reports duration, bridge/anchor counts and estimated GPU hours.

### F33 — Technical accuracy and visual-plausibility review

**Purpose:** Engineering audiences notice wrong circuits; generative models invent fake text and impossible parts.

**Build:** Per-concept review checklist (correct component class, plausible geometry, no gibberish labels or text, no fake schematic symbols, era-appropriate materials), text-free prompting with negatives (`text, letters, labels, logo, watermark`), reviewer verdicts stored with anchor hashes, rejection → targeted regeneration (seed/prompt) with dependency-aware invalidation of every downstream reference-edited descendant and clip consuming changed anchors, until a separately generated reanchor; preserve unrelated ancestors/branches.

**Tests / evidence:** Checklist schema, verdict persistence, a rejection invalidates its transitive dependent edit/bridge subgraph, not merely its two neighbours, negatives always applied; real anchors reviewed by the owner.

**Acceptance gate:** Every anchor in the final film has an owner "accurate enough" verdict or an explicit waiver.

### F34 — Engineering visual language

**Purpose:** A full song of morphs must read as one film, not ~90 unrelated clips.

**Build:** A film style pack (F21): palette (copper, steel, phosphor green, silicon blue), lighting (dark studio, rim light), macro lens look, background treatment, per-act palette shifts with continuity rules across act boundaries; F12 geometry targets (centred subject, consistent scale band) and F23 camera rules per act.

**Tests / evidence:** Style applied deterministically to every anchor prompt; per-act palette drift measured with F12 colour metrics; boundary continuity checks; owner A/B of two candidate looks on a short test sequence (bounded GPU).

**Acceptance gate:** Owner-selected visual language documented and enforced in compiled prompts.

### F35 — Long-chain lineage and drift control

**Purpose:** Seventy-plus sequential reference edits compound drift (detail loss, colour shift, scale creep); one bad anchor would poison every later image.

**Build:** Lineage depth tracking; periodic re-anchoring with fresh T2I keyframes at act starts (explicit `independent_t2i` with continuity review, never silent); per-generation drift metrics (F12 geometry, sharpness, palette vs the act reference); proposal to re-anchor when thresholds are exceeded; shared anchors stay byte-identical across bridges.

**Tests / evidence:** Synthetic drift sequences, threshold proposals, lineage graph integrity, re-anchoring invalidates only downstream items; a real measured drift curve over one act.

**Acceptance gate:** A full act rendered with measured drift inside owner-approved bounds.

### F36 — Production GPU budget and batch scheduling

**Purpose:** ~7–14 GPU-hours (≈ 80 beat-locked bridges of mostly 73 frames; 73-frame cost to be measured) must run safely in bounded, resumable batches without disturbing other desktop work.

**Build:** Budget planner from F11 estimates (per act, per batch, cold/warm), F17 scheduler for off-hours batches with caps (time, job count, VRAM headroom), per-act approval gates, checkpoint/resume after crashes or reboots, progress/ETA reporting, storage budget for ~160–180 stage artifacts plus previews; per-length cost history (37/49/65/73/81-frame bridges) because beat-locked bridges vary in length.

**Tests / evidence:** Budget arithmetic vs history, cap enforcement, resume after a simulated mid-batch crash with no duplicate prompts, busy-queue deferral; measured real batch time vs estimate.

**Acceptance gate:** Owner-approved batches finish within ±20% of estimate with zero duplicate submissions.

### F37 — Soundtrack sync verification, animatic, narration and captions

**Purpose:** Prove and deliver the musical synchronization planned in F32, plus optional voice-over and captions.

**Build:** Owner-supplied licensed or original music only (licence provenance, F20 audit); beat-map review tools (click-track overlay preview for listening, manual downbeat corrections, `owner_verified` sign-off); **animatic** (anchor stills or placeholder cards cut at beat-map times and muxed with the music, no Wan bridges needed); sync report per anchor (target musical event, actual frame time, error); energy-warp report (speed range, pinned endpoints); head/tail hold computation; audio mux with recorded offset; optional narration script with per-line timing targets and owner-recorded audio; picture/audio drift report; captions as a separate local track (SRT), never model-rendered text.

**Tests / evidence:** Synthetic rubato and click-track fixtures (sync report errors ≤ 2 frames, zero drift), animatic timing via ffprobe, silence fixtures, narration timing table, caption file validity, a no-audio build still works; measured sync on the real soundtrack.

**Acceptance gate:** Owner listening approval of the animatic and of each act; every anchor within 2 frames (125 ms) of its downbeat, mean ≤ 1 frame, zero cumulative drift.

### F38 — Act transitions, title cards and overlays

**Purpose:** Signal chapter changes without breaking the continuous-morph concept.

**Build:** Act boundaries on music section starts from the beat map; act-boundary morphs via longer bridges or intermediate ladders (F14); optional local FFmpeg titles and lower thirds (owner text, local fonts, safe areas) composited after the join, never inside Wan prompts; opening and end cards that also fill the head/tail holds; overlay timing tied to beat-map times (F32/F37).

**Tests / evidence:** Overlay placement in 16:9 and 9:16 safe areas, deterministic FFmpeg arguments, overlays never alter the seam frames used for verification, boundary morph frame math.

**Acceptance gate:** Owner-approved act boundaries and titles in a preview render.

### F39 — Batch review and iteration for ~90 bridges

**Purpose:** Reviewing and fixing dozens of clips needs better tools than one-by-one approval.

**Build:** Act-level contact sheets and frame strips, side-by-side candidate comparisons, F16 QA ranking, keyboard-driven approve/reject/rerender in the F18 UI, a rerender queue limited to rejected items with a budget preview, version history per bridge.

**Tests / evidence:** Review state for 90 items, bulk approval within an act, rejection queues only the affected transitive dependency stages, versions preserved, budget preview matches F36.

**Acceptance gate:** Owner completes review of a full act in the tool with every decision recorded in manifests.

### F40 — Full-song film delivery and acceptance

**Purpose:** Ship the finished electrical and compute engineering film.

**Build:** Join all acts (seam-verified), interpolate to 24/30 fps (F25), finish/upscale to 1080p (F26, owner-installed models only), 16:9 and 9:16 presets (F30), music/narration mux, provenance report (models and hashes, workflows, seeds, licences, owner approvals), reproducible manifest, and measured GPU-hours/wall-clock vs the F36 estimate.

**Tests / evidence:** ffprobe golden checks per preset, frame/PTS/audio integrity across ~90 seams, picture covering the full song, provenance completeness, fresh-root replay of at least one act byte-identical (as in MC-RUN-003).

**Acceptance gate:** Owner-approved full-song film in at least two delivery formats with a complete provenance report; every F31–F40 gate has evidence or an explicit owner-accepted blocker.

## Execution, status and artifact protocol

1. Before work fetch **current** GitHub and local git status. Inspect `CLAUDE.md`, `.specify/memory/constitution.md`, `docs/PROGRESS.md`, real workflow/profile files and source/tests. **Do not restart or interrupt ongoing GPU inference**; use read-only `/queue`, `/history`, `/object_info`, `/system_stats` while active.
2. Check `python scripts/windows/speckit.py --status` and `--verify`; project has Python backend. **Do not re-initialize** a valid installation. Inspect `.claude/skills/speckit-*/SKILL.md` to learn real skill invocations (do not fabricate slash commands).
3. Work through **one F11–F40 feature at a time**. Confirm unused number from `specs/`; run `python .specify/scripts/python/create_new_feature.py --json --number N --short-name SLUG "description"` only after checking the installed script. Document actual returned directory. Execute genuine Spec Kit specify → clarify (if needed) → plan/research → tasks → analyze → implement via installed skills. Do not create empty ceremonial specs.
4. Write acceptance-oriented tests before implementations when practical; run `.venv/Scripts/python.exe -m pytest -m "not integration and not gpu"`. Read-only live integration tests are separate; GPU tests always respect owner consent and `--confirm-gpu` and never overrun budgets. No unapproved model installs/hashing while GPU active.
5. Record evidence to `docs/PROGRESS.md`: feature ID, actual spec folder, exact commit, tests & failures, GPU artifact hashes and measurements (or NOT RUN / NOT MEASURED), owner creative review, blockers and next task. Update ledger status in **the first table and relevant section**, preserve historical snapshots, and keep ⁠F01–F10 results grounded.
6. Commit narrowly scoped, reversible, test-passing slices on the owner's currently allowed branch. Do not force-push, clean owner work, overwrite exports, reset GPU queue, or add AI/coauthor trailers. Keep model weights/output media and credentials gitignored.

## Remaining proof / limitations as of audit

- The first full pipeline is **working**, not just planned. **Do not waste time rebuilding it.**
- The MC-RUN-003 from-scratch repeat is **complete and byte-identical**; quality improvements and long-form audio sync remain future work; root `docs/PROGRESS.md` is historical and includes earlier superseded blocker notes.
- F07 and F08 are **partial**: whole-GPU sampled VRAM is not a model-only peak; QA did not catch several creative defects. Model-file SHA-256 was measured in F11 T010, but that does not establish final benchmark/creative quality. F09's music branch is unverified; F10's fresh output-root replay was verified by MC-RUN-003; future 30-feature release gates remain pending.
- ".specify" and initial 10 feature specs are existing work; do not recreate them.

**Next action:** inspect new HEAD, current queue and outstanding F11 T011 benchmark evidence; do not rebuild F11–F13. Start the highest-priority unblocked new Spec Kit feature (F15 offline beat mapping, F14 adaptive ladders after F13, or F16 calibrated QA with labelled examples), while F31 concept research can proceed offline. Any additional GPU inference needs a bounded owner-approved scope.