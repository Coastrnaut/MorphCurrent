# Implementation Plan: Reference-guided next anchors

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
Extend the storyboard schema with `independent_t2i` and optional per-anchor `negative_prompt`; add `run_anchor_chain()` in `anchors.py` that walks anchors in order, binds each child to its parent's verified bytes, enforces dimension continuity and blocks missing edit profiles; add `media.contact_sheet()` (FFmpeg `hstack`, argument list).

## Technical Context
Python 3.11+, no new deps; FFmpeg 8.1.2 on PATH (tests skip if absent). Fake ComfyUI from F03.

## Constitution Check
I (fallback labelled, review required) PASS · II (one job at a time, consent passed through) PASS · III (no node guessing) PASS · IV (parent SHA re-verified; contact sheet exclusive create) PASS · V (byte-identical B: chain passes the same verified file) PASS · VII (schema change additive; existing storyboard still valid) PASS.

## Design
- `schema.Anchor`: `generation: Literal["text_to_image","reference_edit","independent_t2i"]`, `negative_prompt: str | None`; validator per FR-001.
- `anchors.AnchorSpec` (id, method, prompt, negative, seed, reference) and `run_anchor_chain(specs, *, t2i_profile, edit_profile, client, runs_root, submit, width, height, …) -> ChainResult` (jobs by id, blocked list, stop at first non-verified when submitting).
- `media.contact_sheet(images, out, height=240)`.

## Complexity Tracking
None.
