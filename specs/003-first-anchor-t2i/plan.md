# Implementation Plan: First anchor via local text-to-image

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary

Generalise the proven bridge state machine instead of writing a second one: `bridge.advance_job()` becomes the shared executor (upload roles taken from the plan, verification injected). New `anchors.py` plans T2I (and later edit) jobs and verifies images with a stdlib PNG/JPEG checker in `media.py`. CLI `anchor`.

## Technical Context
Python 3.11+; no new dependency (no Pillow: PNG chunk/CRC walk, JPEG SOI/SOF/EOI). Testing: pytest + stateful fake ComfyUI serving PNG bytes. Platform: native Windows. Constraints: identical bridge behaviour; one GPU job; `.part` downloads; content-addressed job dirs under `outputs/runs/`.

## Constitution Check
| Principle | Result |
|---|---|
| I Evidence — GPU gate BLOCKED until real export; mocks labelled | PASS |
| II Consent — `--confirm-gpu` + shared gate incl. cloud check | PASS |
| III Real graph contracts — profile must declare `text_to_image` and pass contract; tests use synthetic graphs of real classes | PASS |
| IV Immutable artifacts — content-addressed dir, `.part`, SHA-256, seeds explicit | PASS |
| VII Compatibility — refactor keeps `run_bridge` signature; all bridge tests must pass unchanged | PASS |

## Design
- `bridge.py`: `_upload` iterates `plan.upload_names`; extract `advance_job(job, plan, client, *, submit, retry, allow_busy_queue, timeout, poll_seconds, verify)`; `run_bridge` = `open_job` + `advance_job(verify=video)`.
- `anchors.py`: `AnchorRequest` (profile, method, positive_prompt, negative_prompt, seed, width, height, reference_image, label), `plan_anchor`, `open_anchor_job`, `run_anchor`, `_verify_image`. Record `kind: anchor_image`, `method`, `image{path, sha256, width, height, format}`, `parent{sha256}` (F04).
- `media.py`: `inspect_image(path) -> {format, width, height}` raising `ImageInvalid`.
- `cli.py`: `anchor` (`--prompt/--prompt-file`, `--negative`, `--seed` required, `--width/--height`, `--profile` required, `--confirm-gpu`, `--resume`, `--retry`, `--allow-busy-queue`, `--timeout`) and `anchor-status`.

## Complexity Tracking
Refactor of bridge executor justified: avoids a duplicate crash-recovery state machine (constitution IV/VII), guarded by the 16 existing bridge tests.
