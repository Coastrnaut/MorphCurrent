---
description: "Task list for F38 Act Transitions, Title Cards and Overlays"
---

# Tasks: Act Transitions, Title Cards and Overlays (F38)

**Input**: Design documents from `specs/038-act-transitions-titles/`
**Tests**: requested (acceptance scenarios) — written first; offline, FFmpeg-gated where encoding.

## Phase 1: Setup

- [X] T001 Create configs/film/titles.yaml (version 1, font `C:/Windows/Fonts/arial.ttf`, defaults fade_s 0.5, opening "From Lightning to Silicon" 0–5 s size 0.10 y 0.45, acts duration_s 4 size 0.08 y 0.80 with empty text overrides, lower_thirds [], end "MorphCurrent" 5 s size 0.10 y 0.45)
- [X] T002 Create tests/test_titles.py with helpers (synthetic frame-locked storyboard with two chapters; tiny titles definition; FFmpeg test movie via lavfi `testsrc` 16 fps)

## Phase 2: Foundational

- [X] T003 Implement `load_titles` with validation ("text non-empty after strip; duration > 0; fade ≤ duration/2; 0 < size ≤ 0.3; 0 < y < 1") and `TitlesError` in src/morph_studio/titles.py, with tests for each refusal

## Phase 3: User Story 1 — Titles render (P1) 🎯 MVP

- [X] T004 [P] [US1] Tests: resolve on the synthetic storyboard → act titles start at their chapter's first anchor time and last their duration; act title inside the opening card deferred; end card at duration − 5; overlay past the end clipped and reported; overlaps reported; storyboard without chapters → only opening/end; covered anchors listed (tests/test_titles.py)
- [X] T005 [US1] Implement `anchor_times`, `resolve` in src/morph_studio/titles.py (default act text from configs/film/acts.yaml)
- [X] T006 [P] [US1] Tests: recipe checksum identical twice and changes with text; filter uses only relative names and `expansion=none`; render onto a test movie → same frame count and duration, input sha256 unchanged, record lists overlays with anchors; text with `:` `'` `%` renders without error; missing font, empty text, existing output refused; storyboard prompts unchanged and no title text in any prompt (FR-002); verification helper fails a frame-count or duration mismatch (FR-006) (tests/test_titles.py)
- [X] T007 [US1] Implement `build_recipe`, `recipe_sha256`, `render` in src/morph_studio/titles.py

## Phase 4: User Story 2 — Safe areas (P1)

- [X] T008 [P] [US2] Tests: short title passes both areas unchanged; long line shrinks for 9:16; line too long even at minimum size flagged; vertical check feeds shrunk size into the recipe (tests/test_titles.py)
- [X] T009 [US2] Implement `safe_check` in src/morph_studio/titles.py

## Phase 5: User Story 3 — Act boundaries (P2)

- [X] T010 [P] [US3] Tests: real film storyboard + sync plan → 4 boundaries (18, 28, 38, 67), proposals 18→13 (−5), 38→43 (+5), 67→70 (+3), none for 28; files unchanged; anchor-count mismatch refused (tests/test_titles.py)
- [X] T011 [US3] Implement `act_boundaries` in src/morph_studio/titles.py

## Phase 6: Polish

- [X] T012 CLI `titles-check`, `titles-render`, `act-boundaries` in src/morph_studio/cli.py with tests (ASCII, exit codes 0/1/2)
- [X] T013 Real evidence: titles-check --vertical on the film; act-boundaries report; titled copy of the full-film card animatic with probe and record under outputs/titles/
- [X] T014 Full suite; docs (docs/ARCHITECTURE.md, docs/SPECKIT_FEATURE_LEDGER.md, docs/PROGRESS.md, README.md)
- [X] T015 Converge loop; commit and push

## Dependencies

Setup → Foundational → US1 → US2 (safe sizes feed the recipe) → US3 (independent) → Polish.

## Parallel examples

T004/T006/T008/T010 are test-writing tasks in one file; write them sequentially but before their implementations. US3 can be implemented independently of US1/US2.

## Implementation strategy

MVP = US1 (resolve + render). Then US2 safe areas, US3 boundary report, CLI and evidence.

## Phase 7: Convergence

- [X] T016 Apply lower-third defaults (size 0.05, y 0.88) when omitted in src/morph_studio/titles.py `load_titles`, with a test, per data-model.md (partial)
- [X] T017 Make `titles-check` print a one-line-per-overlay ASCII summary unless `--json` is given in src/morph_studio/cli.py, with a test, per contracts/cli.md (partial)
