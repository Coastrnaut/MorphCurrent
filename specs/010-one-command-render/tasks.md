---
description: "Task list for F10 one-command render"
---

# Tasks: One-command render

- [X] T001 [P] Fake ComfyUI real-video factory (FFmpeg ramps keyed by anchor upload names) in tests/fake_comfy.py
- [X] T002 [P] [US1/US3] Tests: dry run no network/no writes; missing profiles exit 6 with no write requests, in tests/test_render.py
- [X] T003 [US2] Tests: full offline E2E to 129-frame movie via review gate; rerun 0 `/prompt`; `--accept-heuristics`; status read-only, in tests/test_render.py
- [X] T004 [US2] Implement `run_render`, `render_status` in src/morph_studio/render.py
- [X] T005 [US2] `render` CLI in src/morph_studio/cli.py
- [X] T006 Docs: README quickstart + FULL_PIPELINE_DESIGN operator section updated to implemented commands
- [X] T007 Suite, ledger, PROGRESS, commit

## Blocked
- [ ] T008 Owner-approved real end-to-end run (needs F02 models/exports) and reproducible second run
