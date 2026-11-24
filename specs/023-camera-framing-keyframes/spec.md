# Feature Specification: Camera Moves and Framing Consistency (F23)

**Feature Branch**: `023-camera-framing-keyframes` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F23 Camera trajectories and spatial consistency — offline slice: per-transition camera move with amount compiled into labelled prompt-only text (the installed morph workflow has no camera inputs; graph-level control fails explicitly); endpoint satisfiability from measured anchor geometry; per-anchor framing targets and safe-area checks for 16:9 and 9:16 crops; a camera-check command. No GPU; no invented node parameters."

## Clarifications

### Session 2026-11-24

Resolved autonomously from existing F12/F13 conventions:

- Q: What numeric rule decides satisfiability? → A: Let r = end/start subject extent ratio (mean of width and height ratios) and (dx, dy) = end − start subject centre. push_in a: r ≥ 1 + a/2; pull_out a: r ≤ 1/(1 + a/2); pan_left a: dx ≥ +a/2 (subject moves right when the camera pans left); pan_right a: dx ≤ −a/2; tilt_up a: dy ≥ +a/2; tilt_down a: dy ≤ −a/2; static: centre shift ≤ 0.08 and 0.75 ≤ r ≤ 1.33 (the F12 continuity limits CENTROID_MAX and EXTENT_RANGE). Half the requested amount is required so mild model under-shoot still passes.
- Q: How does the new camera move relate to the existing choreography camera field? → A: a separate optional `camera` on the transition (move, amount, control = prompt or graph); setting both it and a non-static choreography camera is a validation error; when only choreography camera is set, behaviour is unchanged.
- Q: How is the 9:16 crop defined on a 16:9 render? → A: the full-height centre crop of width height × 9/16; safe area = crop shrunk by 5% on every side; the subject's measured extent box must lie inside it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask for a camera move and know what it really does (Priority: P1)

The author adds a camera move to a transition — static, push in, pull out, pan left/right, tilt up/down, orbit left/right or rise — with an amount (how far, as a fraction of the frame). The plan shows the exact prompt wording used and labels it a "prompt-only approximation", because the installed morph workflow has no camera inputs. Asking for real graph-level camera control is refused with a clear explanation.

**Why this priority**: Vague motion words were a cause of drift and mismatched endpoints (MC-RUN-001/002); the author must see exactly what is requested and its limits.

**Independent Test**: A storyboard with a push-in of 15% compiles to a fixed, repeatable prompt clause and a "prompt-only" label; one requesting graph control fails validation naming the missing capability.

**Acceptance Scenarios**:

1. **Given** a transition with a push-in of 0.15, **When** the plan is compiled twice, **Then** the same prompt clause appears both times and the transition is labelled prompt-only.
2. **Given** a transition requesting graph-level camera control, **When** validated against the installed workflow, **Then** it is refused, naming the absent capability; nothing is invented.
3. **Given** a storyboard with no camera moves, **When** compiled, **Then** its plan identity is unchanged from before this feature.

---

### User Story 2 - Catch impossible camera moves before rendering bridges (Priority: P1)

Because both end frames of a morph are fixed images, a camera move must agree with them: a push-in needs the subject to be larger in the end image, a pull-out smaller, a pan shifts the subject the opposite way across the frame, a tilt shifts it vertically, and static keeps framing. After anchors exist (and before bridge GPU time is spent), the author runs a check that reports each transition as satisfiable or unsatisfiable, with the measured numbers.

**Why this priority**: An unsatisfiable request wastes ~8 GPU-minutes per bridge and produces drift.

**Independent Test**: Synthetic anchor images with a small then large subject pass a push-in and fail a pull-out; identical framing passes static and fails a 20% pan.

**Acceptance Scenarios**:

1. **Given** start/end anchors where the end subject is 1.3× larger, **When** checked for push-in 0.15, **Then** satisfiable with the measured size ratio shown.
2. **Given** the same anchors, **When** checked for pull-out, **Then** unsatisfiable with the reason.
3. **Given** a pan left of 0.2 and anchors where the subject did not move, **When** checked, **Then** unsatisfiable with the measured horizontal shift.
4. **Given** an anchor whose subject cannot be measured reliably, **When** checked, **Then** "unknown — review" rather than a false pass or fail.

---

### User Story 3 - Framing targets and delivery crops (Priority: P2)

The author can set per-anchor framing targets — subject centre and size with tolerances — and list delivery crops (the full 16:9 frame and a 9:16 vertical centre crop). The check reports, per anchor, whether the subject is on target and whether it stays inside each crop's safe area.

**Why this priority**: The film ships in 16:9 and 9:16 (F30/F40); a subject cut off by the vertical crop is only cheap to fix before bridges exist.

**Independent Test**: A centred subject passes both crops; a subject at the far right passes 16:9 and fails the 9:16 centre crop.

**Acceptance Scenarios**:

1. **Given** a framing target centre (0.5, 0.5) ± 0.08 and size 0.25–0.6, **When** an anchor measures centre (0.52, 0.49) and size 0.4, **Then** on target.
2. **Given** a 9:16 delivery crop, **When** the subject extends beyond the centre crop's safe area, **Then** that anchor is flagged for that crop only.

---

### User Story 4 - One command for the whole storyboard (Priority: P2)

`camera-check` reports, for a storyboard (and optionally the anchors of a run): each transition's move, prompt clause, label and satisfiability; each anchor's framing and crop results; and an overall verdict.

**Independent Test**: The command runs on the sample storyboard without anchors (moves and labels only) and on a run's anchors (full report), with exit status reflecting unsatisfiable or off-target results.

### Edge Cases

- Amount out of range (negative or above the allowed maximum): validation error.
- Static camera with substantially different endpoint framing: unsatisfiable (the morph would need to move the camera anyway).
- Orbit and rise cannot be verified from 2D framing alone: reported as "not verifiable from framing — review", never as satisfiable.
- No anchors yet: satisfiability and framing are "pending anchors"; prompt compilation still works.
- A move combined with the existing choreography camera field: one source of truth; conflicting values are a validation error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Transitions MUST accept an optional camera move from a fixed list (static, push_in, pull_out, pan_left, pan_right, tilt_up, tilt_down, orbit_left, orbit_right, rise) with an amount between 0 and 0.5 of the frame.
- **FR-002**: Each move MUST compile to fixed prompt wording that includes the amount in words, and the plan MUST label it "prompt-only approximation".
- **FR-003**: Requesting graph-level camera control MUST fail validation, naming that the installed workflow has no camera input.
- **FR-004**: Storyboards without camera moves MUST keep their plan identity.
- **FR-005**: Satisfiability MUST compare measured subject size and position between the two anchors against the move using the thresholds in Clarifications (push/pull by extent ratio, pan by horizontal shift, tilt by vertical shift, static within F12 limits); orbit/rise reported "not verifiable from framing".
- **FR-006**: Unreliable measurements MUST yield "unknown — review".
- **FR-007**: Anchors MAY carry framing targets (centre with tolerance, size range); results MUST be reported per anchor.
- **FR-008**: Delivery crops (16:9 full frame, 9:16 centre crop) MUST be checked per anchor against a safe-area margin.
- **FR-009**: `camera-check` MUST report moves, labels, satisfiability, framing and crops with an overall verdict and a non-zero exit when anything is unsatisfiable or off target.
- **FR-010**: No GPU work and no generation requests.

### Key Entities

- **Camera move**: kind, amount, compiled clause, label (prompt-only).
- **Satisfiability result**: transition, verdict (satisfiable / unsatisfiable / unknown / not verifiable), measured values, reason.
- **Framing target**: centre (x, y) ± tolerance, size range.
- **Crop check**: crop name, safe-area margin, inside / outside per anchor.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of seeded impossible moves in tests are reported unsatisfiable, and 100% of consistent ones satisfiable.
- **SC-002**: The real Orchid→Butterfly→Phoenix anchors are checked and their reports recorded (static camera expected satisfiable within tolerance).
- **SC-003**: The sample storyboard's plan identity is unchanged.
- **SC-004**: Zero generation requests in tests.

## Assumptions

- Subject measurement reuses the existing anchor framing heuristic (F12), which assumes a subject on a darker background; when it is unreliable the result is "unknown — review".
- Real camera-control nodes or LoRAs are out of scope until an owner-approved workflow exposes them (F27 capability registry).
- Safe-area margin defaults to 5% of the crop on each side.
