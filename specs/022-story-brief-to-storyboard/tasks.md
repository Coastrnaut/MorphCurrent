---
description: "Task list for F22 brief to storyboard"
---

# Tasks: F22

- [X] T001 [P] [US1] Golden 8-scene brief tests (counts, references, choreography, duration, determinism) in tests/test_brief.py
- [X] T002 [US1] `Brief`, `plan_storyboard` in src/morph_studio/brief.py
- [X] T003 [US2] `preview` (seconds/frames, total, estimate, blocked) + refusals (duration too short/long, unsafe text)
- [X] T004 [US2] CLI `brief-plan`; example `configs/briefs/engineering-pilot.yaml`
- [X] T005 Suite, ledger, PROGRESS, commit

## Cancelled
- ~~T006 [US3] Optional local LLM drafting~~ — cancelled by the owner 2026-11-24; replaced by Claude Desktop pre-drafting (Phase 3)

## Phase 2: Convergence

- [X] T007 (superseded by T012: `--llm` removed) Add a disabled `brief-plan --llm` extension point that is refused with a clear message (no endpoint configured; nothing written, exit 2) in src/morph_studio/cli.py with a test in tests/test_brief.py per US3 (missing)
- [X] T008 Align plan.md with the actual API (plan_storyboard returns the preview; CLI adds the F11 estimate) in specs/022-story-brief-to-storyboard/plan.md per plan: preview (partial)
- [X] T009 Evaluate all nine constitution v2.0.0 principles in the Constitution Check of specs/022-story-brief-to-storyboard/plan.md per Constitution (partial)

## Phase 3: Owner amendment — Claude Desktop pre-drafting (US3)

- [X] T010 [P] [US3] Tests: pilot brief and sample storyboards pass `lint_draft`; checkpoint/LoRA/node/workflow/URL terms fail naming the field; warnings for independent T2I, missing correspondences, long prompts; `drafted_by` in header but not plan hash; `--llm` rejected by argparse in tests/test_brief.py
- [X] T011 [US3] `lint_draft(data)` (brief or storyboard) and `Brief.drafted_by` in src/morph_studio/brief.py
- [X] T012 [US3] CLI `draft-check FILE` (exit 0 no errors / 3 errors); remove `brief-plan --llm`; header carries `drafted_by` in src/morph_studio/cli.py
- [X] T013 [US3] `docs/DRAFTING.md`: Claude Desktop drafting guide (what to draft, schema rules, physical-morph prompt guidance, forbidden content, validate → dry-run → owner approval); update ledger, ARCHITECTURE, one-shot doc

## Phase 4: Convergence

- [X] T014 Test that a brief whose scene morph names a LoRA or URL fails draft-check naming scenes[i].morph in tests/test_brief.py per US3 acceptance, FR-005 (partial)
