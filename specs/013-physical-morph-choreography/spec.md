# Feature Specification: Physical correspondence and prompt orchestration

**Logical ledger ID**: F13 · **Feature Directory**: `specs/013-physical-morph-choreography` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F13 Physical correspondence and prompt orchestration: structured transformation plans compiled into deterministic positive/negative bridge prompts with fixed-seed A/B variants"

## Gap analysis
| Exists | Gap |
|---|---|
| Transition `prompt` (free prose), `motion`/`mode` labels that never reach the model; bridge negative prompt = whatever the Wan export contains | No structured way to say *what becomes what*, in which order, with which camera; no bridge negatives from the storyboard; no reviewable prompt preview; no controlled prompt-only A/B plan. MC-RUN-001's B→C used a "rising orbit" prose cue that likely caused the swing-away; MC-RUN-002 fixed it by hand |

## User Scenarios & Testing *(mandatory)*
### US1 - Structured choreography compiles to prompts (P1)
A transition may add `choreography`: correspondences (source → target parts), ordered phases (≤ 5), camera (`static`, `slow_push`, `slow_pull`, `orbit_left`, `orbit_right`, `rising`), `keep_centered`, `keep_scale`, extra negatives. It compiles deterministically into a positive prompt (base prose + correspondences + phases + camera/framing + continuity clause) and a negative prompt (continuity defaults + user negatives).
**Acceptance**: golden fixture text for the butterfly→phoenix choreography; same input → same text; whitespace/control characters normalised; > 1,500 characters → error before any ComfyUI call.

### US2 - Bridge uses compiled prompts; old storyboards unchanged (P1)
DAG bridge tasks carry the compiled positive and negative when choreography is present; the Wan request patches both. Storyboards without choreography produce **exactly the same plan hash as before** (MC-RUN reproducibility preserved).

### US3 - Preview and controlled A/B variants (P2)
`prompt-preview STORYBOARD` shows each bridge's compiled prompts. `--variants` lists a prompt-only A/B plan: baseline (prose only) vs compiled, same seed/length/size/model — labelled as a plan, nothing rendered.

### Edge Cases
Unknown camera value → schema error. Empty correspondences with phases only → allowed. A user negative that duplicates a default → deduplicated. Choreography never claims to guarantee motion (stated in preview note).

## Requirements *(mandatory)*
- **FR-001** Schema `Transition.choreography` optional; strict fields as above.
- **FR-002** `compile_bridge_prompts(transition) -> (positive, negative)` pure and deterministic.
- **FR-003** DAG: compiled prompts only when choreography present; bridge task gains `negative_prompt`; plan hash unchanged otherwise.
- **FR-004** Pipeline passes `negative_prompt` to the Wan bridge (bound role exists in the profile).
- **FR-005** Length cap 1,500 chars per prompt; control characters removed.
- **FR-006** `prompt-preview` CLI, offline; variants are labelled plans (GPU run via F29/owner approval).

## Success Criteria *(mandatory)*
- **SC-001** Golden prompts stable; plan hash of `organic-machines.yaml` unchanged.
- **SC-002** A choreographed bridge's Wan graph contains the compiled negative (verified via fake ComfyUI).
- **SC-003** GPU A/B (fixed seed) and the owner's judgement of collapse/flare improvement: BLOCKED until an approved run.

## Assumptions
Wan responds to text only statistically; compiled prompts are hypotheses tested by F13/F29 experiments.
