# Implementation Plan: Engineering Concept Bank and Anchor Subject Research (F31)

**Branch**: `031-engineering-concept-bank` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/031-engineering-concept-bank/spec.md`

## Summary

- **Data**: `configs/concepts/engineering-film.yaml` — 96 Claude-drafted entries in film order across the ten eras (8–11 each), `status: draft`, `approval: null`. Every entry has `accuracy: unverified` and `sources: "general reference knowledge (Claude draft); to be verified in F33"`.
- **Code**: `src/morph_studio/concepts.py`:
  - `ERAS` (ordered ten), `FIELDS`, pydantic `ConceptEntry` / `ConceptBank` (extra forbidden).
  - `BRANDS` (case-insensitive whole words) and `PEOPLE` (capitalized whole words) with `EXCEPTIONS`.
  - `check(bank_path, *, anchors=None, plan=None)` → `{ok, problems:[{id, field, message}], counts, status, total, target}`: schema, unique ids, era membership/order/coverage (≥5 each), `follows` chain, link notes, banned terms in every text field, count ≥ target (from a sync-plan JSON's `summary.anchors` or `len(anchors)`, or a number), approval validity.
  - `coverage(bank)`, `listing(bank)` (numbered text lines).
- CLI: `concepts-check [--bank P] [--plan SYNC_JSON | --target N]`, `concepts-list [--bank P] [--json]`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: PyYAML, pydantic (existing)

**Storage**: one YAML file in `configs/concepts/`

**Testing**: pytest on the real bank plus mutated copies in tmp

**Target Platform**: native Windows 11

**Project Type**: data + validator + CLI

**Performance Goals**: check < 1 s

**Constraints**: text only; no GPU; no remote calls; Claude-drafted (no local LLM)

**Scale/Scope**: ~100 entries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | Accuracy marked unverified; sources honest; no claims of verification | PASS |
| II Local, consent | No inference; drafting is Claude text (owner rule) | PASS |
| III Graph contracts | N/A | N/A |
| IV Immutable artifacts | Versioned data file; approval recorded explicitly | PASS |
| V Physical morph | Every link names a shared shape/material bridge | PASS |
| VI Spec Kit | Full workflow + converge | PASS |
| VII Compatibility | New module/commands only | PASS |
| VIII Loopback UIs | N/A | N/A |
| IX Owner gates | Bank stays draft until owner approval | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/031-engineering-concept-bank/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/cli.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
configs/concepts/engineering-film.yaml   # new data
src/morph_studio/concepts.py             # new
src/morph_studio/cli.py                  # + concepts-check / concepts-list
tests/test_concepts.py                   # new
```

**Structure Decision**: data file plus a small validator module.

## Complexity Tracking

None.
