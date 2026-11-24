# Feature Specification: Multi-format Cinematic Delivery and Final 30-Feature Acceptance (F30)

**Feature Branch**: `030-delivery-presets-release-audit` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F30 Multi-format cinematic delivery and final 30-feature acceptance — offline slice: versioned delivery presets (16:9 1080p, 9:16 1080x1920, 1:1 1080, video-only, licensed-audio, 1440p, smooth 24 fps) as deterministic recipes with checksums; new files plus records verified against expected properties; codec fallback recorded; subject safe-area report for crops; acceptance matrix through F30 or all forty plus a release check with the repository audit; release never declared from tests alone; tagging needs owner approval. No GPU, downloads or remote services. CLI deliver, acceptance --through 30."

## Clarifications

### Session 2026-11-24

Resolved autonomously from the ledger and owner rules:

- Q: What encode settings do the presets use? → A: H.264 (libx264) CRF 16, 4:2:0 8-bit, BT.709 tags, AAC 192 kb/s 48 kHz when audio is kept or added; fallback encoder is MPEG-4 Part 2 at high quality, recorded as a fallback.
- Q: How are crops made for 832×480 sources? → A: Centre crop to the target aspect at full source height (9:16 → 270×480, 1:1 → 480×480), then Lanczos scale to the target size; the crop rectangle is recorded.
- Q: What duration and frame rate are expected? → A: The source duration (within one output frame) and the source frame rate, except the smooth preset (24 fps).
- Q: How are outputs named? → A: `<source stem>_<preset>.mp4` (record `<file>.delivery.json`) in the chosen output folder.
- Q: Which audio does a landscape delivery keep? → A: Landscape, 1440p and smooth presets copy the source's audio if present; video-only drops it; licensed-audio replaces it with the owner's licensed track.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deliver an approved movie in several formats (Priority: P1)

The owner takes an approved movie and produces several deliverables in one command: a 16:9 1080p master, a 9:16 vertical version, a square version, a video-only file, a version with the owner-licensed music, a 1440p master and a smooth 24 fps version. Each preset always does exactly the same steps, identified by a recipe checksum, and each output is measured afterwards to confirm it has the promised size, frame rate, codec, audio and duration.

**Why this priority**: The film must reach landscape and vertical audiences without hand-editing, and every deliverable must be verifiably what it claims to be.

**Independent Test**: Delivering a synthetic 832×480 16 fps clip with presets landscape and vertical produces two files whose measured properties match the presets, each with a record holding the recipe checksum, and the source file is unchanged.

**Acceptance Scenarios**:

1. **Given** an approved movie and a list of presets, **When** delivered, **Then** one new file per preset is written next to a record (preset, recipe version and checksum, steps, measured properties, verification result, timings) and the source is byte-identical afterwards.
2. **Given** the same movie and preset twice into different folders, **When** delivered, **Then** both records show the same recipe checksum.
3. **Given** an existing output file, **When** delivering, **Then** that preset is refused and nothing is overwritten.
4. **Given** the video-only preset, **When** delivered from a movie with audio, **Then** the output has no audio stream.
5. **Given** the licensed-audio preset with a track marked licensed and an offset, **When** delivered, **Then** the output has one audio stream whose duration matches the picture within one frame; **Given** a track not marked licensed, **Then** the preset is refused.
6. **Given** the preferred encoder is unavailable, **When** delivered, **Then** the fallback encoder is used and recorded, and the verification expects the fallback codec.
7. **Given** an output whose measured properties differ from the preset, **When** verified, **Then** the record marks it failed with each mismatch.

---

### User Story 2 - Know whether a crop keeps the subject (Priority: P1)

For vertical and square deliveries the owner sees, for the first and last frames (the approved anchors), whether the subject stays inside the crop's safe area, so a crop that would cut the subject off is noticed before publishing.

**Why this priority**: Centre crops of a wide frame can lose the subject; reframing must be a conscious decision.

**Independent Test**: A synthetic clip with a centred subject reports "inside" for 9:16; a clip with the subject at the far left reports "outside".

**Acceptance Scenarios**:

1. **Given** a centred subject, **When** delivered vertical or square, **Then** the record reports "inside" for both anchors.
2. **Given** a subject near the frame edge, **When** delivered vertical, **Then** the record reports "outside" and a warning, and the file is still produced (the owner decides).

---

### User Story 3 - Final acceptance view (Priority: P2)

The owner asks for the acceptance matrix through F30 (or all forty) and a release check that combines it with the repository audit. The result lists every feature's status and whether real evidence exists or a blocker remains, and never says "release ready" because tests passed; tagging still needs the owner.

**Why this priority**: The ledger rule is to never declare release complete from tests alone.

**Independent Test**: With the current ledger, the matrix through 30 has 30 rows, counts unresolved gates and reports not release-ready while owner-gated items remain.

**Acceptance Scenarios**:

1. **Given** the ledger, **When** asking for acceptance through 30, **Then** 30 rows are returned with status and evidence/blocker.
2. **Given** any unresolved gate or audit error, **When** running the release check, **Then** it reports not ready and lists the reasons.
3. **Given** everything evidenced and a clean audit, **When** running the release check, **Then** it reports "ready for owner review" and still states that tagging needs owner approval.

### Edge Cases

- Input larger than a preset's target: refused for that preset (deliveries never downsize a master; 1440p of a 1080p source is allowed).
- Licensed audio shorter than the picture: refused with a message (no silent padding).
- Smooth 24 fps on a movie already at 24 fps: no frame-rate step; recipe records "none".
- Unknown preset name: refused, listing the valid ones.
- A preset failing does not stop the others; the summary lists each result.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide named presets: landscape-1080p (1920×1080 fit), vertical-1080x1920 (centre crop 9:16, 1080×1920), square-1080 (centre crop 1:1, 1080×1080), video-only-1080p (landscape without audio), licensed-audio-1080p (landscape with owner-licensed audio), hires-1440p (2560×1440 fit) and smooth-24fps-1080p (24 fps frame-rate step then landscape).
- **FR-002**: Each preset MUST be a versioned recipe of ordered steps (frame-rate step, geometry, audio policy, encode settings) whose checksum is recorded and is identical across runs.
- **FR-003**: Delivery MUST write a new file per preset (never overwriting), a record next to it, and leave the source unchanged.
- **FR-004**: Each output MUST be measured and compared with the preset's expectations: width, height, frame rate, video codec, audio present/absent, and duration within one frame of the expected duration; mismatches MUST be listed and the result marked failed.
- **FR-005**: When the preferred encoder is unavailable, a fallback encoder MUST be used, recorded, and expected by verification.
- **FR-006**: The licensed-audio preset MUST require a local audio file marked licensed by the owner, apply the given offset, trim the audio to the picture, and refuse audio shorter than the picture.
- **FR-007**: Crop presets MUST report, for the first and last frames, whether the subject's box lies inside the crop's 5% safe area ("inside" / "outside" / "unknown") and warn on "outside" without refusing.
- **FR-008**: A preset whose target is smaller than the input MUST be refused; an unknown preset MUST be refused listing valid names; one preset's failure MUST NOT stop the others.
- **FR-009**: The acceptance matrix MUST support F01–F30 and F01–F40 views from the ledger, listing status and evidence/blocker per feature.
- **FR-010**: A release check MUST combine the acceptance matrix (through 30) with the repository audit and report "not ready" with reasons, or "ready for owner review"; it MUST state that tagging needs owner approval and MUST NOT tag anything.
- **FR-011**: Command-line access MUST provide `deliver` (input, presets, output folder, optional licensed audio and offset) and `acceptance --through 30|40` plus a release check, with ASCII-safe JSON output and exit codes (0 all verified/ready, 5 some delivery failed verification, 2 refusal; release check 0 ready-for-review, 1 not ready).

### Key Entities

- **Preset**: name, recipe version, steps, expected properties.
- **Delivery record**: input checksum, output checksum, preset, recipe checksum, steps, encoder (and fallback), measured properties, verification, crop safe-area results, timings.
- **Acceptance row**: feature, status, evidenced, blocker.
- **Release check**: matrix summary, audit summary, ready flag, reasons, owner-approval note.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of delivered test outputs match their preset's measured expectations, or are marked failed with the exact mismatch.
- **SC-002**: The same preset produces the same recipe checksum across 100% of repeated runs.
- **SC-003**: The real MC-RUN movie can be delivered in landscape and vertical formats in under a minute on CPU.
- **SC-004**: The release check never reports ready while any F01–F30 gate is unresolved (verified by test with the real ledger).

## Assumptions

- Frame-rate conversion and geometric resampling reuse the F25 and F26 behaviour (blend interpolation; Lanczos scaling); no generative upscaling here.
- Subject boxes come from the existing anchor geometry measurement of the first and last frames.
- Subtitles and metadata are out of scope unless the owner provides them later.
- The final owner-approved multi-scene demonstration is an owner gate; this feature provides the tooling and evidence.
