---
description: "Task list for F33 Technical Accuracy and Visual-Plausibility Review"
---

# Tasks: Technical Accuracy and Visual-Plausibility Review (F33)

**Input**: Design documents from `specs/033-technical-accuracy-review/`
**Tests**: requested — written first; offline.

## Phase 1: Setup

- [X] T001 Create tests/test_accuracy.py with helpers: a synthetic storyboard whose chains cross a text-to-image and an independent_t2i anchor, a fake run folder with anchor image hashes, and the real film storyboard

## Phase 2: Foundational

- [X] T002 Implement `CHECKLIST`, `TEXT_NEGATIVES`, `AccuracyError`, log load/append (JSON Lines, fsync, corrupt lines reported) in src/morph_studio/accuracy.py

## Phase 3: User Story 1 — Checklist and verdicts (P1) 🎯 MVP

- [X] T003 [P] [US1] Tests: checklist lists every anchor with concept subject/description/accuracy note; accurate needs all items pass; reject needs failed item or note; waive needs note; unknown anchor and missing hash refused; image file hashed; latest verdict wins and log keeps all; stale when hash differs
- [X] T004 [US1] Implement `checklist`, `record_verdict`, `latest`

## Phase 4: User Story 2 — Text-free prompting (P1)

- [X] T005 [P] [US2] Tests: regenerated film storyboard passes for all 191 stages; organic-machines reports missing stages/terms; whole-word matching
- [X] T006 [US2] Implement `text_free_check`; add bridge text negatives in src/morph_studio/film.py and regenerate configs/sequences/engineering-film.yaml (update F32 tests if they pin prompts)

## Phase 5: User Story 3 — Rejection impact (P1)

- [X] T007 [P] [US3] Tests: transitive reference-edit descendants invalidated; chain stops at text_to_image and independent_t2i anchors (only bridges touching invalidated anchors added); union of two rejections; final movie included; preserved count; new seeds deterministic and different from current; plan-order regeneration list; film: rejecting a Signal anchor touches nothing outside Signal except its boundary bridge
- [X] T008 [US3] Implement `impact`

## Phase 6: User Story 4 — Acceptance status (P2)

- [X] T009 [P] [US4] Tests: no run → all pending; with run hashes: accurate/waived/rejected/stale/pending classified; gate passes only when all accurate or waived with matching hashes
- [X] T010 [US4] Implement `status`

## Phase 7: Polish

- [X] T011 CLI `accuracy-checklist`, `accuracy-review`, `accuracy-negatives`, `accuracy-impact`, `accuracy-status` with tests (ASCII, exit codes)
- [X] T012 Real evidence: negatives check on the film storyboard; impact of a mid-Signal rejection; status on the real organic-machines run (pending until owner review)
- [X] T013 Full suite; docs (ARCHITECTURE, ledger, PROGRESS, README)
- [ ] T014 Converge loop; commit and push

## Blocked / owner

- [ ] T015 Owner reviews every final-film anchor (accurate or waiver) — acceptance gate

## Dependencies

Setup → Foundational → US1 → US2 → US3 → US4 → Polish.

## Implementation Strategy

MVP = verdict log with stale detection; then negatives, impact, status, CLI.

## Phase 8: Convergence

- [X] T016 Test `accuracy-review --run` (hash taken from the run manifest; unknown anchor refused) and `accuracy-impact` retry numbering from earlier rejections in the log, per FR-009 / Clarifications (partial)
