# Feature Specification: Full-Song Film Delivery and Acceptance (F40)

**Feature Branch**: `040-full-song-film-delivery` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Implemented (offline)

**Input**: User description: "F40 Full-song film delivery and acceptance — offline slice: assemble the film from owner-approved versions (blockers listed; explicit labelled preview mode), seam-verified join in film order without dropping frames on mismatch, full-song coverage check, optional licensed audio; deliver through the existing presets; provenance report (hashes, chosen versions with seeds, models and workflows, licences, owner approvals, measured vs estimated GPU time); F31–F40 gate matrix. CLI film-assemble, film-deliver, film-provenance, film-gates. No GPU."

## Clarifications

### Session 2026-11-24

Resolved with the owner's standing approval to use best judgment:

- Q: Where is the master written and how is it named? → A: `outputs/film/<film>_<UTC timestamp>_<plan8>.mp4` (same scheme as run finals); preview masters end in `_PREVIEW.mp4`; the record is `<master>.assembly.json`.
- Q: Which delivery presets run by default? → A: `landscape-1080p` and `vertical-1080x1920`; `smooth-24fps-1080p` and `licensed-audio-1080p` on request (the latter needs licensed audio).
- Q: Where do model and workflow identities come from? → A: The hash-pinned profile bindings (`configs/profiles/*.binding.json`) and their workflow files, the model catalogue (`configs/model_catalogue.json`, sha256 + licence text) and recorded weight hashes (`outputs/model_hashes.json`); no weights are re-hashed here.
- Q: What is "measured GPU time"? → A: The sum of `timings.execution_seconds` in the job records of the chosen versions; the estimate is the F36 budget for the same plan; the report shows both and their ratio.
- Q: Which licences are listed? → A: Each model's catalogue licence text (unverified texts flagged as missing) and the audio licence flag.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Assemble the finished film from approved clips (Priority: P1)

Once the acts are reviewed, the owner assembles the film: for each bridge the approved version is taken, the clips are joined in film order with seam checks, and the result must cover the whole song. If any bridge is not approved, the owner gets the list of blockers instead of a film. A preview assembly can use the latest versions but is clearly labelled as a preview.

**Why this priority**: This is the film.

**Independent Test**: With synthetic runs where every bridge is approved, assembly writes a master whose frame count equals the planned total; with one unapproved bridge it refuses and names it; preview mode assembles anyway and labels the output.

**Acceptance Scenarios**:

1. **Given** all bridges approved, **When** assembled, **Then** a new master is written with frames = planned total and duration = planned length within one frame, and a record lists each chosen version.
2. **Given** a missing, unapproved, rejected or stale bridge, **When** assembled (not preview), **Then** it is refused with the list of blockers.
3. **Given** preview mode, **When** assembled, **Then** the latest versions are used, unapproved stages are listed, and the file and record are labelled preview.
4. **Given** clips whose boundary frames do not match, **When** assembled, **Then** it is refused (no frames are dropped).
5. **Given** licensed audio, **When** assembled, **Then** it is muxed and trimmed to the picture; unlicensed audio is refused.

---

### User Story 2 - Deliver the formats (Priority: P1)

The owner turns the master into the delivery formats (16:9 1080p, 9:16, 24 fps, licensed-audio) with the existing delivery presets, and the results are recorded with the master.

**Why this priority**: The gate requires at least two delivery formats.

**Independent Test**: Delivering a synthetic master with two presets records two verified outputs; a preview master is delivered with its preview label kept.

**Acceptance Scenarios**:

1. **Given** a master and presets, **When** delivered, **Then** each preset's result (verified or refused with a reason) is recorded; one failure does not stop the others.

---

### User Story 3 - Provenance report (Priority: P1)

The owner gets one report: storyboard and plan hashes; for every stage the chosen version (job id, media hash, seed, run); model and workflow identities; licences; owner approvals (concept bank, look, act approvals, review decisions); and measured GPU time from the job records next to the production estimate.

**Why this priority**: The acceptance gate requires a complete provenance report.

**Independent Test**: For synthetic runs, the report lists every stage with its version and seed, sums measured GPU seconds from job records, compares with the estimate, and lists missing items as incomplete.

**Acceptance Scenarios**:

1. **Given** an assembly record, **When** the report is built, **Then** every stage, model, workflow, licence and approval source is listed, with a completeness flag and the list of missing items.
2. **Given** job records with execution times, **When** reported, **Then** measured total, estimate and their ratio are shown.

---

### User Story 4 - Gate matrix F31–F40 (Priority: P2)

The owner sees, for each of F31–F40, its ledger status and whether it has evidence or an open gate, plus any owner-accepted blockers recorded for it.

**Why this priority**: Final acceptance needs every film-track gate evidenced or explicitly accepted.

**Independent Test**: For the real ledger, the matrix has ten rows; a ledger row with an open owner gate is shown as unresolved unless an accepted-blocker entry exists for it.

**Acceptance Scenarios**:

1. **Given** the ledger, **When** the matrix is built, **Then** it has rows F31–F40 with status, evidenced flag and open gate text.
2. **Given** an accepted-blocker file entry for a feature, **When** built, **Then** that feature shows the owner-accepted blocker and counts as resolved.

### Edge Cases

- A bridge approved on an older version (stale) is a blocker.
- Anchor stills are used for seam checks when available; otherwise only clip boundaries are compared (reported).
- An existing master or delivery output is never overwritten.
- Preview masters are never reported as acceptance evidence.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Assembly MUST choose, per bridge, the version approved in the review state; any missing, unapproved, rejected or stale bridge MUST block a non-preview assembly with a listed reason.
- **FR-002**: Preview assembly MUST use the latest versions, list unapproved stages, and label the output and record as preview.
- **FR-003**: Clips MUST be joined in film order with the existing seam-verified join; mismatching seams MUST refuse; the master MUST have frames = planned total and duration = planned length within one frame.
- **FR-004**: Optional audio MUST be local and marked licensed, muxed and trimmed to the picture.
- **FR-005**: Delivery MUST run the requested existing presets on the master and record each result; failures do not stop other presets.
- **FR-006**: The provenance report MUST list storyboard/plan hashes, per-stage chosen version (job id, media hash, seed, run), models and workflow identities, licences, owner approvals and measured vs estimated GPU seconds, and flag missing items.
- **FR-007**: The gate matrix MUST list F31–F40 with ledger status, evidence flag, open gate and any owner-accepted blocker.
- **FR-008**: Command-line access MUST provide film-assemble, film-deliver, film-provenance and film-gates with ASCII output and exit codes 0 ok, 1 attention needed, 2 refusal.

### Key Entities

- **Assembly record**: film, plan hash, preview flag, chosen versions, blockers, master path, frames, duration, seams, audio.
- **Delivery record**: master, presets, per-preset result.
- **Provenance report**: hashes, stages, models, workflows, licences, approvals, GPU measured/estimated, missing.
- **Gate row**: feature, status, evidenced, gate, accepted blocker.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A non-preview master is produced only when 100% of bridges are approved on their current version.
- **SC-002**: The master's picture covers the full song: frame count equals the planned total exactly.
- **SC-003**: The provenance report covers 100% of stages, with a measured-vs-estimated GPU comparison.
- **SC-004**: The gate matrix covers all ten film-track features.
- **SC-005**: Owner-approved full-song film in at least two delivery formats with a complete provenance report (acceptance gate after rendering).

## Assumptions

- Review state, decisions and versions come from F39; the planned total and song length from the frame-locked storyboard (F32/F37).
- Accepted blockers live in `configs/film/accepted-blockers.yaml` (owner decisions with dates), empty until the owner accepts one.
- Upscaling to 1080p uses the F26/F30 presets that exist; owner-installed upscale models stay an F26 owner gate.
- Fresh-root replay of an act is run by the owner with the existing replay tools after rendering (as MC-RUN-003).
