---
description: "Task list for F39 Batch Review and Iteration"
---

# Tasks: Batch Review and Iteration for the Film's Bridges (F39)

**Input**: Design documents from `specs/039-batch-review-iteration/`
**Tests**: requested (acceptance scenarios) — written first; offline, FFmpeg-gated for media.

## Phase 1: Setup

- [X] T001 Create tests/test_batch_review.py with helpers: a 6-anchor two-act synthetic storyboard (reference-edit chains), and a fake run folder builder writing `run-*/manifest.json` (stages with state, job_dir, job_id, video_sha256/image_sha256, qa, qa_flags), job dirs with `job.json` and tiny media (FFmpeg testsrc clips / PNGs)

## Phase 2: Foundational

- [X] T002 Move the clip-screen severity weights to `qa.SEVERITY` in src/morph_studio/qa.py (hard_cut 3, endpoint_mismatch 3, flare 2, freeze 1) and use it in `analyze_frames`; existing QA tests unchanged

## Phase 3: User Story 1 — Film state (P1) 🎯 MVP

- [X] T003 [P] [US1] Tests: no runs → all stages missing; two runs covering parts → each stage once, unrendered missing, act totals; a stage rendered in both runs with different hashes → 2 versions in run order, latest current; a cache hit (same hash) → 1 version; a run of another storyboard ignored; real film storyboard with no runs → 191 stages (tests/test_batch_review.py)
- [X] T004 [US1] Implement `film_state` (scan runs, versions, QA score, per-run `review.json` import, stale flag, act totals) in src/morph_studio/batch_review.py

## Phase 4: User Story 2 — Decisions (P1)

- [X] T005 [P] [US2] Tests: record appends an entry pinned to the current version (decision ∈ {approved, rejected, pending}; note ≤ 500 chars; reviewer non-empty); unrendered/unknown stage and bad decision refused; log only grows; new version after a decision → stale, the old version still listed and the old decision still pinned to it (SC-004); bulk approval approves only rendered, unflagged bridges with no current decision and reports the count; review order flagged-first by score desc then storyboard order (tests/test_batch_review.py)
- [X] T006 [US2] Implement `record`, `approve_act`, `review_order` in src/morph_studio/batch_review.py

## Phase 5: User Story 3 — Rerender queue (P1)

- [X] T007 [P] [US3] Tests: one rejected bridge → queue of 1; a rejected mid-chain anchor → rest of its chain + adjacent bridges, nothing in the other act; act-opening anchor → only its act; no rejections → empty, 0 s; estimate labelled; `write_rerender` → storyboard with new derived seeds for queued stages and pinned seeds elsewhere, existing output refused (tests/test_batch_review.py)
- [X] T008 [US3] Implement `rerender_queue`, `write_rerender` in src/morph_studio/batch_review.py

## Phase 6: User Story 4 — Review aids (P2)

- [X] T009 [P] [US4] Tests: act sheet → new PNG with one row per rendered bridge (height = rows × row height), missing listed, record JSON; compare → new MP4 with doubled width and the longer duration; fewer than two versions, unknown version, existing output refused (tests/test_batch_review.py)
- [X] T010 [US4] Implement `act_sheet`, `compare` in src/morph_studio/batch_review.py

## Phase 7: User Story 5 — Keyboard act page (P3)

- [X] T011 [P] [US5] Tests: act page lists the act's bridges in review order with A/R/N hints; POST with valid CSRF token appends to the film log; missing/invalid token refused (tests/test_batch_review.py)
- [X] T012 [US5] Implement `/film/<act>` and `POST /film/review` in src/morph_studio/review_ui.py

## Phase 8: Polish

- [X] T013 CLI `film-review-status`, `film-review`, `film-review-approve-act`, `film-rerender-queue`, `film-act-sheet`, `film-compare` in src/morph_studio/cli.py with tests (ASCII, exit codes 0/1/2)
- [X] T014 Real evidence: film-review-status on the film with the existing runs folder; rerender queue for a hypothetical anchor rejection (dry, no log written to the real film log)
- [X] T015 Full suite; docs (docs/ARCHITECTURE.md, docs/SPECKIT_FEATURE_LEDGER.md, docs/PROGRESS.md, README.md)
- [X] T016 Converge loop; commit and push

## Blocked / owner

- [ ] T017 Owner reviews a full act in the tool after the Spark pilot renders (acceptance gate SC-005; Claude prepares sheets and asks with choices)

## Dependencies

Setup → Foundational → US1 → US2 → US3 → US4 → US5 → Polish. US2–US5 all need US1's state.

## Parallel examples

Test tasks T003/T005/T007/T009/T011 share one file and are written before their implementations; US4 and US5 are independent of each other once US1 exists.

## Implementation strategy

MVP = US1 + US2 (state and decisions); then rerender queue, review aids, UI page, CLI and evidence.

## Phase 9: Convergence

- [X] T018 Treat unreadable bridge media as missing in `act_sheet` (refuse only when no clip of the act is readable) in src/morph_studio/batch_review.py, with a test, per FR-009 / US4-AC1 (partial)
- [X] T019 Test that `review-ui --film/--film-log` passes the film options to the server in tests/test_batch_review.py per FR-008 (partial)
