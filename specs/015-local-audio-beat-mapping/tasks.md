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
