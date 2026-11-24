# Feature Specification: Safe baseline, GPU concurrency gates, evidence and provenance

**Logical ledger ID**: F01 (`docs/SPECKIT_FEATURE_LEDGER.md`)

**Feature Directory**: `specs/001-safe-baseline-provenance` (created by `create_new_feature.py --number 1`; no git branch — owner works on `main`)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F01 Safe baseline, GPU concurrency gates, evidence and provenance for MorphCurrent"

## Gap analysis (what already exists vs. what F01 adds)

| Concern | Already implemented (regression baseline) | Gap F01 closes |
|---|---|---|
| Single-bridge GPU consent | `bridge --confirm-gpu`; refuses busy queue unless `--allow-busy-queue` | Consent and queue rules live inside `bridge.py` only; later multi-stage stages (anchors, pipeline) need one shared, testable gate |
| Local-only inference | Loopback-only `ComfyClient` URL check | Nothing stops a workflow from containing a ComfyUI **cloud API node** (344 of 1066 installed classes are `api_node: true`, e.g. `QwenImageEditApi`) — such a node would upload media to a remote service |
| Environment evidence | Ad-hoc snapshots in PROGRESS.md and `job.json` | No single read-only command that records HEAD, dirty state, queue, ComfyUI version, installed model choices and missing image capability; no `docs/ENVIRONMENT.md` |
| Model provenance | Model *filenames* recorded per job; `model_sha256: NOT RECORDED` | Inventory must state explicitly which models are installed and that SHA-256 is NOT MEASURED (hashing multi-GB weights is out of scope while GPU may be busy) |
| VRAM evidence | `peak_vram: NOT MEASURED` | Baseline report must label `vram_free` and `nvidia-smi` readings as snapshots, never peaks |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read-only baseline report (Priority: P1)

The owner (or an engineering session) runs one command and receives a factual, redacted report of the repository revision, working-tree cleanliness, local ComfyUI version, current queue occupancy, installed model files per loader, whether text-to-image / reference-edit capability is present, and the validation status of the existing Wan bridge workflow — without any job being queued or any model being loaded.

**Why this priority**: Every later feature starts from this fact base; a wrong assumption about installed models or an occupied GPU leads to fabricated success or a disrupted owner render.

**Independent Test**: Run the command against a fake ComfyUI that records every request; it must issue only GET requests and print the report.

**Acceptance Scenarios**:

1. **Given** ComfyUI is reachable and idle, **When** the baseline command runs, **Then** the report lists queue `running=0 pending=0`, ComfyUI version, model choices per loader, and image capability `blocked: no image checkpoint installed` when no image weights exist, and only GET requests were made.
2. **Given** ComfyUI is unreachable, **When** the baseline command runs with `--skip-comfy` or the server is down, **Then** the report still contains repository facts and marks ComfyUI as `unreachable` without failing silently.
3. **Given** a running prompt in the queue, **When** the command runs, **Then** the report shows the running prompt ID and `gpu_busy: true` and nothing is cancelled or added.

---

### User Story 2 - One shared GPU consent gate (Priority: P1)

Any stage that would queue GPU work (Wan bridge today, anchor images and full pipeline later) asks a single gate which allows submission only with explicit owner consent, an idle queue (unless explicitly overridden), and a workflow free of cloud API nodes.

**Why this priority**: Constitution II forbids unconsented or stacked GPU work and remote inference; it must be enforced in code, not only in documentation.

**Independent Test**: Unit tests call the gate with combinations of consent/queue/graph and assert allow/deny with reasons.

**Acceptance Scenarios**:

1. **Given** no consent, **When** a stage asks the gate, **Then** submission is denied with reason `consent`.
2. **Given** consent and a busy queue without override, **Then** denied with the count of queued jobs.
3. **Given** consent, idle queue and a graph containing a cloud API node, **Then** denied (and the same graph fails `workflow-check`).
4. **Given** consent and idle queue and a local-only graph, **Then** allowed; existing `bridge --confirm-gpu` behaviour and messages remain unchanged.

---

### User Story 3 - Recorded environment document (Priority: P2)

A committed `docs/ENVIRONMENT.md` contains only measured facts from this machine (versions, VRAM total, installed model filenames, queue state at measurement time), each labelled with date and method, plus explicit NOT MEASURED entries.

**Why this priority**: Gives later sessions a factual starting point; lower priority because the command (Story 1) regenerates it.

**Independent Test**: A docs test checks the file exists, labels peak VRAM and model SHA-256 as NOT MEASURED, and contains no user-profile paths or secrets.

**Acceptance Scenarios**:

1. **Given** the baseline report, **When** ENVIRONMENT.md is written, **Then** every number in it appears in a measured report and peak VRAM / checkpoint hashes are NOT MEASURED.

### Edge Cases

- ComfyUI returns malformed JSON for `/queue` → report marks the section as error, command exits non-zero only with `--strict`.
- `git` executable missing or not a repository → repository section reports `unknown`, no crash.
- `nvidia-smi` missing → GPU snapshot `unavailable`; its presence never implies peak measurement.
- Object-info entry lacks `api_node` but `python_module` starts with `comfy_api_nodes` → still treated as cloud.
- Graph references a class not installed → existing error path, not cloud classification.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The baseline command MUST perform only read-only requests (`GET /system_stats`, `/queue`, `/object_info`, optional `/history`) and MUST NOT upload, submit, interrupt, delete or free memory.
- **FR-002**: The report MUST include git HEAD SHA, branch, dirty-file count, package version, and ComfyUI version/argv/device VRAM total as reported.
- **FR-003**: The report MUST list installed model choices for each known loader input (checkpoint, diffusion model, text encoder, VAE, LoRA) and classify image capability: `text_to_image` and `reference_edit` are `available` only when a matching verified workflow profile exists and validates; otherwise `blocked` with reason.
- **FR-004**: The report MUST label `vram_free` and any `nvidia-smi` reading as `snapshot (not peak)`, and model checkpoint SHA-256 as `NOT MEASURED`.
- **FR-005**: A shared GPU gate MUST deny submission unless consent is explicit, MUST deny when the ComfyUI queue is non-empty unless an explicit override is passed, and MUST deny any graph containing a cloud API node.
- **FR-006**: Workflow validation (`validate_graph`, `workflow-check`) MUST report every cloud API node as an error.
- **FR-007**: Existing bridge behaviour (consent flag, busy-queue refusal message, resume, targeted cancel, verification) MUST be preserved; all pre-existing tests MUST pass unchanged.
- **FR-008**: The report MUST be emitted as JSON to stdout and optionally to a new file that is never overwritten.

### Key Entities

- **BaselineReport**: repository facts, ComfyUI facts, queue snapshot, model inventory, capability classification, workflow-profile validation results, measurement labels.
- **GateDecision**: allowed flag, list of denial reasons, queue counts, cloud nodes found.
- **ModelInventory**: loader role → installed filenames; hashes NOT MEASURED.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The baseline command completes in under 30 seconds against the local server and generates zero write requests (verified by request log in tests).
- **SC-002**: 100% of the four gate-denial conditions (no consent, busy queue, cloud node, combination) are covered by automated tests and deny.
- **SC-003**: All 83 pre-existing offline tests still pass.
- **SC-004**: `docs/ENVIRONMENT.md` contains zero unmeasured numeric claims and labels peak VRAM and checkpoint hashes NOT MEASURED.

## Assumptions

- The owner's ComfyUI is ComfyUI Portable 0.46.0 on `127.0.0.1:8188`; `api_node`/`python_module` metadata in `/object_info` identifies cloud nodes (verified 2026-11-24: 344 `api_node: true`, 363 classes from `comfy_api_nodes`).
- Hashing multi-GB checkpoints is deferred to F07 (opt-in, owner-scheduled).
- Model license verification is a documented owner decision in F02, not automated here.
