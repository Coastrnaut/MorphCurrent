---
description: "Task list for F40 Full-Song Film Delivery and Acceptance"
---

# Tasks: Full-Song Film Delivery and Acceptance (F40)

**Input**: Design documents from `specs/040-full-song-film-delivery/`
**Tests**: requested (acceptance scenarios) — written first; offline, FFmpeg-gated for media.

## Phase 1: Setup

- [X] T001 Create configs/film/accepted-blockers.yaml (`version: 1`, `accepted: []`, comment: owner decisions `{feature, blocker, owner, date: YYYY-MM-DD}`)
- [X] T002 Create tests/test_film_delivery.py with helpers: frame-locked 4-anchor mini storyboard (33-frame bridges), fake runs with solid-colour clips of matching boundaries and PNG anchors, job.json with `timings.execution_seconds`, F39 log writer

## Phase 2: Foundational

- [X] T003 Implement `choose(state, preview=False)` (blocker reasons ∈ {missing, unreviewed, pending, rejected, stale}) in src/morph_studio/film_delivery.py, with tests

## Phase 3: User Story 1 — Assemble (P1) 🎯 MVP

- [X] T004 [P] [US1] Tests: all approved → master frames = planned total (97 for 3×33), duration within one frame, record lists chosen versions; one unapproved/stale/rejected/missing bridge → refused with blockers; preview → assembled, labelled `_PREVIEW`, unapproved listed; mismatching seam → refused; licensed audio muxed, unlicensed refused; existing output refused; unreadable anchor stills → `seam_mode` boundary; real film → 95 blockers (tests/test_film_delivery.py)
- [X] T005 [US1] Implement `assemble` in src/morph_studio/film_delivery.py (join via `stitcher.join_verified`, anchor stills when readable, coverage check, `<master>.assembly.json`)

## Phase 4: User Story 2 — Deliver (P1)

- [X] T006 [P] [US2] Tests: two presets on a synthetic master → two results recorded in `<master>.delivery.json`; a failing preset recorded without stopping the other; preview label carried (tests/test_film_delivery.py)
- [X] T007 [US2] Implement `deliver_master` in src/morph_studio/film_delivery.py

## Phase 5: User Story 3 — Provenance (P1)

- [X] T008 [P] [US3] Tests: report lists every stage with version, job id, seed, run; workflows with pinned sha256 and models; catalogue licences ("NOT RECORDED" → missing); approvals sources; GPU measured = Σ execution seconds vs estimate with ratio; preview report never complete (tests/test_film_delivery.py)
- [X] T009 [US3] Implement `provenance` in src/morph_studio/film_delivery.py

## Phase 6: User Story 4 — Gates (P2)

- [X] T010 [P] [US4] Tests: real ledger → rows F31–F40; open gate unresolved; accepted-blocker entry marks it resolved; malformed entry (bad date, empty owner) refused (tests/test_film_delivery.py)
- [X] T011 [US4] Implement `gates` in src/morph_studio/film_delivery.py

## Phase 7: Polish

- [X] T012 CLI `film-assemble`, `film-deliver`, `film-provenance`, `film-gates` in src/morph_studio/cli.py with tests (ASCII, exit codes 0/1/2)
- [X] T013 Real evidence: `film-assemble` blockers on the real film; `film-gates`; provenance of a synthetic end-to-end assembly; workflow/model inventory from the real bindings
- [X] T014 Full suite; docs (docs/ARCHITECTURE.md, docs/SPECKIT_FEATURE_LEDGER.md, docs/PROGRESS.md, README.md)
- [X] T015 Converge loop; commit and push

## Blocked / owner

- [ ] T016 Render and approve all acts, assemble with the licensed track, deliver ≥ 2 formats, provenance complete, fresh-root replay of one act; owner approval of the film (acceptance gate SC-005, asked with choices)

## Dependencies

Setup → Foundational → US1 → US2 (needs a master) → US3 (needs an assembly record) → US4 (independent) → Polish.

## Parallel examples

US4 is independent of US1–US3; test tasks share one file and precede their implementations.

## Implementation strategy

MVP = US1 assembly; then delivery, provenance, gates, CLI and evidence.

## Phase 8: Convergence

- [X] T017 Test delivery of a preview master keeps the preview label in tests/test_film_delivery.py per US2-AC1 (partial)
- [X] T018 Test `film-deliver` exits 1 when a preset fails in tests/test_film_delivery.py per FR-008 (partial)
