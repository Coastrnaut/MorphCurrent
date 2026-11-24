---
description: "Task list for F03 first anchor via local text-to-image"
---

# Tasks: First anchor via local text-to-image

**Tests**: requested (test-first)

## Phase 1: Foundational
- [X] T001 Generalise `_upload` to iterate `plan.upload_names` and extract `advance_job(..., verify=...)` from `run_bridge` in src/morph_studio/bridge.py (bridge tests unchanged)
- [X] T002 [P] Implement `inspect_image` (PNG chunk/CRC walk, JPEG SOI/SOF/EOI) raising `ImageInvalid` in src/morph_studio/media.py
- [X] T003 [P] Tests for valid/truncated/corrupt PNG and JPEG in tests/test_media_images.py

## Phase 2: User Story 1 — generate anchor A (P1)
- [X] T004 [P] [US1] Fake ComfyUI serving PNG outputs + happy-path, no-consent and cache-hit tests in tests/test_anchors.py
- [X] T005 [US1] Implement `AnchorRequest` (seed required; reference iff `reference_edit`), `plan_anchor`, `open_anchor_job`, `run_anchor`, `_verify_image` in src/morph_studio/anchors.py
- [X] T006 [US1] Add `anchor` and `anchor-status` subcommands in src/morph_studio/cli.py

## Phase 3: User Story 2 — fail closed (P1)
- [X] T007 [US2] Tests: missing model, hash drift, non-image/truncated/wrong-size/zero/multiple outputs, lost response, execution error + retry, tamper, busy queue, in tests/test_anchors.py

## Phase 4: Polish
- [X] T008 Suite + ledger + PROGRESS; commit

## Blocked
- [ ] T009 Owner-approved single GPU T2I render with the real profile (needs F02 T011–T013)
