# Implementation Plan: Composition-aware anchors

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
New `geometry.py`: decode small RGB via FFmpeg, mask by luminance above background (Otsu threshold on gray), centroid/extent/area/symmetry/palette; `compare_geometry(parent, child)`. Hook into `anchors._check_continuity` (advisory, recorded) and `render` review output; CLI `anchor-check`.

## Technical Context
Python 3.11+, FFmpeg (already required); 128×74 = 9,472 px per image, trivial in pure Python. Tests use `make_png` synthetic images.

## Constitution Check
I (heuristic labels, advisory) PASS · III (no node/model changes) PASS · IV (records only add fields) PASS · V (shared B untouched) PASS · VII (chain behaviour unchanged except added record) PASS.

## Data model
Geometry: `{width, height, centroid: [x, y], extent: [w, h], area, symmetry, palette: [[r,g,b]...], threshold, mask_unreliable}`. Comparison: `{method: heuristic, centroid_shift, extent_ratio: [w, h], area_ratio, symmetry_delta, palette_distance, flags[], review}`.

## Complexity Tracking
None.
