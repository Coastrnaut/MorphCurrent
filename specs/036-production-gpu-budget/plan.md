# Implementation Plan: Production GPU Budget and Batch Scheduling (F36)

**Branch**: `036-production-gpu-budget` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/036-production-gpu-budget/spec.md`

## Summary

New `src/morph_studio/production.py`:
- `ingest(runs_root, history_path)` → scan `*/job.json`: verified, `timings.execution_seconds`; bridge (kind contains "bridge"): width/height/length from `values`; anchor: method from `request.method` (or `kind`), width/height; dedupe by `job` (first 16 hex of job id); append to `entries`, atomic write; refuse malformed history.
- `stage_cost(task, history)` → (seconds, label): exact median (ESTIMATED); bridges same size: interpolate/extrapolate linearly in frames over per-length medians (INTERPOLATED / EXTRAPOLATED, extrapolation clamped ≥ 0); else pixel×frame scaling from the largest measured (EXTRAPOLATED); anchors exact (method, size) else scaling by pixels (EXTRAPOLATED); none → NO DATA.
- `budget(plan, history, *, cold_s=60, max_batch_s=7200, max_jobs=20)` → per act (anchor chapter; bridge by start anchor) stats, batches (plan order within act, caps, oversized flag, ETA incl. cold start), totals, storage via `longform.plan_bytes`.
- `approve(log, act, note, owner)`, `approvals(log)`.
- `write_batches(storyboard, act, out_dir, *, plan, history, caps, approvals_log)` → for each batch: sub-storyboard with the batch's anchors plus any anchor referenced by them or by the batch's bridges (boundary/parent anchors included as explicit text-to-image? — no: a referenced parent from a previous batch is included unchanged so its task is identical; its job is cached), all anchor `seed`s and transition `seed`s pinned to the full plan's values; validated; refuse existing files.
- `status(plan, runs_root, history)` → finished = stages whose identity is in `longform.cached_stages`; remaining seconds/ETA; ratios from job records matched to stages (by request values) vs `stage_cost` with the history *excluding* that job; duplicates of `prompt_id` across all job records.
- CLI: `history-ingest`, `prod-budget STORYBOARD`, `prod-approve STORYBOARD --act A --note N`, `prod-batch STORYBOARD --act A`, `prod-status STORYBOARD`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: existing `dag.compile_plan`, `longform.cached_stages/plan_bytes/stage_identities`, `perf.load_history`, `schema`

**Storage**: `configs/perf_history.json` (append), `outputs/production/…`

**Testing**: pytest with synthetic histories and fake runs folders; real film storyboard and real runs folder

**Target Platform**: native Windows 11

**Project Type**: library + CLI

**Performance Goals**: budget/batches < 3 s for 191 stages

**Constraints**: no GPU; batch stages identical to full plan; approval required; no overwrite

**Scale/Scope**: 191 stages, ~30 job records

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | Measured history only; labels on every estimate; ±20% check vs actuals | PASS |
| II Local, consent | Batches rendered only via render --confirm-gpu after owner approval | PASS |
| III Graph contracts | No graph changes | N/A |
| IV Immutable artifacts | Seeds pinned so batch stages reuse content-addressed jobs; duplicate check | PASS |
| V Physical morph | Shared anchors identical (same task → same job) | PASS |
| VI Spec Kit | Full workflow + converge | PASS |
| VII Compatibility | History format unchanged (entries appended) | PASS |
| VIII Loopback UIs | N/A | N/A |
| IX Owner gates | Per-act approval before batch storyboards | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/036-production-gpu-budget/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/cli.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/morph_studio/production.py   # new
src/morph_studio/cli.py          # history-ingest, prod-* commands
configs/perf_history.json        # updated by ingest (measured entries)
tests/test_production.py         # new
```

**Structure Decision**: one module plus CLI wiring.

## Complexity Tracking

None.
