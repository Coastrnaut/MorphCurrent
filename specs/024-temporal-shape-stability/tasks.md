---
description: "Task list for F24 Temporal Shape Continuity and Repair"
---

# Tasks: Temporal Shape Continuity and Repair (F24)

**Input**: Design documents from `specs/024-temporal-shape-stability/`
**Tests**: requested (synthetic deformations, honest evaluation, endpoint regression) — written first.

## Phase 1: Setup

- [X] T001 Create tests/test_continuity.py with synthetic frame builders (128×74 RGB lists: shapes on dark background; smooth grow/move morph; abrupt swap; split into parts; background flash; colour switch)

## Phase 2: Foundational

- [X] T002 Implement clip threshold (max(24, mean endpoint Otsu)), `_mask`, `_parts` (4-connected, components ≥ 0.5% of frame) and `frame_metrics` (occupancy, overlap_prev IoU, parts, background_change, centre, colour, unreliable) in src/morph_studio/continuity.py

## Phase 3: User Story 1 — Locate continuity breaks (P1) 🎯 MVP

- [X] T003 [P] [US1] Tests: smooth morph → no flags; swap → shape_substitution at the swap window (± 2 frames) with overlap < 0.45; split into 4 parts → topology_change with part counts; background flash → background_change; centre teleport → motion_jump; colour switch → colour_jump; unreliable frames excluded; a 5-frame clip is analysed without error in tests/test_continuity.py
- [X] T004 [US1] Implement `detect_continuity(frames)` with the spec Clarification thresholds and `analyze_clip(path)`; CLI `continuity CLIP [--metrics]` (exit 13 on flags, ASCII-safe)

## Phase 4: User Story 2 — Honest evaluation (P1)

- [X] T005 [P] [US2] Tests: `evaluate` on a synthetic labels file with two clips (one hit, one miss) reports recall and misses; missing local clip is skipped with a note in tests/test_continuity.py
- [X] T006 [US2] Implement `evaluate(labels_path, repo_root)` combining F24 and F16 detectors per labelled window (± 4 frames tolerance) and CLI `continuity-eval`

## Phase 5: User Story 3 — Repair proposals (P2)

- [X] T007 [P] [US3] Tests: flags at 30–34 of 65 → refinements per kind + intermediate anchor at frame 32 (33 + 33 frames); window near an endpoint → no anchor (halves < 17), refinements only; no flags → "no repair proposed"; proposal records seed/length/clip hash; `--out` refuses overwrite
- [X] T008 [US3] Implement `propose_repair(report, bridge_task)` and CLI `repair-propose RUN BRIDGE_TASK --out FILE` (clip via release._stage_files, bridge task from run plan.json)

## Phase 6: User Story 4 — Controlled repair comparison (P2)

- [X] T009 [P] [US4] Tests: removed defect + identical endpoints → "candidate improvement — needs owner review"; changed last frame → "endpoint regression"; different lengths → "not comparable"; new defect reported
- [X] T010 [US4] Implement `compare_repair(original_frames, repaired_frames)` (endpoint grey MAD ≤ 2.0) and CLI `repair-compare ORIGINAL REPAIRED` (exit 0 candidate improvement, 14 otherwise)

## Phase 7: Polish

- [X] T011 Real evidence: `continuity` on the labelled real clips and `continuity-eval`; record recall/false flags honestly; < 5 s per clip; continuity.py imports no ComfyUI client
- [X] T012 Full suite; docs (ARCHITECTURE, ledger, PROGRESS, README)
- [X] T013 Converge loop until clean; commit and push

## Blocked / owner

- [ ] T014 Owner-approved controlled repair render of a known collapse/flare bridge (same endpoints/seed/steps) and independent review

## Dependencies

Setup → Foundational → US1 → (US2, US3, US4) → Polish.

## Parallel examples

T003/T005/T007/T009 test authoring in parallel after T002.

## Implementation strategy

MVP = US1 detectors; then evaluation, proposals, comparison.
