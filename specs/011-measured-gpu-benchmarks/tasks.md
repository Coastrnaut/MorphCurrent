---
description: "Task list for F11 reproducible A6000 performance and model provenance"
---

# Tasks: F11

**Tests**: requested (test-first)

## Phase 1: Setup
- [X] T001 History fixture from recorded runs in configs/perf_history.json

## Phase 2: US2 — honest sampling (P1)
- [X] T002 [P] [US2] Tests: gap detection, coverage, external baseline, empty → NOT MEASURED, sampler writes UTC samples, in tests/test_perf.py
- [X] T003 [US2] `VramSampler.samples_utc` + `write()` in src/morph_studio/vram.py; `analyze_samples` in src/morph_studio/perf.py
- [X] T004 [US2] render writes `vram_samples.json` when `--sample-vram` in src/morph_studio/render.py

## Phase 3: US1 — perf report (P1)
- [X] T005 [P] [US1] Tests on MC-RUN-002-shaped fixtures: exec/wall/overhead equal records, reused stages, window peaks labelled whole-GPU, unsampled → NOT MEASURED
- [X] T006 [US1] `collect_stages`, `stage_window_peaks`, `build_report` (+ provenance block) in src/morph_studio/perf.py
- [X] T007 [US1] `perf-report` CLI in src/morph_studio/cli.py

## Phase 4: US3 — estimate (P2)
- [X] T008 [US3] Tests + `estimate` (median of matching history, NO DATA, labelled extrapolation) and `estimate` CLI

## Phase 5: Polish
- [X] T009 Run on real MC-RUN-003 records; record in docs/PROGRESS.md, ledger; commit

## Blocked (owner approval)
- [ ] T010 Wan checkpoint SHA-256 via `models-hash --confirm-io` (idle queue, ~37 GB disk read)
- [ ] T011 Sampled benchmark matrix: cold vs warm 832×480, 640×368 variant
