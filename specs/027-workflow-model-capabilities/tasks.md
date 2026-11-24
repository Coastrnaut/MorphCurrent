---
description: "Task list for F27 Workflow and Model Capability Registry with Safe Upgrades"
---

# Tasks: Workflow and Model Capability Registry with Safe Upgrades (F27)

**Input**: Design documents from `specs/027-workflow-model-capabilities/`
**Tests**: requested — written first; all offline (recorded object_info fixtures, tmp folders).

## Phase 1: Setup

- [X] T001 Create configs/model_catalogue.json mirroring every model row of docs/MODELS.md (folder/file → licence, source, sha256) and tests/test_registry.py with helpers that copy production profiles/workflows into a tmp repo and merge the two recorded object_info fixtures
- [X] T002 Add `upscale` capability (`input_video` role, video output) to `CAPABILITY_CONTRACTS` and the `BindingProfile.capability` Literal in src/morph_studio/workflow_adapter.py, with a contract test (FR-014)

## Phase 2: Foundational

- [X] T003 Implement the loader-role map, `SEVERITY` order, `RegistryRefusal`, catalogue loading and `PRODUCTION_DEFAULTS` in src/morph_studio/registry.py; test that every SHA-256 in the docs/MODELS.md table appears in the catalogue

## Phase 3: User Story 1 — See what every workflow can do (P1) 🎯 MVP

- [X] T004 [P] [US1] Tests in tests/test_registry.py: production profiles offline → 3 `offline-unverified` entries with roles, node classes, models (role, licence, sha256), wan `length_rule` "4n+1"; with merged object_info → `ready` with min/max/step constraints; edited workflow → `stale-hash`; object_info missing a class → `missing-node` with approval message; models root lacking a file → `missing-model` with approval message; cloud class → `cloud-node`; capability missing a role, unparsable profile and missing workflow → `contract-error`; multiple problems → most severe status and all problems listed; model absent from catalogue → "NOT RECORDED"
- [X] T005 [US1] Implement `build_entry` and `build_registry` in src/morph_studio/registry.py (never raises for bad profiles; no downloads; weights never hashed)

## Phase 4: User Story 2 — Compatibility preview (P1)

- [X] T006 [P] [US2] Tests: identical → compatible, no changes; model/hash change only → compatible; role added → compatible; role moved to another node/input/class → needs-rebinding; non-required role removed → needs-rebinding; constraint step changed → needs-rebinding; capability change, output-kind change, required role missing → incompatible
- [X] T007 [US2] Implement `compare(current, candidate)` in src/morph_studio/registry.py

## Phase 5: User Story 3 — Safe selection and rollback (P2)

- [X] T008 [P] [US3] Tests: no record → production default (and none for upscale); no `--approve` → refused, no file written; not ready (offline, stale, missing model, cloud) → refused; incompatible with current → refused; approved ready candidate → active, history entry with both profiles/checksums and note; rollback → previous/default restored and rollback entry appended; rollback with nothing → refused; history never rewritten (prior entries byte-identical)
- [X] T009 [US3] Implement `active_profile`, `select`, `rollback` with atomic `.part` + `os.replace` writes in src/morph_studio/registry.py

## Phase 6: Polish

- [X] T010 CLI `registry`, `registry-diff`, `registry-select`, `registry-rollback` in src/morph_studio/cli.py with tests (ASCII output, exit codes 0/1/2, `--strict`, `--live` uses read-only object_info only)
- [X] T011 Test that registry.py contains no download/install calls (no `urlretrieve`, `pip`, `git clone`, POST/queue use) and that render defaults are unchanged (FR-012)
- [X] T012 Real evidence: `registry` offline and `registry --live --models-root ... --strict` against the running ComfyUI (read-only); record timing and statuses
- [X] T013 Full suite; docs (ARCHITECTURE, ledger, PROGRESS, README, MODELS pointer to catalogue)
- [ ] T014 Converge loop; commit and push

## Blocked / owner

- [ ] T015 Owner installs an alternative local workflow (e.g. the F26 upscale export `workflows/04_upscale_x2.json`) to be inspected, bound and selected under owner approval

## Dependencies

Setup → Foundational → US1 → US2 (uses entries) → US3 (uses entries + compare) → Polish. T004/T006/T008 test tasks precede their implementations.

## Implementation Strategy

MVP = US1 registry listing; then preview; then selection/rollback; CLI last.

## Phase 7: Convergence

- [X] T016 Make `registry-diff` exit 2 (with the reason on stderr) when either profile is unreadable or its workflow is missing, per contracts/cli.md / FR-013 (partial)
