# Feature Specification: Multi-stage recovery, model provenance and VRAM observations

**Logical ledger ID**: F07 · **Feature Directory**: `specs/007-recovery-provenance-metrics` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F07 Persistent multi-stage atomic run manifest, crash/retry/resume without repeat inference, opt-in model SHA provenance and opt-in measured GPU memory sampling"

## Gap analysis
| Exists | Gap |
|---|---|
| Per-stage content-addressed job dirs with atomic `job.json`, persisted prompt ID, reconcile on resume (bridge + anchors via shared executor) | No root run record tying storyboard/plan/stages together; crash safety tested only at selected points; `model_sha256: NOT RECORDED`; peak VRAM `NOT MEASURED` everywhere |

## User Scenarios & Testing *(mandatory)*
### US1 - Root run manifest (P1)
**Acceptance**: `outputs/runs/run-<plan16>/manifest.json` (atomic write) records repo HEAD, storyboard SHA, plan SHA, ComfyUI version, per-stage job dir/id/state/output SHA, consent and VRAM evidence; re-opening for the same plan returns the same run; a different plan gets a different run.
### US2 - Crash at every transition (P1)
**Acceptance**: for each persisted state transition of a GPU stage, a simulated hard crash right after it followed by resume ends `verified` with exactly one `/prompt`.
### US3 - Opt-in model hashing (P2)
**Acceptance**: `models-hash` hashes only files referenced by the profiles, refuses while ComfyUI's queue is non-empty, caches by (path, size, mtime), writes `outputs/model_hashes.json`; anchors/bridges record hashes when the cache has them, otherwise `NOT RECORDED`.
### US4 - Opt-in VRAM sampler (P2)
**Acceptance**: a sampler polls `nvidia-smi` at a fixed interval during a stage and reports peak/min/baseline overall GPU memory used, interval, sample count, start/end, labelled "overall GPU memory (all processes), sampled"; without samples → `NOT MEASURED`.

### Edge Cases
nvidia-smi missing → sampler `unavailable`; changed model file (size/mtime) → re-hash required, stale entry ignored; manifest temp file left by a crash → ignored and replaced.

## Requirements *(mandatory)*
- **FR-001** Atomic manifest writes (temp + replace); never overwrite a stage's job dir.
- **FR-002** Run ID derived from plan SHA; stage status read back from the stage `job.json`.
- **FR-003** Hashing is opt-in, refuses a busy queue, and covers only profile-referenced model files.
- **FR-004** VRAM numbers are only reported from samples; static `/system_stats` is never a peak.
- **FR-005** Existing bridge/anchor behaviour unchanged.

## Success Criteria *(mandatory)*
- **SC-001** 100% of tested crash points resume with one `/prompt`.
- **SC-002** Hash cache hit performs 0 file reads of model bytes.
- **SC-003** Sampler summary correct on synthetic sample series.

## Assumptions
ComfyUI models root default `C:\AI\ComfyUI_windows_portable\ComfyUI\models`, overridable. Folder per loader input: unet_name→diffusion_models, clip_name→text_encoders, vae_name→vae, ckpt_name→checkpoints, lora_name→loras.
