# Feature Specification: Image model and workflow onboarding

**Logical ledger ID**: F02 · **Feature Directory**: `specs/002-image-workflow-onboarding` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F02 Inspect and choose real local image models; obtain and validate T2I and reference-edit API exports and semantic profiles with explicit owner consent for missing model downloads"

## Gap analysis

| Concern | Exists | Gap |
|---|---|---|
| Graph validation vs `/object_info` | `validate_graph`, `validate_profile`, hash pin, assertions, cloud-node rejection (F01) | Profiles do not state which semantic roles a capability *needs*; an image profile missing `reference_image` or with a video output would pass |
| Output extraction | `extract_outputs` handles `images` key | Never exercised for `SaveImage`; no `kind: image` contract |
| Onboarding a new export | Manual reading of JSON | No tool lists an export's nodes, literal model files (installed or not), cloud nodes and role *candidates* for the person writing the binding profile |
| Model choice | `configs/models.yaml` placeholders; docs list "FLUX/Qwen candidates" | No factual candidate table; measured local state (F01): **no image weights installed** |
| Real exports `01_anchor_t2i.json`, `02_anchor_edit.json` | absent | Require owner approval to download weights, a manual render in ComfyUI and Save (API Format) — **owner-gated** |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Capability role contract (Priority: P1)
A binding profile that declares `capability: text_to_image` or `reference_edit` is rejected unless it binds the roles that capability requires and its output is an image.

**Independent Test**: profile fixtures over a graph built only from real captured node classes; missing role / wrong output kind → errors.

**Acceptance Scenarios**:
1. **Given** a `reference_edit` profile without `reference_image`, **When** validated, **Then** error names the missing role.
2. **Given** a `text_to_image` profile whose output kind is `video`, **Then** error.
3. **Given** the existing Wan profile, **Then** still `ok` (it binds `start_image`, `end_image`, `positive_prompt`, `seed`, `length`, video output).

### User Story 2 - Inspect a new API export before binding it (Priority: P1)
The engineer runs `workflow-inspect FILE` on a fresh ComfyUI Save (API Format) export and sees: every node (id, class), cloud flag, literal model filenames with installed/missing status, schema errors, and role candidates (text inputs, seeds, LoadImage inputs, image save nodes) — explicitly marked as candidates requiring human confirmation. Nothing is written or submitted.

**Independent Test**: run on a synthetic export assembled from real captured classes; assert reported missing model, cloud node and candidates; assert no file written.

**Acceptance Scenarios**:
1. **Given** an export referencing `qwen_image_fp8_e4m3fn.safetensors` that is not installed, **Then** the report lists it as `missing` and `ok: false`.
2. **Given** an export with `QwenImageEditApi`, **Then** reported as cloud and `ok: false`.
3. **Given** a UI-format (non-API) workflow file, **Then** a clear error says to use Save (API Format).

### User Story 3 - Factual model decision record for the owner (Priority: P2)
A document lists candidate local model sets with exact filenames/folders as declared by the ComfyUI templates installed on this machine, approximate VRAM fit, and the license items the owner must verify, plus the step-by-step manual export procedure. The owner's approval is recorded before any download.

**Independent Test**: docs test asserts the record states no download has occurred without approval and that the GPU/real-export gate is BLOCKED.

### Edge Cases
- Export contains subgraph-flattened node IDs like `"75:12"` → treated as opaque string IDs.
- Export references a LoRA that is not installed → listed as missing (LoRA is optional in the template but required if present in the graph).
- `SaveImageAdvanced` vs `SaveImage` output classes → both accepted if `output_node: true` in object_info.

## Requirements *(mandatory)*

- **FR-001**: `BindingProfile` with `capability` MUST be checked for required roles: `text_to_image` → `positive_prompt`, `seed`; `reference_edit` → `positive_prompt`, `seed`, `reference_image`; `wan_flf2v` → `start_image`, `end_image`, `positive_prompt`, `seed`, `length`.
- **FR-002**: Image capabilities MUST have ≥1 output with `kind: "image"`; `wan_flf2v` MUST have a `video` output.
- **FR-003**: `workflow-inspect` MUST be read-only (optional GET `/object_info` or a snapshot file), MUST reject non-API JSON, and MUST report nodes, cloud nodes, model literals with installed status, schema errors and role candidates labelled `candidate`.
- **FR-004**: No code path MUST download model weights or install custom nodes.
- **FR-005**: The model decision record MUST cite its source (local template file names) and mark licenses `owner to verify` rather than asserting them.
- **FR-006**: Real `01_anchor_t2i.json` / `02_anchor_edit.json` and their profiles MUST only be added from a real export after a successful local render; until then the GPU/export gate is BLOCKED.

### Key Entities
- **CapabilityContract**: capability → required roles, required output kind.
- **InspectionReport**: nodes, cloud nodes, model literals {node, input, value, installed}, errors, warnings, candidates {role_hint, node_id, input, class}.

## Success Criteria *(mandatory)*
- **SC-001**: 100% of missing-role / wrong-output fixtures are rejected; existing Wan profile still validates.
- **SC-002**: `workflow-inspect` identifies every not-installed model literal and every cloud node in fixtures (0 false negatives).
- **SC-003**: Zero network writes or file writes by `workflow-inspect` (request log + tmp dir check).
- **SC-004**: Owner can go from approval to a validated binding profile following the documented procedure without editing node IDs by guesswork.

## Assumptions
- Candidate families come from the ComfyUI workflow-templates package installed locally (0.11.111): Qwen-Image, Qwen-Image-Edit-2509/2511, Qwen-Image 2.1. Their licenses are not verified here.
- Download size/VRAM figures are approximate and labelled as such.
