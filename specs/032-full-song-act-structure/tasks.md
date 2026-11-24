---
description: "Task list for F32 Full-Song Act Structure, Frame-Locked Timeline and Film Storyboard"
---

# Tasks: Full-Song Act Structure, Frame-Locked Timeline and Film Storyboard (F32)

**Input**: Design documents from `specs/032-full-song-act-structure/`
**Tests**: requested — written first; offline.

## Phase 1: Setup

- [X] T001 Copy the owner's F15 sync plan to configs/film/sync-plan.json; create configs/film/acts.yaml (five acts per Clarifications); create tests/test_film.py with helpers (synthetic sync plan builder, small bank/acts fixtures)

## Phase 2: Foundational

- [X] T002 Record the current plan hashes of configs/sequences/organic-machines.yaml and engineering-pilot.yaml in a test (must stay identical)

## Phase 3: User Story 1 — Frame-locked timeline (P1) 🎯 MVP

- [X] T003 [P] [US1] Tests: frame-locked transitions compile to exact lengths, zero error, anchor frames = running sum, no BPM needed; invalid frames (64, 3, 85 > max) refused; both/neither beats and frames refused; BPM still required when beats used; existing plan hashes unchanged; `snap_frames` on a synthetic rubato beat map → every error ≤ 2 frames, no accumulation; ladder refuses frame-locked transitions with a clear message
- [X] T004 [US1] Implement `Transition.frames` + validator in src/morph_studio/schema.py, frame-locked path + `snap_frames` in src/morph_studio/timeline.py, guard in src/morph_studio/ladder.py

## Phase 4: User Story 2 — Film storyboard (P1)

- [X] T005 [P] [US2] Tests: generated storyboard validates; 96 anchors in bank order; first anchor per act text_to_image, others reference the previous; chapters = acts contiguous; transition frames = sync plan bridges; prompts contain subject and morph note + character; audio set only when given; refusals for count mismatch, bridge outside 33–81, existing output, acts missing/duplicating an era
- [X] T006 [US2] Implement `load_acts`, `build_storyboard`, `write_storyboard` in src/morph_studio/film.py

## Phase 5: User Story 3 — Film report (P2)

- [X] T007 [P] [US3] Tests: per-act numbers sum to totals; unique frames = 1 + Σ(L−1); coverage last anchor + tail hold = song length within one frame; GPU estimate labelled with extrapolated stages counted; editing one act's anchor prompt changes only that act's stages and its two boundary bridges (plan_diff)
- [X] T008 [US3] Implement `film_report`

## Phase 6: Polish

- [X] T009 CLI `film-storyboard`, `film-report` with tests (ASCII, exit codes)
- [X] T010 Real evidence: generate configs/sequences/engineering-film.yaml from the real sync plan + bank; run film-report; record per-act numbers, totals, coverage, GPU hours and timing
- [X] T011 Full suite; docs (ARCHITECTURE, ledger, PROGRESS, README)
- [ ] T012 Converge loop; commit and push

## Blocked / owner

- [ ] T013 Owner approval of the film storyboard (acceptance gate), after concept-bank approval (F31 T013)

## Dependencies

Setup → Foundational → US1 (schema) → US2 (uses frame-locked transitions) → US3 → Polish.

## Implementation Strategy

MVP = frame-locked transitions with unchanged hashes; then the generator; then the report; CLI and evidence.

## Phase 7: Convergence

- [X] T014 Report the head hold (first anchor time) in `film_report` coverage and include it in the song-length match, per Edge Cases "head hold" / FR-009 (partial)
