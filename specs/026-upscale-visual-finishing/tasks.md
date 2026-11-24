---
description: "Task list for F26 Local Resolution Enhancement and Finishing"
---

# Tasks: Local Resolution Enhancement and Finishing (F26)

**Input**: Design documents from `specs/026-upscale-visual-finishing/`
**Tests**: requested — written first; FFmpeg-gated where they encode.

## Phase 1: Setup

- [X] T001 Create tests/test_finishing.py with an FFmpeg helper making an 832×480 16 fps test clip (test pattern) and a colour-cast variant

## Phase 2: Foundational

- [X] T002 Implement `geometry` (fit/fill sizes and offsets per Clarifications) and `chain` in src/morph_studio/finishing.py with pure tests (832×480 → 1872×1080 + 24 px pad; fill 1920×1108 crop 14; 1440p fit 2496×1440 + 32)

## Phase 3: User Story 1 — HD without invented detail (P1) 🎯 MVP

- [X] T003 [P] [US1] Tests: 1080p fit/fill outputs 1920×1080, same frame count/duration, record with chain/codec/colour space/bit depth/timing/device, input byte-identical; existing output refused; input larger than target refused; optional steps recorded; audio copied
- [X] T004 [US1] Implement `finish` (.part + rename, probe, record `<out>.finish.json`)

## Phase 4: User Story 2 — Identity check (P1)

- [X] T005 [P] [US2] Tests: geometric finish passes identity (grey MAD ≤ 4); a heavily altered output fails
- [X] T006 [US2] Implement `identity_check` (undo pad/crop, scale back, compare first/last frames)

## Phase 5: User Story 3 — Colour match (P2)

- [X] T007 [P] [US3] Test: blue-cast clip matched to a neutral anchor → recorded gains (clamped 0.8–1.25) and output mean closer to the anchor
- [X] T008 [US3] Implement `colour_gains` and the colour step

## Phase 6: User Story 4 — Generative models gated (P3)

- [X] T009 [P] [US4] Tests: `upscale_models` lists files read-only (tmp folder); requesting a model raises a refusal naming owner approval
- [X] T010 [US4] Implement `upscale_models` and `require_owner_approval`; CLI `finish --list-models`

## Phase 7: Polish

- [X] T011 CLI `finish` with tests (ASCII-safe, exit codes)
- [X] T012 Real evidence: finish the MC-RUN-004 movie to 1080p fit; record time and identity; finishing.py imports no ComfyUI client
- [X] T013 Full suite; docs (ARCHITECTURE, ledger, PROGRESS, README)
- [X] T014 Converge loop; commit and push

## Blocked / owner

- [ ] T015 Owner review of a high-resolution delivery; any generative upscaler only after explicit owner approval

## Dependencies

Setup → Foundational → US1 → US2 → US3/US4 → Polish.

## Owner-approved follow-up (2026-11-24)

- [ ] T016 Owner approved a 1080p learned upscaler: after the owner-consented download of RealESRGAN_x2plus.pth (BSD-3-Clause, 67,061,725 bytes, official xinntao/Real-ESRGAN v0.2.1 release) into ComfyUI models/upscale_models and the owner's real API export `workflows/04_upscale_x2.json`, add a hash-pinned binding profile validated against /object_info, an `upscale` stage that runs it on approved clips (GPU, idle queue, --confirm-gpu) before the geometric `finish`, and record the identity check (learned models can invent texture)
