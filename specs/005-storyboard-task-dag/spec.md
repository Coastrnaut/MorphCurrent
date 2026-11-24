# Feature Specification: Storyboard task DAG

**Logical ledger ID**: F05 · **Feature Directory**: `specs/005-storyboard-task-dag` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F05 Compile the YAML storyboard into a deterministic anchor dependency DAG and Wan bridge task plan with correct 4n+1 timing"

## Gap analysis
| Exists | Gap |
|---|---|
| `schema.py` strict storyboard (unique IDs, earlier references, linear transitions, `independent_t2i` since F04); `timeline.py` beats→4n+1 frames, derived seeds; `plan` CLI prints bridge timing | No task graph covering anchors **and** bridges **and** the final movie; anchor seeds can be `null` (silently unspecified); no workflow/profile requirements list; no plan hash; no Wan size constraints (multiple of 16) checked before ComfyUI |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dry-run task graph (Priority: P1)
The owner compiles `organic-machines.yaml` offline and sees 3 anchor tasks (orchid T2I, butterfly edit of orchid, phoenix edit of butterfly), 2 bridge tasks depending on both endpoint anchors (B shared, generated once), and a final task with the expected unique frame count, in topological order, plus the required workflows/profiles and whether each exists.
**Acceptance**: 6 tasks; `bridge:orchid->butterfly` and `bridge:butterfly->phoenix` both depend on `anchor:butterfly`; anchor B appears once; 65+65 frames → 129 unique; anchor span 8.0 s; nominal duration 129/16 s.

### User Story 2 - Deterministic, explicit seeds (Priority: P1)
**Acceptance**: compiling twice yields the same plan hash; every anchor and bridge has a concrete integer seed (explicit or derived from `master_seed` and the task id, recorded with `seed_source`); changing one prompt changes the hash.

### User Story 3 - Fail before any ComfyUI write (Priority: P1)
**Acceptance**: unsupported beat duration, width/height not multiple of 16, missing/cyclic/forward references, duplicate IDs → compile error; the compiler performs no network I/O.

### Edge Cases
- Required profile missing (no `anchor_t2i.binding.json` yet) → plan still compiles; requirement marked `missing` so the dry run reports BLOCKED stages.
- `independent_t2i` with continuity reference → dependency edge (ordering), `conditioned_on_parent: false`.
- Audio optional: `audio.file` absent → final task `audio: none`.

## Requirements *(mandatory)*
- **FR-001**: Compile MUST produce tasks `anchor:<id>`, `bridge:<from>-><to>`, `final:movie` with `depends_on`, in deterministic topological order.
- **FR-002**: Anchor tasks MUST carry method, positive prompt (anchor prompt + storyboard style), negative prompt, seed, seed_source, width, height, required capability.
- **FR-003**: Bridge tasks MUST carry frames (4n+1 from beats/BPM/fps), fps, seed, prompt, candidates, requested/actual seconds and timing error.
- **FR-004**: Final task MUST carry unique frame count `1+Σ(L−1)`, anchor span `Σ(L−1)/F`, nominal duration `unique/F`, delivery fps, audio file or none, and the rule "join only after verified shared endpoints".
- **FR-005**: The plan MUST list requirements (profiles per capability with exists/missing) and a SHA-256 plan hash over the canonical task content.
- **FR-006**: Width/height MUST be multiples of 16 (Wan `WanFirstLastFrameToVideo` step 16).
- **FR-007**: A new CLI `dag STORYBOARD` MUST print the plan with no network access; existing `validate`/`plan` unchanged.

## Success Criteria *(mandatory)*
- **SC-001**: organic-machines compiles to exactly 3 anchor + 2 bridge + 1 final tasks with 129 expected unique frames.
- **SC-002**: identical input → identical hash in 100% of repeated runs.
- **SC-003**: all invalid-input fixtures fail during compile.

## Assumptions
Default profile paths: `configs/profiles/anchor_t2i.binding.json`, `configs/profiles/anchor_edit.binding.json` (future F02 outputs), `configs/profiles/wan22_flf2v.binding.json`. Positive anchor prompt = anchor prompt + " " + style description (documented composition rule).
