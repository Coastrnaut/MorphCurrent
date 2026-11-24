---
description: "Task list for F29 Structured Local A/B Experiments and Quality-vs-Cost Optimization"
---

# Tasks: Structured Local A/B Experiments and Quality-vs-Cost Optimization (F29)

**Input**: Design documents from `specs/029-budgeted-experiment-optimizer/`
**Tests**: requested — written first; offline with a stand-in executor (no ComfyUI).

## Phase 1: Setup

- [X] T001 Create tests/test_experiment.py with helpers (tmp repo with the real Wan profile/workflow, two tiny PNG anchors, a history file, a definition builder) and configs/experiments/orchid-length-seed.yaml (MC-RUN anchors orchid→butterfly, lengths 65/81, 2 seeds, budget)

## Phase 2: Foundational

- [X] T002 Implement the definition model, `ALLOWED`, leakage check, seed block (`seeds` or `seed_count` via `derived_seed`), value validation (length ≥ 5 and 4n+1, width/height multiples of 16, fps > 0, profile capability wan_flf2v, images exist) and `effective_defaults` in src/morph_studio/experiment.py with tests

## Phase 3: User Story 1 — Design a bounded comparison (P1) 🎯 MVP

- [X] T003 [P] [US1] Tests: 2 lengths × 2 prompts × 3 seeds → 13 candidates, baseline first, deterministic order (seeds fastest, factors by name) and identical ids across runs; single-value factor warned; duplicate of baseline removed; estimates from matching history else NO DATA; budget max_runs 5 → 8 deferred with limit; max_gpu_s and max_frames deferrals; refusals for leakage, disallowed setting (steps), bad length, bad size, missing image
- [X] T004 [US1] Implement `design`, `out_dir_for` and `plan_summary`

## Phase 4: User Story 2 — Run safely (P1)

- [X] T005 [P] [US2] Tests: no confirm → executor called with submit False and outcomes `validated`, nothing counted done; confirm → strictly sequential calls in order, outcomes appended; GPU budget 100 s at 40 s/candidate → 3 run then "budget exhausted"; max_runs stop; rerun reuses finished; failed outcome counted toward runs; early-stop after N flagged at a level skips the rest of that level; deferred candidates never executed; approved run folders untouched
- [X] T006 [US2] Implement `run` and `bridge_executor` (BridgeRequest → plan_bridge → run_bridge; job record → exec_s, frames, bytes, verification; qa flags)

## Phase 5: User Story 3 — Rate, compare and choose (P2)

- [X] T007 [P] [US3] Tests: rating range/unknown refusals; per-level means; Pareto set equals a hand-computed set (memory not measured → dropped with note); unrated excluded; length mismatch flagged; report has controls, factors, seeds, budget, totals and caveat; Markdown written
- [X] T008 [US3] Implement `rate`, `pareto`, `report` (JSON + Markdown)

## Phase 6: Polish

- [X] T009 CLI `experiment-plan`, `experiment-run`, `experiment-rate`, `experiment-report` in src/morph_studio/cli.py with tests (ASCII, exit codes, `--confirm-gpu` passthrough)
- [X] T010 Real evidence: `experiment-plan` on configs/experiments/orchid-length-seed.yaml with the real perf history; read-only validation run (`experiment-run` without --confirm-gpu) when ComfyUI is idle
- [X] T011 Full suite; docs (ARCHITECTURE, ledger, PROGRESS, README)
- [ ] T012 Converge loop; commit and push

## Blocked / owner

- [ ] T013 Bounded GPU comparison with `--confirm-gpu` within an owner-approved budget, owner ratings and report review (acceptance gate)

## Dependencies

Setup → Foundational → US1 → US2 (runs the design) → US3 (analyses results) → Polish.

## Implementation Strategy

MVP = plan/design; then runner with stand-in executor; analysis; CLI.

## Phase 7: Convergence

- [X] T014 Test `bridge_executor` outcome mapping (exec seconds, produced frames, bytes, QA flags, failed job, validate-only) with stand-in plan_bridge/run_bridge/analyze_clip per T006 / US2-AC2 (partial)
- [X] T015 Report candidates that fail validation as `invalid` (with errors) instead of counting them as validated, per US2-AC1 (partial)
