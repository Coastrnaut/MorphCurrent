---
description: "Task list for F31 Engineering Concept Bank and Anchor Subject Research"
---

# Tasks: Engineering Concept Bank and Anchor Subject Research (F31)

**Input**: Design documents from `specs/031-engineering-concept-bank/`
**Tests**: requested — written first; offline.

## Phase 1: Setup

- [X] T001 Create tests/test_concepts.py with a helper that loads the real bank and writes mutated copies to tmp

## Phase 2: Foundational

- [X] T002 Implement `ERAS`, models, `BRANDS`/`PEOPLE`/`EXCEPTIONS` and the banned-term matcher in src/morph_studio/concepts.py with unit tests (brand case-insensitive; surname capitalized only; units/adjectives allowed)

## Phase 3: User Story 1 — Subject list for the whole film (P1) 🎯 MVP

- [X] T003 [US1] Draft configs/concepts/engineering-film.yaml: 96 entries in film order across the ten eras (8–11 each) with all fields, `follows` chain, morph-affinity notes, accuracy notes, honest sources, `accuracy: unverified`, `status: draft`, `approval: null` (Claude-drafted text; no brands/people)
- [X] T004 [P] [US1] Tests: real bank passes with target 96; every era present and non-decreasing; all entries unverified; status draft

## Phase 4: User Story 2 — Catch problems (P1)

- [X] T005 [P] [US2] Tests: duplicate id, missing field, era backwards, era with < 5 entries, missing link note, broken `follows`, brand term, person name, target above count, sync-plan JSON count, unreadable plan, invalid approval record → each reported with id/field
- [X] T006 [US2] Implement `check`

## Phase 5: User Story 3 — Review era by era (P2)

- [X] T007 [P] [US3] Tests: coverage sums to total over ten eras; listing has one numbered line per entry with era, subject and next link
- [X] T008 [US3] Implement `coverage` and `listing`

## Phase 6: Polish

- [X] T009 CLI `concepts-check`, `concepts-list` with tests (ASCII, exit codes)
- [X] T010 Real evidence: run both commands on the real bank; record counts per era
- [X] T011 Full suite; docs (ARCHITECTURE, ledger, PROGRESS, README)
- [ ] T012 Converge loop; commit and push

## Blocked / owner

- [ ] T013 Owner review and approval of the concept bank (acceptance gate); technical accuracy review is F33

## Dependencies

Setup → Foundational → US1 (data) → US2 (validator) → US3 → Polish.

## Implementation Strategy

MVP = drafted bank that passes the checker; then failure-mode tests, review exports, CLI.
