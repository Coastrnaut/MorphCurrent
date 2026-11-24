# Feature Specification: Technical Accuracy and Visual-Plausibility Review (F33)

**Feature Branch**: `033-technical-accuracy-review` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F33 Technical accuracy and visual-plausibility review — offline slice: per-anchor checklist with the concept's description and accuracy note; owner verdicts (accurate / reject / waive) stored with the anchor image hash in an append-only log, stale when the image changes; text-free prompting check over every anchor and bridge stage (film storyboard must pass); rejection impact invalidating the transitive reference-edit subgraph, touching bridges and the final movie, with a targeted regeneration plan; acceptance status requiring a current accurate verdict or waiver for every anchor. CLI accuracy-checklist, accuracy-review, accuracy-impact, accuracy-status. No GPU; verdicts are the owner's."

## Clarifications

### Session 2026-11-24

Resolved autonomously (owner's standing approval to use best judgment):

- Q: Where is the review log kept? → A: `outputs/reviews/<storyboard name>.accuracy.jsonl` (local, not committed; one JSON line per verdict).
- Q: Where do current anchor image hashes come from? → A: From a run folder's recorded anchor stages (`image_sha256`); a verdict can also be given an image file, whose SHA-256 is computed.
- Q: How is a regeneration seed chosen? → A: Derived deterministically from the storyboard's master seed, the anchor stage id and a retry number (one more than the number of earlier rejections of that anchor), guaranteed different from the current seed.
- Q: When does a stage count as carrying the text-free negatives? → A: When its compiled negative prompt contains each of the five terms as whole words (case-insensitive); a bridge with no negative of its own relies on the workflow's baked-in default, which does not contain them, so it counts as missing.
- Q: Who is the reviewer by default? → A: "owner"; any other name may be given and is recorded.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review each anchor against a fixed checklist (Priority: P1)

For each anchor image, the owner sees what it should depict (subject, description, accuracy note from the concept bank) and five questions: is it the right kind of component, is its geometry plausible, is it free of gibberish text or labels, is it free of fake schematic symbols, are its materials right for the era. The owner records a verdict — accurate, reject or waive — tied to the exact image.

**Why this priority**: Engineering audiences notice wrong circuits and fake text; the final film needs an explicit accuracy decision per anchor.

**Independent Test**: Listing the checklist for the film storyboard gives 96 entries with concept context; recording verdicts for an image stores them with its hash, and re-rendering the image makes the verdict stale.

**Acceptance Scenarios**:

1. **Given** a storyboard with concept-bank anchors, **When** the checklist is listed, **Then** every anchor appears with its subject, description, accuracy note and the five checklist items.
2. **Given** an anchor image, **When** an "accurate" verdict is recorded, **Then** every checklist item must pass; otherwise it is refused.
3. **Given** a "reject" verdict, **When** recorded, **Then** at least one failed item or a note is required.
4. **Given** a "waive" verdict, **When** recorded, **Then** a reason is required.
5. **Given** a recorded verdict, **When** the anchor's image hash later differs, **Then** the verdict is reported stale.
6. **Given** several verdicts for one anchor, **When** status is read, **Then** the latest applies and earlier ones remain in the log.

---

### User Story 2 - Prompts never invite fake text (Priority: P1)

Before rendering, the owner checks that every anchor and every bridge prompt asks the model to avoid text, letters, labels, logos and watermarks.

**Why this priority**: Generative models invent fake labels; negatives must always be present.

**Independent Test**: The check passes for the regenerated film storyboard (all 96 anchors and 95 bridges) and reports the stages missing negatives for a storyboard without them.

**Acceptance Scenarios**:

1. **Given** the film storyboard, **When** checked, **Then** all anchor and bridge stages carry the five negatives.
2. **Given** a storyboard whose anchors or bridges lack them, **When** checked, **Then** each missing stage and term is listed.

---

### User Story 3 - See exactly what a rejection costs (Priority: P1)

When the owner rejects an anchor, they see every stage that must be redone: the anchor, every later anchor edited from it (directly or indirectly), every bridge touching any of those anchors and the final movie — and nothing else. Separately generated anchors (text-to-image, independent) stop the chain. A regeneration plan proposes a new seed for each rejected anchor.

**Why this priority**: Reference edits make a rejection ripple through descendants; neighbours alone are not enough, and unrelated work must be preserved.

**Independent Test**: Rejecting an anchor early in an act of the film storyboard invalidates the rest of that act's chain and the bridges touching it, but no anchor in another act.

**Acceptance Scenarios**:

1. **Given** a rejected anchor with reference-edited descendants, **When** impact is computed, **Then** all transitive descendants, bridges touching any invalidated anchor and the final movie are listed.
2. **Given** a text-to-image or independent anchor downstream, **When** impact is computed, **Then** it and its own descendants are not invalidated (only bridges touching invalidated anchors).
3. **Given** a rejection, **When** the regeneration plan is produced, **Then** each rejected anchor gets a new deterministic seed different from its current seed and the stages to re-render are listed in dependency order.

---

### User Story 4 - Know when the film's anchors are all signed off (Priority: P2)

The owner sees for a storyboard (and its run) how many anchors are accurate, waived, rejected, stale or pending; the gate passes only when every anchor has a current accurate verdict or a waiver.

**Why this priority**: The acceptance gate is every final-film anchor accurate-enough or waived.

**Independent Test**: With verdicts for some anchors, status lists the rest as pending; after all are accurate or waived with matching hashes, the gate passes.

**Acceptance Scenarios**:

1. **Given** a run with anchor image hashes, **When** status is computed, **Then** each anchor is accurate / waived / rejected / stale / pending and the gate passes only if none are rejected, stale or pending.
2. **Given** no run (images not yet generated), **When** status is computed, **Then** every anchor is pending.

### Edge Cases

- A verdict for an anchor id that is not in the storyboard is refused.
- A verdict without an image hash is refused (verdicts belong to images, not prompts).
- Rejecting two anchors in the same chain reports the union once.
- The log is never rewritten; corrupted lines are reported, not silently dropped.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The checklist MUST contain five items: correct component class, plausible geometry, no gibberish text or labels, no fake schematic symbols, era-appropriate materials; listing it per anchor MUST include the concept's subject, description and accuracy note when the anchor id is in the concept bank.
- **FR-002**: Verdicts MUST be one of accurate / reject / waive, recorded with anchor id, image SHA-256, per-item results, note, reviewer and time in an append-only local log; validation per US1 scenarios 2–4.
- **FR-003**: The latest verdict per anchor applies; a verdict whose image hash differs from the anchor's current image hash MUST be reported stale.
- **FR-004**: The text-free check MUST verify that every anchor and bridge stage of a compiled plan has a negative prompt containing text, letters, labels, logo and watermark, reporting missing stages and terms.
- **FR-005**: The film storyboard generator MUST add these negatives to every bridge (anchors already receive them from the style pack), and the regenerated film storyboard MUST pass the check.
- **FR-006**: Rejection impact MUST include the rejected anchors, all transitive reference-edited descendants (stopping at text-to-image and independent anchors), every bridge with an invalidated endpoint and the final movie, and nothing else.
- **FR-007**: The regeneration plan MUST propose a deterministic new seed per rejected anchor (different from its current seed) and list stages to re-render in plan order.
- **FR-008**: Acceptance status MUST classify each anchor as accurate, waived, rejected, stale or pending and pass only when all are accurate or waived with matching hashes.
- **FR-009**: Command-line access MUST provide accuracy-checklist, accuracy-review, accuracy-impact and accuracy-status with ASCII-safe output and exit codes (0 success / gate passed, 1 gate not passed or check failed, 2 refusal).

### Key Entities

- **Checklist item**: key, question.
- **Verdict**: anchor, image_sha256, verdict, items {key: pass/fail}, note, reviewer, time.
- **Impact**: rejected anchors, invalidated anchors, invalidated bridges, final, preserved count, regeneration seeds.
- **Status**: per-anchor state and gate result.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The regenerated film storyboard passes the text-free check for 100% of its 191 GPU stages.
- **SC-002**: Rejection impact matches the hand-computed dependent subgraph in 100% of test cases, including chains crossing a text-to-image boundary.
- **SC-003**: A verdict becomes stale in 100% of cases where the image hash changes.
- **SC-004**: The gate passes only when every anchor is accurate or waived (verified by tests).

## Assumptions

- Verdicts are made by the owner; this feature provides the tools and records, never automatic verdicts.
- The review log lives in the local outputs folder (not committed), keyed by storyboard name.
- Current image hashes come from a run's recorded anchor stages; without a run, anchors are pending.
