---
description: "Task list for F20 Production Acceptance and Reproducible Replay"
---

# Tasks: Production Acceptance and Reproducible Replay (F20)

**Input**: Design documents from `specs/020-release-reproducible-pipeline/`
**Tests**: requested by the spec (seeded defects, round trips, no generation requests) — written first.

## Phase 1: Setup

- [X] T001 Create tests/test_release.py with a synthetic-run fixture (two run dirs sharing job dirs; manifest image_sha256/video_sha256; plan.json; final movie) and a synthetic git repo fixture

## Phase 2: Foundational

- [X] T002 Create src/morph_studio/release.py with `ReleaseError`, `_sha` helper (reuse cache.sha256_file) and `_stage_files(run_dir)` mapping each stage to its output file via job.json (runs_root/basename(job_dir), as in review_ui)

## Phase 3: User Story 1 — Prove a replay reproduces a run (P1) 🎯 MVP

**Independent test**: identical runs → "reproduced"; one changed clip → only that stage "different"; deleted → "missing_b".

- [X] T003 [P] [US1] Tests: identical / different / missing / not_verified / different plans; frames comparison (FFmpeg-gated) labels "visually equivalent" when max mean abs diff ≤ 1.0 with equal counts in tests/test_release.py
- [X] T004 [US1] Implement `compare_runs(a, b, frames=False)` (status per stage: identical|different|missing_a|missing_b|not_verified; verdict reproduced|differs|incomplete; re-hash files on disk) in src/morph_studio/release.py
- [X] T005 [US1] Implement CLI `run-compare` (exit 0 reproduced, 10 otherwise) and `replay` (refuse non-empty runs root; validate-only without --confirm-gpu; render then compare) in src/morph_studio/cli.py with tests (replay without consent makes zero generation requests)

## Phase 4: User Story 2 — Audit sources, licences and hashes (P1)

**Independent test**: current repo audits clean; seeded tampered workflow, unlicensed media, tracked weight/secret each reported.

- [X] T006 [P] [US2] Tests: current repo 0 errors and lists ≥ 10 recorded model hashes; synthetic repo with tampered workflow, `x.png` without same-stem JSON, tracked `model.safetensors`, `.env`, `outputs/a.mp4` and a run `manifest.json` → each an error in tests/test_release.py
- [X] T007 [US2] Implement `audit_repo(root)` (profile pins via graph_sha256; media extensions png/jpg/jpeg/webp/gif/mp4/webm/mov/wav/flac/mp3/opus/ogg need same-stem JSON with `license` and a source; forbidden weights `.safetensors/.ckpt/.gguf/.pt/.pth/.bin/.onnx`, `outputs/`, `library/`, run manifests, secret-like names; parse docs/MODELS.md hashes; never hash weights) and CLI `audit` (exit 11 on errors)

## Phase 5: User Story 3 — Back up and restore a run (P2)

**Independent test**: round trip compares reproduced; corrupted member refused; overwrite refused.

- [X] T008 [P] [US3] Tests: backup/restore round trip + `compare_runs` reproduced; tampered member refused with nothing left behind; existing destination refused; `..`/absolute member refused; missing job dir refused unless `allow_missing_jobs` in tests/test_release.py
- [X] T009 [US3] Implement `backup_run(run, out, allow_missing_jobs=False)` (zip `run/<run>/**`, `jobs/<job>/**`, `SHA256SUMS.json`; refuses existing archive) and `restore_run(archive, runs_root)` (verify all, extract to temp dir, rename; refuse unsafe paths/existing targets) plus CLI `run-backup`, `run-restore`

## Phase 6: User Story 4 — Acceptance matrix (P2)

- [X] T010 [P] [US4] Tests: 20 rows for F01–F20, 40 with --all, each feature once; release_ready false while any gate is pending in tests/test_release.py
- [X] T011 [US4] Implement `acceptance_matrix(ledger, all_features=False)` and CLI `acceptance`

## Phase 7: Polish

- [X] T012 Real-data evidence: run-compare MC-RUN-002 vs fresh-root MC-RUN-003 and backup/restore/compare a real run; record results; test no ComfyUI client import and no `git tag`/push in release.py (FR-007); audit < 5 s and 3-anchor compare < 2 s (plan goals)
- [X] T013 Full suite; README/ARCHITECTURE/ledger/PROGRESS
- [X] T014 Converge loop until clean; commit and push

## Blocked / owner

- [ ] T015 Owner-approved bounded fresh-root GPU replay of a multi-scene storyboard; release tag only after owner approval

## Dependencies

Setup → Foundational → US1 → (US2, US3, US4 independent) → Polish.

## Parallel examples

T003/T006/T008/T010 test authoring can proceed in parallel after T002.

## Implementation strategy

MVP = US1 run comparison; then audit, backup/restore, matrix.

## Phase 9: Convergence

- [X] T016 Test replay with GPU consent (fake ComfyUI) into an empty runs root, compared against a prior run of the same storyboard, in tests/test_release.py per FR-003, US1/AC4 (partial)
- [X] T017 Make `replay` CLI exit codes follow the render exit-code table when the render does not finish, in src/morph_studio/cli.py per contracts/cli.md (partial)
- [X] T018 Roll back already-moved folders if restore fails mid-way, with a test, in src/morph_studio/release.py per US3/AC2 (partial)

## Phase 10: Convergence (found during the owner-approved replay)

- [X] T019 Validation-only `replay` must not write into the fresh runs root (it wrote a run manifest, making the root non-empty for the real replay); use `dry_run` and test that the root stays empty, in src/morph_studio/release.py and tests/test_release.py per FR-003 (contradicts)
