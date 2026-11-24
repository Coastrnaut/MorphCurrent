---
description: "Task list for F19 long-form sequencing"
---

# Tasks: F19

- [X] T001 [P] [US1] Diff tests incl. E2E prediction-vs-actual with fake ComfyUI in tests/test_longform.py
- [X] T002 [US1] Stage identities + `plan_diff` in src/morph_studio/longform.py; CLI `plan-diff`
- [X] T003 [P] [US2] Chapter schema/index/ffmetadata tests; hash-unchanged test
- [X] T004 [US2] `Anchor.chapter`, DAG field, `chapter_index`, `ffmetadata`, proxy storyboard; CLI `timeline`
- [X] T005 [US3] `storage_report`, `estimate_bytes`, render disk preflight (`--min-free-gb`); CLI `storage`
- [X] T006 [US4] 2/10/50-anchor compile tests; random-restart E2E (no duplicates)
- [X] T007 Suite, docs, ledger, PROGRESS, commit

## Blocked / owner
- [ ] T008 Owner-approved bounded multi-scene GPU render with resume

## Phase 2: Convergence

- [X] T009 Treat stages whose identity is verified in any earlier run (run-*/plan.json + manifest) as cached in the render disk preflight, in src/morph_studio/longform.py and src/morph_studio/render.py, with a post-edit test in tests/test_longform.py per US3 "cached stages cost nothing" (partial)
- [X] T010 Test that `render` exits 9 on blocked_disk via the CLI in tests/test_longform.py per FR-005 (partial)
- [X] T011 Evaluate all nine constitution v2.0.0 principles in the Constitution Check of specs/019-resumable-longform-timeline/plan.md per Constitution (partial)
