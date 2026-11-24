# Implementation Plan: Safe baseline, GPU concurrency gates, evidence and provenance

**Branch**: none (owner works on `main`; spec dir `specs/001-safe-baseline-provenance`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-safe-baseline-provenance/spec.md` (logical F01)

## Summary

Add a read-only `morphcurrent baseline` command that reports repository, ComfyUI, queue, installed-model and capability facts with explicit measurement labels; a shared `gates.check_gpu_gate()` used by every GPU-submitting stage (bridge now, anchors/pipeline later); and cloud-API-node rejection inside the existing `validate_graph`. Record measured facts in `docs/ENVIRONMENT.md`.

## Technical Context

**Language/Version**: Python 3.11+ (owner venv 3.12.10)
**Primary Dependencies**: existing — httpx, pydantic v2, PyYAML; no new dependency
**Storage**: JSON to stdout / new file (exclusive create)
**Testing**: pytest with `httpx.MockTransport` recording every request method
**Target Platform**: native Windows 11, local ComfyUI 0.46.0 Portable on 127.0.0.1:8188
**Project Type**: CLI + library (`src/morph_studio`)
**Performance Goals**: baseline report < 30 s (dominated by `/object_info`, ~5 MB)
**Constraints**: zero write requests; no model hashing; no ComfyUI restart; `shell=False` subprocesses (git, nvidia-smi query)
**Scale/Scope**: 2 new modules (`preflight.py`, `gates.py`), small edits to `workflow_adapter.py`, `bridge.py`, `cli.py`

## Constitution Check

| Principle | Check | Result |
|---|---|---|
| I Factual evidence | Report labels snapshots vs. peaks; hashes NOT MEASURED; capability `blocked` unless a validated profile exists | PASS |
| II Windows/privacy/consent | Only GETs; gate enforces consent + idle queue + no cloud nodes; nvidia-smi read-only query | PASS |
| III Real graph contracts, test-first | Cloud-node rule added to the existing validator; tests first | PASS |
| IV Immutable artifacts | `--out` uses exclusive create, never overwrites | PASS |
| V Metamorphosis/timing | Not affected | N/A |
| VI Spec Kit lifecycle | This spec dir recorded in ledger as F01 | PASS |
| VII Compatibility | `bridge` busy-queue message and flags preserved; existing 83 tests must pass | PASS |

Post-design re-check: PASS (no violations; no complexity tracking needed).

## Project Structure

### Documentation (this feature)

```text
specs/001-safe-baseline-provenance/
├── spec.md, plan.md, research.md, data-model.md, quickstart.md
├── contracts/baseline-cli.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/morph_studio/
├── gates.py            # NEW: GateDecision, check_gpu_gate, cloud_nodes
├── preflight.py        # NEW: read-only baseline report, model inventory, capability classification
├── workflow_adapter.py # EDIT: validate_graph errors on cloud API nodes
├── bridge.py           # EDIT: _submit delegates queue/consent check to gates (same message)
└── cli.py              # EDIT: `baseline` subcommand
tests/
├── test_gates.py       # NEW
├── test_preflight.py   # NEW
└── fixtures/object_info_image_nodes.json  # NEW: real captured subset incl. 2 cloud nodes
docs/ENVIRONMENT.md     # NEW: measured facts only
```

**Structure Decision**: extend the single existing package; no new top-level layout.

## Complexity Tracking

None.
