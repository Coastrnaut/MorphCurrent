# Implementation Plan: Local Resolution Enhancement and Finishing (F26)

**Branch**: `026-upscale-visual-finishing` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/026-upscale-visual-finishing/spec.md`

## Summary

New `src/morph_studio/finishing.py`:
- **`geometry(src_w, src_h, target, mode)`**: computes the scaled size and the pad/crop offsets per the Clarifications.
- **`chain(...)`**: builds the FFmpeg filter chain:
  - optional `hqdn3d=1.5:1.5:6:6`, `deblock=filter=weak` and `colorchannelmixer` gains;
  - `scale=W:H:flags=lanczos`;
  - `pad` or `crop`;
  - optional `unsharp=5:5:0.4`;
  - `format=yuv420p`.
- **`colour_gains(anchor, clip)`**: mean RGB of the anchor vs the clip's first frame (F16 RGB decode), clamped to 0.8–1.25.
- **`finish(src, out, target, mode, denoise, deblock, sharpen, anchor)`**:
  1. Refuse an existing output.
  2. Refuse inputs larger than the target.
  3. Run FFmpeg into `.part`, then rename.
  4. Probe and check frames and duration.
  5. Run the identity check.
  6. Write the record `<out>.finish.json` (checksums, chain, `libx264`/`yuv420p`/bt709 tags, 8-bit, wall time, device "CPU (FFmpeg)").
- **`identity_check(src, out, geometry)`**: decodes the first and last frames of both; the output frames are cropped/padded back and scaled to source size with the `scale`/`crop` filters, then compared on grey MAD.
- **`upscale_models(comfy_root)`**: read-only listing of `models/upscale_models`.
- **`require_owner_approval(model)`**: always refuses.

CLI: `finish INPUT --target 1080p|1440p --mode fit|fill [--denoise] [--deblock] [--sharpen] [--match-anchor IMG] --out OUT`; `finish --list-models`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: stdlib + local FFmpeg; existing `media.probe_video`, `qa_subject.decode_rgb_frames`, `qa.decode_gray_frames`, `cache.sha256_file`

**Storage**: new output + `.finish.json` record

**Testing**: pytest with synthetic 832×480 clips from FFmpeg (gated)

**Target Platform**: native Windows 11

**Project Type**: CLI tool

**Performance Goals**: an 8 s 832×480 movie to 1080p in under a minute on CPU

**Constraints**: geometric only; no GPU; no downloads; input immutable

**Scale/Scope**: full film (~6 min) in one call

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | Identity check measured, limitations stated (geometric only) | PASS |
| II Local, consent | CPU FFmpeg; generative models refused without approval; no downloads | PASS |
| III Graph contracts | No graph changes | PASS |
| IV Immutable artifacts | New file via `.part`; input checksum unchanged; record | PASS |
| V Physical morph | Frame count/duration preserved; anchor identity verified | PASS |
| VI Spec Kit | Full workflow + converge | PASS |
| VII Compatibility | No existing behaviour changed | PASS |
| VIII Loopback UIs | N/A | N/A |
| IX Owner gates | Model use and delivery acceptance are the owner's | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/026-upscale-visual-finishing/
├── plan.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/morph_studio/finishing.py   # NEW
src/morph_studio/cli.py         # finish
tests/test_finishing.py         # NEW
```

**Structure Decision**: one new module.

## Complexity Tracking

None.
