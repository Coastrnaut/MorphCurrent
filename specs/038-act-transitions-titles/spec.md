# Feature Specification: Act Transitions, Title Cards and Overlays (F38)

**Feature Branch**: `038-act-transitions-titles` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Implemented (offline)

**Input**: User description: "F38 Act transitions, title cards and overlays — offline slice: checked-in titles definition (opening card, per-act titles at act starts with fades, optional lower thirds, end card; owner text, local font, never in Wan prompts); overlays composited after the join onto a copy with deterministic arguments and a recipe checksum, input untouched, record of covered anchor frames; 16:9 title-safe and optional 9:16 crop-safe check; act-boundary report with nearest music section and a move proposal. CLI titles-check, titles-render, act-boundaries. No GPU."

## Clarifications

### Session 2026-11-24

Resolved autonomously (owner's standing approval to use best judgment):

- Q: Where is the titles definition and which font? → A: `configs/film/titles.yaml`; font `C:/Windows/Fonts/arial.ttf` (checksum recorded in the recipe).
- Q: What text and timing are used by default? → A: Opening card "From Lightning to Silicon" 0–5 s; each act title (Spark, Power, Signal, Logic, Scale) for 4 s from its act's first anchor; end card "MorphCurrent" over the last 5 s; 0.5 s fades; no lower thirds by default (the format supports them). The owner can edit any text.
- Q: How are sizes and positions expressed? → A: Relative to the frame: size as a fraction of frame height (titles 0.08, cards 0.10, lower thirds 0.05), horizontally centred, vertical position as a fraction of height (cards 0.45, act titles 0.80); minimum size when shrinking: 0.035 of height.
- Q: How is text width estimated for the safe-area check? → A: 0.55 × font size per character (Arial average advance); conservative, no font-metric library needed.
- Q: What window is used for section proposals? → A: ±6 anchors around each boundary.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mark each act without breaking the morph (Priority: P1)

The owner adds an opening card, a short title at the start of each act (Spark, Power, Signal, Logic, Scale), optional lower thirds and an end card. They are drawn onto a copy of the finished movie (or the animatic) after the join, using the owner's text and a local font, fading in and out — the generated morph itself never contains text.

**Why this priority**: Chapter changes need signposting while the picture stays one continuous metamorphosis.

**Independent Test**: Rendering the titles onto a short synthetic movie produces a new file of identical duration and frame count, with text visible only in the planned windows, and the input file is byte-identical afterwards.

**Acceptance Scenarios**:

1. **Given** a titles definition and a movie, **When** rendered, **Then** a new file with the same duration and frame count is written, the input is unchanged, and a record lists each overlay's start/end, text and the anchor frames it covers.
2. **Given** the same inputs twice, **When** rendered, **Then** the recipe checksum is identical.
3. **Given** a missing font file, empty text or an existing output, **When** rendering, **Then** it is refused.
4. **Given** the act titles, **When** timed, **Then** each starts at its act's first anchor time (taken from the storyboard) and lasts its duration.

---

### User Story 2 - Text stays inside safe areas (Priority: P1)

Before rendering, the owner checks that every text block fits inside the 16:9 title-safe area and, if a vertical release is planned, inside the 9:16 centre crop; blocks that would not fit are shrunk to fit or flagged.

**Why this priority**: Titles must survive both delivery formats (F30).

**Independent Test**: A long line is shrunk or flagged for the 9:16 crop while a short title passes both.

**Acceptance Scenarios**:

1. **Given** a block that fits, **When** checked, **Then** it passes with its size unchanged.
2. **Given** a block too wide for the requested safe area, **When** checked, **Then** its size is reduced down to a minimum, and flagged if it still does not fit.

---

### User Story 3 - Put act changes on musical section starts (Priority: P2)

The owner sees, for each act boundary, which musical event falls on it, the nearest section start within a few anchors, and a proposal to move the boundary there. Nothing changes automatically.

**Why this priority**: Act changes feel right when they land on section changes in the music.

**Independent Test**: For the film storyboard and sync plan, boundaries near section starts get move proposals with signed anchor offsets; boundaries with no section nearby get none.

**Acceptance Scenarios**:

1. **Given** the film storyboard and sync plan, **When** reported, **Then** each boundary lists its anchor, event, nearest section anchor within the window and the offset, and a proposal when one exists.

### Edge Cases

- Overlays overlapping in time are reported (allowed, but listed).
- An overlay extending past the movie end is clipped and reported.
- Text with characters that need escaping (colon, quote, percent) renders literally.
- A storyboard without chapters has no act titles; only opening/end cards apply.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A checked-in titles definition MUST describe an opening card, per-act titles (default text = act title from the act definition), optional lower thirds and an end card, each with text, start reference (time, act start, or end), duration, fades, size and position, plus the local font file.
- **FR-002**: Overlays MUST be composited after the join onto a new file; the input MUST be byte-identical afterwards; text MUST never be added to generation prompts.
- **FR-003**: The overlay recipe (resolved timings, texts, positions, sizes, font checksum, filter) MUST be deterministic and checksummed; the record MUST list for each overlay the anchor frames inside its window.
- **FR-004**: The safe-area check MUST test each block against the 16:9 title-safe area (90% of the frame) and, when requested, the 9:16 centre-crop safe area, shrinking the size down to a minimum before flagging.
- **FR-005**: The act-boundary report MUST list each boundary's anchor, music event, nearest section-start anchor within a window (default ±6 anchors), signed offset, and a move proposal; it MUST not modify anything.
- **FR-006**: Rendering MUST refuse a missing font, empty text and an existing output, and MUST verify duration and frame count of the result against the input.
- **FR-007**: Command-line access MUST provide titles-check, titles-render and act-boundaries with ASCII-safe output and exit codes 0 ok, 1 flags, 2 refusal.

### Key Entities

- **Titles definition**: font, defaults, opening, acts, lower thirds, end.
- **Overlay**: id, text, start_s, end_s, fade_s, size, x/y position, covered anchor frames.
- **Safe-area result**: overlay, area, fits, size used, flagged.
- **Boundary proposal**: act, anchor index, event, nearest section index, offset.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Rendered output keeps the input's duration and frame count exactly in 100% of tests, with the input unchanged.
- **SC-002**: The same inputs always produce the same recipe checksum.
- **SC-003**: All film titles fit the 16:9 title-safe area and the 9:16 crop-safe area (after any shrinking) or are explicitly flagged.
- **SC-004**: The act-boundary report covers all four film boundaries and proposes moves only where a section start lies within the window.

## Assumptions

- Text is the owner's (default act titles from the act definition); the font is a local file (default Arial from the Windows fonts folder).
- Titles are a finishing layer; the verified joined movie and its seam frames are never modified.
- Moving an act boundary means reassigning which subjects open an act (F32 regeneration); this feature only proposes it.
