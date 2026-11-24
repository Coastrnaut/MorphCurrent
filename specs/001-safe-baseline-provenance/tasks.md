---
description: "Task list for F01 safe baseline, GPU gates and provenance"
---

# Tasks: Safe baseline, GPU concurrency gates, evidence and provenance

**Input**: `specs/001-safe-baseline-provenance/` (plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md)
**Tests**: requested (constitution III, test-first). Test tasks precede implementation.

## Phase 1: Setup

- [X] T001 Capture real `/object_info` subset (25 image-relevant classes incl. 2 cloud nodes) into tests/fixtures/object_info_image_nodes.json
- [X] T002 Record baseline: HEAD 7c54caf, `pytest -m "not integration and not gpu"` = 83 passed / 1 deselected, Spec Kit `--status`/`--verify` ready, ComfyUI queue empty

## Phase 2: Foundational

- [X] T003 Implement `cloud_nodes(graph, object_info)` (rule: `api_node: true` OR `python_module` startswith `comfy_api_nodes`) in src/morph_studio/gates.py

## Phase 3: User Story 2 — shared GPU gate (P1)

**Independent test**: tests/test_gates.py deny/allow matrix.

- [X] T004 [P] [US2] Write tests for consent / busy queue / cloud node / allow cases and validate_graph cloud error in tests/test_gates.py
- [X] T005 [US2] Implement `GateDecision` (`allowed` true only when `reasons` empty; codes `consent`, `queue_busy`, `cloud_node`) and `check_gpu_gate` in src/morph_studio/gates.py
- [X] T006 [US2] Add cloud-node error to `validate_graph` in src/morph_studio/workflow_adapter.py
- [X] T007 [US2] Route `bridge._submit` queue check through `check_gpu_gate`, preserving the existing error text, in src/morph_studio/bridge.py

## Phase 4: User Story 1 — read-only baseline report (P1)

**Independent test**: tests/test_preflight.py with a MockTransport that fails on any non-GET.

- [X] T008 [P] [US1] Write tests: GET-only, idle/busy queue, unreachable ComfyUI, skip-comfy, capability blocked with empty checkpoints, Wan profile available, `--out` refuses overwrite, in tests/test_preflight.py
- [X] T009 [US1] Implement inventory (`checkpoints`, `diffusion_models`, `text_encoders`, `vae`, `loras`; `sha256: "NOT MEASURED"`), capability classification and `build_baseline_report` in src/morph_studio/preflight.py
- [X] T010 [US1] Implement git facts and optional nvidia-smi snapshot (`label: "snapshot (not peak)"`) via argument-list subprocess in src/morph_studio/preflight.py
- [X] T011 [US1] Add `baseline` subcommand (`--skip-comfy`, `--object-info`, `--out` exclusive create, `--strict` exit 3) in src/morph_studio/cli.py

## Phase 5: User Story 3 — environment document (P2)

- [X] T012 [US3] Run live `baseline` read-only and write measured facts to docs/ENVIRONMENT.md
- [X] T013 [US3] Add docs test (NOT MEASURED labels, no user-profile paths) in tests/test_preflight.py

## Phase 6: Polish

- [X] T014 Run full offline suite and `workflow-check`; record counts in PROGRESS.md and docs/SPECKIT_FEATURE_LEDGER.md
- [X] T015 Commit F01 on main with test evidence

## Dependencies

T003 → US2 (T004–T007) and US1 (T008–T011, which reports cloud classes) → US3 → Polish. T004 and T008 may be written in parallel.

## Implementation strategy

MVP = US2 gate (safety) then US1 report; US3 is documentation generated from US1.
