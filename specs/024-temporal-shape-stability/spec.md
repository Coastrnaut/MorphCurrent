# Feature Specification: Temporal Shape Continuity and Repair (F24)

**Feature Branch**: `024-temporal-shape-stability` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F24 Temporal shape/material continuity and repair — offline slice: frame-wise diagnostics beyond F16 (shape overlap, topology proxy, background persistence, motion-path and colour-path smoothness) tolerant of genuine motion; honest evaluation on labelled real clips and synthetic deformations; repair proposals (material-continuity prompt refinements, intermediate anchor at the failure time) for owner review; controlled repair comparison checking unchanged endpoints with a 'candidate improvement — needs owner review' verdict. No GPU."

## Clarifications

### Session 2026-11-24

Resolved autonomously (thresholds fixed here, before any evaluation, per FR-004):

- Q: What exact thresholds define each flag? → A: On the 128×74 analysis frames with the F12 subject mask:
  substitution — consecutive-frame mask overlap (intersection over union) < 0.45 while the clip's median overlap ≥ 0.70;
  topology — separate subject parts (components ≥ 0.5% of the frame) ≥ endpoint maximum + 2, or ≤ endpoint minimum − 2 while the endpoints have ≥ 3 parts, for ≥ 2 consecutive frames;
  background — mean absolute luminance change of pixels outside both frames' masks > max(12, 4 × the clip's median background change);
  motion jump — subject-centre step > max(0.06, 4 × median step);
  colour jump — subject mean-colour step (RGB distance) > max(40, 4 × median step).
- Q: What tolerance counts as "endpoints unchanged" in a repair comparison? → A: mean absolute grey-level difference ≤ 2.0 (8-bit) for both the first and last frames.
- Q: Where is an intermediate anchor placed? → A: at the frame nearest the flagged window's centre whose split keeps both halves valid Wan lengths (k ≡ 0 mod 4, both halves ≥ 17 frames); if impossible, prompt refinements only.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See exactly where and how a morph breaks (Priority: P1)

For a bridge clip the reviewer gets frame-windowed findings that name the kind of break: the subject's shape suddenly replaced by a different one, parts (petals, wings) appearing or vanishing abruptly, the background changing when it should stay put, the subject's centre jumping, or the material/colour suddenly switching. Each finding gives the frames and the measured numbers. Smooth, genuine transformation is not flagged.

**Why this priority**: MC-RUN-001/002 showed collapse, blur and substitution defects that the earlier checks missed; the reviewer needs specific, located evidence.

**Independent Test**: Synthetic clips — a smoothly growing and moving shape (no flags), an abrupt shape swap at one frame (substitution flagged at that frame), a shape that splits into four parts for a few frames (topology flagged), a background that flashes (background flagged).

**Acceptance Scenarios**:

1. **Given** a smooth synthetic morph, **When** analysed, **Then** no continuity flags are raised.
2. **Given** a synthetic clip whose subject is replaced by a different shape between two frames, **When** analysed, **Then** a substitution flag names that frame window and the measured overlap.
3. **Given** a subject that splits into several separate parts for a few frames, **When** analysed, **Then** a topology flag reports the part counts and window.
4. **Given** a background that changes abruptly, **When** analysed, **Then** a background flag reports the window and change.

---

### User Story 2 - Honest evaluation on real labelled clips (Priority: P1)

The diagnostics are evaluated against the labelled real defect windows from earlier runs and against the synthetic deformations, reporting hits, misses and flags in clips labelled clean — with thresholds fixed before evaluation.

**Why this priority**: Constitution I — automated QA must not be presented as more reliable than it is.

**Independent Test**: The evaluation report lists, per labelled clip and defect kind, whether a new or existing detector overlapped the window, plus false flags on clean clips.

**Acceptance Scenarios**:

1. **Given** the labelled clips, **When** evaluated, **Then** recall per defect kind and false-flag counts are reported, with misses listed explicitly.

---

### User Story 3 - Propose a repair for owner review (Priority: P2)

For a flagged bridge the system writes a repair proposal: material-continuity prompt refinements matched to the defect kind (e.g. "the petals remain attached and visible throughout" for vanishing parts), and/or an intermediate reference-edit anchor placed at the failure time to split the bridge in two. The proposal records the original bridge, flags, seed, length and intended controlled comparison. Nothing is rendered.

**Why this priority**: Repairs cost GPU time; the owner decides which to try.

**Independent Test**: A clip with a substitution flag at frames 30–34 of 65 produces a proposal with a prompt refinement and an intermediate anchor at about the middle, with provenance; a clean clip produces "no repair needed".

**Acceptance Scenarios**:

1. **Given** flags on a bridge, **When** a proposal is requested, **Then** refinements per defect kind and an optional intermediate anchor with valid split lengths are written for owner review.
2. **Given** no flags, **When** requested, **Then** the result says no repair is proposed.

---

### User Story 4 - Compare an original and a repaired clip fairly (Priority: P2)

Given the original clip and a repaired one (same endpoints, seed and length), the comparison reports which defects disappeared, persisted or appeared, and verifies the first and last frames did not change. The verdict is at most "candidate improvement — needs owner review".

**Independent Test**: Synthetic original (with substitution) vs repaired (smooth, same endpoints) → defect removed, endpoints unchanged, verdict candidate improvement; a "repair" with a changed last frame → endpoint regression reported, verdict not an improvement.

**Acceptance Scenarios**:

1. **Given** a repaired clip without the original's defect and identical endpoints, **When** compared, **Then** "candidate improvement — needs owner review".
2. **Given** a repaired clip whose last frame differs, **When** compared, **Then** endpoint regression is reported and no improvement is claimed.
3. **Given** clips of different lengths, **When** compared, **Then** refused as not a controlled comparison.

### Edge Cases

- Unreliable subject mask (bright full-frame scenes): frames excluded and reported, not flagged.
- Very short clips (fewer than 9 frames): analysed but continuity windows need at least 3 frames.
- Genuine fast but continuous motion: smoothness uses the clip's own typical frame-to-frame change, so steady fast motion is tolerated.
- A defect at the very first or last frames: reported, and repair proposals never move or replace endpoint anchors.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST compute, per frame, subject mask occupancy, consecutive-frame shape overlap, number of separate subject parts, background change, subject centre and subject mean colour.
- **FR-002**: The system MUST flag substitution, topology change, background change, motion-path jump and colour-path jump as frame windows with measured values, using the fixed thresholds in Clarifications (relative to the clip's own typical change where motion is involved).
- **FR-003**: Smooth synthetic morphs MUST produce no continuity flags.
- **FR-004**: An evaluation MUST report per-kind recall on labelled real clips and synthetic cases, false flags on clean clips, and list misses; thresholds are fixed before evaluation.
- **FR-005**: Repair proposals MUST map each defect kind to material-continuity prompt refinements and MAY add an intermediate anchor at the failure time with valid 4n+1 split lengths; proposals record provenance and are never rendered automatically.
- **FR-006**: Repair comparison MUST require equal frame counts, verify first/last frames unchanged (mean grey difference ≤ 2.0), report removed/persisting/new defects, and give at most "candidate improvement — needs owner review".
- **FR-007**: All findings are labelled heuristic; creative acceptance stays with the owner. No GPU or generation requests.

### Key Entities

- **Frame metrics**: occupancy, overlap with previous frame, part count, background change, centre, mean colour.
- **Continuity flag**: kind, frame window, measured values.
- **Evaluation report**: per clip/kind hit or miss, false flags, recall.
- **Repair proposal**: bridge, flags, refinements, optional intermediate anchor (time, split lengths), provenance.
- **Repair comparison**: removed / persisting / new defects, endpoint check, verdict.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the synthetic deformation cases are flagged with the correct kind and window (± 2 frames); 0 flags on the smooth synthetic morphs.
- **SC-002**: The evaluation on the real labelled clips is recorded with per-kind recall and false flags, including honest misses.
- **SC-003**: Repair comparison never reports an improvement when an endpoint changed (100% of seeded cases).
- **SC-004**: Zero generation requests in tests.

## Assumptions

- Subject separation reuses the F12/F16 luminance mask on a darker background; it is a proxy, not proof of physical identity (no optical flow claims).
- Repaired clips are produced later by an owner-approved bounded GPU run; this slice only proposes and compares.
- Labelled windows are the coarse seeds in `configs/qa_labels.json` (± 4 frames) until owner labels replace them.
