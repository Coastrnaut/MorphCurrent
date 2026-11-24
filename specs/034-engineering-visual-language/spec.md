# Feature Specification: Engineering Visual Language (F34)

**Feature Branch**: `034-engineering-visual-language` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F34 Engineering visual language — offline slice: a checked-in visual-language definition (base pack engineering-noir; two candidate looks with per-act palette, lighting and camera; continuity rule; geometry targets; drift thresholds; owner selects); the film generator applies the chosen or default look to every anchor and bridge; a look check on compiled plans; a drift report from rendered anchors; two short A/B test storyboards for an owner comparison. CLI look-check, look-drift, look-test. No GPU."

## Clarifications

### Session 2026-11-24

Resolved autonomously (owner's standing approval to use best judgment):

- Q: Where does the visual-language definition live? → A: `configs/film/visual-language.yaml` (checked in; `selected: null` until the owner chooses).
- Q: What are the two candidate looks? → A: "copper-to-silicon" (default): a warm-to-cool journey — Spark copper/amber, Power copper/steel, Signal steel/phosphor green, Logic phosphor green/silicon blue, Scale silicon blue/steel. "steel-accent": brushed steel throughout with one accent per act (amber, copper, phosphor green, silicon blue, violet).
- Q: How is drift thresholded? → A: Act colour spread (largest subject-colour distance from the act mean, RGB 0–255 Euclidean) ≤ 60; boundary colour jump (last anchor of an act to first of the next) ≤ 70; centroid offset ≤ 0.08; neighbour extent ratio 0.75–1.33.
- Q: How does a bridge carry its act's camera move? → A: Through the transition's choreography camera (static / slow_push / slow_pull), compiled into the bridge prompt's camera sentence; the look check looks for that sentence.
- Q: Where do A/B test storyboards go? → A: By default `outputs/look-test/<look>.yaml` (local); default act Spark, first five anchors.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One coherent look, act by act (Priority: P1)

The owner defines once how the film looks: a shared base (dark studio, macro lens, rim light) and, for each act, a palette and lighting that shift gently (warm copper and amber for Spark and Power, phosphor green for Signal, silicon blue for Logic and Scale) with a camera move per act. Neighbouring acts always share at least one colour so act boundaries don't jump. Two candidate looks are kept side by side until the owner picks one.

**Why this priority**: Ninety-five morphs must read as one film, not unrelated clips.

**Independent Test**: The checked-in definition validates: two looks, each covering all five acts, every adjacent pair sharing a palette colour, camera moves from the allowed set.

**Acceptance Scenarios**:

1. **Given** the definition, **When** validated, **Then** both looks cover every act, adjacent acts share ≥ 1 palette colour and cameras are static, slow push or slow pull.
2. **Given** a look missing an act or adjacent acts with no shared colour, **When** validated, **Then** it is refused naming the act pair.
3. **Given** no owner selection yet, **When** the default look is requested, **Then** the definition's default look is used and reported as "default (not owner-selected)".

---

### User Story 2 - The look is enforced in every prompt (Priority: P1)

Generating the film storyboard applies the look deterministically: every anchor gets its act's palette and lighting, every bridge its act's camera move, and the text negatives remain. A check on the compiled plan confirms it.

**Why this priority**: The acceptance gate is a documented visual language enforced in compiled prompts.

**Independent Test**: The regenerated film storyboard passes the look check for all 96 anchors and 95 bridges; changing one act's palette changes only that act's anchors (and its bridges' endpoints).

**Acceptance Scenarios**:

1. **Given** the film storyboard generated with a look, **When** checked, **Then** every anchor prompt contains its act's palette colours and lighting, style identity is constant within each act, and every bridge carries its act's camera move.
2. **Given** a storyboard generated without the look (or with a different look), **When** checked against the look, **Then** mismatching stages are listed.
3. **Given** the same inputs, **When** generated twice, **Then** the plan hash is identical.
4. **Given** the look applied, **When** the text-free check (F33) runs, **Then** it still passes.

---

### User Story 3 - Measure drift in real renders (Priority: P2)

After anchors are rendered, the owner sees per act the average subject colour and how far anchors stray from it, the colour jump across each act boundary, subjects that drift off-centre and neighbours whose size jumps — each flagged against the definition's thresholds.

**Why this priority**: Prompts are not guarantees; measured drift tells the owner where the look breaks.

**Independent Test**: A synthetic run with one off-centre anchor and one large colour jump flags exactly those; the real organic-machines run produces a report without errors.

**Acceptance Scenarios**:

1. **Given** a run with rendered anchors, **When** the drift report runs, **Then** it lists per-act mean colour and spread, boundary colour distances, off-centre anchors (centroid more than 0.08 from centre) and neighbour scale ratios outside 0.75–1.33.
2. **Given** anchors not yet rendered, **When** reported, **Then** they are listed as missing, not guessed.

---

### User Story 4 - Choose between two looks (Priority: P3)

The owner gets two short test storyboards — the first few anchors of one act — identical except for the look, ready to render (bounded GPU, owner-run) and compare.

**Why this priority**: The final choice of look is the owner's and needs side-by-side evidence.

**Independent Test**: The two storyboards validate, differ only in style overrides and bridge camera, and have the same anchors, seeds and lengths.

**Acceptance Scenarios**:

1. **Given** the definition, **When** test storyboards are written for an act, **Then** two files are created with identical subjects, seeds and frame lengths and different look settings.
2. **Given** existing output files, **When** writing, **Then** it is refused.

### Edge Cases

- A palette colour written with different case or spacing still counts as shared.
- An act with a single anchor still gets its look.
- Drift on a run whose storyboard has no chapters treats the whole run as one act.
- Selecting a look name that does not exist is refused.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A checked-in visual-language definition MUST name the base style pack, at least two candidate looks, a default look, an owner selection (empty until chosen), geometry targets (centroid offset ≤ 0.08; neighbour scale ratio 0.75–1.33) and drift thresholds (act colour spread, boundary colour jump).
- **FR-002**: Each look MUST give every act a palette (≥ 2 colours), lighting text and a camera move (static, slow push, slow pull); adjacent acts MUST share at least one palette colour; validation MUST refuse violations naming acts.
- **FR-003**: The film storyboard generator MUST apply the selected look (else the default) deterministically: per-anchor style override with the act's palette and lighting, per-bridge camera move, text negatives kept.
- **FR-004**: The look check MUST verify on a compiled plan that each anchor prompt contains its act's palette colours and lighting, that style identity is constant within each act, and that each bridge prompt carries its act's camera move; mismatches MUST be listed.
- **FR-005**: The drift report MUST measure rendered anchors of a run (subject mean colour, centroid, extent) and report per-act mean and spread, boundary colour distances, off-centre anchors and neighbour scale jumps against the thresholds; unrendered anchors MUST be listed as missing.
- **FR-006**: The A/B test MUST write two storyboards for a chosen act (default the first act, first five anchors) identical except for the look, refusing existing outputs.
- **FR-007**: Command-line access MUST provide look-check, look-drift and look-test (and the generator option to choose a look) with ASCII-safe output and exit codes 0 success, 1 check failed/flags, 2 refusal.

### Key Entities

- **Visual language**: base pack, looks, default, selected, geometry targets, thresholds.
- **Look**: per act {palette, lighting, camera}.
- **Look report**: stage mismatches; **Drift report**: per-act colour stats, boundary jumps, geometry flags, missing anchors.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the film storyboard's 191 GPU stages pass the look check with the default look.
- **SC-002**: Regenerating with the same inputs yields the identical plan hash.
- **SC-003**: The drift report flags exactly the planted defects in the synthetic test and runs on the real organic-machines anchors.
- **SC-004**: The two A/B storyboards differ only in look settings (verified by comparing their compiled plans).

## Assumptions

- Palette and lighting are prompt-level controls (style override of the engineering-noir pack); results are verified by measurement, not assumed.
- Subject colour and geometry come from the existing F12 anchor geometry measurement.
- The final look choice and the A/B render are owner actions; this feature provides definitions, enforcement and measurement.
