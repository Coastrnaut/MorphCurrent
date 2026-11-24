# Feature Specification: Full-Song Act Structure, Frame-Locked Timeline and Film Storyboard (F32)

**Feature Branch**: `032-full-song-act-structure` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F32 Full-song act structure, beat-locked timeline and film storyboard — offline slice: frame-locked transitions (exact 4n+1 lengths from the sync plan; old beat storyboards and hashes unchanged; 4-frame snapping helper); five acts over the ten eras with a fresh text-to-image anchor per act and reference edits inside acts; a generator writing one film storyboard from the sync plan, concept bank and act definition; a dry-run film report with per-act numbers, act-boundary music events, total frames, holds vs song length, plan hash and estimated GPU hours. CLI film-storyboard, film-report."

## Clarifications

### Session 2026-11-24

Resolved autonomously from the ledger and owner rules:

- Q: Which eras form which act? → A: Spark = natural electricity + early storage; Power = generation and grid; Signal = signals and communication; Logic = vacuum-tube computing + solid state + integrated circuits; Scale = microprocessors + parallel and GPU compute + data centers and AI hardware (18 / 10 / 10 / 29 / 29 subjects with the current bank).
- Q: Where do the inputs and the generated storyboard live? → A: Act definition `configs/film/acts.yaml`; the current sync plan (timing data only, no audio) `configs/film/sync-plan.json`; generated storyboard `configs/sequences/engineering-film.yaml`. All checked in so the film plan is reproducible.
- Q: How are seeds chosen? → A: Derived from a fixed master seed (31415) and the stage id, as for every storyboard; no per-stage seeds are written.
- Q: How are prompts composed? → A: Anchor: "<subject>: <description>; dominant shapes: <shapes>; materials: <materials>" (style from the engineering-noir pack). Transition: "Continuous physical metamorphosis in one uninterrupted shot: <morph-affinity note>; motion feel: <music character words>. No cuts or dissolves."
- Q: How is GPU time estimated? → A: Median measured time for stages with an exact match (same kind, size, length / method) and pixel×frame extrapolation from the largest measured stage otherwise, each stage labelled ESTIMATED or EXTRAPOLATED; the total is labelled as an estimate.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Anchors exactly on the music, with no drift (Priority: P1)

The owner's storyboard can say "this morph lasts exactly 61 frames" instead of "this morph lasts N beats", so every anchor lands on the absolute frame the music planner chose. Over six minutes the error never accumulates. Older storyboards that count beats behave exactly as before.

**Why this priority**: The whole film's sync depends on anchors sitting on chosen musical events across 95 bridges.

**Independent Test**: A storyboard with frame-locked transitions compiles to bridges of exactly those lengths, anchor frames equal the running sum, and the existing example storyboards produce the same plan hashes as before.

**Acceptance Scenarios**:

1. **Given** transitions with frame lengths, **When** compiled, **Then** each bridge has exactly that length, anchor k sits at 1 + Σ(L−1) frames with zero timing error, and no BPM is required.
2. **Given** a frame length that is not 4n+1, below 5 or above the render maximum, **When** validated, **Then** the storyboard is refused naming the transition.
3. **Given** a transition with both or neither of beats and frames, **When** validated, **Then** it is refused.
4. **Given** the existing beat-based storyboards, **When** compiled, **Then** their plan hashes are unchanged.
5. **Given** a list of target times (e.g. a rubato beat map), **When** snapped to the 4-frame grid, **Then** every frame is within 2 frames of its target and errors do not accumulate.

---

### User Story 2 - A whole-film storyboard in one step (Priority: P1)

From the music plan (96 anchor times, 95 bridge lengths), the 96-subject concept bank and a five-act definition, the owner generates one storyboard: one anchor per subject in order, grouped into acts (Spark, Power, Signal, Logic, Scale), each act opening with a fresh image and continuing with reference edits; each morph gets the planned length and a prompt built from the subject-to-subject bridge note and the music's character for that stretch.

**Why this priority**: This is the storyboard the existing pipeline renders; nothing downstream can start without it.

**Independent Test**: Generating from the real sync plan and concept bank yields a valid storyboard with 96 anchors, 95 transitions whose lengths equal the plan, five contiguous chapters and exactly five text-to-image anchors.

**Acceptance Scenarios**:

1. **Given** matching counts, **When** generated, **Then** anchors follow the concept order, each act's first anchor is text-to-image and the rest reference the previous anchor, chapters equal acts, and transition lengths equal the sync plan's bridges.
2. **Given** a sync plan whose anchor count differs from the bank, or a bridge outside 33–81 frames, **When** generating, **Then** it is refused with the numbers.
3. **Given** an existing output path, **When** generating, **Then** it is refused.
4. **Given** a licensed audio file, **When** generating, **Then** the storyboard references it as owner-licensed; without one it has no audio.
5. **Given** an act definition missing an era or listing one twice, **When** generating, **Then** it is refused.

---

### User Story 3 - Know what the film will cost before rendering (Priority: P2)

A dry-run report shows, per act and in total: anchors, bridges, frames, seconds, the music event at each act boundary, total unique frames (1 + Σ(L−1)), how the picture plus head/tail holds covers the song, the plan hash, and estimated GPU hours from measured history (extrapolated values clearly labelled).

**Why this priority**: The acceptance gate is an owner-approved storyboard whose dry run reports duration, counts and GPU hours.

**Independent Test**: The report for the generated storyboard sums per-act frames to the total, matches the sync plan's song length within one frame plus the tail hold, and gives a labelled GPU estimate without touching the GPU.

**Acceptance Scenarios**:

1. **Given** a film storyboard, **When** reported, **Then** per-act numbers sum to the totals and the total unique frames equal 1 + Σ(L−1).
2. **Given** the sync plan's song length, **When** reported, **Then** last-anchor time plus tail hold equals the song length within one frame.
3. **Given** measured history only for some bridge lengths, **When** reported, **Then** stages without exact data are extrapolated and labelled, and the total is labelled as an estimate.
4. **Given** an edit to one act's anchor prompt, **When** the plans before and after are compared, **Then** only that act's stages and its two boundary bridges change.

### Edge Cases

- A sync plan with a head hold (first anchor after frame 0) is reported, not silently shifted.
- A one-anchor act is allowed (text-to-image only).
- An act boundary that does not coincide with a music section is reported as such (the owner may re-plan); no automatic reshuffle of subjects.
- Prompts are composed only from the concept bank text and the style pack; no brand/person terms can appear (the bank is already checked).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A transition MUST specify exactly one of a beat duration or an exact frame length; frame lengths MUST be 4n+1, ≥ 5 and ≤ the render's maximum bridge frames.
- **FR-002**: BPM MUST be required only when at least one transition uses beats; frame-locked transitions MUST compile with zero timing error.
- **FR-003**: Existing beat-based storyboards MUST compile to the same plan hashes as before this feature.
- **FR-004**: A snapping helper MUST map target times to frames f = 4·round(t·fps/4), reporting each error (≤ 2 frames at 16 fps) without accumulation.
- **FR-005**: A checked-in act definition MUST map each of the ten concept-bank eras to exactly one of five ordered acts; acts MUST be contiguous in era order.
- **FR-006**: The generator MUST produce one anchor per concept in order, with the act's first anchor text-to-image and later anchors reference edits of the previous anchor, chapter = act id, prompts composed from subject, description, shapes and materials, and the engineering-noir style pack.
- **FR-007**: The generator MUST give each transition the sync plan's bridge length and a prompt combining the concept's morph-affinity note with the bridge's music character, and MUST refuse mismatched counts, bridges outside 33–81 frames and existing outputs.
- **FR-008**: The generated storyboard MUST record its sources (sync plan hash, track hash, concept bank version and status, act definition) in a header comment and MUST validate with the existing storyboard schema.
- **FR-009**: The film report MUST give per-act and total anchors, bridges, frames and seconds, the act-boundary music event, total unique frames, last-anchor time, tail hold and song length, the plan hash, and labelled GPU-hour estimates, without any GPU work.
- **FR-010**: Editing one act's content MUST change only that act's stage identities and its two boundary bridges (verified by plan comparison).
- **FR-011**: Command-line access MUST provide film-storyboard and film-report with ASCII-safe output and exit codes 0 success, 2 refusal.

### Key Entities

- **Frame-locked transition**: from, to, frames (4n+1), prompt, seed.
- **Act definition**: ordered acts {id, title, eras}.
- **Film storyboard**: the standard storyboard with chapters = acts and frame-locked transitions.
- **Film report**: per-act stats, totals, coverage, plan hash, GPU estimate.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For the real sync plan, all 96 anchors land on their planned frames exactly (zero drift) and every bridge is 33–81 frames.
- **SC-002**: Existing example storyboards keep identical plan hashes (100%).
- **SC-003**: The film report's total picture plus tail hold matches the song length within one frame.
- **SC-004**: Editing one act changes no stage outside that act and its two boundary bridges.
- **SC-005**: Generating and reporting the full film takes under 5 seconds offline.

## Assumptions

- The current sync plan comes from F15 `sync-plan` on the owner-licensed Mozart track (96 anchors, 95 bridges, song 358.8 s); re-planning produces a new storyboard.
- Act boundaries follow eras (subjects), not re-ordered to music sections in this slice; the report shows how well they coincide.
- Lineage drift over long edit chains is F35's concern; resetting to text-to-image per act limits chains to at most ~31 edits.
- The concept bank is still draft; the generated storyboard inherits that status until the owner approves both.
