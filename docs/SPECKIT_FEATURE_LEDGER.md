# MorphCurrent — 30-feature GitHub Spec Kit engineering ledger

**Scope:** F01–F10 are the existing pipeline implementation and evidence; **F11–F30 are 20 new proposed features**, evolving MorphCurrent from a working short YAML-to-video pipeline into a long-form, musically synchronized, quality-controlled local creative system.

**Grounded audit:** GitHub `main` at `9b79301b31ef6c31db3a465967928ca6aa457b3c`, 2026-11-24. Future Claude sessions must fetch current HEAD and respect concurrent owner edits; never assume this SHA is latest after today.

## Current technical reality (not goals)

- Three **real** ComfyUI API-format exports exist and are bound to actual node IDs: `workflows/01_anchor_t2i.json` (Qwen-Image T2I), `workflows/02_anchor_edit.json` (Qwen Image Edit 2509), `workflows/03_wan22_flf2v.json` (Wan 2.2 I2V FP8 high/low experts). Versioned profile JSONs at `configs/profiles/` and live schema fixtures exist; keep them stable.
- Python implementation already includes `anchors.py`, `bridge.py`, `dag.py`, `render.py`, `qa.py`, `stitcher.py`, `provenance.py`, `vram.py` and supporting schemas, tests, command-line UX and Windows CI. The latest commit reports **193 passing offline tests**. Recheck locally rather than blindly repeating that result.
- `MC-RUN-001` generated orchid→butterfly→phoenix using Qwen image generation/reference editing, completed two 832×480/65-frame/16-fps Wan bridges, and joined a verified **129-frame** H.264 movie after owner review. Original bridge quality was weak in parts despite no QA flags. See `docs/EXPERIMENTS.md` and the end of `docs/PROGRESS.md`.
- `MC-RUN-002` selectively regenerated the **phoenix** from a more front-facing prompt and reran only the butterfly→phoenix bridge; the orchid, butterfly and earlier bridge were reused. Result was joined without a hard cut, though a mid-bridge wing fold remains. MC-RUN-003 then recomputed all five GPU stages from a fresh output root; all three anchors, both bridges, and the final 129-frame movie were byte-identical to MC-RUN-002 (decoded PSNR ∞ and SSIM 1.000). This proves reproducibility under those recorded conditions, not artistic perfection or general determinism across different driver/model versions. The current final output name is `<storyboard>_<UTC timestamp>_<plan8>.mp4`; manifest tracks the actual path.
- GPU memory observations come from an opt-in **whole-GPU** `nvidia-smi` sampler, not per-model or per-process allocations. Qwen file hashes are listed; **Wan weight hashes remain NOT MEASURED**. Longer-form music alignment and calibrated quality review are not yet demonstrated. A clean **from-scratch** reproduction was verified in MC-RUN-003; new features require their own acceptance evidence.
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
| **F11** | `specs/011-measured-gpu-benchmarks/` (created) | F07, F10 | P0 | **OFFLINE-PASS** — `perf-report`, `estimate`, timestamped whole-GPU samples; GPU benchmark matrix + Wan hashing await owner approval |
| **F12** | `specs/012-reference-anchor-continuity/` (created) | F04, F08 | P0 | **OFFLINE-PASS** — geometry heuristics recorded per child anchor, `anchor-check`; matched three-anchor owner approval pending |
| **F13** | `specs/013-physical-morph-choreography/` (created) | F12, F08 | P0 | **OFFLINE-PASS** — `choreography` → compiled bridge prompts/negatives, `prompt-preview --variants`; fixed-seed GPU A/B pending |
| **F14** | `specs/014-adaptive-transition-ladders/` (proposed) | F12, F13, F05 | P1 | **PLANNED — NOT IMPLEMENTED** |
| **F15** | `specs/015-local-audio-beat-mapping/` (proposed) | F05, F09 | P0 | **PLANNED — NOT IMPLEMENTED** |
| **F16** | `specs/016-calibrated-qa-candidates/` (proposed) | F12, F13, F08 | P0 | **PLANNED — NOT IMPLEMENTED** |
| **F17** | `specs/017-vram-aware-job-scheduler/` (proposed) | F11, F07, F14 | P1 | **PLANNED — NOT IMPLEMENTED** |
| **F18** | `specs/018-local-creative-review-ui/` (proposed) | F08, F15, F16 | P1 | **PLANNED — NOT IMPLEMENTED** |
| **F19** | `specs/019-resumable-longform-timeline/` (proposed) | F14, F15, F17 | P1 | **PLANNED — NOT IMPLEMENTED** |
| **F20** | `specs/020-release-reproducible-pipeline/` (proposed) | F11–F19 | P0 final | **PLANNED — NOT IMPLEMENTED** |

| **F21** | `specs/021-style-packs-asset-library/` (proposed) | F12, F18 | P1 | **PLANNED — NOT IMPLEMENTED** |
| **F22** | `specs/022-story-brief-to-storyboard/` (proposed) | F14, F18, F21 | P1 | **PLANNED — NOT IMPLEMENTED** |
| **F23** | `specs/023-camera-framing-keyframes/` (proposed) | F12, F13, F14 | P1 | **PLANNED — NOT IMPLEMENTED** |
| **F24** | `specs/024-temporal-shape-stability/` (proposed) | F13, F16, F23 | P0 quality | **PLANNED — NOT IMPLEMENTED** |
| **F25** | `specs/025-optical-frame-interpolation/` (proposed) | F09, F15, F24 | P1 | **PLANNED — NOT IMPLEMENTED** |
| **F26** | `specs/026-upscale-visual-finishing/` (proposed) | F11, F24, F25 | P1 | **PLANNED — NOT IMPLEMENTED** |
| **F27** | `specs/027-workflow-model-capabilities/` (proposed) | F02, F11, F17 | P1 | **PLANNED — NOT IMPLEMENTED** |
| **F28** | `specs/028-project-archive-migration/` (proposed) | F07, F19, F21 | P1 | **PLANNED — NOT IMPLEMENTED** |
| **F29** | `specs/029-budgeted-experiment-optimizer/` (proposed) | F11, F16, F17, F24 | P1 | **PLANNED — NOT IMPLEMENTED** |
| **F30** | `specs/030-delivery-presets-release-audit/` (proposed) | F18–F29 | P0 final | **PLANNED — NOT IMPLEMENTED** |

No `specs/011-...` through `030-...` are created by this documentation commit. They must be created via the **installed** Python Spec Kit feature flow when that feature becomes active. If a number conflicts, follow the tool's returned directory and update this mapping; preserve existing specs.

### F11 — Reproducible A6000 performance and model provenance

**Purpose:** Turn whole-GPU snapshots into interpretable repeatable cost/performance evidence without harming existing workloads.

**Build:** Provide opt-in measured stage timers, correct whole-GPU VRAM coverage and other-process baseline, owner-approved idle-queue Wan checkpoint SHA-256 inventory, driver/torch/ComfyUI provenance, GPU memory pressure detection and conservative cost estimates. Benchmark warm vs cold cache, Qwen T2I, Qwen edit, Wan 640x368 vs 832x480, safe model offload; never imply whole-GPU usage is MorphCurrent-only.

**Tests / evidence:** Mock nv-smi samples including missing intervals and concurrent external process; numerical report and no fake per-process peaks; real A6000 samples only when owner authorizes a bounded run; regression with MC-RUN-001/002 historical data.

**Acceptance gate:** Report explicitly distinguishes MEASURED / ESTIMATED / NOT MEASURED; no unapproved model hashing or disruptive jobs.

**Status (2026-11-24):** OFFLINE-PASS in `specs/011-measured-gpu-benchmarks` — see docs/PROGRESS.md F11 entry. Blocked on owner approval: T010 Wan SHA-256 (`models-hash --confirm-io`), T011 sampled cold/warm and 640×368 vs 832×480 benchmark renders.

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

**Build:** Add offline audio import, licensed-local-file guard, BPM/onset/downbeat detection with confidence, half/double-tempo safeguards, audio section markers, human correction, variable bridge beat budgets, 4n+1 rounding/retime with explicit drift report and FFmpeg mux. Work without audio remains supported; never fetch music, upload it or silently retime copyrighted tracks.

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

**Build:** Parse a natural-language brief into explicit concepts, anchor progression, physical morph correspondences, beat/length budget, camera/storyboard constraints and candidate prompt text. Default deterministic rule/template compiler; optional local on-device/loopback LLM integration only if already installed, licensed and owner-enabled, with no user media uploaded or GPU starvation. Always validate schema, display the generated plan, expose edits and require approval before running.

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

**Build:** Create postprocessing profiles for FFmpeg-native and optionally verified local optical-flow/model-based interpolation, with explicit cadence mapping, PTS preservation, anchor/seam protection and fallback on motion failures. Interpolation runs only on produced/approved clips or verified assembled movies, and its algorithm/version and artifacts are hashed separately from original inference. Keep 16 fps originals lossless/immutable.

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

## Execution, status and artifact protocol

1. Before work fetch **current** GitHub and local git status. Inspect `CLAUDE.md`, `.specify/memory/constitution.md`, `docs/PROGRESS.md`, real workflow/profile files and source/tests. **Do not restart or interrupt ongoing GPU inference**; use read-only `/queue`, `/history`, `/object_info`, `/system_stats` while active.
2. Check `python scripts/windows/speckit.py --status` and `--verify`; project has Python backend. **Do not re-initialize** a valid installation. Inspect `.claude/skills/speckit-*/SKILL.md` to learn real skill invocations (do not fabricate slash commands).
3. Work through **one F11–F20 feature at a time**. Confirm unused number from `specs/`; run `python .specify/scripts/python/create_new_feature.py --json --number N --short-name SLUG "description"` only after checking the installed script. Document actual returned directory. Execute genuine Spec Kit specify → clarify (if needed) → plan/research → tasks → analyze → implement via installed skills. Do not create empty ceremonial specs.
4. Write acceptance-oriented tests before implementations when practical; run `.venv/Scripts/python.exe -m pytest -m "not integration and not gpu"`. Read-only live integration tests are separate; GPU tests always respect owner consent and `--confirm-gpu` and never overrun budgets. No unapproved model installs/hashing while GPU active.
5. Record evidence to `docs/PROGRESS.md`: feature ID, actual spec folder, exact commit, tests & failures, GPU artifact hashes and measurements (or NOT RUN / NOT MEASURED), owner creative review, blockers and next task. Update ledger status in **the first table and relevant section**, preserve historical snapshots, and keep ⁠F01–F10 results grounded.
6. Commit narrowly scoped, reversible, test-passing slices on the owner's currently allowed branch. Do not force-push, clean owner work, overwrite exports, reset GPU queue, or add AI/coauthor trailers. Keep model weights/output media and credentials gitignored.

## Remaining proof / limitations as of audit

- The first full pipeline is **working**, not just planned. **Do not waste time rebuilding it.**
- The MC-RUN-003 from-scratch repeat is **complete and byte-identical**; quality improvements and long-form audio sync remain future work; root `docs/PROGRESS.md` is historical and includes earlier superseded blocker notes.
- F07 and F08 are **partial**: whole-GPU sampled VRAM is not a model-only peak; QA did not catch several creative defects. F09's music branch is unverified; F10's fresh output-root replay was verified by MC-RUN-003; future 30-feature release gates remain pending.
- ".specify" and initial 10 feature specs are existing work; do not recreate them.

**Next action:** start F11 after checking the current owner's GPU activity and any newer commits. Continue F12/F13/F15/F16/F21/F22 offline if F11 GPU timing is blocked, without marking GPU gates complete.