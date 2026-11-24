---
description: "Task list for F36 Production GPU Budget and Batch Scheduling"
---

# Tasks: Production GPU Budget and Batch Scheduling (F36)

**Input**: Design documents from `specs/036-production-gpu-budget/`
**Tests**: requested — written first; offline.

## Phase 1: Setup

- [X] T001 Create tests/test_production.py with helpers (synthetic history; fake runs folder with verified bridge/anchor job records incl. timings and prompt ids)

## Phase 2: User Story 1 — History ingest (P1) 🎯 MVP

- [X] T002 [P] [US1] Tests: verified measured jobs added once with kind/size/frames|method/exec; re-ingest adds nothing; unfinished/failed/unmeasured skipped and counted; malformed history refused
- [X] T003 [US1] Implement `ingest` in src/morph_studio/production.py

## Phase 3: User Story 2 — Budget (P1)

- [X] T004 [P] [US2] Tests: 73-frame bridge interpolated between measured 65 and 81 (INTERPOLATED); 33-frame extrapolated (EXTRAPOLATED, ≥ 0); exact match median (ESTIMATED); no size match → pixel scaling; anchors by method; film budget per act sums to totals with labels and storage bytes
- [X] T005 [US2] Implement `stage_cost`, `budget`

## Phase 4: User Story 3 — Batches and approval (P1)

- [X] T006 [P] [US3] Tests: batches within caps, never crossing acts, oversized single stage flagged; unapproved act refused; approved act → batch storyboards whose stages equal the full plan's (seed, prompts, size, length, reference) incl. needed parent/boundary anchors; existing files refused; revoke blocks again
- [X] T007 [US3] Implement `approve`, `approvals`, batch planning, `write_batches`

## Phase 5: User Story 4 — Status (P2)

- [X] T008 [P] [US4] Tests: finished vs remaining from cached stages; ratio flags outside 0.8–1.2 (leave-one-out); duplicate prompt id detected; real runs folder → zero duplicates
- [X] T009 [US4] Implement `status`

## Phase 6: Polish

- [X] T010 CLI `history-ingest`, `prod-budget`, `prod-approve`, `prod-batch`, `prod-status` with tests (ASCII, exit codes)
- [X] T011 Real evidence: ingest the real runs folder (F29 81-frame bridges), film budget per act, batch plan, status/duplicates on the real runs folder
- [X] T012 Full suite; docs (ARCHITECTURE, ledger, PROGRESS, README)
- [ ] T013 Converge loop; commit and push

## Blocked / owner

- [ ] T014 Owner-approved batches rendered and finishing within ±20% of estimate with zero duplicate submissions (acceptance gate)

## Dependencies

Setup → US1 → US2 → US3 → US4 → Polish.

## Phase 7: Convergence

- [X] T015 List anchors a batch renders outside its own stages (the next act's first anchor needed by the boundary bridge) as `early_stages` and include their cost in the batch ETA, per Edge Cases "boundary anchor" (partial)
