# Feature Specification: Quality heuristics, candidate ranking, selective rerender

**Logical ledger ID**: F08 · **Feature Directory**: `specs/008-quality-selective-rerender` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F08 Visual and temporal QA heuristics, candidate ranking and limited rerender of only failed transitions, with human approval for subjective quality"

## Gap analysis
| Exists | Gap |
|---|---|
| ffprobe metadata verification; contact sheet (F04); MC-FLF2V-003 manual observations (collapse frames ~24–40, flare ~48) | No decoded-frame analysis; no candidate seeds; no way to rerender only one failed bridge; no recorded human review |

## User Scenarios & Testing *(mandatory)*
### US1 - Temporal heuristics (P1)
Decode a clip to small grayscale frames locally (FFmpeg) and flag: **hard cut** (frame-difference spike far above the clip's median), **freeze** (≥ N consecutive near-identical frames), **flare** (mean-luminance jump), **endpoint mismatch** (first/last frame vs its anchor image).
**Acceptance**: synthetic clips with an inserted cut / frozen run / white flash / wrong endpoint are flagged; a smooth gradient clip is not flagged.
### US2 - Candidates and selective rerender (P1)
A transition with `candidates: k` gets k deterministic seeds (task seed, then derived). Ranking orders candidates by heuristic flags (fewer/less severe first) and is labelled *heuristic*. A rerender plan lists only bridges whose selected candidate failed QA or was rejected by the human; anchors and other bridges are untouched.
**Acceptance**: B→C rejected → plan contains only B→C candidate jobs; A→B and anchors are reused.
### US3 - Human review record (P2)
**Acceptance**: `review` file per run records approve/reject per bridge with note; F09 joining requires `approved` for each bridge unless `--accept-heuristics` is passed explicitly.

### Edge Cases
Clip shorter than 3 frames → QA error; very dark clip → luminance thresholds relative to clip statistics; ffmpeg missing → QA `unavailable`, never `pass`.

## Requirements *(mandatory)*
- **FR-001** Frames decoded locally via FFmpeg argument list to 64×36 gray; metrics in pure Python.
- **FR-002** Every report states `method: heuristic` and never claims artistic quality; PSNR/SSIM not used as acceptance.
- **FR-003** Candidate seeds deterministic: `[seed] + derived_seed(master_seed, f"{task}:candidate:{i}")`.
- **FR-004** Rerender plan includes only failed/rejected bridges.
- **FR-005** Review state persisted; default `pending`.

## Success Criteria *(mandatory)*
- **SC-001** 4/4 synthetic defects detected; 0 false flags on the smooth clip.
- **SC-002** Rerender plan touches 1 of 2 bridges in the reject-B→C scenario.

## Assumptions
Thresholds are initial heuristics (cut: diff > 6× median and > 20 levels; freeze: ≥ 6 frames with diff < 0.5; flare: luminance jump > 40 levels; endpoint: mean abs diff > 25 levels) to be tuned on owner-reviewed clips (MC-FLF2V-003 is the first calibration candidate).
