# Feature Specification: Engineering Concept Bank and Anchor Subject Research (F31)

**Feature Branch**: `031-engineering-concept-bank` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F31 Engineering concept bank and anchor subject research — offline slice: a checked-in, Claude-drafted bank of 96 ordered subjects (one per anchor of the current Mozart sync plan) across ten eras of electricity and computing, each with physical description, shapes, materials, scale, morph-affinity to the next, accuracy note, honest sources and unverified status; generic depictions only (no brands, logos, trademarked designs or real people); a validator for schema, unique ids, era order, single-chain reachability, banned terms, link notes, count vs the sync plan and draft status; per-era coverage report and review export. CLI concepts-check, concepts-list. No GPU."

## Clarifications

### Session 2026-11-24

Resolved autonomously from the ledger and owner rules:

- Q: Where does the bank live and in what form? → A: `configs/concepts/engineering-film.yaml` (YAML, human-editable), with `version`, `status`, `approval` (null until the owner approves), `eras` and `entries`.
- Q: How is the single chain expressed? → A: List order is film order and every entry except the first names the entry it `follows`; the check requires `follows` to equal the previous entry's id, so branches, gaps and unknown ids are caught.
- Q: How are banned terms matched without false positives? → A: Brand and logo terms match as whole words regardless of case; real people's surnames match only as capitalized whole words (so lower-case units such as volt, ohm, watt, hertz and tesla, and adjectives such as voltaic, stay allowed); explicit exceptions are listed in the checker.
- Q: How evenly should the 96 entries spread over the ten eras? → A: Roughly evenly (8–11 per era); the check requires every era to have at least 5 entries.
- Q: What makes an approval record valid? → A: A non-empty owner name and an ISO date (YYYY-MM-DD); with a valid record the status may be "approved", otherwise it must be "draft".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A ready-to-review subject list for the whole film (Priority: P1)

The owner opens one file listing every anchor subject of the film in order, from lightning to AI hardware, ten eras in sequence. Each subject says what it physically looks like (shapes, materials, scale), how it can turn into the next one (a shared shape or material), and how sure we are about the technical details. Nothing in it names a company, product brand, logo or real person.

**Why this priority**: The full-song film needs one subject per anchor before any storyboard, prompt or render can exist.

**Independent Test**: The checked-in bank has 96 entries — at least the anchor count of the current sync plan — in non-decreasing era order, each with all fields and a link note to the next entry.

**Acceptance Scenarios**:

1. **Given** the bank, **When** checked, **Then** it has at least as many entries as the sync plan has anchors, every era appears, eras never go backwards, and ids are unique.
2. **Given** any entry except the last, **When** checked, **Then** it has a non-empty morph-affinity note describing the shape or material bridge to the next entry.
3. **Given** any entry, **When** checked, **Then** its accuracy status is "unverified" (or "reviewed" once F33 review happens) and its sources field states honestly what it rests on.
4. **Given** the bank, **When** checked, **Then** its overall status is "draft" until the owner records approval.

---

### User Story 2 - Catch problems automatically (Priority: P1)

Whenever the bank is edited, a check reports exactly what is wrong: missing fields, duplicate ids, an era out of order, an entry not connected in the chain, a missing link note, a brand or person name, or too few entries for the planned film.

**Why this priority**: The bank will be edited many times; mistakes must not reach prompts.

**Independent Test**: Deliberately broken copies of the bank each fail with the specific reason.

**Acceptance Scenarios**:

1. **Given** a duplicate id, a missing field, an era going backwards, or a missing link note, **When** checked, **Then** each is reported with the entry id.
2. **Given** a brand, logo reference or real person's name in any text field, **When** checked, **Then** it is reported with the field and term.
3. **Given** a sync plan with more anchors than entries, **When** checked against it, **Then** it fails stating both numbers.
4. **Given** an entry whose `follows` link points to an unknown id or forms a branch, **When** checked, **Then** reachability fails (a single ordered chain is required).

---

### User Story 3 - Review it era by era (Priority: P2)

The owner gets a per-era count and a plain list (number, era, subject, link to next) to review quickly and approve.

**Why this priority**: Owner review is the acceptance gate.

**Independent Test**: The list export has 96 numbered lines; the coverage report sums to 96 across ten eras.

**Acceptance Scenarios**:

1. **Given** the bank, **When** listed, **Then** each entry appears once in order with its era, subject and next-link note.
2. **Given** the bank, **When** the coverage report is produced, **Then** per-era counts sum to the total.

### Edge Cases

- The last entry has no next link (allowed only for the last).
- Ordinary words that contain a banned name (e.g. "voltaic", "teslas" as a unit) must not trigger false positives where the word is generic; the banned list matches whole words and explicit exceptions are recorded.
- An approval record without an owner name/date is invalid.
- A sync plan file that cannot be read fails the count check clearly instead of passing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The bank MUST list entries in film order, each with: id (slug), era (one of the ten), subject, physical description, dominant shapes, materials, scale, morph-affinity note to the next entry, accuracy note, sources consulted and accuracy status.
- **FR-002**: The bank MUST contain at least 96 entries covering all ten eras in order: natural electricity, early storage, generation and grid, signals and communication, vacuum-tube computing, solid state, integrated circuits, microprocessors, parallel/GPU compute, data centers and AI hardware.
- **FR-003**: Entries MUST be generic and physically plausible: no brand names, logos, trademarked product designs or real people's names or likenesses in any text field.
- **FR-004**: Sources MUST be stated honestly (general reference knowledge pending F33 verification); no entry may claim verification it has not had; accuracy status starts "unverified".
- **FR-005**: The validator MUST check schema completeness, unique ids, non-decreasing era order, presence of every era, a single linear chain (each entry's predecessor is the previous entry; no branches or unknown ids), link notes on every non-final entry, banned terms (whole-word, case-insensitive, with recorded exceptions) and the entry count against a sync plan's anchor count or a target.
- **FR-006**: The bank MUST carry an overall status "draft" until an owner approval (name and date) is recorded; the validator MUST report the status and refuse an approval record missing either field.
- **FR-007**: A coverage report MUST give per-era counts summing to the total, and a list export MUST give numbered lines (number, era, subject, next link).
- **FR-008**: Command-line access MUST provide concepts-check (optional sync plan or target count; exit 0 valid, 1 problems) and concepts-list (text or JSON), with ASCII-safe output.

### Key Entities

- **Concept entry**: id, era, subject, description, shapes, materials, scale, morph_to_next, accuracy_note, sources, accuracy.
- **Concept bank**: version, status (draft/approved), approval (owner, date), era list, entries.
- **Check report**: problems (entry id, field, message), counts per era, status, anchor target.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The checked-in bank passes the validator with zero problems against the current Mozart sync plan.
- **SC-002**: 100% of the deliberately broken variants in tests are rejected with the specific reason.
- **SC-003**: Zero brand, logo or real-person terms appear in the bank.
- **SC-004**: The owner can review the full list in one plain numbered export of 96 lines.

## Assumptions

- The current Mozart sync plan has 96 anchors (95 bridges); later re-planning may change the count, and the check compares against whatever plan is supplied.
- Technical accuracy review is F33; this feature only drafts and structures.
- Text is drafted by Claude in this session (owner rule: Claude drafting, no local LLM).
