# Implementation Plan: Soundtrack Sync Verification, Animatic, Narration and Captions (F37)

**Branch**: `037-soundtrack-narration-timing` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/037-soundtrack-narration-timing/spec.md`

## Summary

New `src/morph_studio/soundtrack.py`:
- `anchor_times(storyboard)` → anchor frames from `timeline.compile_timeline` (frame 0 + Σ(L−1)), offset by the plan's first anchor frame.
- `sync_report(storyboard, sync_plan)` → rows {anchor, event, target_s, actual_s, error_frames}, mean/max |error|, drift, gate.
- `warp_report(sync_plan)` → rows {bridge, min_speed, max_speed, pinned, flags} (speeds from consecutive map deltas).
- `animatic(storyboard, out, *, run_dir=None, audio=None, licensed=False, offset=0.0, tail_s=0.0)` → still per anchor (run image via `release._stage_files`, else FFmpeg `color` card of the act tone), concatenated with an ffconcat list of durations = (next anchor frame − frame)/fps (last: tail), scaled/padded to 832×480 at 16 fps; audio `-ss offset -t duration`; `.part` + rename; probe-verified duration (≤ 1 frame) and audio presence; record JSON.
- `srt_write(cues, path)`, `srt_parse(path)`; `captions(storyboard, bank=None)` cues per anchor from anchor time to next.
- `narration_check(script, storyboard)` → resolved lines, flags (overlap, past_end, unknown_anchor), gaps, SRT.
- `click_track(beatmap, out, *, music=None)` → FFmpeg sine bursts via `adelay`/`amix` (or synthesized PCM with `wave` module — stdlib, exact) mixed with music via FFmpeg when given.
- `verify_beatmap(beatmap_path, out, owner, corrections)`.
- CLI: `sync-report`, `warp-report`, `animatic`, `captions`, `narration-check`, `click-track`, `beatmap-verify`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: stdlib (`wave`, `struct`, `math`), local FFmpeg/ffprobe; existing `timeline`, `schema`, `media.probe_video`, `release._stage_files`, `concepts`

**Storage**: outputs under `outputs/animatic|captions|narration|beatmap`

**Testing**: pytest with synthetic storyboards/sync plans, FFmpeg-gated animatic tests, real film storyboard + sync plan

**Target Platform**: native Windows 11

**Project Type**: library + CLI

**Performance Goals**: full-film animatic (96 cards, ~6 min) in < 2 min on CPU

**Constraints**: no generated text in pictures; audio only when licensed; no GPU; never overwrite

**Scale/Scope**: 96 anchors, ~6 min

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | Sync measured per anchor; probe-verified animatic | PASS |
| II Local, consent | Licensed audio only; local FFmpeg | PASS |
| III Graph contracts | N/A | N/A |
| IV Immutable artifacts | New files only; beat-map verification writes a new file | PASS |
| V Physical morph | Anchor frames on the 4n+1 grid preserved | PASS |
| VI Spec Kit | Full workflow + converge | PASS |
| VII Compatibility | New module/commands only | PASS |
| VIII Loopback UIs | N/A | N/A |
| IX Owner gates | Listening approval and beat-map verification are the owner's | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/037-soundtrack-narration-timing/
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
src/morph_studio/soundtrack.py   # new
src/morph_studio/cli.py          # sync-report, warp-report, animatic, captions, narration-check, click-track, beatmap-verify
tests/test_soundtrack.py         # new
```

**Structure Decision**: one module plus CLI wiring.

## Complexity Tracking

None.
