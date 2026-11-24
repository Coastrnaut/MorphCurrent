---
description: "Task list for F37 Soundtrack Sync Verification, Animatic, Narration and Captions"
---

# Tasks: Soundtrack Sync Verification, Animatic, Narration and Captions (F37)

**Input**: Design documents from `specs/037-soundtrack-narration-timing/`
**Tests**: requested — written first; offline (FFmpeg-gated where encoding).

## Phase 1: Setup

- [X] T001 Create tests/test_soundtrack.py with helpers (synthetic frame-locked storyboard with two chapters + matching sync plan; sine audio file; beat map)

## Phase 2: User Story 1 — Sync report (P1) 🎯 MVP

- [X] T002 [P] [US1] Tests: matching storyboard → all errors 0, drift 0, gate passed; one bridge +4 frames → later anchors off by 4, drift 4, gate failed; count mismatch refused; real film storyboard + sync plan → 96 rows, gate passed
- [X] T003 [US1] Implement `anchor_times`, `sync_report` in src/morph_studio/soundtrack.py

## Phase 3: User Story 2 — Warp report (P2)

- [X] T004 [P] [US2] Tests: real sync plan → 95 bridges pinned, speeds within 0.5–2; tampered map (unpinned end, speed 3) flagged
- [X] T005 [US2] Implement `warp_report`

## Phase 4: User Story 3 — Animatic (P1)

- [X] T006 [P] [US3] Tests: no run, no audio → duration = planned length ± 1 frame, no audio stream, cards used; with a fake run still for one anchor → that cut uses the still; licensed audio with offset → audio stream present, trimmed to picture; unlicensed refused; existing output refused
- [X] T007 [US3] Implement `animatic`

## Phase 5: User Story 4 — Captions and narration (P2)

- [X] T008 [P] [US4] Tests: captions → valid SRT, one cue per anchor in order, round-trip parse; narration script with overlap, past-end line, unknown anchor → flags/refusal, gaps reported, SRT written
- [X] T009 [US4] Implement `srt_write`, `srt_parse`, `captions`, `narration_check`

## Phase 6: User Story 5 — Beat map review (P3)

- [X] T010 [P] [US5] Tests: click track WAV has clicks at downbeat times (sample positions); music mix produces audio file; verify with corrections → new file, sorted, verified/owner/date, original unchanged; empty owner and non-increasing corrections refused
- [X] T011 [US5] Implement `click_track`, `verify_beatmap`

## Phase 7: Polish

- [X] T012 CLI `sync-report`, `warp-report`, `animatic`, `captions`, `narration-check`, `click-track`, `beatmap-verify` with tests (ASCII, exit codes)
- [X] T013 Real evidence: sync and warp reports on the film; full-film card animatic (no audio) with probe; film captions SRT
- [X] T014 Full suite; docs (ARCHITECTURE, ledger, PROGRESS, README)
- [ ] T015 Converge loop; commit and push

## Blocked / owner

- [ ] T016 Owner listening approval of the animatic with the licensed track and of each act; beat-map verification (acceptance gate)

## Dependencies

Setup → US1 → US2 → US3 → US4 → US5 → Polish.

## Phase 8: Convergence

- [X] T017 Add CLI tests for `narration-check` (exit 1 on flags, 2 on unknown anchor), `click-track` and `beatmap-verify` (`--correct I=T` parsing, exit 2 on empty owner), per FR-008 (partial)
