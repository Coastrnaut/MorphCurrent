# Implementation Plan: One-command render

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
`render.py` `run_render(storyboard_path, client_factory, *, confirm_gpu, accept_heuristics, …)` composing F03–F09; `render_status(run_dir)`; CLI `render` (`--dry-run`, `--confirm-gpu`, `--status`, `--accept-heuristics`, `--allow-busy-queue`, `--sample-vram`, profile overrides). Fake ComfyUI gains a real-video factory (FFmpeg ramps keyed by uploaded anchor names so a shared B gives matching seams).

## Constitution Check
I PASS (states: blocked / validated / awaiting_review / complete; GPU acceptance not claimed) · II PASS (dry-run offline, consent flag, gate) · III PASS · IV PASS (content-addressed stages, manifest) · V PASS (shared B, verified seams, no xfade) · VII PASS.

## Contract
`contracts/render-cli.md`. Exit codes: 0 complete/validated/dry-run ok, 6 blocked, 7 awaiting review, 5 stage failed, 2 error.

## Complexity Tracking
None.
