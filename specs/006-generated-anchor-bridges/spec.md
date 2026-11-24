# Feature Specification: Generated anchors → Wan bridges

**Logical ledger ID**: F06 · **Feature Directory**: `specs/006-generated-anchor-bridges` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F06 Use the generated anchor images and the existing verified Wan 2.2 FLF2V bridge pipeline to render bridge videos automatically, never replacing the known-good bridge with guessed nodes"

## Gap analysis
| Exists | Gap |
|---|---|
| `bridge.py` + validated `03_wan22_flf2v.json`/profile (MC-FLF2V-003); F04 chain yields verified anchor jobs; F05 bridge tasks (frames, seed, prompt, size, fps) | Nothing connects them: bridge requests are hand-typed paths, which could be the example JPGs |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bridges from generated anchors (Priority: P1)
**Acceptance**: for each DAG bridge task the stage takes start/end images only from verified anchor jobs (SHA re-checked), patches the unchanged Wan profile with the task's prompt/seed/length/fps/size, and runs it via the existing bridge executor. Both bridges consume the identical B SHA. Rerun → zero new `/prompt`.

### User Story 2 - Safety (Priority: P1)
**Acceptance**: unverified/missing endpoint anchor → bridge not planned (blocked); Wan model missing in `/object_info` → bridge fails at validation (no other checkpoint substituted); busy queue → refused; without consent → `validated` only; the manual `bridge` CLI keeps working.

### Edge Cases
- Transition `candidates > 1` → F06 renders the primary candidate (task seed) only and records `candidates_pending`; ranking/rerender is F08.
- Lost `/prompt` response mid-bridge → inherited reconcile logic; no double submit.

## Requirements *(mandatory)*
- **FR-001**: Bridge start/end MUST be `anchor_image_path()` of verified anchor jobs.
- **FR-002**: Bridge requests MUST use the DAG task's `positive_prompt`, `seed`, `frames`→`length`, `fps`, `width`, `height` and the Wan profile path from the plan requirements.
- **FR-003**: Execution MUST reuse `plan_bridge` + `run_bridge` unchanged; one GPU job at a time; stop after the first non-verified bridge when submitting.
- **FR-004**: The stage MUST record per bridge: anchor job IDs and SHAs used, job dir, state; and assert that consecutive bridges share the same anchor SHA.

## Success Criteria *(mandatory)*
- **SC-001**: 100% of bridge inputs in tests are generated-anchor SHAs; B SHA identical across both bridges.
- **SC-002**: Rerun issues 0 `/prompt` requests.
- **SC-003**: All pre-existing bridge tests pass.

## Assumptions
GPU verification of a generated-A/B bridge requires F02–F04 GPU gates first (BLOCKED).
