# Feature Specification: Production GPU Budget and Batch Scheduling (F36)

**Feature Branch**: `036-production-gpu-budget` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F36 Production GPU budget and batch scheduling — offline slice: ingest measured job timings into the cost history (no duplicates); per-act and total budget with exact medians, labelled per-length interpolation, cold-start allowance and storage estimate; batches per act under caps with ETA and per-act owner approval; self-contained batch storyboards with seeds pinned to the full film so jobs are reused; progress, estimate-vs-actual (±20%) and duplicate-submission checks. CLI history-ingest, prod-budget, prod-approve, prod-batch, prod-status. No GPU."

## Clarifications

### Session 2026-11-24

Resolved autonomously (owner's standing approval to use best judgment):

- Q: What are the default caps and cold-start allowance? → A: 7,200 GPU seconds (2 h) and 20 jobs per batch; 60 s cold start per batch (model loading), all overridable.
- Q: Where do approvals and batch storyboards go? → A: `outputs/production/<storyboard>.approvals.jsonl` (append-only) and `outputs/production/<storyboard>/<act>-b<NN>.yaml`.
- Q: Which history file and runs folder are used? → A: `configs/perf_history.json` (checked in; measured numbers only) and `outputs/runs`.
- Q: Which act does a bridge belong to? → A: The act of its start anchor (the boundary bridge belongs to the earlier act).
- Q: How is ETA reported? → A: Sum of stage estimates plus the batch cold start, as GPU seconds and hours, assuming batches run one after another.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Learn from every render (Priority: P1)

After any render, the owner folds the measured GPU times of finished jobs into the cost history, so estimates reflect real costs for every bridge length and anchor type — without counting a job twice.

**Why this priority**: The film's bridges vary from 33 to 81 frames; estimates are only as good as the measured lengths.

**Independent Test**: Ingesting the real runs folder adds the four F29 experiment bridges (65 and 81 frames) once; ingesting again adds nothing.

**Acceptance Scenarios**:

1. **Given** finished, verified jobs with measured times, **When** ingested, **Then** each is added once with kind, size, length or method and time.
2. **Given** jobs already in the history (by job id), **When** ingested again, **Then** nothing is added.
3. **Given** unfinished, failed or unmeasured jobs, **When** ingested, **Then** they are skipped and counted.

---

### User Story 2 - Know the cost per act before starting (Priority: P1)

The owner sees, per act and in total, how many anchors and bridges remain and how long they should take on the GPU, using exact measurements where they exist and clearly labelled interpolation between measured bridge lengths otherwise, plus a per-batch warm-up allowance and the disk space needed.

**Why this priority**: 13+ GPU hours must be planned honestly before committing.

**Independent Test**: For the film storyboard the budget lists five acts whose totals sum to the film total; every stage carries an ESTIMATED / INTERPOLATED / EXTRAPOLATED label; a 73-frame bridge between measured 65 and 81 frames gets an interpolated cost between them.

**Acceptance Scenarios**:

1. **Given** measured 65- and 81-frame bridges at 832×480, **When** a 73-frame bridge is costed, **Then** its estimate lies between them and is labelled INTERPOLATED.
2. **Given** a length outside measured lengths, **When** costed, **Then** it is extrapolated linearly from the nearest two measured lengths and labelled EXTRAPOLATED.
3. **Given** the film storyboard, **When** budgeted, **Then** per-act anchors, bridges, GPU seconds and labels are shown and sum to the totals, with storage bytes.

---

### User Story 3 - Run the film in safe, approved batches (Priority: P1)

The owner splits each act into batches that respect a GPU-time cap and a job cap, approves an act, and gets ready-to-render batch storyboards whose stages are exactly the full film's stages (same seeds, prompts and lengths), so rendering a batch fills the same cache the full film uses. Rendering uses the existing render command with its GPU confirmation, caps and resume.

**Why this priority**: Batches must be bounded, approved and resumable, with zero duplicate work.

**Independent Test**: For an approved act, the written batch storyboards compile to stages identical (same seeds, prompts, frame counts, references) to the corresponding stages of the full film plan; an unapproved act is refused.

**Acceptance Scenarios**:

1. **Given** caps, **When** batches are planned, **Then** each batch stays within the caps (a single stage larger than the cap gets its own batch, flagged), never mixes acts, and has an ETA.
2. **Given** an act without an approval record, **When** batch storyboards are requested, **Then** it is refused.
3. **Given** an approved act, **When** batch storyboards are written, **Then** every anchor and bridge stage in them matches the full plan's stage (seed, prompt, negative, size, length, reference), including boundary anchors needed by the act's bridges.
4. **Given** existing output files, **When** writing, **Then** it is refused.

---

### User Story 4 - Watch progress and accuracy (Priority: P2)

During and after batches, the owner sees which stages are finished, the remaining GPU estimate and ETA, how each finished stage's real time compares with its estimate (within ±20% or not), and confirmation that no prompt was submitted twice.

**Why this priority**: The acceptance gate is batches within ±20% of estimate with zero duplicate submissions.

**Independent Test**: With a fake runs folder, status reports finished/remaining counts, an over-budget stage is flagged, and a duplicated prompt id is detected.

**Acceptance Scenarios**:

1. **Given** a runs folder, **When** status is computed for the film, **Then** finished stages (cached, verified jobs) and remaining GPU estimate are reported.
2. **Given** finished stages with measured times, **When** compared, **Then** each ratio actual/estimate is shown and those outside 0.8–1.2 are flagged.
3. **Given** two job records sharing a ComfyUI prompt id, **When** checked, **Then** a duplicate submission is reported.

### Edge Cases

- No measured bridge at a stage's size: fall back to pixel×frame scaling from the largest measured size, labelled EXTRAPOLATED.
- An act's bridge into the next act needs that act's first anchor: it is included in the batch (it is a text-to-image anchor, cheap) and counted in the batch estimate.
- Approval records are append-only; revoking is a new record.
- A history file that is missing is created; a malformed one is refused, not overwritten.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: History ingest MUST add verified, measured job timings (bridge: width, height, frames; anchor: method, width, height) to the cost history once per job id and report added/skipped counts.
- **FR-002**: Costing MUST use the median of exact matches; for bridges without an exact match, linear interpolation in frames between the nearest measured lengths of the same size (INTERPOLATED) or linear extrapolation from the nearest two (EXTRAPOLATED); otherwise pixel×frame scaling (EXTRAPOLATED); anchors by method and size, else scaling.
- **FR-003**: The budget MUST report per act and total: anchors, bridges, GPU seconds, label counts, a cold-start allowance per batch, and storage bytes.
- **FR-004**: Batch planning MUST split each act's stages (its anchors and the bridges starting in it) in plan order into batches within the GPU-time and job caps, never crossing acts, with per-batch ETA; oversized single stages get their own flagged batch.
- **FR-005**: Per-act approval records (act, note, owner, time) MUST be appended to a local log; batch storyboards MUST be refused for unapproved acts.
- **FR-006**: Batch storyboards MUST pin every seed to the full plan's values and reproduce the full plan's stages exactly (seed, prompts, size, length, reference), include boundary anchors needed by the batch's bridges, validate, and refuse to overwrite.
- **FR-007**: Status MUST report finished and remaining stages, remaining GPU estimate and ETA, per-stage actual/estimate ratios with flags outside 0.8–1.2, and duplicate prompt submissions across job records.
- **FR-008**: Command-line access MUST provide history-ingest, prod-budget, prod-approve, prod-batch and prod-status with ASCII-safe output and exit codes 0 success, 1 flags (status), 2 refusal.

### Key Entities

- **Cost entry**: run, kind, width, height, frames or method, exec seconds, job.
- **Stage estimate**: stage, act, seconds, label.
- **Batch**: act, index, stages, estimate, ETA, oversized flag.
- **Approval**: act, note, owner, time.
- **Status**: finished, remaining, remaining seconds, ETA, ratios, duplicates.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Re-ingesting the same runs adds zero entries (100% duplicate-free).
- **SC-002**: Batch storyboards reproduce the full plan's stages identically for 100% of their stages.
- **SC-003**: No planned batch exceeds its caps except flagged single oversized stages.
- **SC-004**: Duplicate prompt submissions are detected in 100% of test cases; the real runs folder shows zero.

## Assumptions

- Rendering a batch uses the existing render command (GPU confirmation, idle queue, caps, resume); this feature plans and checks, it does not render.
- The cold-start allowance (model loading at the start of a batch) is a configurable constant until measured.
- Batches share the content-addressed job store, so a later full-film render reuses every finished stage.
