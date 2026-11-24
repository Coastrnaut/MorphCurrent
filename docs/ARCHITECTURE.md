# Architecture

MorphCurrent is a Python controller that drives a **local** ComfyUI server. It never runs models itself; every image and video comes from ComfyUI on `127.0.0.1`.

```text
storyboard YAML
  └─ dag.py: anchors + bridges + final task (deterministic plan hash)
       ├─ anchor:orchid     text-to-image         (workflows/01_anchor_t2i.json)
       ├─ anchor:butterfly  reference edit of A   (workflows/02_anchor_edit.json)
       ├─ anchor:phoenix    reference edit of B
       ├─ bridge:orchid->butterfly   Wan 2.2 FLF2V (workflows/03_wan22_flf2v.json)
       ├─ bridge:butterfly->phoenix  same B bytes as the previous bridge's end frame
       └─ final:movie       QA → human review → seam-verified join (+ optional audio)
```

## Modules (`src/morph_studio/`)

| Module | Responsibility |
|---|---|
| `schema.py` | Strict storyboard model (anchors, transitions, render, audio). |
| `timeline.py` | Beats/BPM → Wan frame counts (`L = 4n+1`), derived seeds. |
| `dag.py` | Storyboard → task graph, required profiles, plan hash. |
| `comfy_client.py` | Loopback-only REST client: upload, `/prompt`, `/history`, `/view`, targeted cancel. |
| `workflow_adapter.py` | Binding profiles, graph validation against `/object_info`, patching, output extraction. |
| `gates.py` | Single GPU gate: explicit consent, idle queue, no ComfyUI cloud API nodes. |
| `bridge.py` | Crash-safe stage executor (`advance_job`) and the Wan bridge job. |
| `anchors.py` | Anchor image jobs and the A→B→C reference-edit chain. |
| `pipeline.py` | Feeds verified anchor images into bridge jobs. |
| `render.py` | One-command orchestration, review gate, status. |
| `run_manifest.py` | Root run manifest (`outputs/runs/run-<plan16>/manifest.json`). |
| `qa.py` | Heuristic cut/freeze/flare/endpoint checks, candidate seeds, review records. |
| `stitcher.py` | Seam check and FFmpeg join without crossfades. |
| `media.py` | ffprobe, PNG/JPEG integrity, contact sheets. |
| `provenance.py`, `vram.py` | Opt-in model SHA-256 cache and nvidia-smi memory sampling. |
| `preflight.py`, `onboarding.py` | Read-only `baseline` report and `workflow-inspect`. |

## Workflows and binding profiles

Each `workflows/*.json` is a real ComfyUI **Save (API Format)** export. A matching `configs/profiles/*.binding.json` names the real node IDs for semantic roles (prompt, seed, size, images, output), pins the graph's canonical SHA-256 and lists assertions the bindings rely on (e.g. turbo off, 20 steps). A profile also declares a `capability` whose required roles are enforced:

| Capability | Required roles | Output |
|---|---|---|
| `text_to_image` | `positive_prompt`, `seed` | image |
| `reference_edit` | `positive_prompt`, `seed`, `reference_image` | image |
| `wan_flf2v` | `start_image`, `end_image`, `positive_prompt`, `seed`, `length` | video |

Any re-export changes the hash and fails `workflow-check` until the bindings are re-verified. Graphs containing ComfyUI cloud API nodes are rejected.

## Stage jobs and recovery

Every stage is an immutable directory `outputs/runs/<job16>/` with `job.json`, the exact submitted graph and its outputs. The job ID is a content hash of the patched graph, input image bytes, workflow hash and code version, so an identical request is reused with zero ComfyUI calls.

State machine (persisted after every transition): `planned → uploaded → validated → submitting → submitted → completed → downloaded → verified` (or `failed` / `cancelled`). The ComfyUI `prompt_id` is chosen and saved *before* `POST /prompt`; on resume it is reconciled against `/history` and `/queue`, so a lost response never double-submits. Downloads go to `.part` files and are renamed only after completion.

## Timing and joining

For Wan length `L` at `F` fps, anchors are `(L-1)/F` seconds apart; a clip lasts `L/F`. Adjacent bridges share anchor B **byte for byte**. After decoding and comparing the last frame of A→B with the first frame of B→C, the duplicate is dropped and clips are concatenated with no crossfade: two 65-frame bridges give **129** unique frames (8.0 s anchor span, 129/16 s playback). A seam that doesn't match is refused, not trimmed. The join is scripted (`stitcher.join_verified`, called by `render`): FFmpeg `trim=start_frame=1` on every later clip, `concat`, H.264 re-encode to a `.part` file, ffprobe frame-count check, then rename to `final/<storyboard>_<UTC timestamp>_<plan8>.mp4`, whose path is recorded in the run manifest so reruns reuse it.

## Quality

`qa.py` flags gross defects only (hard cuts, freezes, flashes, endpoint mismatch). It does not judge creative quality: on MC-FLF2V-003 it reports no flags despite visible mid-morph collapse. Joining therefore waits for a human `review … approved` per bridge (or an explicit `--accept-heuristics`).

## Safety boundaries

- Loopback-only ComfyUI; no remote inference, uploads or cloud API nodes.
- GPU work only with `--confirm-gpu`, one job at a time, never while ComfyUI's queue is busy; never cancels others' jobs.
- Peak VRAM comes only from the opt-in sampler; `/system_stats` snapshots are never treated as peaks.
- Weights, generated media and run outputs stay out of Git (`outputs/` is ignored).

## F11–F30 extensions (F11–F13 offline slices implemented; others planned)

The existing Qwen→Qwen-edit→Wan→QA→human review→FFmpeg pipeline is **GPU-demonstrated**; future features must extend those modules rather than replacing working code. See [the 40-feature ledger](SPECKIT_FEATURE_LEDGER.md) for acceptance gates and exact dependencies.

- **Temporal continuity and repair (F24):** `continuity.py` analyses the F16 128×74 frames with one clip-level mask threshold (centred Otsu of the endpoints): consecutive mask overlap (shape substitution), connected parts (topology), background change outside both masks, centre and colour paths (jumps vs 4× the clip's median step); thresholds fixed in the spec before evaluation. `continuity-eval` reports by-kind and any-detector window recall on `configs/qa_labels.json`; `repair-propose` writes owner-review refinements and an optional intermediate anchor at a valid 4n+1 split; `repair-compare` requires equal length and unchanged endpoints (grey MAD ≤ 2.0) and caps its verdict at *candidate improvement — needs owner review*.
- **Camera and framing (F23):** `camera.py`: the installed Wan FLF2V graph is conditioned only on first/last frames and has no camera input, so `transitions[].camera` (static, push/pull, pan, tilt, orbit, rise + amount) compiles to a deterministic clause labelled *prompt-only approximation*; `control: graph` is refused. `satisfiability` checks a move against the fixed endpoint anchors' F12 geometry (push needs a larger end subject, pan shifts it the opposite way, static stays within F12 limits; orbit/rise not verifiable); `framing_check`/`crop_check` test per-anchor targets and 16:9 / 9:16 safe areas; `camera-check STORYBOARD [--run]`.
- **Production acceptance (F20):** `release.py`: `compare_runs` re-hashes each stage's output in two runs (identical / different / missing / not verified; optional decoded-frame difference, ≤ 1.0 = visually equivalent), `replay` renders into an empty runs root only with `--confirm-gpu`, `audit_repo` checks profile pins, media licence provenance and forbidden tracked files without hashing weights, `backup_run`/`restore_run` zip a run plus its job folders with `SHA256SUMS.json` (verified, path-safe, never overwrite), `acceptance_matrix` reads the ledger. No tool tags releases.
- **Local review UI (F18):** `review_ui.py` serves a stdlib, strictly-loopback page (`review-ui`): runs index, per-run stage states, anchors/contact sheet, playable clips with QA flags (Range-capable media served only by manifest-derived allowlist tokens), approve/reject/pending forms writing `review.json` through the same `qa.record_review` as the CLI, and a read-only plan view. Host check, per-process form token + Origin check, CSP `default-src 'self'`, no scripts, no request logs; no render or ComfyUI path.
- **Long-form sequencing (F19):** `longform.py` gives each stage a Merkle identity (inference-relevant fields + profiles + dependency identities) so `plan-diff` shows what an edit re-runs; optional contiguous `anchors[].chapter` feeds `timeline` (anchor/chapter timestamps, FFMETADATA1 chapters, proxy storyboard); `render --confirm-gpu` refuses before any submission if estimated outputs would breach `--min-free-gb`.
- **Observability and cost (F11, F17):** benchmark per-stage latency and opt-in whole-GPU VRAM, account for unrelated processes, and use an idle-queue single-job scheduler. Keep current `--confirm-gpu` and safe crash/resume semantics.
- **Continuity and transition intelligence (F12–F14, F16):** anchor framing/orientation constraints, physical correspondence plan, bounded multi-hop intermediate anchors and owner-labelled defect calibration. Preserve exact reference byte identity; QA metrics never silently replace human review.
- **Audio synchronization (F15):** import only owner-authorized local audio, estimate tempo/downbeats with confidence and manual overrides, allocate 4n+1 frame budgets and record tempo/duration residuals before joining.
- **Operator UI (F18):** optional local desktop/strict-loopback review workflow that edits the same typed storyboard and manifest as the CLI; no remote service or mandatory account; approval must remain explicit.
- **Longform and release (F19–F20):** chapter-level DAG/partial cache invalidation, previews and storage quotas, fresh-output-root replay, Windows packaging and a full acceptance suite. All source model weights/media remain outside Git.

F11 reporting, F12 geometry and F13 choreography are implemented offline; remaining items are **design targets**. The latest verified baseline uses timestamped output `final/<storyboard>_<UTC timestamp>_<plan8>.mp4` and a manifest-held path; do not revert to a fixed filename or assume these future extensions are already implemented.

- **F21–F22 — local assets and authoring:** private style/reference collections and approved editable creative-brief-to-storyboard planning; all sequences and prompts are pre-drafted in Claude Desktop sessions (text only, no local LLM) and checked locally by `draft-check` ([DRAFTING.md](DRAFTING.md)).
- **F23–F24 — spatial/temporal continuity:** actual-workflow-supported camera and framing constraints, material motion continuity and human-approved repair of collapse/flare defects.
- **F25–F26 — local finishing:** frame interpolation to target FPS, optional upscale/color/denoise, preservation of 16 FPS originals, true FFmpeg PTS/seam/audio verification.
- **F27–F28 — compatibility and portable projects:** versioned real ComfyUI model capability adapters, safe migration and archive restore, no weights or private media by default.
- **F29–F30 — experimental optimization and delivery:** bounded A/B sweeps, Pareto quality/cost analysis, safe export presets and final audited 30-feature acceptance.

MC-RUN-003 reproduced all Qwen-generated anchors, Wan bridges and 129-frame final video byte-identically to MC-RUN-002 in a fresh output root; this is **baseline evidence**, not evidence that F11–F30 exist.

## F31–F40 production track (planned)

An electrical & compute engineering film that runs the full length of its song (358.822 s Mozart track → ~90 bridges, ~91 anchors, ≈ 6.9–13.7 generation GPU-hours ESTIMATED, not including rerenders or finishing; may exceed five minutes) musically synchronized with a layered, visualizer-informed strategy (self-normalized band energies, onsets and sections from a hashed audio feature track; anchors on chosen musical events — onsets, section starts, energy peaks, verified downbeats when reliable; energy-warped playback inside bridges; see [MUSIC_SYNC.md](MUSIC_SYNC.md); acts follow the music's sections; ≈ 80 beat-locked bridges of 33–81 frames, |error| ≤ 2 frames with no drift; animatic listening check before bridges), built on F11–F30: concept bank, act structure, technical-accuracy review, visual language, long-chain drift control, GPU budgeting, soundtrack/narration timing, act titles, batch review and final delivery. See `docs/SPECKIT_FEATURE_LEDGER.md`.


### Production pilot and reference-lineage safety

P0: sourced 8–12-bridge offline pilot storyboard, verified frame counts and estimates. P1: bounded owner-approved GPU pilot measuring morphology, VRAM and render cost. P2: complete act with reviewed reanchor/descendant invalidation, seam, optional audio and captions. P3: full-song production only after earlier gates pass. A reference-edited anchor's replacement invalidates its transitive dependent image edits and their bridge clips until an independently regenerated reanchor breaks the chain. For 90 adjacent 65-frame bridges, 5761 unique frames = 360 s anchor span and 360.0625 s nominal playback at 16 fps, covering the 358.822 s song.
