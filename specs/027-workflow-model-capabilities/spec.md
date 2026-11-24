# Feature Specification: Workflow and Model Capability Registry with Safe Upgrades (F27)

**Feature Branch**: `027-workflow-model-capabilities` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F27 Multi-workflow local model capability registry and safe upgrades — offline slice: read-only registry built from every binding profile (capability, workflow identity, input roles, output kind, frame constraints, required node classes, referenced model files by role with licence/hash from a checked-in catalogue) with a status per entry; compatibility preview between a current and a candidate profile with a verdict; owner-approved selection of a candidate profile per capability with history and rollback, production Qwen/Wan defaults preserved, never silently replaced; missing models/custom nodes reported as needing owner approval, nothing downloaded or installed, cloud API nodes refused. CLI registry, registry-diff, registry-select, registry-rollback. No GPU."

## Clarifications

### Session 2026-11-24

Resolved autonomously from the ledger and owner rules:

- Q: Which profile is the production default for each capability? → A: text_to_image = `configs/profiles/anchor_t2i.binding.json`, reference_edit = `configs/profiles/anchor_edit.binding.json`, wan_flf2v = `configs/profiles/wan22_flf2v.binding.json`; a capability with no production profile (upscale) has no default until the owner selects one.
- Q: Where is the selection record kept and do render commands read it? → A: `configs/registry/selection.json` (created only by an approved selection); in this slice render commands do not read it, so production behaviour is unchanged; a read-only "active profile" lookup is provided for later opt-in.
- Q: Should the upscale workflow (F26 T016) be a recognised capability now? → A: Yes; `upscale` is added as a capability whose contract requires an input-video role and a video output, so the owner's export can be registered as soon as it exists.
- Q: When does the registry command signal a problem through its exit code? → A: Only with a strict flag: exit 1 when any entry is not `ready`; otherwise exit 0 and the statuses are in the output.
- Q: Which preview changes count as compatible? → A: Changed model files, changed workflow checksum, changed notes and added optional roles are compatible; a role moved to another node, input or node type, a removed role not required by the capability, or a changed numeric constraint needs re-binding; a changed capability, changed output kind, or a missing capability-required role is incompatible.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See what every local workflow can do (Priority: P1)

The owner lists every installed workflow profile and sees, for each, what it produces (text-to-image, reference edit, first/last-frame video, upscale), which inputs it accepts, the frame constraints it imposes, which node types and model files it needs (with each model's role, licence and recorded checksum), and a single status telling whether it is ready to use or what is wrong.

**Why this priority**: Future models must be added without hard-coding node numbers into product logic; the owner needs one trustworthy inventory first.

**Independent Test**: Building the registry from the three production profiles with no ComfyUI connection lists three entries marked offline-unverified, each with its roles, constraints, models and catalogue licence; supplying a recorded node catalogue marks them ready.

**Acceptance Scenarios**:

1. **Given** the production profiles and a recorded node catalogue that contains every node type, **When** the registry is built, **Then** each entry is `ready` and lists capability, workflow path and checksum, roles, output kind, frame constraints, node types and models.
2. **Given** no node catalogue, **When** the registry is built, **Then** each structurally valid entry is `offline-unverified` (never `ready`).
3. **Given** a profile whose workflow file was edited after pinning, **When** the registry is built, **Then** that entry is `stale-hash`.
4. **Given** a node catalogue missing one of a workflow's node types, **When** the registry is built, **Then** that entry is `missing-node` and names the type as needing owner approval to install.
5. **Given** a models folder lacking a referenced model file, **When** the registry is built with that folder, **Then** the entry is `missing-model`, names the file, and says a download needs owner approval.
6. **Given** a workflow containing a cloud API node, **When** the registry is built, **Then** the entry is `cloud-node` and can never be selected.
7. **Given** a profile that declares a capability but lacks one of its required roles or output kind, **When** the registry is built, **Then** the entry is `contract-error`.

---

### User Story 2 - Preview whether a new workflow version is compatible (Priority: P1)

Before adopting a new or re-exported workflow, the owner compares it with the current one and sees exactly what changed: roles added or removed, node types changed behind a role, input constraints changed (for example frame-count step or size step), output kind changed, models changed, workflow checksum changed. A verdict says compatible, needs re-binding, or incompatible.

**Why this priority**: Silent graph changes broke reproducibility before; changes must be visible before they are used.

**Independent Test**: Comparing two versioned test profiles yields the expected differences and verdicts for each change type.

**Acceptance Scenarios**:

1. **Given** two profiles that differ only in model files or workflow checksum, **When** compared, **Then** the verdict is `compatible` and the changes are listed.
2. **Given** a candidate whose role moved to a different node or node type, or whose frame/size constraints changed, **When** compared, **Then** the verdict is `needs-rebinding`.
3. **Given** a candidate with a different capability, a different output kind, or missing a role the capability requires, **When** compared, **Then** the verdict is `incompatible`.

---

### User Story 3 - Adopt or back out a workflow safely (Priority: P2)

The owner makes a candidate profile the active one for a capability only by giving explicit approval, and only when it validates cleanly (ready status, compatible or re-bound preview not incompatible). Each selection is recorded with time, previous and new profile and their checksums. The owner can roll back to the previous selection at any time. With no selection recorded, the production Qwen/Wan profiles stay the defaults.

**Why this priority**: Upgrades must be reversible and never replace production defaults behind the owner's back.

**Independent Test**: In a temporary folder, selecting without approval is refused; selecting with approval records history and changes the active profile; rolling back restores the previous one; an incompatible, cloud or stale candidate is refused even with approval.

**Acceptance Scenarios**:

1. **Given** no selection record, **When** the active profile for a capability is asked for, **Then** the production default is returned.
2. **Given** a ready candidate, **When** selected without the approval flag, **Then** it is refused and nothing changes.
3. **Given** a ready candidate and the approval flag, **When** selected, **Then** it becomes active and a history entry records both profiles and checksums.
4. **Given** one or more selections, **When** rolled back, **Then** the previous profile (or the production default) is active again and the rollback is itself recorded.
5. **Given** a candidate that is not ready, or whose preview verdict is incompatible, **When** selected with approval, **Then** it is refused with the reason.

### Edge Cases

- A profile file that does not parse is listed with status `contract-error` and the parse message, not a crash.
- A workflow file that is missing is listed as `contract-error` ("workflow not found").
- Several problems at once: the status shows the most severe (cloud-node > contract-error > stale-hash > missing-node > missing-model > offline-unverified > ready) and all problems are listed.
- A model file referenced by a workflow but absent from the catalogue is shown with licence and checksum "NOT RECORDED".
- Rollback with no history is refused with a clear message.
- A candidate whose model files are absent locally cannot be selected; the message says the owner must approve any download.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST build a registry entry for every binding profile in the profiles folder, including capability, workflow path and recorded and actual checksums, input roles, output kind, required node types, referenced model files with role, and frame/size constraints.
- **FR-002**: Model roles MUST be derived from the loader input that references the file (diffusion, text encoder, VAE, checkpoint, LoRA, upscaler, CLIP vision) and each model MUST be joined to a checked-in model catalogue giving licence, source and checksum, or "NOT RECORDED".
- **FR-003**: Frame and size constraints MUST be read from the node catalogue when supplied (minimum, maximum, step for bound numeric roles) and, for first/last-frame video, the length rule 4n+1 MUST be reported.
- **FR-004**: Each entry MUST receive one status from: ready, offline-unverified, stale-hash, missing-node, missing-model, contract-error, cloud-node, using the severity order in Edge Cases, plus a list of every problem found.
- **FR-005**: Missing node types and missing model files MUST be reported as requiring owner approval to install or download; the system MUST NOT download, install or modify any model, node or ComfyUI file.
- **FR-006**: The system MUST compare a current and a candidate profile and list added roles, removed roles, roles whose node or node type changed, constraint changes, output-kind change, capability change, model changes and checksum change, with verdict compatible / needs-rebinding / incompatible per US2 rules.
- **FR-007**: The active profile for a capability MUST default to the production profile listed in Clarifications when no selection is recorded; a capability without a production profile has no active profile until selected.
- **FR-008**: Selecting a candidate MUST require an explicit owner approval flag, a `ready` registry status (which requires a supplied node catalogue) and a preview verdict that is not incompatible; otherwise it MUST be refused and nothing written.
- **FR-009**: Every selection and rollback MUST be appended to a selection history with UTC time, capability, previous and new profile paths and workflow checksums, and the approval note; history MUST never be rewritten.
- **FR-010**: Rollback MUST restore the previous active profile for that capability (or the production default) and MUST be refused when there is nothing to roll back.
- **FR-011**: Cloud API nodes MUST make an entry unselectable.
- **FR-012**: Production render behaviour MUST be unchanged: existing commands keep their current default profiles unless the owner opts in to the selection record.
- **FR-013**: Command-line access MUST provide: registry listing (with optional node catalogue file or read-only live query, and optional models folder), profile comparison, selection with approval, and rollback; output MUST be ASCII-safe JSON and exit codes MUST distinguish success (0), refusal (2) and problems found (1 for a registry with non-ready entries only when the strict flag is given).
- **FR-014**: The capability contracts MUST include `upscale` (input-video role, video output) alongside text-to-image, reference edit and first/last-frame video.

### Key Entities

- **Capability entry**: one profile's registry record — profile name and path, capability, workflow path, recorded/actual checksum, roles, output kinds, node types, models, constraints, status, problems.
- **Model reference**: folder, file name, role, licence, source, catalogue checksum, present locally (yes/no/unknown).
- **Compatibility preview**: current and candidate identities, list of changes by type, verdict.
- **Selection record**: per-capability active profile plus an append-only history of selections and rollbacks.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The registry for the three production profiles builds in under 2 seconds offline and shows 100% of their roles, node types and model files.
- **SC-002**: With the recorded node catalogues, all three production profiles report `ready`; every one of the seven statuses is produced by at least one test case.
- **SC-003**: Every change type in US2 is detected in tests, with the documented verdict, in 100% of cases.
- **SC-004**: Zero downloads, installs, or writes outside the selection record occur in any test or command (verified by tests).
- **SC-005**: Select → rollback returns the active profile to its prior value in 100% of tested sequences, and the production defaults are unchanged when no selection exists.

## Assumptions

- The checked-in model catalogue is a small data file built from `docs/MODELS.md` (the human-readable record stays authoritative for people).
- The node catalogue is the ComfyUI node schema, read from a recorded file or a read-only live query on the loopback address; without it no entry can be `ready`.
- The selection record lives in the repository's configuration folder and is opt-in; render commands do not read it unless asked (FR-012).
- No alternative owner-installed video/image workflow exists yet; real-data acceptance uses the three production profiles (OFFLINE-PASS per the ledger), and the F26 upscale workflow joins when exported.
