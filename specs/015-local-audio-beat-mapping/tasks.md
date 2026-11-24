---
description: "Task list for F15 local music analysis and sync"
---

# Tasks: F15

- [X] T001 [P] [US1] Synthetic click-track tests (90/120/140 BPM, offset, stereo, sample rates, silence, missing file) in tests/test_audio.py
- [X] T002 [US1] `load_mono`, `onset_envelope`, `estimate_tempo`, `track_beats`, `downbeat_phase`, `analyze_audio` in src/morph_studio/audio.py
- [X] T003 [US2] `Audio.licensed` guard + URL rejection in src/morph_studio/schema.py; plan-hash regression
- [X] T004 [US3] `sync_report` with per-boundary error and cumulative drift; tests for 120/90 BPM
- [X] T005 CLI `audio-analyze FILE`, `audio-sync STORYBOARD [--analysis]`
- [X] T006 Suite, ledger, PROGRESS, commit

## Blocked / owner
- [ ] T007 Owner-licensed real track: analysis + approved synced render

## Phase: US4 classical rework (owner request 2026-11-24)
- [X] T008 [P] [US4] Synthetic classical tests (soft attacks + accelerando, pp→ff swell, sections) in tests/test_audio_classical.py
- [X] T009 [US4] Sub-band (Patin-style) onset strength, local tempo curve with prior, DP beat tracker, section novelty in src/morph_studio/audio_classical.py
- [X] T010 [US4] Single `analyze_audio` for all music (owner: no style switch); sections in `audio-visualize`
- [X] T011 [US4] Run on Mozart 40/I; record in PROGRESS; commit

## Phase: US5 layered synchronization foundation (owner request 2026-11-24)

- [X] T012 [P] [US5] Tests in tests/test_sync_features.py: synthetic WAV with accents at known times → feature track fields per 16 fps frame, onset peaks at the accents; deterministic content hash; irregular accents (no steady beat) still produce a full-coverage plan
- [X] T013 [US5] `feature_track`, `track_record` (audio SHA-256, settings, content hash) in src/morph_studio/sync_features.py reusing audio_bands.band_levels and beat_analysis.sections
- [X] T014 [P] [US5] Tests: `events` scoring (onset peaks, section starts 2.0, vol_att peaks; downbeat +0.5 only with verified/confident beat map); `plan_anchors` lands anchors within ±2 frames of accents, all bridges 33–81 frames 4n+1, first anchor 0, last anchor ≥ song end − one grid step; song shorter than one minimum bridge → clear error; silent stretch → preferred-length bridges; end between grid points → final hold reported
- [X] T015 [US5] Implement `events` and `plan_anchors` (DP over 4-frame grid, score − 0.5·|L−preferred|/64) in src/morph_studio/sync_features.py
- [X] T016 [P] [US5] Tests: `bridge_character` (bass-heavy, treble-heavy, building, settling, steady) and `energy_warp` (monotone, pinned endpoints, speed within 0.5×–2×)
- [X] T017 [US5] Implement `bridge_character`, `energy_warp`, `sync_plan` (hash, coverage) in src/morph_studio/sync_features.py
- [X] T018 [US5] CLI `audio-features FILE --out [--fps]` and `sync-plan FEATURES --out [--preferred] [--beatmap]` (refuse overwrite, ASCII-safe) in src/morph_studio/cli.py with tests
- [X] T019 [US5] Real evidence: feature track + plan for the Mozart recording (< 1 min); record counts, lengths, character mix, warp ranges in docs/PROGRESS.md; ledger F15 row
- [ ] T020 [US5] Full suite; converge loop until clean; commit (push pending owner force-push of rewritten history)

## Phase: Convergence (US5)

- [X] T021 Align the SyncPlan data shape in plan.md with the code (bridges use `from_frame`/`to_frame`) in specs/015-local-audio-beat-mapping/plan.md per plan: data shape (partial)
