# Feature Specification: Long-Chain Lineage and Drift Control (F35)

**Feature Branch**: `035-long-chain-lineage-drift` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F35 Long-chain lineage and drift control — offline slice: per-anchor lineage (root, edit depth, chain; per-act and maximum depth vs a limit); drift curve of rendered anchors versus their act reference (colour, sharpness, centring, scale) against thresholds in a checked-in config; explicit re-anchor proposals (independent text-to-image keyframe with continuity reference) with exact invalidation and a proposed storyboard in a new file; shared-anchor byte-identity check across bridge jobs. CLI lineage, lineage-drift, lineage-propose, lineage-shared. No GPU."

## Clarifications

### Session 2026-11-24

Resolved autonomously (owner's standing approval to use best judgment):

- Q: Where are the depth limit and drift thresholds kept? → A: `configs/film/lineage.yaml`: depth limit 12; colour distance ≤ 60; sharpness ratio ≥ 0.6; centroid offset ≤ 0.08; scale ratio 0.75–1.33.
- Q: Why a depth limit of 12? → A: Measured chains so far are only 2 edits deep; 12 is a conservative starting point that splits the film's 28-edit acts into chains of at most 12, to be recalibrated from the first rendered act's drift curve.
- Q: Where is a proposed storyboard written? → A: To the path given, by default `outputs/proposals/<storyboard name>.reanchored.yaml` (local), never over an existing file.
- Q: How is sharpness measured? → A: With the F16 subject sharpness metric on the decoded anchor image; the ratio is anchor sharpness ÷ act-reference sharpness.
- Q: What exactly does a re-anchored anchor become? → A: `generation: independent_t2i` with `reference` = the previous anchor (a continuity hint for review, not image conditioning); its prompt is unchanged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See how deep every edit chain goes (Priority: P1)

For every anchor the owner sees where its image ultimately comes from (the last separately generated anchor), how many reference edits deep it is, and the chain in between, plus the deepest chain per act and overall, compared with a configured limit.

**Why this priority**: Each reference edit compounds drift; long chains are where detail loss and colour shift accumulate.

**Independent Test**: For the film storyboard, depths restart at 0 at each act start and the maximum depth equals the longest act minus one; a synthetic chain crossing an independent anchor restarts its depth there.

**Acceptance Scenarios**:

1. **Given** a compiled plan, **When** lineage is computed, **Then** each anchor has root, depth and chain, where a text-to-image or independent anchor has depth 0 and is its own root.
2. **Given** a depth limit, **When** checked, **Then** anchors deeper than the limit are listed.
3. **Given** the film storyboard, **When** computed, **Then** per-act maximum depths are reported (anchors − 1 per act).

---

### User Story 2 - Measure drift along a rendered chain (Priority: P1)

After rendering, the owner sees a drift curve: for each anchor, its depth and how far it has moved from its act's reference image in subject colour, sharpness, centring and scale, flagged against owner-adjustable thresholds.

**Why this priority**: The acceptance gate is a rendered act with measured drift inside owner-approved bounds.

**Independent Test**: A synthetic rendered chain with increasing colour shift and falling sharpness flags the anchors past the thresholds; the real organic-machines run produces a three-point curve.

**Acceptance Scenarios**:

1. **Given** a run with rendered anchors, **When** the drift curve is computed, **Then** every rendered anchor reports depth, colour distance, sharpness ratio, centroid offset and scale ratio relative to its act reference, with flags.
2. **Given** an anchor not yet rendered or whose act reference is not rendered, **When** computed, **Then** it is listed as missing rather than measured.
3. **Given** the act reference itself, **When** computed, **Then** its drift is zero / ratio 1.

---

### User Story 3 - Re-anchor before drift poisons the rest (Priority: P1)

Where a chain is too deep or drift is over the limit, the owner gets a proposal to restart the chain at a specific anchor as an explicitly marked independent keyframe that keeps a continuity reference to the previous anchor, together with exactly what would have to be re-rendered, and a proposed storyboard written to a separate file — nothing changes until the owner adopts it.

**Why this priority**: One bad anchor would otherwise affect every later image; re-anchoring must be deliberate and visible.

**Independent Test**: For the film storyboard with a depth limit of 12, proposals land at depth-12 points inside long acts; the proposed storyboard validates, marks those anchors independent with continuity references, and the original file is unchanged.

**Acceptance Scenarios**:

1. **Given** a depth limit, **When** proposals are made, **Then** the chosen anchors are the first in each chain whose depth would exceed the limit, repeated along the chain so no depth exceeds it.
2. **Given** drift flags from a run, **When** proposals are made with that run, **Then** the first flagged anchor of each act is proposed as well.
3. **Given** a proposal, **When** listed, **Then** it names the stages to re-render (the anchor, its edit descendants until the next separately generated anchor, bridges touching them).
4. **Given** a proposal written to a new file, **When** compiled, **Then** it validates and the original storyboard is byte-identical; writing over an existing file is refused.

---

### User Story 4 - Shared anchors stay byte-identical (Priority: P2)

The owner can confirm that every bridge of a run used exactly the anchor images recorded for its two endpoints, so the same bytes are shared by neighbouring bridges.

**Why this priority**: Seam safety depends on identical shared anchors.

**Independent Test**: On the real organic-machines run every bridge matches; a tampered bridge record is reported.

**Acceptance Scenarios**:

1. **Given** a run, **When** checked, **Then** every bridge's start and end image hashes equal the recorded anchor hashes.
2. **Given** a mismatch or missing record, **When** checked, **Then** it is reported with the bridge and endpoint.

### Edge Cases

- An anchor whose reference is an independent anchor starts a new chain (depth 1 from that root).
- Proposals never pick an act's first anchor (already separately generated).
- A run whose manifest lacks bridge jobs reports them as unchecked, not as matches.
- Drift with unreliable subject masks (F12 flags) is reported with the flag instead of numbers.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Lineage MUST give every anchor its root, depth (reference edits since the root) and chain, and report per-act and overall maximum depth and anchors exceeding the configured depth limit.
- **FR-002**: A checked-in lineage config MUST hold the depth limit and drift thresholds (colour distance, minimum sharpness ratio, centroid offset, scale ratio band).
- **FR-003**: The drift curve MUST measure each rendered anchor against its act reference (first anchor of its chapter, else of the storyboard): colour distance, sharpness ratio, centroid offset, scale ratio; flag threshold breaches; list missing anchors.
- **FR-004**: Re-anchor proposals MUST select anchors so no chain exceeds the depth limit and include the first drift-flagged anchor per act when a run is given; each proposal MUST list the stages it invalidates using the F33 impact rule.
- **FR-005**: A proposed storyboard MUST be written only to a new file, mark proposed anchors as independent text-to-image with a continuity reference to the previous anchor, validate, and leave the original unchanged.
- **FR-006**: The shared-anchor check MUST compare each bridge job's start/end image hashes with the run's recorded anchor hashes and report matches, mismatches and unchecked bridges.
- **FR-007**: Command-line access MUST provide lineage, lineage-drift, lineage-propose and lineage-shared with ASCII-safe output and exit codes 0 ok, 1 limits exceeded / flags / mismatches, 2 refusal.

### Key Entities

- **Lineage entry**: anchor, root, depth, chain, act.
- **Drift point**: anchor, depth, colour distance, sharpness ratio, centroid offset, scale ratio, flags.
- **Re-anchor proposal**: anchor, reason (depth / drift), invalidated stages.
- **Shared-anchor result**: bridge, endpoint, expected hash, used hash, status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Lineage depths match hand-computed values for synthetic chains (100%) and the film's per-act maxima equal anchors − 1.
- **SC-002**: With a depth limit of 12 the proposed film storyboard has no chain deeper than 12.
- **SC-003**: The real organic-machines run reports 2/2 bridges with byte-identical shared anchors.
- **SC-004**: The original storyboard is unchanged after every proposal (verified by checksum).

## Assumptions

- Drift is measured with the existing F12 geometry and F16 sharpness metrics on rendered anchor images.
- Thresholds are starting points for owner calibration after a rendered act.
- The full-act render with drift inside approved bounds is the owner-gated acceptance step.
