# Implementation Plan: Workflow and Model Capability Registry with Safe Upgrades (F27)

**Branch**: `027-workflow-model-capabilities` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/027-workflow-model-capabilities/spec.md`

## Summary

New `src/morph_studio/registry.py`, built on the existing `workflow_adapter` (profiles, graph hash, `validate_profile`, capability contracts), `provenance.models_in_graph`-style loader scanning and `gates.cloud_nodes`:

- **Model catalogue** `configs/model_catalogue.json` (checked in, data only): `{"folder/file": {"licence", "source", "sha256"}}` mirrored from `docs/MODELS.md`.
- **`build_entry(profile_path, object_info=None, models_root=None, catalogue=None)`** → capability entry: profile, capability, workflow path, recorded/actual SHA-256, roles (node, input, class), output kinds, node classes, models (folder, file, role, licence, sha256, present), constraints (per bound numeric role: min/max/step from object_info; `length_rule: "4n+1"` for `wan_flf2v`), problems, status. Never raises for a bad profile: parse/workflow errors become `contract-error`.
- **Status** = most severe of problems by `SEVERITY = [cloud-node, contract-error, stale-hash, missing-node, missing-model, offline-unverified, ready]`.
- **`build_registry(profiles_dir, ...)`** → list of entries sorted by profile path.
- **`compare(current, candidate)`** (two entries) → changes list `{type, role?, before, after}` and verdict per Clarifications.
- **Selection** `configs/registry/selection.json`: `{"schema": 1, "active": {capability: {profile, workflow_sha256}}, "history": [...]}`; `PRODUCTION_DEFAULTS`; `active_profile(capability, path)`; `select(candidate_path, *, approve, note, object_info, selection_path, ...)` (refusals raise `RegistryRefusal`; atomic `.part` + rename write); `rollback(capability, selection_path)`.
- `workflow_adapter.CAPABILITY_CONTRACTS` gains `upscale: (("input_video",), "video")` and the `capability` Literal gains `"upscale"`.
- The registry keeps its own loader-role map (adds `model_name` → upscaler, CLIP vision); `provenance.MODEL_FOLDERS` and the hashing tool are left unchanged.

CLI: `registry [--profiles DIR] [--object-info FILE | --live] [--models-root DIR] [--strict]`; `registry-diff CURRENT CANDIDATE [--object-info FILE]`; `registry-select --profile P --approve [--note TEXT] (--object-info FILE | --live) [--models-root DIR] [--selection FILE]`; `registry-rollback --capability C [--selection FILE]`. Exit codes 0 ok, 1 strict problems, 2 refusal.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: stdlib + pydantic (already used); existing `workflow_adapter`, `gates`, `comfy_client` (read-only `/object_info` for `--live`)

**Storage**: checked-in `configs/model_catalogue.json`; opt-in `configs/registry/selection.json`

**Testing**: pytest with tmp profiles derived from the real production profiles and the recorded object_info fixtures

**Target Platform**: native Windows 11

**Project Type**: CLI tool / library module

**Performance Goals**: registry of 3 profiles < 2 s offline

**Constraints**: read-only towards ComfyUI and models; no downloads/installs; production defaults untouched; no GPU

**Scale/Scope**: a handful of profiles

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | Status derived from real files/hashes/object_info; offline never claims ready | PASS |
| II Local, consent | No downloads/installs; missing items need owner approval; cloud nodes refused | PASS |
| III Graph contracts | Reuses `validate_profile` checks against object_info; never rewrites graphs | PASS |
| IV Immutable artifacts | Selection history append-only; atomic writes | PASS |
| V Physical morph | 4n+1 rule reported for FLF2V | PASS |
| VI Spec Kit | Full workflow + converge | PASS |
| VII Compatibility | Render defaults unchanged; contract addition is additive | PASS |
| VIII Loopback UIs | `--live` reads only 127.0.0.1 | PASS |
| IX Owner gates | Selection needs `--approve`; model installs stay owner actions | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/027-workflow-model-capabilities/
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
src/morph_studio/registry.py          # new
src/morph_studio/workflow_adapter.py  # + upscale capability contract
src/morph_studio/cli.py               # + registry commands
configs/model_catalogue.json         # new, data
tests/test_registry.py                # new
```

**Structure Decision**: single module plus CLI wiring, matching F20–F26.

## Complexity Tracking

None.
