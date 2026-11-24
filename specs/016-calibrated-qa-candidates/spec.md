# Feature Specification: Quality calibration and subject-aware QA

**Logical ledger ID**: F16 · **Feature Directory**: `specs/016-calibrated-qa-candidates` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F16 Quality calibration: per-frame subject area, centroid and sharpness detectors for collapse, off-centre drift and blur, scored with precision/recall against owner-observed defect windows"

## Gap analysis
| Exists (F08) | Gap |
|---|---|
| Gray 64×36 frame diffs: hard cut, freeze, flare, endpoint mismatch | Raised **no flags** on MC-FLF2V-003 (petal collapse frames 24–40, flare ~48), MC-RUN-001 orchid→butterfly (drift right/blur 32–48) and butterfly→phoenix (shrink to small blur ~16, near-cut) — all visible defects. No labelled reference set, no precision/recall |

## User Scenarios & Testing *(mandatory)*
### US1 - Subject-aware per-frame metrics (P1)
For each decoded frame (128×74 RGB, local FFmpeg): subject area, centroid, extent (F12 geometry) and sharpness (mean absolute Laplacian on the subject).
### US2 - Detectors (P1)
- `subject_collapse`: area below 0.55 × the smaller endpoint area for ≥ 3 frames.
- `subject_drift`: centroid more than 0.12 of the frame from the straight line between endpoint centroids for ≥ 3 frames.
- `blur_dip`: sharpness below 0.5 × the smaller endpoint sharpness for ≥ 3 frames.
Each flag reports its frame window; labelled heuristic.
**Acceptance**: synthetic clips (subject shrinking mid-clip, sliding off-centre, blurred mid-clip) flagged in the right window; a steady morph between two similar subjects not flagged.

### US3 - Calibration against labelled windows (P1)
A labels file records owner-observed defect windows per clip (seeded from the documented observations). `qa-calibrate LABELS` runs detectors on the referenced local clips and reports per-detector precision/recall (window overlap) and the clean-clip false-positive rate.
**Acceptance**: report generated from real local clips; numbers recorded honestly in PROGRESS even if poor.

### Edge Cases
Clip missing locally → skipped with reason. Bright-background clip → `mask_unreliable` frames excluded.

## Requirements *(mandatory)*
- **FR-001** Metrics decoded locally; no GPU, no network.
- **FR-002** Detectors labelled heuristic; review still required (no auto-accept).
- **FR-003** `qa` CLI gains these flags (existing F08 flags unchanged).
- **FR-004** Labels JSON schema: `{clip, kind, frames: [start, end], source}`; calibration uses only listed clips; train/test split noted (thresholds fixed before evaluation, not fitted to these labels).

## Success Criteria *(mandatory)*
- **SC-001** Synthetic defects detected 100%, synthetic clean clip 0 flags.
- **SC-002** Recall on the documented real defects improves over F08 (which found 0); measured value recorded.
- **SC-003** Owner-labelled held-out set and threshold tuning: pending owner labels.

## Assumptions
Labels seeded from docs/EXPERIMENTS.md observations are coarse (± several frames).
