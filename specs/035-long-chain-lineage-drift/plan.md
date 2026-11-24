# Implementation Plan: Long-Chain Lineage and Drift Control (F35)

**Branch**: `035-long-chain-lineage-drift` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/035-long-chain-lineage-drift/spec.md`

## Summary

- **Data**: `configs/film/lineage.yaml` — `depth_limit: 12`, `drift {colour_max: 60, sharpness_min_ratio: 0.6, centroid_max: 0.08, scale_ratio: [0.75, 1.33]}`.
- **New `src/morph_studio/lineage.py`**:
  - `lineage(plan)` → entries per anchor in plan order: root/depth via `conditioned_on_parent` + `reference` (depth = parent depth + 1, else 0), chain, chapter; `per_act_max`, `max_depth`; `over_limit(entries, limit)`.
  - `drift_curve(storyboard, run_dir, config)` → per anchor vs act reference (first anchor of the chapter / storyboard): `geometry.image_geometry` (mean_colour, centroid, extent, flags) + `qa_subject.frame_metrics` sharpness on `qa_subject.decode_rgb_frames(image)`; flags; missing.
  - `propose(plan, limit, curve=None)` → walk each chain; cut where depth would exceed the limit (new depth counted from the cut); add the first drift-flagged anchor per act; never an act's first anchor; each proposal with `accuracy.impact` invalidation.
  - `apply_proposals(storyboard_path, anchors, out)` → copy YAML, set `generation: independent_t2i`, `reference` = previous anchor; validate; refuse existing output; original untouched.
  - `shared_check(run_dir)` → for each bridge stage in the manifest, job.json `anchors.start_image/end_image.sha256` vs manifest `anchor:<id>.image_sha256`.
- CLI: `lineage STORYBOARD [--config]`, `lineage-drift STORYBOARD --run R [--config]`, `lineage-propose STORYBOARD [--run R] [--out O] [--config]`, `lineage-shared --run R`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: existing `dag.compile_plan`, `accuracy.impact`, `geometry.image_geometry`, `qa_subject.decode_rgb_frames/frame_metrics`, `release._stage_files`

**Storage**: `configs/film/lineage.yaml`; proposals in `outputs/proposals/`

**Testing**: pytest with synthetic plans, FFmpeg-generated images for drift, fake run manifests/job records; real film storyboard and organic run

**Target Platform**: native Windows 11

**Project Type**: library + CLI + data

**Performance Goals**: lineage/propose < 2 s on 96 anchors

**Constraints**: no GPU; proposals never modify the original storyboard; explicit independent anchors only

**Scale/Scope**: 96 anchors

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | Drift measured from renders; thresholds labelled as starting points | PASS |
| II Local, consent | Offline; re-anchoring proposals require owner adoption | PASS |
| III Graph contracts | No graph changes | N/A |
| IV Immutable artifacts | Proposals in new files; shared-anchor hash check | PASS |
| V Physical morph | Shared anchors byte-identical; lineage invalidation per constitution | PASS |
| VI Spec Kit | Full workflow + converge | PASS |
| VII Compatibility | New module/commands only | PASS |
| VIII Loopback UIs | N/A | N/A |
| IX Owner gates | Re-anchor adoption and drift bounds are owner decisions | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/035-long-chain-lineage-drift/
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
configs/film/lineage.yaml        # new
src/morph_studio/lineage.py      # new
src/morph_studio/cli.py          # lineage-* commands
tests/test_lineage.py            # new
```

**Structure Decision**: one module plus config.

## Complexity Tracking

None.
