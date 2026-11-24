---
description: "Task list for F25 Delivery Frame Rates and Energy-Warped Retiming"
---

# Tasks: Delivery Frame Rates and Energy-Warped Retiming (F25)

**Input**: Design documents from `specs/025-optical-frame-interpolation/`
**Tests**: requested — written first; FFmpeg-gated where they encode video.

## Phase 1: Setup

- [X] T001 Create tests/test_interpolate.py with FFmpeg helpers: 16 fps synthetic clip whose frame k has grey level 4k (65 frames), and a clip with a hard cut at frame 32

## Phase 2: Foundational

- [X] T002 Implement `FILTERS`, `anchor_alignment(duration, fps)` (Fraction-exact) and `ffmpeg_version()` in src/morph_studio/interpolate.py

## Phase 3: User Story 1 — Convert without losing the original (P1) 🎯 MVP

- [X] T003 [P] [US1] Tests: 16→24 blend keeps duration within one output frame, sidecar has checksums/filter/version, input byte-identical; existing output refused; repeat/motion at 30/48/60 also succeed; an input with an audio stream keeps its audio
- [X] T004 [US1] Implement `convert` (.part + rename, probe, sidecar `<out>.interp.json`, input checksum re-verified) in src/morph_studio/interpolate.py

## Phase 4: User Story 2 — Anchor alignment (P1)

- [X] T005 [P] [US2] Tests: 2.0 s clip → 9 anchor marks, all exact at 24/48/60, 5 exact at 30 with others offset ≤ half a frame
- [X] T006 [US2] Include alignment in the conversion record

## Phase 5: User Story 3 — No blending across cuts (P2)

- [X] T007 [P] [US3] Test: hard-cut clip with blend → method_used repeat, fallback reason names the cut frame
- [X] T008 [US3] Hard-cut check via qa.analyze_clip in `convert`

## Phase 6: User Story 4 — Energy-warped retiming (P2)

- [X] T009 [P] [US4] Tests: `warp_times` inverse of a map; apply_warp with a fast-middle map keeps first/last frames (grey MAD ≤ 3), frame count and duration, faster brightness rise in the middle; identity map ≈ source; wrong-length map refused
- [X] T010 [US4] Implement `warp_times` and `apply_warp` (ffconcat with per-frame durations, fps=16 nearest, sidecar `.warp.json`)

## Phase 7: Polish

- [X] T011 CLI `interpolate` and `warp-apply` (from a map file or a sync-plan bridge index) with tests; ASCII-safe output
- [X] T012 Real evidence: convert the MC-RUN-004 final movie to 24 fps (blend) and apply a real sync-plan warp to a real bridge; record numbers
- [X] T013 Full suite; interpolate.py imports no ComfyUI client (FR-007); docs (ARCHITECTURE, ledger, PROGRESS, README)
- [X] T014 Converge loop; commit and push

## Blocked / owner

- [ ] T015 Owner review of interpolated and warped output (seam integrity, look)

## Dependencies

Setup → Foundational → US1 → US2/US3 (extend convert) → US4 → Polish.

## Phase 8: Convergence

- [X] T016 Test that a held (frozen) stretch stays frozen after blend conversion, in tests/test_interpolate.py per Edge case "frozen frames" (partial)
