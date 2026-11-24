# Implementation Plan: Full-Song Act Structure, Frame-Locked Timeline and Film Storyboard (F32)

**Branch**: `032-full-song-act-structure` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/032-full-song-act-structure/spec.md`

## Summary

- **Schema** (`schema.py`): `Transition.duration_beats` becomes optional; new `Transition.frames: int | None` (4n+1, ≥ 5). Validator: exactly one of the two per transition; `frames ≤ render.max_bridge_frames`; BPM required only if any transition uses beats.
- **Timeline** (`timeline.py`): `compile_timeline` uses `t.frames` when set (requested = actual = (L−1)/fps, error 0); beat path unchanged, so existing plan hashes stay identical. New `snap_frames(times, fps)` → [{t, frame, error_frames}].
- **Ladder guard** (`ladder.py`): refuse frame-locked transitions explicitly (ladders split beats) instead of a KeyError.
- **New `src/morph_studio/film.py`**:
  - `load_acts(path)` — validates ten eras → five ordered contiguous acts.
  - `build_storyboard(sync_plan, bank, acts, *, audio=None, master_seed=31415)` → storyboard dict (validated through `Storyboard`), plus `header` provenance comment; `write_storyboard(..., out)` refuses existing output.
  - `film_report(storyboard_path, *, sync_plan=None, history=None, repo_root)` → per-act/total stats from `compile_plan`, boundary events from the sync plan anchors, coverage, plan hash, `perf.estimate(extrapolate=True)` aggregated per act.
- Data: `configs/film/acts.yaml`, `configs/film/sync-plan.json` (copied from the owner's F15 run), generated `configs/sequences/engineering-film.yaml`.
- CLI: `film-storyboard --plan P --bank B --acts A --out O [--audio F]`, `film-report STORYBOARD [--plan P] [--history H]`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: PyYAML, pydantic; existing `schema`, `timeline`, `dag.compile_plan`, `longform.plan_diff/stage_identities`, `perf.estimate`, `concepts`

**Storage**: YAML/JSON in `configs/film/` and `configs/sequences/`

**Testing**: pytest; synthetic sync plans; real sync plan + bank for evidence; hash-stability tests on existing storyboards

**Target Platform**: native Windows 11

**Project Type**: library + CLI + data

**Performance Goals**: generate + report < 5 s

**Constraints**: no GPU; existing plan hashes unchanged; Wan 4n+1; 33–81-frame bridges

**Scale/Scope**: 96 anchors / 95 bridges / ~5,700 frames

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | GPU hours labelled ESTIMATED/EXTRAPOLATED; coverage measured | PASS |
| II Local, consent | Dry run only; audio referenced only when owner-licensed | PASS |
| III Graph contracts | No graph changes | N/A |
| IV Immutable artifacts | Deterministic plan hashes; existing hashes unchanged | PASS |
| V Physical morph | 4n+1 lengths; shared anchors; act chains limit edit lineage | PASS |
| VI Spec Kit | Full workflow + converge | PASS |
| VII Compatibility | Beat storyboards unchanged; ladder refuses frame-locked explicitly | PASS |
| VIII Loopback UIs | N/A | N/A |
| IX Owner gates | Storyboard approval and GPU batches stay owner decisions | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/032-full-song-act-structure/
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
src/morph_studio/schema.py     # Transition.frames
src/morph_studio/timeline.py   # frame-locked compile + snap_frames
src/morph_studio/ladder.py     # explicit refusal for frame-locked transitions
src/morph_studio/film.py       # new
src/morph_studio/cli.py        # film-storyboard, film-report
configs/film/acts.yaml, configs/film/sync-plan.json, configs/sequences/engineering-film.yaml
tests/test_film.py             # new
```

**Structure Decision**: small schema/timeline extension plus one new module.

## Complexity Tracking

None.
