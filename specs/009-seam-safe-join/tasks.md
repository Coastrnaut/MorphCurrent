---
description: "Task list for F09 seam-safe join"
---

# Tasks: Seam-safe join

- [X] T001 [P] [US1/US2] FFmpeg synthetic-clip tests: matching seam → 2L−1 frames, endpoints correct; mismatch refused; no xfade, in tests/test_seam_join.py
- [X] T002 [US1] `check_seams`, `join_verified` (+ ffprobe verify, `.part`) in src/morph_studio/stitcher.py
- [X] T003 [US3] Audio option in `build_join_command`/`join_verified` + tests (video-only has no audio stream; audio cut to video duration)
- [X] T004 Suite, ledger, PROGRESS, commit

## Blocked
- [ ] T005 Seam check on two real Wan bridges sharing generated B (GPU chain blocked)
