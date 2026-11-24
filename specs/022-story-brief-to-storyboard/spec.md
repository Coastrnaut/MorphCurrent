# Feature Specification: Creative brief to editable storyboard

**Logical ledger ID**: F22 · **Feature Directory**: `specs/022-story-brief-to-storyboard` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F22 Creative brief to editable storyboard: deterministic shot planner that turns an ordered subject list, duration, tempo and style pack into a schema-valid storyboard with preview" — amended 2026-11-24 by the owner: no local LLM drafting; Claude Desktop sessions pre-draft all sequences and prompts

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

### US3 - Claude Desktop sessions pre-draft sequences and prompts (P1)
All creative drafting — briefs (`configs/briefs/*.yaml`), storyboards (`configs/sequences/*.yaml`), anchor prompts, morph hints and choreography — is pre-drafted as plain text in Claude Desktop sessions following `docs/DRAFTING.md`. There is **no local LLM** and no model runs for drafting inside MorphCurrent. Claude sessions never receive generated media; images and video stay local. Every draft is then checked locally by `draft-check FILE` (brief or storyboard): schema validity, a compiled plan with bridge lengths, no model/checkpoint/LoRA/node/workflow names or URLs in creative text, reference-edit lineage, choreography coverage and prompt length. Errors block; warnings are advisory. A brief may record `drafted_by` (e.g. "Claude Desktop session 2026-11-24"), carried into the generated storyboard header. The owner reviews and approves before any render.
**Acceptance**: the pilot brief and both sample storyboards pass `draft-check`; a draft naming a checkpoint, LoRA, ComfyUI node or URL fails with the offending field named; `brief-plan` has no `--llm` option.

### Edge Cases
Duration too short for the number of scenes (each bridge ≥ 5 frames) → error with the minimum duration; too long for `max_bridge_frames` → error suggesting more scenes or ladders (F14).

## Requirements *(mandatory)*
- **FR-001** Deterministic templating; no network; no GPU.
- **FR-002** Beats per transition = equal share of `duration_s`, mapped through `frame_count_for_beats`; report residual.
- **FR-003** Output passes `Storyboard` validation and `compile_plan`.
- **FR-004** Text fields cleaned (control chars removed, whitespace collapsed, length-capped).
- **FR-005** `draft-check FILE` validates Claude-drafted briefs and storyboards locally (errors: schema, plan compile, model/node/workflow names, URLs; warnings: independent T2I, missing correspondences, prompts > 600 chars); exit 0 when there are no errors (warnings allowed), 3 when any error.
- **FR-006** Optional `Brief.drafted_by` (≤ 120 chars) written to the generated storyboard header; never part of the plan hash.

## Success Criteria *(mandatory)*
- **SC-001** Eight-scene golden brief → valid plan, 7 bridges, duration within tolerance.
- **SC-002** Determinism and refusals tested.

## Assumptions
Drafting reasoning may be cloud-hosted (Claude Desktop); media execution stays local (CLAUDE.md guardrail). No local LLM will be installed for drafting (owner decision 2026-11-24).
Prompts are templates for human editing; the owner reviews before rendering.
