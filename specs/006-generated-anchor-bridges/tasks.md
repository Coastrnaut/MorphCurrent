---
description: "Task list for F06 generated anchors to Wan bridges"
---

# Tasks: Generated anchors → Wan bridges

**Tests**: requested

## Phase 1: User Story 1 (P1)
- [X] T001 [P] [US1] Tests: A→B→C anchors then two bridges; inputs are anchor SHAs; shared B; rerun 0 `/prompt`, in tests/test_pipeline_bridges.py
- [X] T002 [US1] Implement `bridge_request_for`, `run_bridge_stage` in src/morph_studio/pipeline.py

## Phase 2: User Story 2 (P1)
- [X] T003 [US2] Tests: unverified anchor blocks; Wan model missing fails validation; no consent → validated; busy queue refused, in tests/test_pipeline_bridges.py

## Phase 3: Polish
- [X] T004 Suite, ledger, PROGRESS, commit

## Blocked
- [ ] T005 Owner-approved GPU bridge from generated A/B (after F03/F04 GPU gates)
