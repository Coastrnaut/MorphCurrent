# Feature Specification: Delivery Frame Rates and Energy-Warped Retiming (F25)

**Feature Branch**: `025-optical-frame-interpolation` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F25 Delivery frame rates and energy-warped retiming — offline slice: convert approved 16 fps clips or movies to 24/30/48/60 fps with local profiles (repeat, blend, motion-compensated) into a new file with a provenance sidecar; verify duration and report anchor-time alignment; refuse blending across hard cuts; apply a bridge's energy-warp map with pinned endpoints and unchanged duration. CLI interpolate and warp-apply. No GPU."

## Clarifications

### Session 2026-11-24

Resolved autonomously from existing conventions (F09 join, F20 audit):

- Q: How are outputs encoded? → A: H.264, constant frame rate, `yuv420p`, quality CRF 16 (configurable), audio stream copied; frame comparisons in tests use a mean grey difference tolerance of ≤ 3 (8-bit) because the encoding is lossy.
- Q: What exactly do the three methods do? → A: repeat = nearest-frame resampling; blend = linear blending of the two nearest source frames; motion = motion-compensated interpolation with the encoder's built-in scene-change detection. All are the installed FFmpeg's own filters; the exact filter string is stored in the record.
- Q: How is a warp map turned into frame timing? → A: the map gives, for each output frame i (at 16 fps), a source position; its inverse T(k) gives the time each source frame k is reached. Source frame k is shown from T(k) to T(k+1) (the last frame for one frame period), then the sequence is resampled to a constant 16 fps by nearest frame, so the first and last frames are exact and the duration is unchanged; delivery rates are then produced by the normal conversion.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deliver at a smoother frame rate without losing the original (Priority: P1)

The owner converts an approved 16 fps bridge or joined movie to 24, 30, 48 or 60 fps using one of three local methods — repeat frames, blend neighbouring frames, or motion-compensated interpolation. The result is a new file with a record of exactly how it was made; the original 16 fps file is never changed.

**Why this priority**: Delivery formats (F30/F40) need standard frame rates; the generated 16 fps masters are the provenance-bearing originals.

**Independent Test**: Converting a synthetic 65-frame 16 fps clip to 24 fps produces a new file of the same duration (within one output frame) and a record with both checksums; the original's checksum is unchanged.

**Acceptance Scenarios**:

1. **Given** a 16 fps clip, **When** converted to 24 fps with frame blending, **Then** the output lasts the same time (± one output frame), the record names the method, settings, tool version and both checksums, and the original is byte-identical.
2. **Given** an existing output path, **When** converting, **Then** it is refused.

---

### User Story 2 - Keep musical sync through the conversion (Priority: P1)

Anchors sit on quarter-second marks (multiples of 4 frames at 16 fps). The report lists, for each anchor time, whether an output frame lands exactly on it — always at 24, 48 and 60 fps; at 30 fps only on half-second marks — so the owner knows whether music sync survives the chosen rate.

**Why this priority**: The film's anchors are timed to musical events (docs/MUSIC_SYNC.md).

**Independent Test**: For a 2-second clip, the report shows all 9 anchor times exact at 24 fps, and 5 of 9 exact at 30 fps.

**Acceptance Scenarios**:

1. **Given** anchor times every 0.25 s, **When** converting to 30 fps, **Then** times on half-second marks are exact and the others are reported with their offset (≤ half an output frame).

---

### User Story 3 - Never blend across a hard cut (Priority: P2)

If the input contains a hard cut, blending or motion interpolation would smear two shots together. The conversion detects this, falls back to frame repeat, and says so.

**Independent Test**: A synthetic clip with an abrupt cut, requested with blending, is converted with frame repeat and the report names the cut frame.

**Acceptance Scenarios**:

1. **Given** a clip with a hard cut, **When** blending is requested, **Then** frame repeat is used and the fallback is reported.

---

### User Story 4 - Make the morph breathe with the music (Priority: P2)

Given a bridge clip and its energy-warp map (from the sync plan), the owner renders a retimed version: the morph moves faster when the music surges and slower when it calms, while the first and last frames and the total duration stay exactly the same.

**Why this priority**: This is the continuous energy-to-motion coupling of the sync strategy.

**Independent Test**: A synthetic clip whose frames encode their index as brightness, warped with a map that speeds up the middle, keeps first/last frames and duration, and its brightness rises faster in the fast section.

**Acceptance Scenarios**:

1. **Given** a warp map with a fast middle section, **When** applied, **Then** first and last frames match the source, the frame count and duration are unchanged, and progress is faster in the middle.
2. **Given** a map whose length does not match the clip, **When** applied, **Then** it is refused.

### Edge Cases

- Frozen (repeated) frames in the source: interpolation leaves them frozen; no invented motion.
- Odd frame counts and rational rates: duration checks use exact rational arithmetic.
- Audio present in the input: carried over unchanged.
- An identity warp map: output equals the source frame-for-frame.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Conversion MUST support target rates 24, 30, 48 and 60 fps and methods repeat, blend and motion-compensated, all computed locally.
- **FR-002**: Conversion MUST write a new file (refusing to overwrite) and a sidecar record with input/output checksums, method, settings, tool version and timing results; the input MUST remain unchanged.
- **FR-003**: Output duration MUST equal input duration within one output frame; otherwise the conversion is reported as failed.
- **FR-004**: The report MUST list each anchor time (multiples of 0.25 s within the clip) as exact or offset by a stated amount.
- **FR-005**: Blend and motion methods MUST fall back to repeat when the input contains a hard cut, and report the fallback.
- **FR-006**: Warp application MUST keep the first and last frames and the total duration, require a map with one entry per source frame, and produce a constant-rate output.
- **FR-007**: No GPU, network or generation requests.

### Key Entities

- **Conversion record**: input/output paths and checksums, target rate, method (requested and used), settings, tool version, durations, anchor alignment, fallback reason.
- **Warp result**: input/output checksums, map summary (min/max speed), endpoint check, duration check.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of conversions in tests preserve duration within one output frame and leave the original byte-identical.
- **SC-002**: Anchor alignment is reported correctly for 24, 30, 48 and 60 fps in tests (exact counts as specified).
- **SC-003**: Hard-cut inputs never receive blending in tests (100% fallback).
- **SC-004**: Warped outputs keep first/last frames and duration in 100% of tests.

## Assumptions

- Interpolation uses the locally installed FFmpeg's built-in filters; learned interpolation models are out of scope until owner-approved (F27).
- Hard-cut detection reuses the existing temporal QA (F08).
- Retimed and interpolated outputs are finishing artifacts; inference masters stay at 16 fps.
