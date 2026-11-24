# Implementation Plan: Production Acceptance and Reproducible Replay (F20)

**Branch**: `020-release-reproducible-pipeline` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/020-release-reproducible-pipeline/spec.md`

## Summary

New module `src/morph_studio/release.py` with four offline tools: `compare_runs` (stage-by-stage
content-hash comparison of two run directories, optional decoded-frame comparison via
`qa.decode_gray_frames`), `audit_repo` (workflow/profile pins, media licence provenance, forbidden
tracked files from `git ls-files`, recorded model hashes parsed from `docs/MODELS.md` — never hashing
weights), `backup_run`/`restore_run` (zip + `SHA256SUMS.json`, verified, path-safe, no overwrite),
`acceptance_matrix` (parse the ledger status table). CLI: `run-compare`, `replay`, `audit`,
`run-backup`, `run-restore`, `acceptance`. `replay` = `run_render` into an empty runs root (GPU
only with `--confirm-gpu`) followed by `compare_runs`.

## Technical Context

**Language/Version**: Python 3.11+ (controller `.venv`)

**Primary Dependencies**: stdlib (`zipfile`, `hashlib`, `subprocess`, `json`, `re`); existing
`run_manifest`, `render`, `qa`, `workflow_adapter`, `cache.sha256_file`

**Storage**: run directories (`run-*/manifest.json`, `plan.json`, `review.json`), job dirs in the runs root, zip archives chosen by the user

**Testing**: pytest with synthetic runs (fake job dirs) and a synthetic git repo for audit; FFmpeg-gated frame test

**Target Platform**: native Windows 11

**Project Type**: CLI tool

**Performance Goals**: audit < 5 s on this repo (no weight hashing); compare of a 3-anchor run < 2 s without frame decoding

**Constraints**: read-only except backup/restore targets; no network; no release tagging

**Scale/Scope**: runs up to ~150 stages (five-minute film)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | Byte verdicts; frame comparison labelled informational; real MC-RUN-001 vs MC-RUN-003 comparison as evidence | PASS |
| II Local, GPU consent | Only `replay --confirm-gpu` may render, into a fresh root; audit never hashes weights | PASS |
| III Graph contracts | Audit verifies workflow pins against profiles with the existing `graph_sha256` | PASS |
| IV Immutable artifacts | Backup/restore checksum every file; restore refuses overwrite, writes via temp dir then rename | PASS |
| V Timing | Unaffected | PASS |
| VI Spec Kit | Full skill workflow + converge loop | PASS |
| VII Hygiene | Audit enforces no tracked weights/media/secrets; music licence provenance | PASS |
| VIII Loopback UIs | No UI | N/A |
| IX Owner gates | Release tagging and GPU replay remain owner decisions | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/020-release-reproducible-pipeline/
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
src/morph_studio/
├── release.py      # NEW
└── cli.py          # + run-compare, replay, audit, run-backup, run-restore, acceptance
tests/
└── test_release.py # NEW
```

**Structure Decision**: single new module, matching existing feature modules.

## Complexity Tracking

None.
