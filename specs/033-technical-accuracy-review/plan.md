# Implementation Plan: Technical Accuracy and Visual-Plausibility Review (F33)

**Branch**: `033-technical-accuracy-review` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/033-technical-accuracy-review/spec.md`

## Summary

New `src/morph_studio/accuracy.py`:
- `CHECKLIST` (5 keys + questions), `TEXT_NEGATIVES = ("text", "letters", "labels", "logo", "watermark")`, `AccuracyError`.
- `checklist(storyboard, bank)` → per anchor: id, chapter, method, concept subject/description/accuracy_note (when in the bank), items.
- `record_verdict(log, storyboard, anchor, *, verdict, image_sha256=None, image=None, failed=(), note="", reviewer="owner")` — validation per FR-002; append one JSON line (fsync).
- `load_log(log)` → (entries, corrupt line numbers); `latest(entries)`.
- `text_free_check(plan)` → {ok, missing: [{stage, terms}]} over anchor and bridge tasks.
- `impact(plan, rejected)` → BFS over anchor tasks where child `conditioned_on_parent` and `reference` ∈ invalidated; bridges whose from/to is invalidated; `final:movie`; `preserved` count; `regenerate` [{anchor, current_seed, new_seed, retry}] with `derived_seed(master, f"{task}:retry{n}")` bumping n until different; ordered by plan order.
- `status(plan, entries, run_dir=None)` → per anchor state from latest verdict vs run manifest `image_sha256`; gate.
- `film.py`: every bridge gains `choreography: {negative: [text, letters, labels, logo, watermark]}` (camera static); regenerate `configs/sequences/engineering-film.yaml`.
- CLI: `accuracy-checklist STORYBOARD [--bank]`, `accuracy-review STORYBOARD ANCHOR --verdict V (--sha256 H | --image F | --run R) [--fail ITEM ...] [--note] [--reviewer] [--log]`, `accuracy-impact STORYBOARD --reject A [--reject B]`, `accuracy-status STORYBOARD [--run R] [--log]`, plus `--text-check` flag on `accuracy-status`… kept separate as `accuracy-negatives STORYBOARD`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: existing `dag.compile_plan`, `timeline.derived_seed`, `concepts`, `cache.sha256_file`, `release._load_manifest`

**Storage**: `outputs/reviews/<storyboard>.accuracy.jsonl` (append-only)

**Testing**: pytest on synthetic storyboards (chains crossing t2i/independent boundaries) and the film storyboard

**Target Platform**: native Windows 11

**Project Type**: library + CLI

**Performance Goals**: all commands < 2 s for 96 anchors

**Constraints**: no GPU; verdicts only from the owner; log never rewritten

**Scale/Scope**: ~100 anchors

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | Verdicts tied to image hashes; stale detection; no automatic verdicts | PASS |
| II Local, consent | Local files only | PASS |
| III Graph contracts | Negatives via existing choreography path; no graph edits | PASS |
| IV Immutable artifacts | Append-only log; invalidation by dependency graph | PASS |
| V Physical morph | Reference-edit lineage invalidation is transitive (constitution rule) | PASS |
| VI Spec Kit | Full workflow + converge | PASS |
| VII Compatibility | Film storyboard regenerated (plan hash changes intentionally); others untouched | PASS |
| VIII Loopback UIs | N/A | N/A |
| IX Owner gates | Accuracy verdicts and waivers are owner decisions | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/033-technical-accuracy-review/
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
src/morph_studio/accuracy.py   # new
src/morph_studio/film.py       # bridge text negatives
src/morph_studio/cli.py        # accuracy-* commands
configs/sequences/engineering-film.yaml  # regenerated
tests/test_accuracy.py         # new
```

**Structure Decision**: one module plus a small generator change.

## Complexity Tracking

None.
