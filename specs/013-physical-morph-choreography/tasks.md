---
description: "Task list for F13 physical correspondence and prompt orchestration"
---

# Tasks: F13

- [X] T001 [P] [US1] Golden-prompt, normalisation, length-cap and dedup tests in tests/test_prompt_compiler.py
- [X] T002 [US1] `Choreography` model in src/morph_studio/schema.py; `compile_bridge_prompts` in src/morph_studio/prompt_compiler.py
- [X] T003 [US2] DAG uses compiled prompts + `negative_prompt`; plan-hash regression test for organic-machines.yaml
- [X] T004 [US2] `bridge_request_for` passes `negative_prompt`; fake-ComfyUI test that the Wan graph node 78 gets it
- [X] T005 [US3] `prompt-preview STORYBOARD [--variants]` CLI
- [X] T006 Suite, ledger, PROGRESS, commit

## Blocked / owner
- [ ] T007 Fixed-seed prompt-only GPU A/B on butterfly→phoenix with owner review
