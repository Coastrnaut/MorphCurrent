---
name: render-batch
description: Validate and plan a MorphCurrent storyboard, then dispatch only after verifying real model workflows and explicit GPU approval.
---
# Render batch

1. Read `CLAUDE.md`, `PROGRESS.md`, `docs/ARCHITECTURE.md`.
2. Run `python -m morph_studio.cli validate <storyboard>` and `python -m morph_studio.cli plan <storyboard>`.
3. Verify `/system_stats` and `/object_info`, real API exports, semantic node bindings, checkpoint paths and license status.
4. Before any GPU job, record target resolution, frame count, model precision, VRAM strategy and intended candidates.
5. If render executor is not implemented or prerequisites are missing, stop with actionable BLOCKED status, not a fake render.
6. On approved live renders, persist prompt IDs and manifests; after completion verify outputs via ComfyUI history.
7. Update `PROGRESS.md` with artifacts and real measurements.
