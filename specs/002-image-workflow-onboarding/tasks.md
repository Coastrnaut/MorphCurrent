---
description: "Task list for F02 image model and workflow onboarding"
---

# Tasks: Image model and workflow onboarding

**Input**: `specs/002-image-workflow-onboarding/` · **Tests**: requested (test-first)

## Phase 1: Setup
- [X] T001 Read model metadata of local Qwen templates (read-only) and record in specs/002-image-workflow-onboarding/research.md

## Phase 2: User Story 1 — capability role contract (P1)
- [X] T002 [P] [US1] Tests: missing reference_image, video output on T2I profile, Wan profile still ok, in tests/test_onboarding.py
- [X] T003 [US1] Add `CAPABILITY_CONTRACTS` (text_to_image → positive_prompt, seed / image; reference_edit → positive_prompt, seed, reference_image / image; wan_flf2v → start_image, end_image, positive_prompt, seed, length / video) and checks in `validate_profile` in src/morph_studio/workflow_adapter.py

## Phase 3: User Story 2 — workflow-inspect (P1)
- [X] T004 [P] [US2] Tests: missing model literal, cloud node, UI-format rejection, candidates labelled `candidate`, no file writes, in tests/test_onboarding.py
- [X] T005 [US2] Implement `inspect_export(graph, object_info|None)` in src/morph_studio/onboarding.py
- [X] T006 [US2] Add `workflow-inspect` subcommand (`--object-info`, `--offline`; exit 0/4/2) in src/morph_studio/cli.py

## Phase 4: User Story 3 — decision record (P2)
- [X] T007 [US3] Write docs/ANCHOR_MODEL_DECISION.md (candidates from local templates, licenses `owner to verify`, manual export procedure, approval line) and link from docs/ANCHOR_MODEL_ONBOARDING.md and configs/models.yaml
- [X] T008 [US3] Docs test (gate BLOCKED, no download without approval) in tests/test_onboarding.py

## Phase 5: Polish
- [X] T009 Run suite + live read-only `workflow-check`; update PROGRESS.md and ledger (F02 = OFFLINE-PASS, GPU/export BLOCKED)
- [X] T010 Commit F02 offline slice

## Blocked (owner-gated, not executable this session)
- [ ] T011 Owner approves model set; owner downloads weights into ComfyUI model folders
- [~] T012 Owner renders one T2I and one edit image in ComfyUI UI, saves API exports to workflows/01_anchor_t2i.json and workflows/02_anchor_edit.json
- [ ] T013 Write configs/profiles/anchor_t2i.binding.json and anchor_edit.binding.json from the real exports; validate live

## Dependencies
US1 and US2 independent; US3 independent; T011 → T012 → T013.
