# Implementation Plan: Queue- and budget-aware execution

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
New `scheduler.py`: `RunLock` (context manager), `Budget` (`allow(kind, task) -> bool` charges the job and its estimated seconds only when allowed; `summary()`; `on_check` heartbeats the lock), `schedule_preview(plan, history, max_gpu_s, max_jobs)`. Hooks: `run_anchor_chain(..., budget=None)` and `run_bridge_stage(..., budget=None)` check before submitting a not-yet-verified job; `run_render(..., max_jobs, max_gpu_s)` builds the budget, holds the lock for `--confirm-gpu` (an always-allow budget heartbeats it before every submission when no caps are given), returns `paused_budget` and records the budget summary in the manifest. CLI: `render --max-jobs --max-gpu-s`, `schedule`.

## Constitution Check
Re-evaluated against constitution v2.0.0:

| Principle | Status |
|---|---|
| I Evidence | PASS — fake-ComfyUI pause/resume, lock and heartbeat tests; multi-session GPU batch kept pending (T007) |
| II Local inference, GPU consent | PASS — one MorphCurrent GPU render per runs root; never interrupts; `--confirm-gpu` still required |
| III Graph contracts, test-first | PASS — no graph changes; tests precede hooks |
| IV Immutable artifacts, safe resume | PASS — budgets checked before submission; verified stages free; no duplicate prompts |
| V Physical morph timing | PASS — unaffected |
| VI Forty features / Spec Kit | PASS — retroactive converge loop run under the v2.0.0 workflow |
| VII Compatibility and hygiene | PASS — no caps → unchanged results |
| VIII Loopback UIs | N/A — no UI |
| IX Owner gates | PASS — budgets make bounded owner-approved sessions possible |

## Complexity Tracking
None.
