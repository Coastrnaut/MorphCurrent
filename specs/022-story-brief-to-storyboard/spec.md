# Feature Specification: Creative brief to editable storyboard

**Logical ledger ID**: F22 · **Feature Directory**: `specs/022-story-brief-to-storyboard` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F22 Creative brief to editable storyboard: deterministic shot planner that turns an ordered subject list, duration, tempo and style pack into a schema-valid storyboard with preview, optional local LLM disabled by default"

## Gap analysis
| Exists | Gap |
|---|---|
| Hand-written storyboards; DAG dry run; style packs (F21); choreography (F13); ladders (F14); estimates (F11) | Writing an 8- or 76-scene storyboard by hand is error-prone; no way to go from a short brief to a valid plan with duration/GPU preview |

## User Scenarios & Testing *(mandatory)*
### US1 - Brief → storyboard (P1)
A brief YAML lists: `title`, ordered `scenes` (each `subject`, optional `details`, optional `morph` hint describing how it turns into the next), `duration_s` (target), `bpm` (default 120), `style_pack`, optional `render` size/fps, optional `seed`. The planner writes a storyboard: first anchor `text_to_image` from the subject (+ details), the rest `reference_edit` ("Transform the subject into …"), transitions with F13 choreography (static camera, keep centered/scale, correspondence from the `morph` hint), beats per transition chosen so the total matches `duration_s` with valid 4n+1 lengths, seeds explicit and derived.
**Acceptance**: an 8-scene brief → 8 anchors, 7 transitions, schema-valid, dry-run plan compiles with 7 bridges; total anchor span within one bridge interval of the target; identical brief → identical YAML.

### US2 - Preview, edits and safety (P1)
`brief-plan BRIEF --out STORYBOARD.yaml` prints a preview (scene list, per-transition seconds and frames, total, estimated GPU time from F11 history, blocked profiles) and refuses to overwrite. Unsafe/odd input (empty subject, > 200 chars, control characters, path-like title) fails with clear messages; the output filename is chosen by the user, never derived from brief text. The brief never names models or nodes (none are generated).

### US3 - Optional local LLM (P3)
Documented as a disabled extension point (`--llm` refused unless a local, owner-enabled endpoint is configured — not implemented in this slice).

### Edge Cases
Duration too short for the number of scenes (each bridge ≥ 5 frames) → error with the minimum duration; too long for `max_bridge_frames` → error suggesting more scenes or ladders (F14).

## Requirements *(mandatory)*
- **FR-001** Deterministic templating; no network; no GPU.
- **FR-002** Beats per transition = equal share of `duration_s`, mapped through `frame_count_for_beats`; report residual.
- **FR-003** Output passes `Storyboard` validation and `compile_plan`.
- **FR-004** Text fields cleaned (control chars removed, whitespace collapsed, length-capped).

## Success Criteria *(mandatory)*
- **SC-001** Eight-scene golden brief → valid plan, 7 bridges, duration within tolerance.
- **SC-002** Determinism and refusals tested.

## Assumptions
Prompts are templates for human editing; the owner reviews before rendering.
