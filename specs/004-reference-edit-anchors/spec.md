# Feature Specification: Reference-guided next anchors (B from A, C from B)

**Logical ledger ID**: F04 · **Feature Directory**: `specs/004-reference-edit-anchors` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F04 Generate the next/last anchors B and C by real reference edit of their parent anchor, with an explicitly chosen independent text-to-image fallback that is never silently substituted"

## Gap analysis

| Concern | Exists (F03) | Gap |
|---|---|---|
| Single reference-edit job | `AnchorRequest(method="reference_edit", reference_image=…)`, upload content-addressed, `parent.sha256` recorded | No chain runner: the parent must be a *verified* anchor and its exact bytes reused |
| Fallback | `independent_t2i` method accepted on T2I profiles | Storyboard schema has no `independent_t2i`; nothing prevents silently using T2I when the edit profile is missing |
| Geometry continuity | per-image size check | Child must have the parent's dimensions (both endpoints of a Wan bridge) |
| Review | none | Side-by-side contact sheet of parent/child for human compatibility review |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A→B→C chain (Priority: P1)
Given verified profiles, the chain generates A (T2I), then B by editing A's verified bytes, then C by editing B's verified bytes, sequentially, one GPU job at a time.
**Acceptance**: B's `parent.sha256` = A's image SHA; C's = B's; all three share dimensions; re-running reuses all three with no new `/prompt`.

### User Story 2 - No silent substitution (Priority: P1)
**Acceptance**: (1) anchor declared `reference_edit` with no edit profile → chain stops with BLOCKED message naming the missing profile and the explicit `independent_t2i` option; nothing generated for it. (2) anchor declared `independent_t2i` → generated on the T2I profile, recorded `method: independent_t2i`, `continuity_parent` = declared reference, `review: human approval required`. (3) Parent not verified or tampered → refuse.

### User Story 3 - Compatibility contact sheet (Priority: P2)
**Acceptance**: a PNG contact sheet with parent and child side by side is written beside the chain (FFmpeg, argument list); missing FFmpeg → reported skipped, not failed.

### Edge Cases
- Reference forms a cycle or points forward → rejected by schema (existing rule extended).
- Edit graph rescales (e.g. `FluxKontextImageScale`) → dimension mismatch with parent fails the child with a clear error instead of producing an unusable bridge pair.
- Reference anchor with different generation method (e.g. independent_t2i parent) → allowed; parent bytes are whatever was verified.

## Requirements *(mandatory)*
- **FR-001**: Storyboard `generation` MUST accept `text_to_image`, `reference_edit`, `independent_t2i`; `reference` is required for `reference_edit`, optional (continuity parent) for `independent_t2i`, forbidden for `text_to_image`; references must point to earlier anchors.
- **FR-002**: The chain MUST pass the parent's verified image file (SHA re-checked) as `reference_image`.
- **FR-003**: Missing edit profile for a `reference_edit` anchor MUST block, never fall back.
- **FR-004**: Every child MUST match its parent's width/height or fail.
- **FR-005**: `independent_t2i` anchors MUST be recorded as such with `review: required`.
- **FR-006**: Contact sheets MUST be produced via FFmpeg argument arrays (`shell=False`) and never overwrite.

## Success Criteria *(mandatory)*
- **SC-001**: In tests, B's and C's parent hashes equal the actual parent image hashes (100%).
- **SC-002**: 0 generated images for a blocked `reference_edit` anchor.
- **SC-003**: Rerun of a completed chain issues 0 `/prompt` requests.

## Assumptions
- Real edit profile comes from F02 (owner-gated); tests use synthetic Qwen-shaped profiles.
