# Implementation Plan: Multi-format Cinematic Delivery and Final 30-Feature Acceptance (F30)

**Branch**: `030-delivery-presets-release-audit` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/030-delivery-presets-release-audit/spec.md`

## Summary

New `src/morph_studio/delivery.py`:

- **`PRESETS`** (recipe version 1): name → {target (w,h), geometry `fit`|`crop`, aspect for crops, fps (None = source, 24 for smooth), audio `copy`|`drop`|`licensed`}. `recipe(name)` → ordered steps `[fps_step, geometry, audio, encode]` with concrete filter strings for the source size; `recipe_sha256` = sha256 of canonical JSON of {version, preset, steps without source-specific sizes? } — the recipe hash covers the preset definition and encode settings (source-independent), so it is identical across runs and sources.
- **Encoders**: `available_encoders()` (`ffmpeg -hide_banner -encoders`, cached); preferred `libx264` (CRF 16, yuv420p, bt709 tags), fallback `mpeg4` (`-q:v 2`, codec name `mpeg4`); audio AAC 192k 48 kHz.
- **`deliver_one(src, out_dir, preset, *, audio=None, audio_licensed=False, audio_offset=0.0)`**: refuse existing output and inputs larger than the target; optional fps step via `interpolate.convert(..., method="blend")` into a temp file; geometry: fit via `finishing.geometry/chain`, crop via `crop=cw:h:x:0,scale=W:H:flags=lanczos,setsar=1,format=yuv420p`; audio per policy (licensed: `-ss offset -t duration` on the audio input, refuse if the remaining audio is shorter than the picture by more than one frame); encode to `.part` then rename; probe (`media.probe_video` + audio stream probe) → `verify(expected, measured)`; crop safe-area via `geometry.image_geometry` on first/last frames + generic aspect safe-area box test; record `<out>.delivery.json`.
- **`deliver(src, out_dir, presets, ...)`**: runs each preset, collecting results and errors (one failure does not stop the others).
- `release.acceptance_matrix(..., through=20|30|40)` (keep `all_features` compatibility) and `release.release_check(ledger, repo_root, through=30)` = matrix + `audit_repo` → `{ready_for_owner_review, reasons, note}`.
- CLI: `deliver INPUT --preset P [--preset P...] --out-dir D [--audio F --audio-licensed --audio-offset S]`; `acceptance --through 30|40` and `release-check`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: stdlib + local FFmpeg/ffprobe; existing `finishing`, `interpolate`, `media.probe_video`, `geometry.image_geometry`, `cache.sha256_file`, `release`

**Storage**: new output files + `.delivery.json` records

**Testing**: pytest with synthetic FFmpeg clips (gated on FFmpeg), real ledger for acceptance

**Target Platform**: native Windows 11

**Project Type**: CLI tool / library module

**Performance Goals**: MC-RUN movie in two presets < 1 min on CPU

**Constraints**: geometric only, no GPU/downloads/remote; never overwrite; source immutable; never tag

**Scale/Scope**: full film (~6 min) per preset

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | Every output probed against its preset; release never declared from tests | PASS |
| II Local, consent | Local FFmpeg only; licensed audio needs owner flag | PASS |
| III Graph contracts | No graph changes | N/A |
| IV Immutable artifacts | New files via `.part`; source checksum unchanged; records | PASS |
| V Physical morph | Duration preserved; anchors' framing reported for crops | PASS |
| VI Spec Kit | Full workflow + converge | PASS |
| VII Compatibility | `acceptance --all` kept; new flags additive | PASS |
| VIII Loopback UIs | N/A | N/A |
| IX Owner gates | Tagging and final demo stay owner decisions | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/030-delivery-presets-release-audit/
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
src/morph_studio/delivery.py   # new
src/morph_studio/release.py    # acceptance through 30/40 + release_check
src/morph_studio/cli.py        # deliver, acceptance --through, release-check
tests/test_delivery.py         # new
```

**Structure Decision**: single module plus small release/CLI additions.

## Complexity Tracking

None.
