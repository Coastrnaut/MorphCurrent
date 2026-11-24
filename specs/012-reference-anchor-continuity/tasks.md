---
description: "Task list for F12 composition-aware anchors"
---

# Tasks: F12

- [X] T001 [P] [US1] Synthetic-image tests (centred, shifted, scaled, lopsided, bright background, tiny) in tests/test_geometry.py
- [X] T002 [US1] `decode_rgb_small`, `anchor_geometry` in src/morph_studio/geometry.py
- [X] T003 [US2] `compare_geometry` + flag thresholds + tests
- [X] T004 [US2] Real-data regression on local MC-RUN-001/002 phoenix vs butterfly (recorded in docs/PROGRESS.md; outputs not committed)
- [X] T005 [US3] Record geometry/comparison in `_check_continuity` (src/morph_studio/anchors.py) and surface anchor flags in render review output (src/morph_studio/render.py); test in tests/test_anchor_chain.py
- [X] T006 [US3] `anchor-check A B` CLI
- [X] T007 Suite, ledger, PROGRESS, commit

## Blocked / owner
- [ ] T008 Owner-approved matched three-anchor set using the checks (GPU candidates, F16 calibration)
