# Implementation Plan: Camera Moves and Framing Consistency (F23)

**Branch**: `023-camera-framing-keyframes` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/023-camera-framing-keyframes/spec.md`

## Summary

Schema: optional `Transition.camera` (`move`, `amount` 0–0.5, `control` prompt|graph),
`Anchor.framing` (centre ± tolerance, size range) and `RenderConfig.delivery_crops` ("16:9", "9:16").
`prompt_compiler` appends a deterministic camera clause; the DAG records
`camera: {move, amount, clause, label: "prompt-only approximation"}` on bridge tasks only when set
(plan hashes otherwise unchanged). `control: graph` is refused by checking the pinned Wan workflow for
any camera-control node (none exist). New `camera.py`: `camera_clause`, `satisfiability` (F12 geometry,
thresholds from Clarifications), `framing_check`, `crop_check`, `camera_check(storyboard, run_dir)`.
CLI `camera-check STORYBOARD [--run RUN]` (exit 12 on unsatisfiable/off-target).

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: pydantic, existing `geometry.image_geometry`, `release._stage_files`, `workflow_adapter.load_api_workflow`

**Storage**: none new (reads storyboards, pinned workflow, run anchor images)

**Testing**: pytest with synthetic PNG anchors (bright rectangle on dark background) via `fake_comfy.make_png`-style helpers

**Target Platform**: native Windows 11

**Project Type**: CLI tool

**Performance Goals**: camera-check of a 3-anchor run < 2 s

**Constraints**: no GPU, no invented node parameters, sample plan hash unchanged

**Scale/Scope**: up to ~90 transitions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | Camera control labelled prompt-only; orbit/rise "not verifiable"; real anchors checked | PASS |
| II Local, GPU consent | Offline only | PASS |
| III Graph contracts | `control: graph` refused because the pinned workflow has no camera node; nothing invented | PASS |
| IV Immutable artifacts | Camera fields join the plan only when set | PASS |
| V Physical morph timing | Endpoint satisfiability protects FLF2V fixed endpoints | PASS |
| VI Spec Kit | Full workflow + converge loop | PASS |
| VII Compatibility | Existing choreography camera unchanged; conflict is an explicit error | PASS |
| VIII Loopback UIs | N/A | N/A |
| IX Owner gates | Operator-approved two-bridge GPU test remains owner-gated | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/023-camera-framing-keyframes/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/cli.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/morph_studio/
├── camera.py            # NEW
├── schema.py            # CameraMove, FramingTarget, delivery_crops
├── prompt_compiler.py   # camera clause
├── dag.py               # bridge task camera record; graph-control refusal
└── cli.py               # camera-check
tests/test_camera.py     # NEW
```

**Structure Decision**: one new module plus small schema/compiler/DAG hooks.

## Complexity Tracking

None.
