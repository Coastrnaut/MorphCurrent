# Feature Specification: Production Acceptance and Reproducible Replay (F20)

**Feature Branch**: `020-release-reproducible-pipeline` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F20 Production acceptance and reproducible replay — offline slice: replay comparison of two runs (image/video bytes, optional decoded frames, documented variance) with an owner-gated fresh-root replay helper; source/licence/hash audit (workflow and profile pins, music licence provenance, nothing forbidden tracked, recorded model hashes listed without re-hashing weights during GPU work); run backup and restore with a SHA-256 manifest, verified restore, no overwrite; acceptance matrix of F01–F20 from the ledger. Release tagging needs owner approval. No GPU in tests."

## Clarifications

### Session 2026-11-24

Resolved autonomously from the constitution, CLAUDE.md and the existing music provenance convention:

- Q: What counts as licence provenance for a tracked media file? → A: a sibling JSON with the same stem (e.g. `x.opus` + `x.json`) that names a licence and a source; the audio/image/video extensions checked are png, jpg, jpeg, webp, gif, mp4, webm, mov, wav, flac, mp3, opus, ogg.
- Q: Which tracked files are forbidden? → A: weights (`.safetensors`, `.ckpt`, `.gguf`, `.pt`, `.pth`, `.bin`, `.onnx`), anything under `outputs/` or `library/`, run records (`manifest.json` inside a `run-*` folder), and secret-like names (`.env*`, `*.pem`, `*.key`, `*credentials*`, `*secret*`, `*token*`).
- Q: When are decoded frames "equivalent"? → A: the verdict stays byte-based; frame comparison is informational, labelling a differing clip "visually equivalent" when frame counts match and the largest mean absolute per-frame difference is ≤ 1.0 on an 8-bit scale.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prove a replay reproduces a run (Priority: P1)

The owner renders the same storyboard into a fresh output folder and asks whether it reproduced the original run. The comparison lists every stage (each anchor image, each bridge clip, the final movie) as identical, different or missing on either side. For different videos it can also compare decoded frames, reporting the largest per-frame difference so near-identical results are distinguishable from real changes.

**Why this priority**: Fresh-root reproducibility (MC-RUN-003) is the core trust claim of the product; it must be checkable by a command, not by hand.

**Independent Test**: Two synthetic runs with identical content compare as all-identical; changing one clip's bytes reports exactly that stage as different; deleting one reports it missing.

**Acceptance Scenarios**:

1. **Given** two runs of the same plan with byte-identical outputs, **When** compared, **Then** every stage is reported identical and the overall verdict is "reproduced".
2. **Given** one bridge clip differs, **When** compared, **Then** only that stage is "different" with both hashes shown, and the verdict is "differs".
3. **Given** runs of different plans, **When** compared, **Then** the report says the plans differ and compares only stages present in both.
4. **Given** the replay helper without GPU consent, **When** run, **Then** it only validates and makes no generation request.

---

### User Story 2 - Audit sources, licences and hashes before a release (Priority: P1)

Before any release, the owner runs an audit that checks the repository: every workflow export matches the hash pinned by its binding profile; every committed media file has licence provenance; no model weights, generated media, run records or secrets are tracked; and the model hashes recorded in the models document are listed. The audit never re-hashes large model files.

**Why this priority**: Constitution principles I, III, IV and VII require evidence that sources and licences are clean before calling anything a release.

**Independent Test**: The current repository audits clean; a synthetic repository with a tampered workflow, an unlicensed media file and a tracked weight file reports each problem.

**Acceptance Scenarios**:

1. **Given** the current repository, **When** audited, **Then** zero errors are reported.
2. **Given** a workflow edited after its profile was pinned, **When** audited, **Then** the mismatch is an error naming the profile.
3. **Given** a tracked media file without licence provenance, or a tracked weight/movie/secret-like file, **When** audited, **Then** each is an error.

---

### User Story 3 - Back up and restore a run (Priority: P2)

The owner archives a finished run — its record, reviews, plan and every job folder it references — into one archive with a checksum list, and can later restore it into an empty location. Restore verifies every file and refuses to overwrite anything.

**Why this priority**: Long renders represent many GPU-hours; losing them is costly.

**Independent Test**: Back up a synthetic run, restore it elsewhere and compare: all files identical; a corrupted archive member is refused; restoring over existing data is refused.

**Acceptance Scenarios**:

1. **Given** a run, **When** backed up and restored into an empty folder, **Then** the restored run compares identical to the original.
2. **Given** an archive member whose bytes changed, **When** restored, **Then** restore stops with that file named and leaves nothing partially written.
3. **Given** a destination that already contains the run, **When** restoring, **Then** it is refused.

---

### User Story 4 - Acceptance matrix (Priority: P2)

The owner gets a matrix of F01–F20 (and optionally all forty) features with their recorded status and whether each is evidenced or still has an unresolved owner/GPU gate, so a release decision can be made.

**Independent Test**: The matrix lists 20 rows for F01–F20 with a status each, and counts unresolved gates.

**Acceptance Scenarios**:

1. **Given** the ledger, **When** the matrix is produced, **Then** each of F01–F20 appears exactly once with its status and a release-ready verdict that is "no" while any gate is unresolved.

---

### Edge Cases

- A run references a job folder that no longer exists: backup reports it missing and refuses unless explicitly allowed to skip.
- Archive paths containing `..` or absolute paths: refused on restore.
- Comparison of runs whose stages are pending (not verified): reported "not verified", not "different".
- Audit while a GPU job runs: audit is read-only and never hashes model weights.
- Release tagging is never performed by these tools; it requires owner approval.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST compare two runs stage by stage by content hash and report identical / different / missing / not verified per stage plus an overall verdict.
- **FR-002**: Comparison MUST optionally compare decoded frames of differing videos, reporting frame counts and the largest mean absolute per-frame difference; ≤ 1.0 (8-bit) with equal frame counts is labelled "visually equivalent" (informational; the verdict stays byte-based).
- **FR-003**: A replay helper MUST render a storyboard into a fresh, empty output folder only with explicit GPU consent and then compare against a named reference run; without consent it only validates.
- **FR-004**: The audit MUST verify workflow-to-profile hash pins, licence provenance for tracked media (sibling same-stem JSON naming licence and source), absence of tracked weights/`outputs/`/`library/`/run records/secret-like files (lists in Clarifications), and list recorded model hashes — without hashing model weights.
- **FR-005**: Backup MUST archive a run with its referenced job folders and a SHA-256 checksum list; restore MUST verify every checksum, reject unsafe paths and refuse to overwrite.
- **FR-006**: The acceptance matrix MUST list F01–F20 (optionally F01–F40) with status, evidenced/unresolved and a release-ready verdict.
- **FR-007**: None of these tools may tag a release, contact the generation service (except the consented replay) or upload anything.

### Key Entities

- **Run comparison**: two runs, per-stage verdicts, overall verdict, optional frame differences.
- **Audit report**: checks with pass/error/warning and evidence.
- **Run archive**: archive file plus checksum list; restored run.
- **Acceptance row**: feature id, status text, evidenced/unresolved.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Comparing the MC-RUN-002 run with its fresh-root reproduction MC-RUN-003 (and the BENCH-001 832×480 runs) reports every stage identical; comparing MC-RUN-001 (different phoenix plan) reports exactly the changed stages.
- **SC-002**: The current repository audit reports 0 errors; each seeded defect in tests is detected (100%).
- **SC-003**: Backup → restore round trip reproduces 100% of files byte-identically; any single corrupted member is detected.
- **SC-004**: Zero generation requests are made in tests.

## Assumptions

- Fresh-root GPU replay of a longer sequence is an owner-approved bounded batch, not part of tests.
- Archives are local files; nothing is uploaded.
- Frame comparison uses the existing local video decoding already used by quality checks.
- Packaging/installer and CI smoke harness are deferred to F30 (delivery presets and release audit).
