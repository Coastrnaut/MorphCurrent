# Feature Specification: Intermediate anchors and variable-length morph ladders

**Logical ledger ID**: F14 · **Feature Directory**: `specs/014-adaptive-transition-ladders` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F14 Intermediate anchors and variable-length morph routing: interpretable risk heuristics, ladder proposals that split distant transitions into reviewed intermediate anchors with valid 4n+1 lengths and a GPU budget cap"

## Gap analysis
| Exists | Gap |
|---|---|
| Linear storyboards (any number of anchors); per-transition `duration_beats` → 4n+1 frames (49/65/81 all valid); F12 geometry comparison; F13 choreography; F11 time estimates; F08/F16 selective rerender | No way to *judge* that a transition is too far for one bridge, nor to propose an intermediate anchor with a sensible prompt, split the beat budget into valid Wan lengths and check the GPU cost — a five-minute engineering film has many distant pairs (e.g. lightning → Leyden jar) |

## User Scenarios & Testing *(mandatory)*
### US1 - Transition risk (P1)
For each transition, an interpretable risk score (0–1) with reasons from (a) prompt dissimilarity (content-word Jaccard distance) and, when anchor images exist, (b) F12 geometry flags (centroid shift, scale change, symmetry drop, palette shift).
**Acceptance**: near-identical prompts → low risk; unrelated subjects → high risk with `prompt_distance` reason; geometry flags add named reasons.

### US2 - Ladder proposal (P1)
`ladder-propose STORYBOARD --split FROM->TO [--steps N] --out NEW.yaml` inserts N intermediate `reference_edit` anchors between FROM and TO, with deterministic prompts that state the halfway form (blending the two subjects' prompts with explicit "halfway between" wording), derived seeds, and the transition's beats split across the new segments, each mapped to a valid 4n+1 length. The output is a schema-valid storyboard *proposal* (nothing rendered), with a header comment recording lineage (source storyboard SHA, split transition, author).
**Acceptance**: 8 beats at 120 BPM split in 2 → two 4-beat segments of 33 frames; anchor ids unique; references chain FROM → mid → TO; TO's reference updated to the new mid anchor; downstream anchors unchanged; plan compiles; deterministic output.

### US3 - Budget and limits (P1)
Proposals report added GPU time (F11 `estimate` history) and refuse when the total would exceed `--max-gpu-s` or the number of new anchors exceeds `--max-new` (default 3 per split); impossible splits (segment shorter than 5 frames / Wan minimum) fail with a clear error.

### Edge Cases
FROM→TO not adjacent → error. Splitting the first anchor's T2I → the mid anchor is `reference_edit` of FROM. Existing `choreography` on the split transition is copied to each segment.

## Requirements *(mandatory)*
- **FR-001** Risk is deterministic, reported with reasons; never auto-applied.
- **FR-002** Proposal writes a new file (refuses overwrite); input storyboard untouched.
- **FR-003** Segment frames from `timeline.frame_count_for_beats`; segments must each be ≥ 5 frames and ≤ `max_bridge_frames`.
- **FR-004** Budget check uses measured history; missing history → NO DATA reported and refusal only if `--max-gpu-s` given.
- **FR-005** Shared-anchor byte identity and seam math unchanged (the proposal is an ordinary linear storyboard).

## Success Criteria *(mandatory)*
- **SC-001** Split math exact for 4/8/12-beat transitions at 90/120 BPM fixtures.
- **SC-002** Budget/limit refusals tested.
- **SC-003** Owner-reviewed multi-hop render: pending GPU approval.

## Assumptions
Prompt blending is text-only; the edit model decides the actual halfway form, so proposals need human review.
