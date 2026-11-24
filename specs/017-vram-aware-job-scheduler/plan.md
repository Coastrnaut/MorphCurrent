# Implementation Plan: Queue- and budget-aware execution

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
New `scheduler.py`: `RunLock` (context manager), `Budget` (`allow(kind, task) -> bool`, `charge`), `schedule_preview(plan, history, max_gpu_s, max_jobs)`. Hooks: `run_anchor_chain(..., budget=None)` and `run_bridge_stage(..., budget=None)` check before submitting a not-yet-verified job; `run_render(..., max_jobs, max_gpu_s)` builds the budget, holds the lock for `--confirm-gpu`, returns `paused_budget`. CLI: `render --max-jobs --max-gpu-s`, `schedule`.

## Constitution Check
II (one job at a time across processes; never interrupt) PASS · IV (resume without duplicates) PASS · VII (no caps → unchanged behaviour) PASS.

## Complexity Tracking
None.
