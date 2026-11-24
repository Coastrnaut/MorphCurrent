---
description: "Task list for F22 brief to storyboard"
---

# Tasks: F22

- [X] T001 [P] [US1] Golden 8-scene brief tests (counts, references, choreography, duration, determinism) in tests/test_brief.py
- [X] T002 [US1] `Brief`, `plan_storyboard` in src/morph_studio/brief.py
- [X] T003 [US2] `preview` (seconds/frames, total, estimate, blocked) + refusals (duration too short/long, unsafe text)
- [X] T004 [US2] CLI `brief-plan`; example `configs/briefs/engineering-pilot.yaml`
- [X] T005 Suite, ledger, PROGRESS, commit

## Deferred
- [ ] T006 [US3] Optional local LLM drafting (owner-enabled endpoint only)

## Phase 2: Convergence

- [X] T007 Add a disabled `brief-plan --llm` extension point that is refused with a clear message (no endpoint configured; nothing written, exit 2) in src/morph_studio/cli.py with a test in tests/test_brief.py per US3 (missing)
- [X] T008 Align plan.md with the actual API (plan_storyboard returns the preview; CLI adds the F11 estimate) in specs/022-story-brief-to-storyboard/plan.md per plan: preview (partial)
- [X] T009 Evaluate all nine constitution v2.0.0 principles in the Constitution Check of specs/022-story-brief-to-storyboard/plan.md per Constitution (partial)
