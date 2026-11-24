---
description: "Task list for F34 Engineering Visual Language"
---

# Tasks: Engineering Visual Language (F34)

**Input**: Design documents from `specs/034-engineering-visual-language/`
**Tests**: requested — written first; offline (FFmpeg-gated where images are generated).

## Phase 1: Setup

- [X] T001 Create configs/film/visual-language.yaml (two looks per Clarifications, default copper-to-silicon, selected null, geometry and drift thresholds) and tests/test_look.py with helpers (synthetic coloured-subject PNGs via FFmpeg, fake run manifest + job outputs)

## Phase 2: Foundational

- [X] T002 Implement `load_language` and `choose` in src/morph_studio/look.py with tests (valid definition; missing act, too few colours, bad camera, adjacent acts without shared colour refused; case/space-insensitive sharing; unknown look refused; default reported as not owner-selected)

## Phase 3: User Story 1+2 — Look applied and enforced (P1) 🎯 MVP

- [X] T003 [P] [US2] Tests: film storyboard regenerated with the default look passes `look_check` for 191 stages; F33 text-free check still passes; same inputs → identical plan hash; storyboard without the look fails with listed mismatches; changing one act's palette changes only that act's anchor stages and bridges touching them
- [X] T004 [US2] Implement `apply_look`, `look_check`; wire `language`/`look` into src/morph_studio/film.py and regenerate configs/sequences/engineering-film.yaml

## Phase 4: User Story 3 — Drift (P2)

- [X] T005 [P] [US3] Tests: synthetic run with one off-centre anchor and one large colour jump at an act boundary → exactly those flagged; missing anchors listed; storyboard without chapters → one act
- [X] T006 [US3] Implement `drift_report`

## Phase 5: User Story 4 — A/B test (P3)

- [X] T007 [P] [US4] Tests: two storyboards written, valid, identical anchors/seeds/frames, different style overrides and bridge camera; existing outputs refused; unknown act refused
- [X] T008 [US4] Implement `look_test`

## Phase 6: Polish

- [X] T009 CLI `look-check`, `look-drift`, `look-test`, `film-storyboard --language/--look` with tests (ASCII, exit codes)
- [X] T010 Real evidence: look-check on the regenerated film storyboard; look-drift on the organic-machines run; look-test files
- [X] T011 Full suite; docs (ARCHITECTURE, ledger, PROGRESS, README)
- [ ] T012 Converge loop; commit and push

## Blocked / owner

- [ ] T013 Owner renders the two A/B storyboards (bounded GPU) and records the selected look (acceptance gate)

## Dependencies

Setup → Foundational → US1/US2 → US3 → US4 → Polish.

## Phase 7: Convergence

- [X] T014 Add a synthetic drift test for a storyboard without chapters (one act) and a neighbour scale jump outside 0.75-1.33, per T005 / Edge Cases (partial)
