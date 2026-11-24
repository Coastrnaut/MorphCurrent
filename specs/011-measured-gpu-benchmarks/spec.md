# Feature Specification: Reproducible A6000 performance and model provenance

**Logical ledger ID**: F11 · **Feature Directory**: `specs/011-measured-gpu-benchmarks` (from `create_new_feature.py --number 11`) · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F11 Reproducible A6000 performance and model provenance: stage timers, whole-GPU VRAM sampling with gap and external-baseline handling, provenance, measured vs estimated cost reports"

## Gap analysis

| Exists (F07/F10) | Gap |
|---|---|
| `VramSampler`: one summary (baseline/peak/min) for the whole anchors+bridges window | No timestamps kept, so memory cannot be related to individual stages; no gap detection; summary label is right but nothing separates other-process baseline from the stage rise |
| Stage `job.json`: UTC events (planned…verified), ComfyUI `execution_seconds` from `/history` | No report that collects them across a run; no wall-clock vs execution split; no historical comparison |
| `models-hash --confirm-io` (opt-in, idle-queue only); Qwen hashes known, Wan NOT MEASURED | Report does not show which hashes are measured; no driver/torch/ComfyUI provenance block |
| `render --dry-run` lists GPU job counts | No time estimate; nothing marks estimates as ESTIMATED vs MEASURED |
| Historical evidence: MC-FLF2V-003 (640×368 bridge 234 s), MC-RUN-001/002/003 (832×480 bridges ≈495 s, anchors 19–52 s) | Not machine-readable; not used as regression fixtures |

## User Scenarios & Testing *(mandatory)*

### US1 - Performance report for a finished run (P1)
`perf-report RUN_DIR` lists each stage with wall-clock time (submit→verified), ComfyUI execution time, queue/overhead time, and — when the run was sampled — the whole-GPU memory baseline before the run and the peak observed inside that stage's execution window. Every number carries a label: MEASURED, ESTIMATED or NOT MEASURED.
**Acceptance**: on a manifest + jobs fixture modelled on MC-RUN-002, the report gives per-stage execution seconds equal to the job records, labels stage VRAM as "whole GPU during stage window" and never as per-process; a run without sampling reports VRAM NOT MEASURED.

### US2 - Honest VRAM sampling (P1)
The sampler keeps UTC-timestamped samples, saved next to the run. The analysis detects gaps (interval > 3× nominal), reports coverage, and treats memory already in use before the first stage as external baseline.
**Acceptance**: synthetic series with a missing interval → `gaps` reported and coverage < 100%; series with an external process ramping during a stage → reported peak is labelled as including other processes; empty series → NOT MEASURED.

### US3 - Time estimate before rendering (P2)
`estimate STORYBOARD` (offline) predicts per-stage and total GPU time from measured history keyed by stage kind and resolution/frames, labelled ESTIMATED with the source runs; stages with no history are "NO DATA", not guessed.
**Acceptance**: organic-machines at 832×480 → anchors ≈20/52/50 s and bridges ≈495 s from the MC-RUN fixtures; a 1280×720 bridge → NO DATA (no extrapolation unless `--extrapolate`, which scales by pixel×frame count and says so).

### US4 - Provenance block (P2)
The report includes driver version, GPU name, ComfyUI/PyTorch versions (from the run's recorded snapshots), and model SHA-256 per model file from the provenance cache, each MEASURED or NOT MEASURED.

### Edge Cases
Job without timings (failed stage) → listed with state, times NOT MEASURED. Clock skew between sampler (UTC, sub-second) and job events (UTC seconds) → windows widened by 1 s and stated. Reused stages (cache hit) → marked `reused`, excluded from the run's GPU total.

## Requirements *(mandatory)*
- **FR-001** Sampler records `(utc_epoch, used_mib)` samples and writes them to `vram_samples.json` in the run dir when sampling is on.
- **FR-002** Analysis reports nominal interval, observed max gap, gaps list, coverage %, external baseline (first sample before the first submission), peak, and per-stage window peaks — labelled whole-GPU.
- **FR-003** `perf-report` reads only local files; no ComfyUI calls, no GPU.
- **FR-004** `estimate` uses only recorded measurements; unknown configurations return NO DATA unless explicitly extrapolated (labelled ESTIMATED-EXTRAPOLATED).
- **FR-005** Every numeric field carries a status label; no per-process memory claims.
- **FR-006** Historical MC-FLF2V-003 and MC-RUN-001..003 measurements ship as a versioned fixture used by tests and as default estimate history.
- **FR-007** No model hashing or GPU job is started by any F11 command.

## Success Criteria *(mandatory)*
- **SC-001** Report numbers equal the source job records in 100% of fixture stages.
- **SC-002** Gap and external-process cases are flagged in tests; zero "per-process" labels anywhere.
- **SC-003** Estimate for the sample storyboard is within 10% of MC-RUN-002 measured stage times.
- **SC-004** GPU benchmark matrix (warm/cold, 640×368 vs 832×480) runs only after explicit bounded owner approval — BLOCKED until then.

## Assumptions
Whole-GPU sampling cannot separate MorphCurrent from other apps on WDDM (no per-process memory); stated, not solved.
