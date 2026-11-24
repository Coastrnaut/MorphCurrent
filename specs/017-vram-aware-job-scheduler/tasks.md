---
description: "Task list for F17 queue- and budget-aware execution"
---

# Tasks: F17

- [X] T001 [P] [US1] Lock tests (contention, stale takeover, release) in tests/test_scheduler.py
- [X] T002 [US1] `RunLock` in src/morph_studio/scheduler.py
- [X] T003 [P] [US2] Budget pause/resume E2E test with fake ComfyUI (no duplicate prompts)
- [X] T004 [US2] `Budget`; hooks in anchors.run_anchor_chain, pipeline.run_bridge_stage; render caps + lock + paused_budget (exit 8)
- [X] T005 [US3] `schedule_preview` + `schedule` CLI
- [X] T006 Suite, ledger, PROGRESS, commit

## Blocked / owner
- [ ] T007 Owner-approved bounded multi-session GPU batch

## Phase 2: Convergence

- [X] T008 Heartbeat the run lock before every new GPU submission even without caps (uncapped long renders must not look stale) in src/morph_studio/render.py with a test in tests/test_scheduler.py per FR-001, Constitution II (partial)
- [X] T009 Record the budget summary (counters, caps, blocked next task) in the run manifest on paused_budget in src/morph_studio/render.py with a test per FR-003 (partial)
- [X] T010 Test that a fully cached render under --max-jobs 0 completes without submissions in tests/test_scheduler.py per Edge case "all stages cached" (partial)
- [X] T011 Align plan.md Budget API description (allow charges; no separate charge) in specs/017-vram-aware-job-scheduler/plan.md per plan: Budget.charge (partial)
- [X] T012 Evaluate all nine constitution v2.0.0 principles in the Constitution Check of specs/017-vram-aware-job-scheduler/plan.md per Constitution (partial)
