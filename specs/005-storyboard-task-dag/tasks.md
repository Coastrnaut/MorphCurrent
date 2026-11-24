---
description: "Task list for F05 storyboard task DAG"
---

# Tasks: Storyboard task DAG

**Tests**: requested

## Phase 1: Foundational
- [X] T001 [P] Width/height multiple-of-16 validation in src/morph_studio/schema.py

## Phase 2: User Story 1 + 2 — task graph and determinism (P1)
- [X] T002 [P] [US1] Tests: 3+2+1 tasks, shared B dependency, 129 frames / 8.0 s / 129/16 s, requirements missing/existing, plan hash stable & sensitive, derived seeds, in tests/test_dag.py
- [X] T003 [US1] Implement `compile_plan` (anchor/bridge/final tasks, topological order, requirements, plan hash) in src/morph_studio/dag.py
- [X] T004 [US1] `dag` subcommand in src/morph_studio/cli.py

## Phase 3: User Story 3 — fail before ComfyUI (P1)
- [X] T005 [US3] Tests: bad beats, size not multiple of 16, forward reference; no network (no ComfyClient constructed), in tests/test_dag.py

## Phase 4: Polish
- [X] T006 Suite, ledger, PROGRESS, commit
