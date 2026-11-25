# Feature Specification: Batch Review and Iteration for the Film's Bridges (F39)

**Feature Branch**: `039-batch-review-iteration` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Implemented (offline)

**Input**: User description: "F39 Batch review and iteration for the ~95 film bridges — offline slice: film review state gathered across all batch run manifests (status, QA flags/score, versions, latest decision); append-only review log with approve/reject/pending, bulk approval within an act, QA-ranked review order; rerender queue (rejected bridges only themselves, rejected anchors their dependent anchors and adjacent bridges) with budget preview and an optional rerender storyboard; act contact sheet of bridge frame strips and a side-by-side comparison of two versions; keyboard-driven act review page in the loopback review UI. CLI film-review-status, film-review, film-review-approve-act, film-rerender-queue, film-act-sheet, film-compare. No GPU."

## Clarifications

### Session 2026-11-24

Resolved with the owner's standing approval to use best judgment:

- Q: Where do review decisions live, and do the per-run review files still count? → A: One append-only film log `outputs/reviews/<film>.batch-review.jsonl`; existing per-run `review.json` decisions are read as earlier entries (pinned to that run's version) so nothing recorded is lost.
- Q: How is a stage's QA score defined? → A: The same severity weights as the clip screen (hard cut 3, endpoint mismatch 3, flare 2, freeze 1) summed over the stage's recorded flags; 0 when unflagged.
- Q: What counts as a version? → A: A distinct media hash (video for bridges, image for anchors) seen in any manifest; first-seen order by manifest creation time; the latest is current.
- Q: Who is the reviewer by default? → A: `owner`; the CLI and UI accept a name.
- Q: How is the rerender budget estimated? → A: With the production cost model (F36 history; labels ESTIMATED/INTERPOLATED/EXTRAPOLATED).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See where the whole film stands (Priority: P1)

The film is rendered in many batches. The owner sees one table of all 96 anchors and 95 bridges: which act each belongs to, whether it is rendered yet, its quality flags and score, how many versions exist, and the latest decision.

**Why this priority**: Without one combined view, ninety-odd clips spread over a dozen batch runs cannot be reviewed reliably.

**Independent Test**: With two synthetic batch runs covering parts of a storyboard, the status lists every stage once, marks unrendered stages missing, and counts two versions for a stage rendered in both runs.

**Acceptance Scenarios**:

1. **Given** the film storyboard and batch runs, **When** status is requested, **Then** every anchor and bridge appears exactly once with act, state, QA, version count and decision, plus per-act totals.
2. **Given** a stage rendered twice with different outputs, **When** status is requested, **Then** both versions are listed in render order and the latest is current.
3. **Given** no runs, **When** status is requested, **Then** every stage is missing.

---

### User Story 2 - Decide quickly, act by act (Priority: P1)

The owner records approve, reject or pending for a stage, with a note; each decision is pinned to the version reviewed and appended to a per-film log (never rewritten). They can approve, in one step, every rendered, unflagged, undecided bridge of an act, and they review in quality order — flagged and worst-scoring clips first.

**Why this priority**: Bulk approval of clean clips and worst-first ordering is what makes reviewing ~95 bridges practical.

**Independent Test**: Bulk approval of an act approves only its rendered, unflagged, undecided bridges and leaves flagged, missing and decided ones untouched; the log only grows.

**Acceptance Scenarios**:

1. **Given** a decision, **When** recorded, **Then** a log entry with stage, decision, note, reviewer, time and pinned version is appended, and the status shows it.
2. **Given** a decision on a stage that is not rendered, or an unknown stage or decision, **When** recorded, **Then** it is refused.
3. **Given** an act, **When** bulk-approved, **Then** only rendered, unflagged, undecided bridges of that act are approved and the count is reported.
4. **Given** a new version rendered after a decision, **When** status is requested, **Then** the stage shows the decision as stale (it applies to an older version) and it re-enters the review order.
5. **Given** an act, **When** the review order is requested, **Then** flagged stages come first, then by worst score, then storyboard order.

---

### User Story 3 - Rerender only what was rejected (Priority: P1)

The owner sees what a rerender would cover: a rejected bridge queues only itself; a rejected anchor queues itself, every anchor edited from it (directly or indirectly) and the bridges touching any of them. A budget preview uses the production cost model; on request a rerender storyboard is written for exactly those stages.

**Why this priority**: Rejections must not trigger needless GPU work, and anchor rejections must not leave stale dependants.

**Independent Test**: Rejecting one bridge queues one bridge; rejecting an anchor in the middle of a reference-edit chain queues the rest of that chain and their adjacent bridges, and nothing in other acts.

**Acceptance Scenarios**:

1. **Given** rejected stages, **When** the queue is built, **Then** it lists exactly the affected stages with a GPU-time estimate labelled as an estimate.
2. **Given** an output path, **When** requested, **Then** a rerender storyboard is written with pinned seeds; an existing file is refused.
3. **Given** no rejections, **When** the queue is built, **Then** it is empty with zero cost.

---

### User Story 4 - Review aids for an act (Priority: P2)

The owner gets an act contact sheet (one row per bridge: first, middle and last frame) and a side-by-side comparison clip of two versions of one bridge.

**Why this priority**: Visual comparison speeds decisions, but the decisions themselves come from Story 2.

**Independent Test**: For synthetic clips, the sheet has one row per rendered bridge with three frames each, and the comparison clip has both versions side by side with the longer duration.

**Acceptance Scenarios**:

1. **Given** an act with rendered bridges, **When** the sheet is built, **Then** a new image with one labelled row per rendered bridge is written; missing bridges are listed.
2. **Given** two versions of a bridge, **When** compared, **Then** a new side-by-side clip is written; an unknown version or an existing output is refused.

---

### User Story 5 - Keyboard review in the review page (Priority: P3)

In the loopback review interface the owner opens an act, sees its bridges in review order with their clips, and approves (A), rejects (R) or skips (N) with the keyboard; decisions go to the same log.

**Why this priority**: Convenience over the command line; same decisions, same log.

**Independent Test**: The act page lists the act's bridges in review order and a posted decision with a valid form token appends to the log; a missing token is refused.

**Acceptance Scenarios**:

1. **Given** the review server, **When** the act page is opened, **Then** it lists bridges in review order with keyboard hints.
2. **Given** a posted decision with a valid token, **When** received, **Then** it is appended to the film log; without a token it is refused.

### Edge Cases

- A batch run of a different storyboard is ignored; runs are matched to the film by stage ids.
- Two runs with the same output (cache hit) count as one version.
- A decision is pinned to the current version; a later version makes it stale rather than silently inheriting it.
- A rejected anchor that opens an act (text-to-image) queues only its own act's chain.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST gather the review state of every anchor and bridge of a film storyboard across all run manifests in a runs folder, with act, state (missing, rendered, verified), QA status/flags/score, versions (distinct outputs with job id, media hash, run, time) and the latest decision.
- **FR-002**: Decisions MUST be appended to a per-film review log (approve, reject, pending; note; reviewer; time; pinned version) and never rewritten; decisions on unrendered or unknown stages MUST be refused.
- **FR-003**: A decision pinned to an older version MUST be reported as stale.
- **FR-004**: Bulk approval MUST approve only rendered, unflagged bridges of one act that have no current decision (none, pending, or stale) and report the count.
- **FR-005**: The review order MUST list flagged stages first, then by worst QA score, then storyboard order.
- **FR-006**: The rerender queue MUST contain rejected bridges, rejected anchors, anchors transitively edited from rejected anchors, and the bridges touching any queued anchor — nothing else — with an estimated GPU time from the production cost model; it MAY write a rerender storyboard (refusing to overwrite).
- **FR-007**: The act contact sheet MUST show first, middle and last frame per rendered bridge of an act; the comparison clip MUST place two versions of one bridge side by side; both write new files only.
- **FR-008**: The loopback review interface MUST offer an act page with keyboard approve/reject/next that writes to the same log, protected by the existing form token.
- **FR-009**: Command-line access MUST provide film-review-status, film-review, film-review-approve-act, film-rerender-queue, film-act-sheet and film-compare with ASCII-safe output and exit codes 0 ok, 1 attention needed, 2 refusal.

### Key Entities

- **Stage state**: stage id, kind, act, state, QA, versions, decision, stale flag.
- **Version**: job id, media hash, run, time, media path.
- **Review entry**: time, stage, decision, note, reviewer, version.
- **Rerender queue**: stages, reasons, estimated GPU seconds.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The status covers 100% of the film's 191 stages exactly once.
- **SC-002**: Bulk approval of an act changes only eligible bridges (0 flagged, missing or already-decided stages changed).
- **SC-003**: The rerender queue contains exactly the transitive dependants of rejections — verified on chains of known shape.
- **SC-004**: Versions are never lost: every distinct output ever recorded for a stage stays listed.
- **SC-005**: Owner completes review of a full act with every decision recorded (acceptance gate after rendering).

## Assumptions

- Batch runs live in one runs folder (`outputs/runs`) and use the film's stage ids (`anchor:<id>`, `bridge:<from>-><to>`).
- The film log lives at `outputs/reviews/<film>.batch-review.jsonl`; it is local, not committed.
- Visual approval is the owner's; per the owner's 2026-11-24 choice, Claude prepares evidence and asks with options.
