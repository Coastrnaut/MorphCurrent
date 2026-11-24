# Implementation Plan: Act Transitions, Title Cards and Overlays (F38)

**Branch**: `038-act-transitions-titles` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/038-act-transitions-titles/spec.md`

## Summary

New `src/morph_studio/titles.py` plus `configs/film/titles.yaml`:
- `load_titles(path)` → validated definition (font, defaults, opening, acts, lower_thirds, end).
- `resolve(titles, storyboard, *, duration_s=None, acts=None)` → overlays with start/end seconds: opening at a time; act titles at the first anchor of each chapter (anchor time = anchor frame / generation fps, frames from `soundtrack.anchor_frames`); lower thirds by time or anchor; end card at `duration − d`. Act titles that would start inside the opening card are deferred to its end; overlaps and clipping at the movie end are reported; covered anchors are listed per overlay.
- `safe_check(overlays, width, height, *, vertical=False)` → per overlay and area: estimated width `0.55 × size × chars`, fits / shrunk size / flagged (16:9 title-safe 90 %; 9:16 centre crop `H·9/16`, 90 %).
- `build_recipe(...)` → canonical JSON (overlays, sizes in px, font sha256, filter string, encoder args) and `recipe_sha256`.
- `render(movie, out, titles, storyboard, *, vertical=False)` → copies the font and per-overlay text files into a temp dir, runs FFmpeg with that dir as working directory and a filter that only uses relative names (`fontfile=font.ttf`, `textfile=tNN.txt`, `expansion=none`), alpha fade expressions, audio copied; `.part` + rename; input sha256 checked before/after; probe-verified frame count and duration against the input; record JSON next to the output.
- `act_boundaries(storyboard, sync_plan, window=6)` → per boundary: act, anchor index, event, nearest section anchor within the window, signed offset, proposal text. Read-only.
- CLI: `titles-check`, `titles-render`, `act-boundaries`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: stdlib (`hashlib`, `tempfile`, `shutil`, `subprocess`), PyYAML, local FFmpeg with `drawtext` (libfreetype), existing `schema`, `soundtrack.anchor_frames`, `media.probe_video`, `film.load_acts`

**Storage**: `configs/film/titles.yaml` (checked in); renders and records under `outputs/titles/`

**Testing**: pytest; synthetic storyboards and a short FFmpeg test movie (FFmpeg-gated); real film storyboard + sync plan for the boundary report

**Target Platform**: native Windows 11

**Project Type**: library + CLI

**Performance Goals**: titles on the full 6-minute animatic in < 3 min CPU

**Constraints**: no GPU; input never modified; output never overwritten; no text in generation prompts

**Scale/Scope**: 7 default overlays (opening, 5 acts, end), 4 boundaries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | Probe-verified frame count/duration; input hash before/after; record of covered anchors | PASS |
| II Local, consent | Local FFmpeg and local font only | PASS |
| III Graph contracts | No ComfyUI graphs touched; titles never enter prompts | PASS |
| IV Immutable artifacts | New output only (`.part` + rename), refuses existing output | PASS |
| V Physical morph | Overlays are a finishing layer; seam checks use the un-overlaid movie | PASS |
| VI Spec Kit | Full workflow + converge | PASS |
| VII Compatibility | New module/commands only | PASS |
| VIII Loopback UIs | N/A | N/A |
| IX Owner gates | Boundary moves are proposals only; text is the owner's | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/038-act-transitions-titles/
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
configs/film/titles.yaml         # new, owner-editable
src/morph_studio/titles.py       # new
src/morph_studio/cli.py          # titles-check, titles-render, act-boundaries
tests/test_titles.py             # new
```

**Structure Decision**: single library module + CLI, following F37.

## Complexity Tracking

None.
