# Implementation Plan: Reproducible A6000 performance and model provenance

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
Extend `VramSampler` with UTC-stamped samples and persistence; new `perf.py` (sample analysis, stage collection from job records, report, estimator, provenance); history fixture `configs/perf_history.json`; CLI `perf-report` and `estimate`; render writes `vram_samples.json`.

## Technical Context
Python 3.11+, stdlib only. Tests: synthetic sample series, job/manifest fixtures modelled on real MC-RUN-002 records. Platform: native Windows; nvidia-smi only via existing sampler.

## Constitution Check
I Evidence — MEASURED/ESTIMATED/NOT MEASURED labels, whole-GPU caveat: PASS · II Consent — no GPU/hash side effects; benchmark matrix gated: PASS · IV Immutable — reads records, writes only new report/sample files: PASS · VII Compatibility — `VramSampler.summary()` unchanged keys (adds fields), render behaviour unchanged except an extra file: PASS.

## Design
- `vram.VramSampler`: `samples_utc: list[tuple[float, int]]`; `write(path)`.
- `perf.analyze_samples(samples, interval)` → coverage, gaps, external_baseline, peak.
- `perf.collect_stages(run_dir)` → per-stage dicts from manifest + job.json (state, reused, kind, size/frames, wall_s, exec_s, overhead_s).
- `perf.stage_window_peaks(stages, samples)`.
- `perf.build_report(run_dir, model_hash_cache)`; `perf.estimate(plan, history, extrapolate)`.
- History fixture: entries `{run, stage_kind, width, height, frames, exec_s}`.

## Complexity Tracking
None.
