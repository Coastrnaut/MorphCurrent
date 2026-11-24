---
description: "Task list for F23 Camera Moves and Framing Consistency"
---

# Tasks: Camera Moves and Framing Consistency (F23)

**Input**: Design documents from `specs/023-camera-framing-keyframes/`
**Tests**: requested (seeded impossible moves, deterministic mapping, explicit graph refusal) — written first.

## Phase 1: Setup

- [X] T001 Create tests/test_camera.py with a synthetic-anchor helper (bright rectangle at a given centre/size on a dark background, written as PNG)

## Phase 2: Foundational

- [X] T002 Add `CameraMove` (move list per data-model, amount 0–0.5 default 0.1, control prompt|graph), `FramingTarget` (center, tolerance 0–0.5 default 0.08, size [min,max] default [0.2,0.8]) and `RenderConfig.delivery_crops` ("16:9"|"9:16") to src/morph_studio/schema.py; error when `camera` and a non-static `choreography.camera` are both set

## Phase 3: User Story 1 — Camera move with honest labelling (P1) 🎯 MVP

- [X] T003 [P] [US1] Tests: deterministic clause for each move (amount words slightly/moderately/strongly + "about N% of the frame"); bridge task records `camera` with label "prompt-only approximation"; `control: graph` refused naming the missing capability; sample plan hash unchanged; conflict with choreography camera rejected; amount < 0 or > 0.5 rejected in tests/test_camera.py
- [X] T004 [US1] Implement `camera_clause(move, amount)` and `graph_camera_nodes(graph)` in src/morph_studio/camera.py; append the clause in src/morph_studio/prompt_compiler.py; record `camera` on bridge tasks and refuse `control: graph` in src/morph_studio/dag.py

## Phase 4: User Story 2 — Endpoint satisfiability (P1)

- [X] T005 [P] [US2] Tests: push_in passes with end 1.3× larger and fails as pull_out; pan_left 0.2 fails when the subject did not move and passes when it shifted right ≥ 0.1; tilt; static within F12 limits; orbit/rise → not_verifiable; unreliable mask → unknown in tests/test_camera.py
- [X] T006 [US2] Implement `satisfiability(move, amount, start_geo, end_geo)` per spec Clarifications thresholds in src/morph_studio/camera.py

## Phase 5: User Story 3 — Framing targets and crops (P2)

- [X] T007 [P] [US3] Tests: on-target anchor; off-centre anchor flagged; centred subject inside 16:9 and 9:16 safe areas; right-edge subject outside 9:16 only in tests/test_camera.py
- [X] T008 [US3] Implement `framing_check(geo, target)` and `crop_check(geo, width, height, crops, margin=0.05)` in src/morph_studio/camera.py

## Phase 6: User Story 4 — camera-check command (P2)

- [X] T009 [P] [US4] Tests: storyboard-only report (pending anchors, exit 0); run report from synthetic run anchors with an unsatisfiable move (exit 12) in tests/test_camera.py
- [X] T010 [US4] Implement `camera_check(storyboard, run_dir=None, repo_root=".")` (anchor images via release._stage_files) and CLI `camera-check` in src/morph_studio/camera.py and src/morph_studio/cli.py

## Phase 7: Polish

- [X] T011 Real evidence: camera-check on the real organic-machines run anchors; record report; < 2 s; camera.py imports no ComfyUI client (FR-010)
- [X] T012 Full suite; docs (ARCHITECTURE, ledger, PROGRESS, README command list)
- [X] T013 Converge loop until clean; commit and push

## Blocked / owner

- [ ] T014 Operator-approved two-bridge GPU test with a camera move (stable geometry, measured bounds)

## Dependencies

Setup → Foundational → US1 → US2 → US3 → US4 → Polish (US2/US3 independent of each other).

## Parallel examples

T003, T005, T007 test authoring in parallel after T002.

## Implementation strategy

MVP = US1 labelled camera clause; then satisfiability, framing/crops, command.

## Phase 8: Convergence

- [X] T015 Check graph camera control against the workflow named by the active `wan_flf2v` binding profile and always refuse `control: graph` (no camera input, or camera node present but unbound until F27), with tests, in src/morph_studio/camera.py and src/morph_studio/dag.py per FR-003, plan: pinned workflow (partial)
