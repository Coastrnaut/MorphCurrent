---
description: "Task list for F16 subject-aware QA and calibration"
---

# Tasks: F16

- [X] T001 [P] [US2] Synthetic clips (shrink, drift, blur, clean) tests in tests/test_qa_subject.py
- [X] T002 [US1] `decode_rgb_frames`, `frame_metrics` in src/morph_studio/qa_subject.py
- [X] T003 [US2] `detect_subject_defects` (collapse, drift, blur windows); merge into `qa.analyze_clip`
- [X] T004 [US3] `configs/qa_labels.json` from documented observations; `calibrate` + `qa-calibrate` CLI
- [X] T005 Run calibration on real local clips; record in PROGRESS; ledger; commit

## Blocked / owner
- [ ] T006 Owner-labelled held-out windows; threshold tuning on train split only
