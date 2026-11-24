# Implementation Plan: Recovery, provenance, VRAM

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
`run_manifest.py` (RunManifest), `provenance.py` (model hash cache + `models-hash` CLI, busy-queue refusal), `vram.py` (threaded nvidia-smi sampler with injectable runner/clock); crash-point tests parametrised over executor transitions.

## Technical Context
Python 3.11+, stdlib threading/subprocess (argument lists). Tests inject fake runners; no real hashing of large weights in tests.

## Constitution Check
I PASS (sampled vs NOT MEASURED) · II PASS (hash refuses busy queue; opt-in) · IV PASS (atomic writes, cache by size+mtime, never filename-only identity for content) · VII PASS.

## Design
- `RunManifest.open(runs_root, plan, storyboard_path, repo_head)`; `record_stage(task_id, job)`; `record(key, value)`; `save()` atomic.
- `provenance.MODEL_FOLDERS`, `models_in_profile(graph)`, `hash_models(paths, cache_file)`, `lookup(filenames, cache)`.
- `vram.VramSampler(interval=0.5, run=..)` context manager → `summary()`.

## Complexity Tracking
None.
