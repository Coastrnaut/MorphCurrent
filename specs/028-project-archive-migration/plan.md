# Implementation Plan: Portable Project Archives, Migrations and Local Backup (F28)

**Branch**: `028-project-archive-migration` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/028-project-archive-migration/spec.md`

## Summary

New `src/morph_studio/package.py` (stdlib `zipfile` + existing modules):

- **Constants**: `FORMAT = 1`, `KIND = "morphcurrent_project"`, `SUMS = "SHA256SUMS.json"`, `DESCRIPTION = "project.json"`, `WEIGHT_EXT`, `MEDIA_EXT` (png/jpg/jpeg/webp/mp4/mov/webm/mkv/gif), `AUDIO_EXT` (wav/mp3/flac/ogg/m4a/aac), limits `MAX_MEMBERS=10_000`, `MAX_NON_MEDIA=2 GiB` (non-media members), `MAX_TOTAL=64 GiB` (all members; never raised by the package's own claims), `MAX_RATIO=200` for members > 1 MiB, `REDACTED="<redacted-local-path>"`.
- **`export_project(storyboard, out, *, repo_root=".", run_dir=None, profiles=None, include_media=False, include_audio=False)`**:
  1. Refuse existing `out`; load storyboard; `dag.compile_plan(..., repo_root)` → plan checksum and the capabilities used → profiles (production defaults/overrides) and workflow exports; style pack chain files from `styles`.
  2. Registry metadata via `registry.build_entry` (offline) → profile identities + model report (`bundled: false`).
  3. Run provenance (optional): `manifest.json`, `plan.json`, `review.json` with paths redacted by `redact()` (relative to run/repo, else marker; count); per-stage chosen output checksums from the manifest.
  4. Media: inventory of run media + stage outputs (via `release._stage_files`/job outputs) and storyboard audio; included under `media/` only with authorization (`include_audio` needs `include_media`); every excluded file listed with checksum or `not found`.
  5. Refuse any weights file; write `.part` then `os.replace`; checksum list over all members.
- **`inspect_package(path)`** → `{ok, format, kind, problems, summary}` without extracting: zip validity, name safety (`_unsafe_name`), duplicates and case collisions, limits from the central directory before reading, checksum verification by streaming members, description checks (unknown future format, duplicate anchor/stage IDs, absolute paths anywhere in JSON), migration of format 0.
- **Migrations**: `MIGRATIONS = {0: _from_run_backup}`; `detect_format(names, description)`; `migrate(desc, from_format)` deep-copies, applies steps in order, raises `PackageError("migration step 0->1 failed: ...")` leaving input untouched. Format 0 = F20 archive (`run/<name>/…`, `jobs/…`, `SHA256SUMS.json`, no `project.json`): synthesized description from the run manifest (storyboard name, plan checksum, stages, outputs).
- **`import_project(path, dest, *, models_root=None)`**: inspect (must pass) → refuse a file or non-empty `dest` → extract to `dest.parent/.<dest>.import-<hex>` (each target resolved and checked inside staging) → `os.replace` to `dest` (or into an empty existing `dest`) → readiness: recompile plan from `dest` (when storyboard present) vs recorded checksum, registry statuses (`build_registry(dest/configs/profiles, repo_root=dest, models_root=...)`), missing models with approval note.
- CLI: `project-export STORYBOARD --out P [--run DIR] [--include-media] [--include-audio] [--repo-root R]`, `project-inspect P`, `project-import P --dest D [--models-root M]`. Exit 0 / 2.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: stdlib (`zipfile`, `hashlib`, `json`), existing `schema`, `dag`, `styles`, `registry`, `release`, `cache`

**Storage**: one zip file; import destination folder

**Testing**: pytest with tmp repos copying real storyboards/profiles/workflows; synthetic malicious zips built in tests

**Target Platform**: native Windows 11

**Project Type**: CLI tool / library module

**Performance Goals**: pilot export + inspect < 5 s without media

**Constraints**: no inference, no downloads, never overwrite, nothing outside destination, weights never bundled, media opt-in

**Scale/Scope**: one storyboard and at most one run per package

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | Readiness is a recomputed plan checksum and real registry statuses | PASS |
| II Local, consent | No downloads/inference; media/music only with owner authorization; weights refused | PASS |
| III Graph contracts | Workflows/profiles carried byte-for-byte with checksums; never rewritten | PASS |
| IV Immutable artifacts | Atomic `.part` writes; no overwrite; staged import with cleanup | PASS |
| V Physical morph | Plan (anchors, timing, shared anchors) preserved and re-verified | PASS |
| VI Spec Kit | Full workflow + converge | PASS |
| VII Compatibility / hygiene | F20 backups open via migration; packages are not committed | PASS |
| VIII Loopback UIs | N/A | N/A |
| IX Owner gates | Media/music inclusion and model downloads stay owner decisions | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/028-project-archive-migration/
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
src/morph_studio/package.py   # new
src/morph_studio/cli.py       # + project-export / project-inspect / project-import
tests/test_package.py         # new
```

**Structure Decision**: single module plus CLI wiring, matching F20–F27.

## Complexity Tracking

None.
