# Implementation Plan: Quality heuristics and selective rerender

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
`qa.py`: `decode_gray_frames(path)` (FFmpeg rawvideo gray 64×36), `analyze_frames(frames, start_ref, end_ref)`, `analyze_clip(path, start_image, end_image)`, `candidate_seeds`, `rank_candidates`, `rerender_plan(dag, verdicts, reviews)`, `Review` JSON persistence.

## Technical Context
Python 3.11+, no numpy (byte arithmetic on 2304-pixel frames is fast enough for ≤ 200 frames); FFmpeg 8.1.2.

## Constitution Check
I PASS (heuristic labels; human review gate) · II PASS (local decode) · V PASS (rerender only failing bridge; anchors preserved) · VII PASS.

## Complexity Tracking
None.
