# Implementation Plan: Batch Review and Iteration for the Film's Bridges (F39)

**Branch**: `039-batch-review-iteration` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/039-batch-review-iteration/spec.md`

## Summary

New `src/morph_studio/batch_review.py`:
- `film_state(storyboard, runs_root, log)` → compiles the film plan; scans every `<runs_root>/run-*/manifest.json` (ordered by `created_at`), keeps stages whose ids are in the film plan, collects versions per stage (distinct `video_sha256` / `image_sha256`; job id, run, time, media path via the job dir), QA status/flags/score (`qa.SEVERITY`), and the latest decision (per-run `review.json` entries pinned to that run's version, then the film log). Stale = decision version ≠ current version. Per-act totals.
- `record(log, state, stage, decision, note, reviewer)` → validates and appends a JSONL entry pinned to the current version.
- `approve_act(log, state, act, reviewer)` → bulk approval of eligible bridges.
- `review_order(state, act=None)` → flagged first (score desc), then storyboard order.
- `rerender_queue(state, plan)` → rejected bridges + rejected anchors + `conditioned_on_parent` descendants + adjacent bridges; `production.stage_cost` estimate; `write_rerender(storyboard, queue, out)` → contiguous segment storyboard with pinned seeds for unchanged stages and `derived_seed(master, "<task>:rerender:<n>")` for queued stages.
- `act_sheet(state, act, out)` → FFmpeg first/middle/last frames per rendered bridge, tiled with a label column via `media.contact_sheet`-style tiling.
- `compare(state, stage, v1, v2, out)` → FFmpeg `hstack` (scaled to equal height, padded to the longer duration).
- Review UI: `/film/<act>` page and `POST /film/review` (existing CSRF token), keyboard script (A/R/N).
- CLI: `film-review-status`, `film-review`, `film-review-approve-act`, `film-rerender-queue`, `film-act-sheet`, `film-compare`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: stdlib; existing `dag.compile_plan`, `run_manifest`, `qa`, `production.stage_cost`, `review_ui`, `media`, `seeds.derived_seed`; local FFmpeg

**Storage**: append-only `outputs/reviews/<film>.batch-review.jsonl`; sheets/compare clips under `outputs/reviews/`

**Testing**: pytest with synthetic run folders (manifests, job dirs, tiny clips/PNGs), FFmpeg-gated media tests, review-UI handler tests

**Target Platform**: native Windows 11, loopback UI only

**Project Type**: library + CLI + local web page

**Performance Goals**: film state for 191 stages over a dozen runs < 2 s

**Constraints**: no GPU; logs append-only; never overwrite outputs

**Scale/Scope**: 96 anchors, 95 bridges, ~10 batch runs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | State built from manifests and media hashes, not claims | PASS |
| II Local, consent | Local files, loopback UI, no GPU | PASS |
| III Graph contracts | No graphs touched | N/A |
| IV Immutable artifacts | Append-only log; versions never dropped; new files only | PASS |
| V Physical morph | Rerender keeps reference-edit lineage (dependants re-queued) | PASS |
| VI Spec Kit | Full workflow + converge | PASS |
| VII Compatibility | Per-run `review.json` still read; existing review UI unchanged | PASS |
| VIII Loopback UIs | 127.0.0.1 only; CSRF token on POST | PASS |
| IX Owner gates | Decisions are the owner's; Claude asks with choices | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/039-batch-review-iteration/
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
src/morph_studio/batch_review.py   # new
src/morph_studio/qa.py             # SEVERITY constant (shared weights)
src/morph_studio/review_ui.py      # /film/<act> page + POST /film/review
src/morph_studio/cli.py            # six film-review commands
tests/test_batch_review.py         # new
```

**Structure Decision**: single module + CLI + UI routes, following F18/F36.

## Complexity Tracking

None.
