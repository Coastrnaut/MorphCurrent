# Feature Specification: Local Resolution Enhancement and Finishing (F26)

**Feature Branch**: `026-upscale-visual-finishing` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F26 Local resolution enhancement and finishing — offline slice: geometric 1080p/1440p finishing with fit/pad or fill/crop, optional light denoise/deblock/sharpen and colour match to an anchor, new file + record; identity check on first/last frames, duration and frame count unchanged; generative upscalers listed read-only and refused without owner approval. CLI finish. No GPU."

## Clarifications

### Session 2026-11-24

Resolved autonomously:

- Q: What exact geometry do fit and fill produce? → A: scale factor = min (fit) or max (fill) of target_w/src_w and target_h/src_h; scaled size rounded to even numbers; fit pads with black to the target, fill centre-crops to the target. For 832×480: 1080p fit = 1872×1080 + 24 px padding each side; 1080p fill = 1920×1108 cropped by 14 px top and bottom; 1440p fit = 2496×1440 + 32 px each side.
- Q: What are the light clean-up settings? → A: denoise = gentle temporal/spatial (strength 1.5/1.5/6/6), deblock = weak, sharpen = 5×5 kernel at 0.4; resampling is Lanczos.
- Q: What tolerance does the identity check use, and how is the colour match bounded? → A: mean absolute grey difference ≤ 4 (8-bit) between source frames and finished frames scaled back to source size with padding/crop undone; colour gains = anchor mean / input first-frame mean per channel, clamped to 0.8–1.25 and recorded.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deliver at HD without inventing detail (Priority: P1)

The owner finishes an approved 832×480 clip or movie to 1080p or 1440p. Because 832×480 is slightly wider than 16:9 proportions allow at those heights, the owner chooses to fit the whole picture with thin padding or fill the frame with a slight crop. Resampling is purely geometric, so no detail is invented. Optional light clean-up steps (denoise, deblock, sharpen) can be switched on individually.

**Why this priority**: Delivery formats need HD; generative enhancement risks altering approved anchors.

**Independent Test**: Finishing a synthetic clip to 1080p with fit produces a 1920×1080 file with the same frame count and duration and a record of the exact chain.

**Acceptance Scenarios**:

1. **Given** an 832×480 clip, **When** finished to 1080p with fit, **Then** the output is 1920×1080 with the full picture visible (padding only on the short sides), same frame count and duration, and a record listing the chain, codec, colour space, bit depth, timing and device.
2. **Given** the same clip, **When** finished with fill, **Then** the output is 1920×1080 with no padding (a small crop instead).
3. **Given** an existing output path, **When** finishing, **Then** it is refused.

---

### User Story 2 - Prove the approved anchors were not altered (Priority: P1)

After finishing, the first and last output frames are scaled back to the source size (undoing padding or crop) and compared with the source frames. If they differ beyond a small tolerance the result is flagged, so an approved anchor's identity can never silently change.

**Why this priority**: Constitution IV/V — anchors are approved artifacts; finishing must not change what they show.

**Independent Test**: A finished clip passes the identity check; a deliberately colour-shifted output fails it.

**Acceptance Scenarios**:

1. **Given** a geometric finish, **When** checked, **Then** first and last frames match the source within tolerance.
2. **Given** a heavy colour match that changes the picture strongly, **When** checked, **Then** the identity check reports the change instead of passing silently.

---

### User Story 3 - Colour-match a finish to an approved anchor (Priority: P2)

The owner can match the finished clip's overall colour to an approved anchor image (per-channel gain), for consistency across bridges. The applied gains are recorded.

**Independent Test**: A clip with a slightly blue cast matched to a neutral anchor comes out with per-channel means closer to the anchor's.

**Acceptance Scenarios**:

1. **Given** an anchor image and a clip with a colour cast, **When** matched, **Then** the gains are recorded and the output's mean colour is closer to the anchor than the input's.

---

### User Story 4 - Generative upscalers stay behind owner approval (Priority: P3)

The owner can see which upscaling models are installed locally, but requesting one is refused until the owner explicitly approves its use. Nothing is downloaded.

**Independent Test**: Listing reports the installed model folder contents; requesting a model returns a refusal naming the approval requirement.

### Edge Cases

- Input already larger than the target: refused (finishing never downsizes).
- Input with audio: audio copied unchanged.
- Odd input sizes: output dimensions forced even for the encoder.
- Clean-up steps all off: pure geometric resampling.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Finishing MUST support 1080p (1920×1080) and 1440p (2560×1440) targets with fit (pad) or fill (crop) modes and geometric resampling only.
- **FR-002**: Light denoise, deblock and sharpen MUST be individually optional and recorded.
- **FR-003**: Output MUST be a new file (no overwrite) with a record of input/output checksums, full processing chain, codec, colour space, bit depth, wall-clock time and device; the input stays unchanged.
- **FR-004**: Duration and frame count MUST be unchanged.
- **FR-005**: An identity check MUST compare first and last frames (scaled back to source size, padding/crop undone) with the source and report pass/fail with the measured difference.
- **FR-006**: Optional colour match MUST apply per-channel gains derived from an anchor image and record them.
- **FR-007**: Installed generative upscalers MUST be listable read-only and refused for use until an owner-approved, hash-pinned workflow exists for them (owner approved a 1080p upscaler on 2026-11-24 — wired in T016 after the consented download and workflow export); no downloads by the tool.
- **FR-008**: No GPU, network or generation requests.

### Key Entities

- **Finish record**: target, mode, steps, colour gains, chain, codec/colour space/bit depth, timing, device, checksums, identity result.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of test finishes keep frame count and duration and leave the input byte-identical.
- **SC-002**: The identity check passes for geometric finishes and fails for a deliberately altered output in tests.
- **SC-003**: A real approved movie is finished to 1080p with the time and identity result recorded.
- **SC-004**: Zero generation requests and zero downloads.

## Assumptions

- Generative upscaling (learned models, possibly GPU) is a later owner-approved step (F27 capability registry); this slice is CPU and geometric.
- Padding colour is black (the film's backgrounds are dark).
