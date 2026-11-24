# MorphCurrent — ten-feature Spec Kit implementation ledger

This is the **authoritative implementation backlog** for the remaining goal: **automatically generate the first and last images using local ComfyUI, feed them into Wan 2.2 FLF2V, and assemble continuous morph videos**. No image endpoints should need to be supplied manually in the completed system. The owner operates **Claude Desktop Code** on **native Windows 11**, with an RTX A6000 (48 GiB), a local ComfyUI server, and Python-only helper scripts.

**Baseline inspected:** `main` commit `2deb3863a89f37cc99be77867edda10df88b9878` (2026-11-24). Each later session MUST refresh `main` and reconcile local edits before acting. This ledger is a plan, not a claim that ten features have been implemented.

## Existing verified work to preserve

- Real **Wan 2.2 14B I2V FLF2V** ComfyUI API export at `workflows/03_wan22_flf2v.json`, with versioned semantic bindings at `configs/profiles/wan22_flf2v.binding.json`. Profile's graph hash and observed `/object_info` were validated against local ComfyUI 0.46.0.
- `src/morph_studio/bridge.py` already has safe image upload, hash-based job identity, single-bridge submission, resume, targeted cancellation, `/history` retrieval, downloaded MP4 and `ffprobe` verification. Its explicit `--confirm-gpu` approval must remain intact.
- The repository logs MC-FLF2V-001 (owner manual 49-frame), MC-FLF2V-002 (owner manual 65-frame), and MC-FLF2V-003 (first MorphCurrent-dispatched 65-frame video). MC-FLF2V-003 was frame-identical to MC-FLF2V-002, **not** an artistic-quality pass. No trustworthy peak GPU-memory measurement exists yet.
- Existing `schema.py`, `timeline.py`, YAML storyboards, ComfyUI REST client, two example external source images, and offline Windows tests remain valuable. Do not rewrite the existing bridge from scratch.
- **Missing:** verified ComfyUI text-to-image workflow export `01_anchor_t2i.json`, verified reference-edit export `02_anchor_edit.json`, anchor image models/permissions, anchor generation adapter, multi-anchor pipeline/DAG, quality-gated joining, and one-command start-to-finish operation.

## Product acceptance target

Given only a local YAML creative storyboard (and optionally a licensed local music file), the controller must:

1. Generate **anchor A** from its prompt in a real ComfyUI text-to-image graph.
2. Generate **anchor B** from A with a real ComfyUI reference-edit graph; repeat B→C as needed. A deliberately selected **independent text-to-image** fallback is allowed, but must be labeled as such and pass continuity approval; never silently pretend it was reference editing.
3. Reuse the *exact bytes of anchor B* as the endpoint of bridge A→B and the startpoint of bridge B→C.
4. For each pair, automatically patch the **existing verified** Wan FLF2V graph and dispatch a bounded single GPU job with explicit operator approval, check outputs, and save an immutable manifest.
5. Inspect frames, retry selected failed or poor segments, and join video clips at verified shared endpoints with no arbitrary crossfade. Optionally align owner-provided music without requiring audio for silent videos.
6. Produce final MP4, generated endpoint images, stage MP4s, QA contact sheets and reproducibility manifest with no manual graph or node-ID editing.

The **dry-run path** must work before any GPU access, show exactly which models/workflows are required, and not accidentally submit work. Completed results must survive restart and reuse verified artifacts when rerun with the same inputs and model hashes.

## Ten logical features — scope, ownership and status

| ID | Proposed Spec Kit slug | Depends on | Existing reuse | Status on authoring |
|---|---|---|---|---|
| F01 | `safe-baseline-and-provenance` → `specs/001-safe-baseline-provenance` | — | Current Wan bridge, history, tests | **COMPLETE** — offline tests + live read-only checks; F01 has no GPU gate |
| F02 | `image-model-and-workflow-onboarding` → `specs/002-image-workflow-onboarding` | F01 | ComfyUI API client, semantic bindings | **OFFLINE-PASS; GPU/export BLOCKED** — no image weights installed, owner model approval required |
| F03 | `first-anchor-text-to-image` → `specs/003-first-anchor-t2i` | F02 | Client upload/history, hash functions | **OFFLINE-PASS; GPU BLOCKED** (needs F02 real T2I profile + owner render approval) |
| F04 | `reference-guided-next-anchor` → `specs/004-reference-edit-anchors` | F03 | Storyboard anchor reference semantics | **OFFLINE-PASS; GPU BLOCKED** (needs F02 real edit profile) |
| F05 | `full-storyboard-task-graph` → `specs/005-storyboard-task-dag` | F03, F04 | `schema.py`, `timeline.py` | **COMPLETE** — offline by nature (no GPU gate); dry-run DAG verified |
| F06 | `generated-anchors-to-wan-bridges` → `specs/006-generated-anchor-bridges` | F05 | Proven `bridge.py` / FLF2V profile | **OFFLINE-PASS; GPU BLOCKED** (needs generated A/B from F03/F04 GPU gates) |
| F07 | `multi-stage-recovery-and-metrics` → `specs/007-recovery-provenance-metrics` | F06 | Existing single-bridge job log | **OFFLINE-PASS** — model hashes and sampled peak VRAM NOT MEASURED on hardware yet |
| F08 | `visual-quality-selective-rerender` → `specs/008-quality-selective-rerender` | F06, F07 | Baseline clip observations | **OFFLINE-PASS** — heuristics uncalibrated; human review required |
| F09 | `seam-safe-video-and-audio` → `specs/009-seam-safe-join` | F05–F08 | Timeline + FFmpeg foundations | **OFFLINE-PASS** — real Wan seam not yet measured (GPU chain blocked) |
| F10 | `one-command-end-to-end-release` | F01–F09 | CLI + native Windows CI | **PLANNED** |

**Statuses:** PLANNED → SPECCED → IMPLEMENTING → OFFLINE-PASS → GPU-VERIFIED → COMPLETE. If the feature requires an image-model download or a new GPU run, set **BLOCKED** and state the exact permission or missing artifact; do not mark it complete on mocked tests. The ten IDs above are *logical ledger identifiers*, not guaranteed free numbered branch names.

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

**Acceptance:** Mock end-to-end T2I→edit→Wan consumes generated image SHA values, not example `assets/anchors/*.jpg`; bridge output verified for frame count/dimensions/fps; one owner-approved live generated-A/B bridge tests actual GPU path after dependencies exist. No duplicate `/prompt` on identical resume.

### F07 — Crash-safe multi-stage recovery, model provenance and VRAM observations

**Purpose.** No repeated costly inference after interruption; no fake memory statistics.

**Build:** Root job journal with per-stage immutable hashes, declared dependency models and SHA256 of checkpoint weights, exact workflow versions, real prompt IDs, atomic `.part` file commits, resume and selective retry. Use an **opt-in** `nvidia-smi` time-series during future owner-approved GPU runs, recording measured interval/coverage and distinguishing resident overall GPU use from per-process allocation; do not hash giant models while the current smoke job is active. Reconcile unknown state against queue/history, never global cancel.

**Acceptance:** Mock hard crash after each state transition, missing history, network loss, tampered image and changed model hash; verified stages reused without new GPU submission. If peak VRAM is not sampled, metric remains `NOT MEASURED`.

### F08 — Quality assessment, candidate ranking and selective rerender

**Purpose.** Address mid-morph subject collapse/flaring without destroying good anchor or bridge results.

**Build:** Local frame sampling/contact sheets, endpoint match, temporal sudden-cut/flash/freeze detection, clipping/framing and blur checks. Score as **heuristics**, preserve all candidate seeds/parameters; require human creative approval for subjective quality. Use historical MC-FLF2V-001/003 defects and the revised prompt from `docs/RENDER_BASELINE_001.md` as hypotheses. Rerender only the failed bridge with bounded candidates and explicit GPU approval.

**Acceptance:** Synthetic tests detect hard cuts, freezes, endpoint mismatch and sudden flare; smooth sequence doesn't falsely report a cut; reselect/retry B→C never re-renders verified A or A→B. No assertion that SSIM or PSNR alone proves visual morph quality.

### F09 — Seam-safe MP4 and optional music/beat sync

**Purpose.** Produce an actual Orchid→Butterfly→Phoenix continuous movie rather than disconnected MP4 files.

**Build:** Inspect actual boundary decoded frames; drop duplicates only when verified B matches, otherwise block/repair; normalize PTS, fps, pixel format, audio time base and codecs with native FFmpeg argument arrays (`shell=False`). Two 65-frame segments at 16 fps produce 129 unique frames only if B endpoints match: anchor timestamp span 8.0s vs file playback duration 129/16 = 8.0625s. Add optional owner-supplied licensed audio, BPM/downbeat offset and explicit time reconciliation; no music required for default MP4.

**Acceptance:** Synthetic golden 2-bridge frames prove expected 129 frames, correct endpoints, reproducible codec/timebase and no xfade; mismatched B is flagged instead of blindly trimming. Video-only and music-enabled output both tested separately.

### F10 — One-command native Windows end-to-end product

**Purpose.** From creative text YAML to generated stills, bridge clips, contact sheets, manifest and joined MP4 with one CLI command.

**Build:** Add `morphcurrent render <storyboard> --dry-run`, explicit GPU-authorized execution flag, `--resume`, read-only `--status`, bounded jobs and appropriate offline developer UX. Preserve existing `bridge` CLI. Keep all artifacts in gitignored `outputs/runs/<id>/`, provide user guidance on installing/approving T2I/edit models and downloading/output inspection. Document setup for native Windows, no WSL/PowerShell/Docker cloud inference.

**Acceptance:** With real T2I/edit workflows installed and a separately approved bounded GPU run, YAML alone produces A/B/C images, two verified Wan bridges and final MP4, without manually preparing endpoints or ComfyUI node edits. Repeated run reuses verified stages; missing image model yields precise BLOCKED preflight, not a fake completed video. Offline CI and end-to-end local GPU evidence remain distinct.

## Execution record (actual Spec Kit folders, evidence, blockers)

Spec Kit 1.2.4, `script=py`, skills `speckit-*` under `.claude/skills/`. Features are created with `python .specify/scripts/python/create_new_feature.py --json --number N --short-name SLUG "..."`; no git branch is created (owner works on `main`). `.specify/feature.json` points at the active spec.

| Fxx | Real spec directory | Status | Commit | Tests | Model + workflow evidence | GPU result | Blocker | Next action |
|---|---|---|---|---|---|---|---|---|
| F01 | `specs/001-safe-baseline-provenance` | COMPLETE | see PROGRESS F01 entry | offline 83 → 100 passed (1 deselected); integration 1 passed | live `baseline` 2026-11-24: Wan profile validates; checkpoints folder empty; 363 cloud API classes now rejected | NOT APPLICABLE (read-only only) | — | F02 |
| F02 | `specs/002-image-workflow-onboarding` | OFFLINE-PASS (GPU/export BLOCKED) | see PROGRESS F02 entry | offline 113 passed | capability role contracts; `workflow-inspect`; candidates from local templates in `docs/ANCHOR_MODEL_DECISION.md` | NOT RUN | owner must approve + download a model set, render once, Save (API Format) `01_`/`02_` | owner decision; meanwhile F05 offline |
| F03 | `specs/003-first-anchor-t2i` | OFFLINE-PASS (GPU BLOCKED) | see PROGRESS F03 entry | offline 137 passed | `anchors.py` on shared `bridge.advance_job`; stdlib PNG/JPEG checks; synthetic Qwen-shaped profile only | NOT RUN | F02 T011–T013 | one approved T2I render |
| F04 | `specs/004-reference-edit-anchors` | OFFLINE-PASS (GPU BLOCKED) | see PROGRESS F04 entry | offline 146 passed | `run_anchor_chain`: child edits parent's verified bytes; missing edit profile BLOCKS (no fallback); `independent_t2i` labelled, review required; dimension continuity; FFmpeg contact sheet | NOT RUN | F02 T011–T013 | one approved A→B edit render |
| F05 | `specs/005-storyboard-task-dag` | COMPLETE | see PROGRESS F05 entry | offline 155 passed | `morphcurrent dag`: 3 anchors + 2 bridges + final, 129 unique frames, explicit/derived seeds, plan hash, requirements (anchor profiles missing) | NOT APPLICABLE | — | F06 |
| F06 | `specs/006-generated-anchor-bridges` | OFFLINE-PASS (GPU BLOCKED) | see PROGRESS F06 entry | offline 160 passed | `pipeline.run_bridge_stage`: bridge endpoints only from verified anchor jobs; unchanged Wan profile/executor; shared B SHA asserted | NOT RUN | F03/F04 GPU gates | approved generated-A/B bridge |
| F07 | `specs/007-recovery-provenance-metrics` | OFFLINE-PASS | see PROGRESS F07 entry | offline 173 passed | `RunManifest`, crash-after-every-transition resume (7 states, 1 `/prompt`), `models-hash` (opt-in, idle queue only, size+mtime cache), `VramSampler` | NOT RUN | owner timing for multi-GB hashing; an approved render to sample | F09 |
| F08 | `specs/008-quality-selective-rerender` | OFFLINE-PASS | see PROGRESS F08 entry | offline 181 passed | `qa.py` cut/freeze/flare/endpoint heuristics; candidate seeds; rerender only failed/rejected bridges; `review.json`; on MC-FLF2V-003 heuristics report no flags although collapse/flare is visible → not a quality gate | NOT RUN | owner visual review to calibrate | F09 |
| F09 | `specs/009-seam-safe-join` | OFFLINE-PASS | see PROGRESS F09 entry | offline 186 passed | `join_verified`: decoded seam check, concat/trim (no xfade), ffprobe frame count Σ L − (n−1), `.part`, optional local audio cut to video length | NOT RUN | real generated A→B, B→C clips | F10 |

## Per-feature Spec Kit execution protocol (mandatory)

1. **Observe before writing:** Read `CLAUDE.md`, `.specify/memory/constitution.md`, this ledger, `PROGRESS.md`, local `git status`, current GitHub HEAD, existing `specs/` and working code. Record a fresh baseline, especially ongoing GPU queue state. Do not clobber dirty work.
2. **Verify installed Python Spec Kit:** `python scripts/windows/speckit.py --status`, then `python scripts/windows/speckit.py --verify`. The observed install uses Claude skills named `speckit-specify`, `speckit-clarify`, `speckit-plan`, `speckit-tasks`, `speckit-analyze`, `speckit-implement` (and `speckit-constitution`). Inspect installed skill signatures, do not assume a slash command exists in every Claude version. Reinitialize only if broken and backed up; never run bare `specify init` on Windows.
3. **Feature directories and numbering:** F01–F10 are **logical identifiers**, not guarantees that `001`–`010` are available. `python .specify/scripts/python/create_new_feature.py --help` documents `--number` and `--short-name`. Check for collisions; use a free actual number and record **logical Fxx ↔ actual `specs/NNN-slug/`**. The official script may auto-correct requested numbers and changes `.specify/feature.json` for the active spec. Do not pre-create ten active specs, invent branch names or delete/overwrite existing specs.
4. **For each feature:** Invoke **real installed Spec Kit skills** for `specify → clarify (if necessary) → plan → tasks → analyze → implement`. Produce genuine `spec.md`, `plan.md`, research/decision notes, data-model/contracts/quickstart as appropriate, and `tasks.md`; include functional requirements, test plan, permission gates and dependency acceptance. Do not just mention these phases in a response.
5. **Execute and record:** Write failing tests first where practical; implement incremental typed Python, run `python -m pytest -m "not integration and not gpu"`, capture *actual* output, then run explicitly approved local integration/GPU checks only when safe. Commit one coherent feature at a time with source/docs/tests; keep `PROGRESS.md` and the ledger table current. If GPU gate is blocked, finish offline tasks honestly and move to independent work; do not mark COMPLETE.
6. **Handoff:** For each feature record `Fxx | real spec directory | status | branch/commit | tests | model+workflow evidence | GPU result or NOT RUN | blocker | next action`. Carry forward active GPU/queue state without interruption. Never claim work was done asynchronously or after the current session ends.

## Non-negotiable operator boundaries

- **Do not interrupt, pause, restart, or preempt an ongoing user GPU smoke run.** During an active run: read-only status and offline code/spec work only; no new render, VRAM-intensive model hash, ComfyUI restart or model installation.
- Each *new* GPU generation needs a bounded explicit owner approval. A prior bridge consent does not authorize a model-install, a ten-feature sweep or unlimited GPU jobs.
- ComfyUI only on `127.0.0.1`; no media uploads to cloud services or public ComfyUI API. Claude Desktop reasoning itself may use cloud inference, but model/media inference must stay local.
- Do not commit `.safetensors`, generated videos, private media, credentials, machine secrets, or giant intermediate assets.
- Existing validated Wan graph/profile and experimentally verified MC-FLF2V evidence are **regression baselines**, not scaffolding to replace. If the code must change, add compatibility tests and verify before proceeding.

**How to start:** Open `docs/CLAUDE_DESKTOP_ONESHOT.md`, copy its **entire contents** into Claude Desktop Code with this repository selected. The file itself contains **only the prompt**, no wrapper, copy marker, code fence or explanatory instructions before/after the prompt.
