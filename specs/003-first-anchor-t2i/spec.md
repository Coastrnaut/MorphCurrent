# Feature Specification: First anchor via local text-to-image

**Logical ledger ID**: F03 · **Feature Directory**: `specs/003-first-anchor-t2i` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F03 Generate the first anchor A through local ComfyUI text-to-image automatically, verify the image and write an immutable manifest"

## Gap analysis

| Concern | Exists | Gap |
|---|---|---|
| Resumable ComfyUI job state machine | `bridge.py`: upload → validate → submit (client prompt_id persisted first) → reconcile → await → download (`.part`) → verify; immutable content-addressed job dir | Hard-wired to Wan video: two image roles, ffprobe verification, `kind: wan22_flf2v_bridge` |
| Consent / queue / cloud gate | `gates.check_gpu_gate` (F01) | — |
| Image profile contract | F02 contracts; synthetic Qwen-shaped graphs | No executor for `text_to_image` profiles |
| Image verification | none | PNG/JPEG integrity and dimensions, exactly one output image, SHA-256 |
| CLI | `bridge` | No `anchor` command |
| Real T2I export/profile | **absent** (F02 BLOCKED) | GPU gate stays BLOCKED |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate anchor A from a prompt (Priority: P1)
Given a verified `text_to_image` binding profile, the owner runs one command with prompt, negative prompt, seed and size; without `--confirm-gpu` it validates and stops; with it, one ComfyUI job runs and an immutable anchor directory holds the PNG plus a manifest (prompt, negative, seed, size, graph SHA, profile, model filenames, image SHA-256, dimensions, prompt ID, timings).

**Independent Test**: fake ComfyUI returning a generated PNG.

**Acceptance Scenarios**:
1. **Given** no `--confirm-gpu`, **When** run, **Then** state `validated`, zero `/prompt` requests.
2. **Given** consent and idle queue, **Then** state `verified`, image SHA-256 and dimensions recorded, dimensions equal requested width/height.
3. **Given** the identical request again, **Then** the verified anchor is reused with zero HTTP calls.

### User Story 2 - Fail closed on bad states (Priority: P1)
**Acceptance Scenarios**:
1. Model missing in `/object_info` → `failed` at validation, nothing submitted.
2. Workflow hash drift / invalid graph → plan refuses.
3. Output is not an image / truncated PNG / wrong dimensions / zero or multiple images → `failed` with a specific error.
4. Lost `/prompt` response → resume confirms via `/history` and never double-submits.
5. Execution error in `/history` → `failed`; `--retry` restarts cleanly.
6. Downloaded file later tampered → refuses to overwrite/accept a different SHA.
7. Busy queue → refused unless explicitly overridden.

### Edge Cases
- Profile has no `width`/`height` roles → size taken from graph; verification compares to the graph's values when the role exists, else records measured size only.
- `reference_image` supplied for a T2I request → rejected (F04 handles edits).
- Request with method `independent_t2i` → allowed on a T2I profile, recorded as such (F04 consumer).

## Requirements *(mandatory)*
- **FR-001**: An anchor request MUST name the profile, positive prompt, explicit seed (no silent randomization), optional negative prompt and size; profile capability MUST be `text_to_image`.
- **FR-002**: The job ID MUST be a content hash of patched graph, profile workflow hash, inputs, reference bytes (none for T2I) and code version; identical requests reuse the job.
- **FR-003**: Submission MUST pass the shared GPU gate (consent, idle queue, no cloud nodes).
- **FR-004**: Exactly one image output MUST be downloaded via `.part` + rename and verified as a structurally valid PNG or JPEG with recorded dimensions and SHA-256.
- **FR-005**: The manifest MUST record method (`text_to_image` or `independent_t2i`), prompts, seed, size, profile, workflow SHA, patched graph SHA, model filenames, `model_sha256: NOT RECORDED`, prompt ID, timings, image record.
- **FR-006**: Existing `bridge` behaviour and tests MUST be unchanged.

### Key Entities
AnchorRequest, AnchorPlan, Anchor job record (`anchor.json` = shared job schema + `image`).

## Success Criteria *(mandatory)*
- **SC-001**: All 7 failure scenarios of US2 covered by tests and end in a non-verified state without duplicate submission.
- **SC-002**: Re-running a verified request makes zero network calls.
- **SC-003**: Pre-existing 113 tests pass.
- **SC-004**: With an approved model, one command produces a verified anchor in one GPU job (GPU gate — BLOCKED until F02 export exists).

## Assumptions
- Real profile will bind at least `positive_prompt`, `seed`; `negative_prompt`, `width`, `height`, `filename_prefix` when the export exposes them.
- Pillow is not a dependency; integrity checks use the standard library.
