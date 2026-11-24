# Feature Specification: Composition-aware anchors and reference-edit QA

**Logical ledger ID**: F12 · **Feature Directory**: `specs/012-reference-anchor-continuity` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F12 Composition-aware anchor generation and reference-edit QA: subject centroid, extent, silhouette orientation and palette checks between parent and child anchors, per-anchor negatives and human approval"

## Gap analysis
| Exists | Gap |
|---|---|
| F04 chain: child edits parent's exact bytes; size continuity enforced; `continuity` record; per-anchor `negative_prompt` (schema) | No check of *where/how big/which way* the subject is. MC-RUN-001's phoenix was side-on and off-centre; the butterfly test edit was enlarged — nothing flagged them before a 8-minute bridge was spent |
| Contact sheet for human review | No per-pair numbers to guide the reviewer; no recorded anchor approval |

## User Scenarios & Testing *(mandatory)*
### US1 - Geometry of an anchor (P1)
For any anchor image, compute (locally, from a small decoded copy): subject mask against the dark background, centroid (x, y as fractions), bounding extent (w, h fractions), area fraction, left-right mirror symmetry (proxy for frontal vs profile view) and a coarse colour palette.
**Acceptance**: synthetic centred symmetric shape → centroid ≈ (0.5, 0.5), symmetry ≥ 0.9; shape shifted right → centroid x > 0.6; lopsided shape → symmetry low.

### US2 - Parent/child continuity check (P1)
Compare child to parent: centroid shift, scale ratio (extent and area), symmetry drop, palette distance. Each exceeding a threshold produces a named flag; result is advisory (`review: required` when flagged), never silently passing and never presented as anatomy understanding.
**Acceptance**: real-data regression (local outputs, recorded in PROGRESS): MC-RUN-001 side-on phoenix vs butterfly → flagged (symmetry drop and/or centroid shift); MC-RUN-002 frontal phoenix vs butterfly → no geometry flags. Synthetic shift/scale/crop cases flagged; identical image not flagged.

### US3 - Integrated into the pipeline (P2)
The anchor chain records geometry and the comparison in each child's job record and the run manifest; `render` surfaces anchor flags in its review stop output and status. `anchor-check A B` CLI compares any two images.

### Edge Cases
Bright background (mask fails: area > 0.9) → `mask_unreliable` instead of numbers. Tiny subject (area < 1%) → flagged `subject_too_small`. Different image sizes → fractions still comparable.

## Requirements *(mandatory)*
- **FR-001** Geometry from a local FFmpeg-decoded 128×74 RGB copy; pure Python maths; no network, no GPU.
- **FR-002** Flags: `centroid_shift` (> 0.08 of frame), `scale_change` (extent ratio outside 0.75–1.33), `symmetry_drop` (child symmetry < parent − 0.15), `palette_shift` (mean colour distance > 60), `mask_unreliable`, `subject_too_small`.
- **FR-003** Results labelled `heuristic`; review required when any flag; never auto-reject.
- **FR-004** Chain stores geometry + comparison in the child job record (`continuity.geometry`) and manifest stage.
- **FR-005** Existing behaviour (size check, byte-identical parent, bridges) unchanged.

## Success Criteria *(mandatory)*
- **SC-001** Old side-on phoenix flagged (real local images). *Measured 2026-11-24:* old phoenix → `symmetry_drop` (0.94 → 0.49) as intended; the frontal phoenix passes symmetry (0.79) but is flagged `scale_change` (wingspan 1.41× the butterfly's) — a real, visible difference, so the original "not flagged" expectation was wrong and the threshold is kept.
- **SC-002** 100% of synthetic shift/scale/asymmetry fixtures flagged; identical pair clean.

## Assumptions
Dark-background storyboards (current style). Thresholds are initial; calibration with owner-labelled anchors is F16.
