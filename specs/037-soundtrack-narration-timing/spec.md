# Feature Specification: Soundtrack Sync Verification, Animatic, Narration and Captions (F37)

**Feature Branch**: `037-soundtrack-narration-timing` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F37 Soundtrack sync verification, animatic, narration and captions — offline slice: per-anchor sync report (target event, actual frame time, error, mean/max, drift; gate ≤ 2 frames, mean ≤ 1, zero drift); energy-warp report; animatic of stills or plain per-act cards cut at anchor times and muxed with licensed audio (or none), probe-verified; SRT captions; narration timing check with table and SRT; click-track preview and owner beat-map verification. CLI sync-report, warp-report, animatic, captions, narration-check, click-track, beatmap-verify. No GPU."

## Clarifications

### Session 2026-11-24

Resolved autonomously (owner's standing approval to use best judgment):

- Q: What format is the animatic? → A: 832×480 at the generation frame rate (16 fps) so every cut lands exactly on an anchor frame; H.264; AAC audio when licensed audio is given.
- Q: What colours are the placeholder cards? → A: One fixed dark tone per act (spark copper-brown, power bronze, signal green, logic blue, scale indigo; other chapters get a deterministic tone from their name), no text.
- Q: What does a narration script look like? → A: YAML `lines: [{text, at: <anchor id> | t: <seconds>, duration: <seconds>}]`.
- Q: What does the click track sound like? → A: 30 ms 1 kHz clicks at the downbeats in a 48 kHz WAV, music mixed underneath at reduced level when given.
- Q: Where do outputs go by default? → A: `outputs/animatic/<storyboard>.mp4`, `outputs/captions/<storyboard>.srt`, `outputs/narration/<storyboard>.srt`, `outputs/beatmap/…`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prove every anchor lands on its musical moment (Priority: P1)

The owner sees, for each anchor of the film storyboard, which musical event it was meant to hit (onset, energy peak, section start, downbeat) and when, where the picture actually places it, and the error in frames — plus the mean and worst error and whether error accumulates over the song.

**Why this priority**: The acceptance gate is every anchor within 2 frames, mean ≤ 1, zero drift.

**Independent Test**: For the real film storyboard and sync plan, all 96 anchors have zero error and zero drift; a storyboard with one bridge two frames too long reports drift from that point on.

**Acceptance Scenarios**:

1. **Given** a frame-locked storyboard and its sync plan, **When** the report runs, **Then** each anchor lists target event, target time, actual time and error in frames, with mean, maximum and drift, and the gate result.
2. **Given** a storyboard whose bridge lengths differ from the plan, **When** reported, **Then** the affected anchors exceed the gate and cumulative drift is shown.
3. **Given** a storyboard with a different number of anchors than the plan, **When** reported, **Then** it is refused with both counts.

---

### User Story 2 - See the energy warp is safe (Priority: P2)

For each bridge the owner sees the playback speed range the music-driven warp will use and confirms both anchor endpoints are pinned.

**Why this priority**: Warping must never move anchors off their beats or exceed the 0.5×–2× limits.

**Independent Test**: The real sync plan reports all 95 bridges pinned with speeds inside 0.5–2.

**Acceptance Scenarios**:

1. **Given** a sync plan, **When** the warp report runs, **Then** each bridge shows min/max speed and whether its first and last frames are pinned, with violations flagged.

---

### User Story 3 - Watch and hear the film before any GPU work (Priority: P1)

The owner builds an animatic: one still per anchor (the rendered anchor image if a run has it, otherwise a plain card coloured by act — never generated text), each held until the next anchor time, muxed with the owner's licensed music with the recorded offset. It plays as a normal video whose cut points match the anchor times and whose length matches the song.

**Why this priority**: Listening to the cut against the music is the owner's first sync approval and costs no GPU.

**Independent Test**: A synthetic two-act storyboard produces an animatic whose duration equals the planned picture length within one frame, whose cut points are at the anchor frames, and which has audio only when audio is given.

**Acceptance Scenarios**:

1. **Given** a storyboard and no run, **When** the animatic is built, **Then** it uses one plain card per anchor (act colour), lasts the planned length within one frame, and has no audio stream when no audio is given.
2. **Given** a run with rendered anchors, **When** built, **Then** rendered stills are used for those anchors and cards for the rest.
3. **Given** licensed audio and an offset, **When** built, **Then** the audio is trimmed from the offset and muxed; unlicensed audio is refused.
4. **Given** an existing output, **When** building, **Then** it is refused.

---

### User Story 4 - Captions and narration as separate tracks (Priority: P2)

The owner gets an SRT caption track (one cue per anchor naming its subject, or narration lines) and can check a narration script whose lines target anchors or times: overlaps, lines running past the end and gaps are reported in a timing table, and the script becomes an SRT.

**Why this priority**: Text must never be rendered by the model; captions and narration are separate local tracks.

**Independent Test**: Caption SRT for the film has 96 well-formed cues in time order; a narration script with an overlap and a line past the end reports both.

**Acceptance Scenarios**:

1. **Given** a storyboard (and concept bank), **When** captions are written, **Then** a valid SRT with one cue per anchor (subject text) in time order is produced.
2. **Given** a narration script, **When** checked, **Then** each line's start/end is resolved, overlaps and lines past the picture end are flagged, and an SRT is written.

---

### User Story 5 - Verify the beat map by ear (Priority: P3)

The owner listens to the music with clicks on the beat map's downbeats, corrects any wrong downbeats, and marks the beat map verified with their name and date.

**Why this priority**: Downbeats are only trusted for anchor timing when owner-verified.

**Independent Test**: A click-track preview of a synthetic beat map has clicks at the listed times; applying corrections and verifying writes a new beat map with `verified: true`, owner and date; the original is unchanged.

**Acceptance Scenarios**:

1. **Given** a beat map (and optional music), **When** the click track is made, **Then** an audio file with clicks at each downbeat (mixed under the music if given) is written.
2. **Given** corrections (index → new time) and an owner name, **When** verified, **Then** a new beat map with corrected, sorted downbeats and `verified: true`, `verified_by`, `verified_on` is written; empty owner refused.

### Edge Cases

- Silence or no audio: the animatic still builds (video only).
- A narration line referencing an unknown anchor is refused.
- Caption text is sanitized for SRT (no blank lines inside a cue).
- Beat-map corrections that make times non-increasing are refused.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The sync report MUST compare each storyboard anchor's frame time (from its bridge lengths, starting at the plan's first anchor) with the sync plan's target, giving per-anchor event, target, actual, error (frames), mean |error|, max |error|, drift (last error − first error) and gate pass/fail (max ≤ 2, mean ≤ 1, drift 0).
- **FR-002**: The warp report MUST list per bridge min/max speed and endpoint pinning (first map value 0, last = length − 1), flagging speeds outside 0.5–2 or unpinned endpoints.
- **FR-003**: The animatic MUST hold one still per anchor from its frame time to the next (last held through the tail hold), use rendered anchor images when available and plain act-coloured cards otherwise, contain no generated text, and probe-verify duration (within one frame) and audio presence.
- **FR-004**: Audio MUST be used only when marked licensed by the owner, trimmed from the given offset to the picture length.
- **FR-005**: Captions MUST be a valid SRT file with sequential cues in time order and non-empty text; anchor captions use the concept subject (else the anchor id).
- **FR-006**: The narration check MUST resolve each line's start (anchor time or explicit time) and end (start + duration), flag overlaps, lines past the end and unknown anchors, report gaps, and write an SRT.
- **FR-007**: The click track MUST place a short click at each downbeat (mixed under the music when given); beat-map verification MUST apply corrections, keep times strictly increasing, record owner and date, and write a new file.
- **FR-008**: Command-line access MUST provide sync-report, warp-report, animatic, captions, narration-check, click-track and beatmap-verify with ASCII-safe output and exit codes 0 pass, 1 gate failed / flags, 2 refusal.

### Key Entities

- **Sync row**: anchor, event, target_s, actual_s, error_frames.
- **Warp row**: bridge, min_speed, max_speed, pinned, flags.
- **Animatic record**: cuts, duration, audio, stills used, cards used.
- **Caption cue / narration line**: index, start, end, text.
- **Beat map**: downbeats, verified, verified_by, verified_on, corrections.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the real film storyboard and sync plan: 96/96 anchors within 2 frames, mean ≤ 1, zero drift.
- **SC-002**: The animatic duration matches the planned picture length within one frame in 100% of tests, and the no-audio build works.
- **SC-003**: All generated SRT files parse back to the same cues (100%).
- **SC-004**: Beat-map verification never modifies the original file and always records owner and date.

## Assumptions

- The owner supplies and confirms the licence of the music; MorphCurrent never fetches audio.
- The animatic uses placeholder cards until anchors are rendered; it is a timing tool, not a visual preview of morphs.
- Narration audio recording is the owner's; this feature handles the script timing and captions.
