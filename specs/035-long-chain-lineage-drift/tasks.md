---
description: "Task list for F35 Long-Chain Lineage and Drift Control"
---

# Tasks: Long-Chain Lineage and Drift Control (F35)

**Input**: Design documents from `specs/035-long-chain-lineage-drift/`
**Tests**: requested — written first; offline (FFmpeg-gated for drift images).

## Phase 1: Setup

- [X] T001 Create configs/film/lineage.yaml and tests/test_lineage.py with helpers (synthetic chain storyboard crossing an independent anchor; FFmpeg images with increasing colour shift/blur; fake run with bridge job records)

## Phase 2: User Story 1 — Lineage (P1) 🎯 MVP

- [X] T002 [P] [US1] Tests: roots/depths/chains for a synthetic chain (independent restarts depth); over-limit listing; film per-act maxima = anchors − 1 per act (17/9/9/28/28)
- [X] T003 [US1] Implement `load_config`, `lineage`, over-limit report in src/morph_studio/lineage.py

## Phase 3: User Story 2 — Drift curve (P1)

- [X] T004 [P] [US2] Tests: synthetic rendered chain flags colour and sharpness past thresholds; reference has zero drift/ratio 1; missing anchors listed; unreliable masks reported as flags
- [X] T005 [US2] Implement `drift_curve`

## Phase 4: User Story 3 — Re-anchor proposals (P1)

- [X] T006 [P] [US3] Tests: film with limit 12 → proposals so that max depth after ≤ 12, none at act starts; drift-flagged anchors added when a curve is given; invalidation lists match the F33 impact rule; proposed storyboard validates, marks proposed anchors independent with continuity reference, original byte-identical; existing output refused
- [X] T007 [US3] Implement `propose`, `apply_proposals`

## Phase 5: User Story 4 — Shared anchors (P2)

- [X] T008 [P] [US4] Tests: fake run matches; tampered hash → mismatch; missing job record → unchecked
- [X] T009 [US4] Implement `shared_check`

## Phase 6: Polish

- [X] T010 CLI `lineage`, `lineage-drift`, `lineage-propose`, `lineage-shared` with tests (ASCII, exit codes)
- [X] T011 Real evidence: lineage + proposals on the film storyboard; drift curve and shared-anchor check on the real organic-machines run
- [X] T012 Full suite; docs (ARCHITECTURE, ledger, PROGRESS, README)
- [ ] T013 Converge loop; commit and push

## Blocked / owner

- [ ] T014 Render one full act and approve drift bounds (acceptance gate)

## Dependencies

Setup → US1 → US2 → US3 (uses lineage + curve) → US4 → Polish.

## Phase 7: Convergence

- [X] T015 Test that a rendered anchor with an unreliable subject mask (near-full-frame bright image) is reported with an `unreliable` flag instead of numbers, per T004 / Edge Cases (partial)
