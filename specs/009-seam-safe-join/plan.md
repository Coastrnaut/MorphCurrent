# Implementation Plan: Seam-safe join

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
`stitcher.py`: `check_seams(clips, anchors=None)` using `qa.decode_gray_frames`; `build_join_command(..., audio=None, audio_offset=0, video_seconds=None)` (backward compatible); `join_verified(clips, output, fps, audio=None, …)` → seam report + ffprobe verification + `.part` rename.

## Technical Context
Python 3.11+, FFmpeg/ffprobe 8.1.2; synthetic clips piped as raw gray frames.

## Constitution Check
V PASS (verified decoded seams, no crossfade, 4n+1 arithmetic) · IV PASS (`.part`, no overwrite) · II PASS (local audio only) · VII PASS (existing 3 stitcher tests kept).

## Complexity Tracking
None.
