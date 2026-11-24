---
description: "Task list for F30 Multi-format Cinematic Delivery and Final 30-Feature Acceptance"
---

# Tasks: Multi-format Cinematic Delivery and Final 30-Feature Acceptance (F30)

**Input**: Design documents from `specs/030-delivery-presets-release-audit/`
**Tests**: requested — written first; FFmpeg-gated where they encode.

## Phase 1: Setup

- [X] T001 Create tests/test_delivery.py with FFmpeg helpers: synthetic 832×480 16 fps clip with optional audio and a subject box placed centre or at the left edge; a sine audio file

## Phase 2: Foundational

- [X] T002 Implement `PRESETS`, `recipe`, `recipe_sha256`, encoder detection/fallback and `crop_rect` + generic safe-area test in src/morph_studio/delivery.py with pure tests (7 presets; checksum stable and distinct per preset; 9:16 crop of 832×480 = 270×480 at x=281; 1:1 = 480×480 at x=176)

## Phase 3: User Story 1 — Deliver in several formats (P1) 🎯 MVP

- [X] T003 [P] [US1] Tests: landscape + vertical + square + hires + smooth from one clip → measured size/fps/codec/duration match, record with recipe checksum, source unchanged; repeated delivery to another folder → same checksum; existing output refused; video-only has no audio; licensed audio muxed (duration within one frame) and refused when not licensed or too short; encoder fallback recorded and verified (monkeypatched encoder list); verification mismatch marked failed; target smaller than input refused; unknown preset refused; one failure does not stop others
- [X] T004 [US1] Implement `deliver_one`, `verify` and `deliver`

## Phase 4: User Story 2 — Crop safe area (P1)

- [X] T005 [P] [US2] Tests: centred subject → inside for vertical and square; left-edge subject → outside with warning and file still produced
- [X] T006 [US2] Implement crop safe-area reporting from first/last frames (`geometry.image_geometry`)

## Phase 5: User Story 3 — Final acceptance (P2)

- [X] T007 [P] [US3] Tests: `acceptance_matrix(through=30)` returns 30 rows from the real ledger; `through=40` 40 rows; `all_features` still works; `release_check` not ready with reasons on the real ledger; synthetic fully-evidenced ledger + clean audit → ready_for_owner_review with owner note; no tagging code
- [X] T008 [US3] Implement `acceptance_matrix(through=...)` and `release_check` in src/morph_studio/release.py

## Phase 6: Polish

- [X] T009 CLI `deliver` (+ `--list-presets`), `acceptance --through`, `release-check` in src/morph_studio/cli.py with tests (ASCII, exit codes 0/5/2 and 0/1)
- [X] T010 Real evidence: deliver the MC-RUN-004 movie in landscape-1080p and vertical-1080x1920 (and smooth-24fps-1080p); record times, verification and crop report; run `acceptance --through 30` and `release-check`
- [X] T011 Full suite; docs (ARCHITECTURE, ledger, PROGRESS, README)
- [ ] T012 Converge loop; commit and push

## Blocked / owner

- [ ] T013 Final owner-approved multi-scene demonstration with optional synced audio and at least two delivery presets; release tagging only on owner approval

## Dependencies

Setup → Foundational → US1 → US2 (crop presets) → US3 (independent) → Polish.

## Implementation Strategy

MVP = presets + landscape/vertical delivery with verification; then safe area; acceptance; CLI.

## Phase 7: Convergence

- [X] T014 Record the frame-rate step actually applied (`blend <src>->24` or `none (already 24 fps)`) in the delivery record, per Edge Cases "smooth preset on a 24 fps source" (partial)
