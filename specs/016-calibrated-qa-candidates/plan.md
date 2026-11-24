# Implementation Plan: Subject-aware QA and calibration

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
New `qa_subject.py`: `decode_rgb_frames` (FFmpeg, 128×74), `frame_metrics` (reuses `geometry.anchor_geometry` + Laplacian sharpness), `detect_subject_defects`, `calibrate(labels)`. `qa.analyze_clip` merges the new flags. Labels: `configs/qa_labels.json` (seeded from documented observations). CLI `qa-calibrate`.

## Constitution Check
I (heuristic; honest metrics; thresholds fixed before evaluation) PASS · II (local decode) PASS · VII (F08 flags unchanged) PASS.

## Complexity Tracking
None.
