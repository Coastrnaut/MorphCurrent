---
description: "Task list for F28 Portable Project Archives, Migrations and Local Backup"
---

# Tasks: Portable Project Archives, Migrations and Local Backup (F28)

**Input**: Design documents from `specs/028-project-archive-migration/`
**Tests**: requested — written first; all offline (tmp repos copying the real storyboards/profiles/workflows, synthetic run folders and hand-built malicious zips).

## Phase 1: Setup

- [X] T001 Create tests/test_package.py with helpers: tmp repo (real `configs/sequences/organic-machines.yaml`, profiles, workflows, a style-pack storyboard), a synthetic run folder (manifest with relative and absolute paths, plan.json, review.json, final movie bytes, job output files) and a zip builder for crafted members

## Phase 2: Foundational

- [X] T002 Implement constants, `PackageError`, `_unsafe_name`, absolute-path detection and `redact()` in src/morph_studio/package.py with unit tests (traversal, absolute, drive, UNC, backslash, `:` streams, reserved names incl. `nul.txt`, trailing dot/space; redaction relative vs marker and count)

## Phase 3: User Story 1 — Package a project (P1) 🎯 MVP

- [X] T003 [P] [US1] Tests: export contains storyboard, profiles, workflows, style packs, project.json (format, storyboard sha, plan sha, profiles with registry status, model report `bundled: false`) and checksum list covering every member; with run → manifest/plan/review included, no absolute paths, redaction count, stage output checksums; no media without authorization and excluded list with checksums; media authorization adds final movie and stage outputs under `media/`; audio requires `--include-audio` plus media; weights refused; existing output refused; no `.part` left
- [X] T004 [US1] Implement `export_project` in src/morph_studio/package.py

## Phase 4: User Story 2 — Inspect safely (P1)

- [X] T005 [P] [US2] Tests: good package passes with summary; tampered member, future format, each unsafe name class, duplicate names, case collision, member/size/ratio limits (limits monkeypatched small), duplicate anchor/stage IDs, absolute path in project.json, not-a-zip → refused with reason; inspection writes nothing
- [X] T006 [US2] Implement `inspect_package` (central-directory limits first, streamed checksum verification with size cap)

## Phase 5: User Story 3 — Migrations (P2)

- [X] T007 [P] [US3] Tests: an F20 `backup_run` archive is detected as format 0 and migrated (run name, plan sha, stages) and passes inspection; a failing migration step raises naming the step and leaves the input dict and archive bytes unchanged
- [X] T008 [US3] Implement `detect_format`, `MIGRATIONS`, `migrate`

## Phase 6: User Story 4 — Import and readiness (P2)

- [X] T009 [P] [US4] Tests: export → import into a new dir restores every member byte-identically, readiness plan checksum matches, profile statuses listed; second import into same non-empty dir refused; failed inspection writes nothing; destination that is a file refused; models root lacking files → missing models with approval note; no staging folder left behind on failure (simulated `os.replace` error)
- [X] T010 [US4] Implement `import_project` and `readiness` in src/morph_studio/package.py

## Phase 7: Polish

- [X] T011 CLI `project-export`, `project-inspect`, `project-import` in src/morph_studio/cli.py with tests (ASCII, exit codes 0/2)
- [X] T012 Test that package.py has no network/inference calls (no `ComfyClient`, `httpx`, `urlopen`)
- [X] T013 Real evidence: export organic-machines with run run-ba2d9dbedb6189be (no media), inspect, import into a second temp directory, record time, member count, plan match, redactions; inspect an F20 backup of the same run
- [X] T014 Full suite; docs (ARCHITECTURE, ledger, PROGRESS, README)
- [ ] T015 Converge loop; commit and push

## Blocked / owner

- [ ] T016 Owner restores a package on a second Windows machine/directory of their choice and reviews the editing/provenance context (acceptance gate)

## Dependencies

Setup → Foundational → US1 → US2 (inspects exported packages) → US3 (inspection of old formats) → US4 (import uses inspect) → Polish.

## Implementation Strategy

MVP = export; then inspection; migrations; import; CLI last.

## Phase 8: Convergence

- [X] T017 List run stage outputs whose job files are missing in the media inventory as `not found` (never included) per Edge Cases "job folders missing" (partial)
- [X] T018 Recreate a pre-existing empty import destination if the final rename fails, per FR-012 (partial)
