---
description: "Task list for F07 recovery, provenance and VRAM observations"
---

# Tasks: Recovery, provenance, VRAM

**Tests**: requested

- [X] T001 [P] [US2] Crash-after-each-transition resume tests (anchor + bridge executor) in tests/test_recovery.py
- [X] T002 [P] [US1] Tests + `RunManifest` (atomic, run id from plan SHA, stage records) in src/morph_studio/run_manifest.py, tests/test_recovery.py
- [X] T003 [P] [US3] Tests + model hash cache, busy-queue refusal, `models-hash` CLI in src/morph_studio/provenance.py, src/morph_studio/cli.py
- [X] T004 [P] [US4] Tests + `VramSampler` in src/morph_studio/vram.py
- [X] T005 Suite, ledger, PROGRESS, commit

## Blocked / owner-scheduled
- [ ] T006 Run `models-hash` on the owner machine while idle (multi-GB I/O; owner chooses timing)
- [ ] T007 First sampled peak-VRAM measurement during an owner-approved render
