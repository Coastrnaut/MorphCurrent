# Feature Specification: Queue- and budget-aware local execution

**Logical ledger ID**: F17 · **Feature Directory**: `specs/017-vram-aware-job-scheduler` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F17 Queue and budget aware local execution: cross-process run lock, per-run job and GPU-time budgets that pause and resume renders without duplicate submissions, dependency-ordered schedule preview"

## Gap analysis
| Exists | Gap |
|---|---|
| One GPU job at a time inside one process; idle-queue gate; content-addressed resume; F11 estimates; F07 VRAM sampling | Two MorphCurrent processes could interleave GPU jobs; a long film (≈ 6–11 GPU-hours) cannot be capped or split into bounded sessions; no preview of what fits a budget |

## User Scenarios & Testing *(mandatory)*
### US1 - Cross-process run lock (P1)
A GPU render takes an exclusive lock file in the runs root (pid, host, start time, heartbeat). A second `--confirm-gpu` render refuses with the holder's details. A lock whose heartbeat is older than 30 minutes is stale and may be taken over (logged). Dry runs and validation never take the lock.

### US2 - Budgets with pause/resume (P1)
`render --confirm-gpu --max-jobs N --max-gpu-s S` counts only *new* GPU submissions (verified/cached stages are free) and stops **before** submitting a stage that would exceed either cap (GPU seconds from F11 history; unknown cost counts as exceeding a finite `--max-gpu-s`). The run ends `paused_budget` (exit 8) with the next task named; rerunning resumes with zero duplicate submissions.
**Acceptance**: fake ComfyUI, 3 anchors + 2 bridges: `--max-jobs 2` → 2 submissions, paused at anchor 3; rerun with no cap → 3 more submissions, complete; total 5 = no duplicates.

### US3 - Schedule preview (P2)
`schedule STORYBOARD [--max-gpu-s S] [--max-jobs N]` lists stages in dependency order with estimated seconds, cumulative time and which stages fit; offline.

### Edge Cases
Crash while holding the lock → stale after timeout; lock released in `finally`. Budget with all stages cached → completes without counting.

## Requirements *(mandatory)*
- **FR-001** Lock: exclusive create; heartbeat refreshed between stages; release on exit; stale threshold configurable.
- **FR-002** Budget check happens before planning a GPU submission; never interrupts a running job.
- **FR-003** Paused runs record `paused_budget`, counters and next task in the manifest.
- **FR-004** `schedule` uses F11 estimates and labels NO DATA stages.

## Success Criteria *(mandatory)*
- **SC-001** No duplicate `/prompt` across pause/resume (fake ComfyUI count).
- **SC-002** Lock contention and stale takeover tested.
- **SC-003** Owner-approved bounded multi-session batch: pending.

## Assumptions
Single GPU; multi-GPU out of scope. Model-stage grouping beyond dependency order is not attempted (each stage already loads its own models).
