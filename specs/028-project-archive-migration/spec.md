# Feature Specification: Portable Project Archives, Migrations and Local Backup (F28)

**Feature Branch**: `028-project-archive-migration` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F28 Portable project archives, manifest migrations and local backup — offline slice: export a single-file project package (storyboard, style pack chain, profiles and workflow exports with checksums and registry metadata, model/licence report, optional run provenance with local paths redacted; media and music excluded unless the owner authorizes; weights always refused; checksum list); inspect a package without extracting it (checksums, schema version, unsafe names, archive-bomb limits, duplicate IDs, foreign absolute paths); versioned migrations including F20 run backups, with rollback on failure; import into a new sandboxed directory and report replay readiness (recompiled plan checksum matches, missing models). No inference, no downloads. CLI project-export, project-inspect, project-import."

## Clarifications

### Session 2026-11-24

Resolved autonomously from the ledger and owner rules:

- Q: Which profiles and workflows does a package include? → A: Exactly those the storyboard's compiled plan uses (production defaults unless the owner passes profile overrides), plus their workflow exports.
- Q: How are files laid out inside the package? → A: At their repository-relative paths (storyboard under `configs/sequences/`, packs under `configs/styles/`, profiles under `configs/profiles/`, exports under `workflows/`, run records under `run/<run name>/`, authorized media under `media/`), plus `project.json` and the checksum list at the top, so an imported folder can be re-planned as-is.
- Q: Which run files are included without media authorization? → A: Only the run record, plan and review decisions; job folders are not copied, but each stage's chosen output checksum is recorded. With media authorization the final movie, previews/contact sheets and each stage's output file are added under `media/`.
- Q: How are local paths redacted? → A: Paths inside the run folder or repository become relative names; any other absolute path becomes `<redacted-local-path>`; the number of redactions is recorded.
- Q: Which plan checksum is the replay reference? → A: The plan compiled from the storyboard at export time; when a run is included its own plan checksum is recorded too and the report says whether they agree.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Package a project to back it up or share it (Priority: P1)

The owner exports one storyboard as a single package file. It holds everything needed to understand and re-plan the project: the storyboard, its style packs, the exact workflow profiles and exports it uses with their checksums, and a report of every model it needs with licence and checksum (models themselves are never included). Optionally it also carries one run's provenance: its plan, decisions and the checksums of the chosen outputs, with the owner's local folder paths removed. Images, clips, movies, style reference images and music stay out unless the owner explicitly authorizes including them.

**Why this priority**: The project must survive a disk loss or move to a second machine without leaking private media by default.

**Independent Test**: Exporting the pilot storyboard yields one package whose checksum list covers every member, contains no media, music or model weights, and whose model report lists every model with licence and checksum.

**Acceptance Scenarios**:

1. **Given** a storyboard, **When** exported, **Then** the package contains the storyboard, style packs (if any), profiles and workflow exports, a project description and a checksum list covering every other member.
2. **Given** a run folder, **When** exported with that run, **Then** the package carries the plan, run record and review decisions, chosen output checksums, and no absolute local paths (each is replaced by a relative name or a redaction marker, and the count of redactions is reported).
3. **Given** no media authorization, **When** exported, **Then** no image, video or audio file is included and each excluded file is listed with its checksum.
4. **Given** media authorization, **When** exported, **Then** the run's anchors, clips and final movie (and, with a separate music authorization, the licensed audio file) are included and checksummed.
5. **Given** any file that is model weights, **When** export would include it, **Then** export is refused even with authorization.
6. **Given** an existing output path, **When** exporting, **Then** export is refused and nothing is overwritten.

---

### User Story 2 - Check a package is safe before opening it (Priority: P1)

Before anything is written, the owner inspects a package and learns whether it is intact and safe: every checksum matches, its format version is known, no member name could write outside the destination or onto special Windows names, it would not expand to an unreasonable size, and its contents have no duplicate anchor or stage identifiers or foreign absolute paths.

**Why this priority**: Packages may come from another machine; opening one must never write unsafely.

**Independent Test**: A set of deliberately corrupted or malicious packages are each rejected with the specific reason, while a good package passes, and nothing is extracted during inspection.

**Acceptance Scenarios**:

1. **Given** a good package, **When** inspected, **Then** it passes and reports its format version, contents summary and media included/excluded.
2. **Given** a member whose bytes changed, **When** inspected, **Then** it fails naming the member.
3. **Given** a newer, unknown format version, **When** inspected, **Then** it is refused as "from a newer MorphCurrent".
4. **Given** member names using `..`, absolute paths, drive letters, network paths, reserved device names (CON, NUL, COM1…), alternate data streams, or two names differing only by letter case, **When** inspected, **Then** each is refused.
5. **Given** a package exceeding the member-count, expanded-size or compression-ratio limits, **When** inspected, **Then** it is refused before decompressing everything.
6. **Given** a project description containing duplicate anchor or stage identifiers or an absolute local path, **When** inspected, **Then** it fails with that reason.

---

### User Story 3 - Open older packages (Priority: P2)

The owner can open packages made in an older format — including run backups made by the earlier release-backup tool — because they are upgraded step by step to the current format. If any step fails, the original stays exactly as it was and the failure is reported.

**Why this priority**: Archives must stay usable as the format evolves.

**Independent Test**: An F20 run-backup archive is recognised, upgraded in memory to the current format (exposing its run provenance), and a deliberately failing migration step leaves the input bytes unchanged.

**Acceptance Scenarios**:

1. **Given** an F20 run backup, **When** inspected or imported, **Then** it is reported as format 0 and upgraded to the current format.
2. **Given** a migration step that fails, **When** run, **Then** the error names the step and the original package and data are unchanged.

---

### User Story 4 - Restore safely and check it can be replayed (Priority: P2)

The owner imports a package into a new folder. Nothing outside that folder is written, an existing non-empty folder is never overwritten, and a half-finished import leaves nothing behind. Afterwards a readiness report says whether the storyboard re-plans to exactly the recorded plan, which workflows are ready and which models are missing on this machine (with the reminder that downloads need owner approval).

**Why this priority**: The acceptance gate is a safe restore on a second Windows directory that preserves the editing and provenance context.

**Independent Test**: Exporting the pilot storyboard with its run and importing into a fresh temporary folder recreates the files byte-for-byte; the recompiled plan checksum equals the recorded one; importing again into the same folder is refused.

**Acceptance Scenarios**:

1. **Given** a good package and a new folder, **When** imported, **Then** every file is restored with matching checksums and the readiness report shows the plan checksum matches.
2. **Given** an existing non-empty folder, **When** importing, **Then** it is refused and nothing is written.
3. **Given** a package that fails inspection, **When** importing, **Then** nothing is written.
4. **Given** a models folder lacking some models, **When** the readiness report runs with it, **Then** those models are listed as missing, needing owner approval to download.

### Edge Cases

- A storyboard without style pack or run: package still valid; provenance section absent.
- A run whose job folders are missing: outputs listed by recorded checksum only; media cannot be included for them (reported).
- A package that is not a zip file at all: rejected as corrupt.
- Duplicate member names inside the archive (possible in zip files): rejected.
- Music referenced by the storyboard but not authorized: listed as excluded with checksum when the file exists, "not found" otherwise.
- Import destination given as a file path: refused.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Export MUST write one package file, laid out at repository-relative paths (see Clarifications), containing a project description, the storyboard, its style pack chain files, the binding profiles and workflow exports the storyboard's plan uses, and a checksum list covering every other member; it MUST refuse an existing output path and write atomically.
- **FR-002**: The project description MUST record format version, creation time, tool version, storyboard name and checksum, plan checksum, profile identities (capability, workflow checksum, registry status), and a model report (folder, file, role, licence, checksum) stating models are not bundled.
- **FR-003**: When a run is given, export MUST include its plan, run record and review decisions, and record the chosen output checksums per stage; every absolute local path in included records MUST be replaced by a relative name or a redaction marker, with the redaction count reported.
- **FR-004**: Images, videos and audio MUST be excluded unless the owner gives a media authorization (and, for music, a separate music authorization); excluded files MUST be listed with checksum when available.
- **FR-005**: Export MUST refuse to include any model-weights file (by extension: safetensors, pth, pt, ckpt, bin, gguf, onnx) regardless of authorization.
- **FR-006**: Inspection MUST verify every checksum without extracting to disk and report pass/fail with specific reasons.
- **FR-007**: Inspection MUST refuse unknown future format versions.
- **FR-008**: Inspection MUST refuse unsafe member names: parent traversal, absolute, drive-letter or network paths, backslashes, reserved Windows device names, colon/alternate data streams, duplicates, and names equal ignoring case.
- **FR-009**: Inspection MUST refuse packages over limits: more than 10,000 members, more than 2 GiB expanded across non-media members or more than 64 GiB in total (limits depend on the actual members, never on what the package claims about itself), or any member with compression ratio above 200:1 (members over 1 MiB expanded).
- **FR-010**: Inspection MUST fail when the project description has duplicate anchor or stage identifiers or contains an absolute local path.
- **FR-011**: A versioned migration chain MUST upgrade older formats (format 0 = F20 run backup) to the current format in memory; a failing step MUST leave the input unchanged and name the failed step.
- **FR-012**: Import MUST run inspection first, refuse a non-empty or file destination, write only inside the destination via a staging folder renamed into place, and leave nothing on failure.
- **FR-013**: After import, a readiness report MUST recompile the storyboard plan from the restored files and compare it to the recorded plan checksum, list workflow registry statuses, and list missing models (when a models folder is given) as needing owner approval to download; no inference or download occurs.
- **FR-014**: Command-line access MUST provide project-export, project-inspect and project-import with ASCII-safe JSON output and exit codes 0 success, 2 refusal or unsafe package.

### Key Entities

- **Project package**: single file with project description, project files, optional provenance and media, and checksum list.
- **Project description**: format version, identities, model report, provenance summary, media inventory, redactions.
- **Migration step**: from-version, to-version, transformation; applied in memory in order.
- **Readiness report**: plan checksum match, registry statuses, missing models, restored file count.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Export → import of the pilot project restores 100% of members with matching checksums and an identical recompiled plan checksum.
- **SC-002**: 100% of the malicious/corrupt test packages (traversal, absolute, drive, network, reserved name, data stream, case collision, duplicate, bomb, bad checksum, future version, duplicate IDs, foreign path, not-a-zip) are refused with zero files written.
- **SC-003**: Packages exported without authorization contain zero image, video, audio or model-weights members.
- **SC-004**: An F20 run backup opens as a migrated current-format package; a failed migration leaves input bytes unchanged.
- **SC-005**: Exporting and inspecting the pilot project completes in under 5 seconds without media.

## Assumptions

- The package is a standard zip file so it can be opened by ordinary tools for manual review.
- Workflows and profiles are small repository files and are always included; their checksums let the receiver detect edits.
- Style reference images count as media (owner's private references).
- Real-data acceptance uses the existing pilot/organic-machines storyboard and an existing run folder on this machine, restored into a second temporary Windows directory.
