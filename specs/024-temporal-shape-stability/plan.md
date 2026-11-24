# Implementation Plan: Temporal Shape Continuity and Repair (F24)

**Branch**: `024-temporal-shape-stability` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/024-temporal-shape-stability/spec.md`

## Summary

New `src/morph_studio/continuity.py` working on the F16 128×74 RGB frames (`qa_subject.decode_rgb_frames`):
one clip-level mask threshold (mean of the endpoint frames' Otsu thresholds, so masks are comparable
across frames), per-frame metrics (occupancy, overlap with the previous mask, connected parts ≥ 0.5% of
the frame, background change outside both masks, centre, mean colour), `detect_continuity` with the
fixed Clarification thresholds, `evaluate` against `configs/qa_labels.json` + synthetic cases,
`propose_repair` (refinements per kind, optional intermediate anchor at a valid 4n+1 split), and
`compare_repair` (equal length, endpoint grey MAD ≤ 2.0, removed/persisting/new flags, capped verdict).
CLI: `continuity CLIP`, `continuity-eval`, `repair-propose RUN BRIDGE_TASK --out FILE`, `repair-compare ORIGINAL REPAIRED`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: stdlib; existing `geometry._otsu`, `qa_subject.decode_rgb_frames`, `release._stage_files`

**Storage**: proposals written as YAML/JSON files chosen by the user (refuse overwrite)

**Testing**: pytest on synthetic frame lists (no FFmpeg) plus FFmpeg-gated real-clip evaluation

**Target Platform**: native Windows 11

**Project Type**: CLI tool

**Performance Goals**: one 65-frame clip analysed in < 5 s

**Constraints**: no GPU; heuristic labels; thresholds fixed in spec Clarifications before evaluation

**Scale/Scope**: up to ~90 bridges per film

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | Thresholds fixed before evaluation; misses reported; verdict capped at "candidate improvement — needs owner review" | PASS |
| II Local, GPU consent | Offline; repairs proposed, never rendered | PASS |
| III Graph contracts | No graph changes | PASS |
| IV Immutable artifacts | Proposals are new files; originals untouched; endpoints never replaced | PASS |
| V Physical morph | Repairs favour physical continuity (refinements, intermediate anchors), no dissolves | PASS |
| VI Spec Kit | Full workflow + converge loop | PASS |
| VII Compatibility | F16 detectors unchanged | PASS |
| VIII Loopback UIs | N/A | N/A |
| IX Owner gates | Repair renders and acceptance are owner decisions | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/024-temporal-shape-stability/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/cli.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/morph_studio/continuity.py   # NEW
src/morph_studio/cli.py          # continuity, continuity-eval, repair-propose, repair-compare
tests/test_continuity.py         # NEW
```

**Structure Decision**: one new module, reusing F12/F16 decoding and masks.

## Complexity Tracking

None.
