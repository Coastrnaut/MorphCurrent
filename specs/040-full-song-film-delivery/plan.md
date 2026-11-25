# Implementation Plan: Full-Song Film Delivery and Acceptance (F40)

**Branch**: `040-full-song-film-delivery` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/040-full-song-film-delivery/spec.md`

## Summary

New `src/morph_studio/film_delivery.py`:
- `choose(state, preview=False)` → per bridge (film order) the approved current version, or (preview) the current version; blockers with reasons (missing, unreviewed, pending, rejected, stale); anchors' current versions for seam stills.
- `assemble(storyboard, runs_root, log, out=None, *, preview, audio, audio_licensed, offset)` → refuses on blockers (non-preview) or missing clips (preview); planned total = last anchor frame + 1 (`soundtrack.anchor_frames`); `stitcher.join_verified` with anchor stills when every still is readable (else clip boundaries only, noted); verifies frames = planned total and duration within one frame; record `<master>.assembly.json`; name `outputs/film/<film>_<UTC>_<plan8>[_PREVIEW].mp4`.
- `deliver_master(master, out_dir, presets, audio, audio_licensed)` → `delivery.deliver`; record `<master>.delivery.json`; preview label carried over.
- `provenance(assembly, *, repo_root, history)` → hashes, stages (chosen version, job id, seed from plan, run), workflows (profile bindings → workflow sha256 + `provenance.models_in_graph`), models (catalogue sha256/licence, recorded hashes), approvals (concept bank, visual language, act approvals log, F39 decisions), GPU measured (job `timings.execution_seconds`) vs F36 `budget` totals, `missing` list, `complete` flag.
- `gates(ledger, accepted)` → F31–F40 rows from `release.acceptance_matrix(through=40)` plus `configs/film/accepted-blockers.yaml`.
- CLI: `film-assemble`, `film-deliver`, `film-provenance`, `film-gates`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: existing `batch_review`, `stitcher.join_verified`, `delivery.deliver`, `soundtrack.anchor_frames`, `production.budget`, `release.acceptance_matrix`, `provenance.models_in_graph`; local FFmpeg

**Storage**: masters and records under `outputs/film/`; `configs/film/accepted-blockers.yaml` (checked in, empty list)

**Testing**: pytest with synthetic runs (solid-colour clips with matching boundaries, frame-locked mini storyboard), FFmpeg-gated join/delivery, real ledger for the gate matrix, real film for blockers

**Target Platform**: native Windows 11

**Project Type**: library + CLI

**Performance Goals**: blockers for the real film < 2 s

**Constraints**: no GPU; never overwrite; no frame dropping; preview never counts as evidence

**Scale/Scope**: 95 bridges, ~6-minute master

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | Probe-verified frame count/duration; provenance from records and hashes | PASS |
| II Local, consent | Local media; licensed audio only; no downloads | PASS |
| III Graph contracts | Workflows identified by pinned hashes, not re-written | PASS |
| IV Immutable artifacts | New files only, `.part` join, records beside outputs | PASS |
| V Physical morph | Seam-verified join; mismatches refuse | PASS |
| VI Spec Kit | Full workflow + converge | PASS |
| VII Compatibility | Reuses join and delivery code unchanged | PASS |
| VIII Loopback UIs | N/A | N/A |
| IX Owner gates | Only approved versions; owner accepts blockers explicitly | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/040-full-song-film-delivery/
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
src/morph_studio/film_delivery.py   # new
configs/film/accepted-blockers.yaml # new (empty)
src/morph_studio/cli.py             # four film commands
tests/test_film_delivery.py         # new
```

**Structure Decision**: one module composing existing pieces.

## Complexity Tracking

None.
