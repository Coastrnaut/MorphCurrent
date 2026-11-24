---
description: "Task list for F04 reference-guided next anchors"
---

# Tasks: Reference-guided next anchors

**Tests**: requested

## Phase 1: Foundational
- [X] T001 [P] Schema: `independent_t2i` generation, optional `negative_prompt`, reference rules (FR-001) + tests in src/morph_studio/schema.py, tests/test_schema.py

## Phase 2: User Story 1 — A→B→C chain (P1)
- [X] T002 [P] [US1] Tests: parent hashes, shared dimensions, rerun zero `/prompt`, in tests/test_anchor_chain.py
- [X] T003 [US1] Implement `AnchorSpec`, `run_anchor_chain` in src/morph_studio/anchors.py

## Phase 3: User Story 2 — no silent substitution (P1)
- [X] T004 [US2] Tests: missing edit profile blocks; independent_t2i labelled with review required; dimension mismatch fails child; unverified parent refused, in tests/test_anchor_chain.py

## Phase 4: User Story 3 — contact sheet (P2)
- [X] T005 [US3] `contact_sheet()` in src/morph_studio/media.py + ffmpeg-gated test in tests/test_anchor_chain.py

## Phase 5: Polish
- [X] T006 Suite, ledger, PROGRESS, commit

## Blocked
- [ ] T007 Owner-approved GPU A→B edit render with the real edit profile (needs F02 T011–T013)
