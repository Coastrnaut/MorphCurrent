# Implementation Plan: Image model and workflow onboarding

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary

Add capability role contracts to profile validation, a read-only `workflow-inspect` command for fresh API exports, and an owner decision record (`docs/ANCHOR_MODEL_DECISION.md`) built from the ComfyUI templates installed locally. The real exports and the GPU gate stay BLOCKED pending owner approval.

## Technical Context

**Language/Version**: Python 3.11+ · **Dependencies**: existing (pydantic, httpx) · **Testing**: pytest, fixtures `object_info_image_nodes.json` (real) + synthetic graphs of real classes · **Platform**: native Windows 11 · **Constraints**: no downloads, no writes by inspect, no node-ID guessing in code (candidates only) · **Scope**: `workflow_adapter.py` (contracts), new `onboarding.py` (inspect), `cli.py`, docs.

## Constitution Check

| Principle | Result |
|---|---|
| I Evidence — licenses `owner to verify`, sizes approximate, gate BLOCKED | PASS |
| II Consent — no download code path; decision record requires approval | PASS |
| III Real graph contracts — exports only from real renders; inspect proposes *candidates*, never writes a profile | PASS |
| IV/V | N/A |
| VI Lifecycle — 002 dir mapped to F02 | PASS |
| VII Compatibility — Wan profile must still validate; contract check only when `capability` set | PASS |

## Project Structure

```text
src/morph_studio/workflow_adapter.py  # CAPABILITY_CONTRACTS + checks in validate_profile
src/morph_studio/onboarding.py        # NEW inspect_export()
src/morph_studio/cli.py               # workflow-inspect
tests/test_onboarding.py              # NEW
docs/ANCHOR_MODEL_DECISION.md         # NEW owner decision record
configs/models.yaml                   # point at decision record; still null/unverified
```

## Research (Phase 0) — see research.md

## Complexity Tracking
None.
