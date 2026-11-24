# Feature Specification: One-command end-to-end render

**Logical ledger ID**: F10 · **Feature Directory**: `specs/010-one-command-render` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F10 One-command dry-run, approved render, resume and status UX with native Windows docs and the full three-anchor two-bridge acceptance"

## Gap analysis
| Exists (F01–F09) | Gap |
|---|---|
| gate, preflight, anchors + chain, DAG, bridge stage, run manifest, QA/review, seam join — each with its own entry point | No single command; no run-level status; no preflight that turns missing profiles into a precise BLOCKED exit before any ComfyUI write |

## User Scenarios & Testing *(mandatory)*
### US1 - Dry run (P1)
`render STORYBOARD --dry-run` prints DAG, required profiles (exists/missing), GPU job count and BLOCKED reasons; makes no network request and writes nothing.
### US2 - Approved render, resume, status (P1)
`render STORYBOARD --confirm-gpu` runs anchors → bridges (one GPU job at a time) → QA + contact sheet, then stops `awaiting_review` until each bridge is approved with `review` (or `--accept-heuristics` is given explicitly), then joins with verified seams into `final/movie.mp4`. Re-running the same command resumes with zero repeat inference. `render --status RUN_DIR` is read-only. Without `--confirm-gpu` it validates only.
### US3 - Precise BLOCKED preflight (P1)
Missing T2I/edit profile → exit 6 with the missing files and the pointer to `docs/ANCHOR_MODEL_DECISION.md`; no ComfyUI write.

**Acceptance (offline, fake ComfyUI producing real FFmpeg clips)**: organic-machines → 3 anchors, 2 bridges (shared B SHA), QA, contact sheet, review gate, final MP4 with 129 frames, manifest complete; second run 0 new `/prompt`. **Acceptance (GPU)**: same with real models — BLOCKED (F02).

## Requirements *(mandatory)*
- **FR-001** Dry run: zero network, zero writes.
- **FR-002** Preflight blocks on missing profiles before any ComfyUI call that writes.
- **FR-003** Consent only via `--confirm-gpu`; busy queue refused unless `--allow-busy-queue`.
- **FR-004** Join only when every bridge is human-approved, or `--accept-heuristics` and QA has no flags.
- **FR-005** Artifacts under `outputs/runs/run-<plan16>/`; stage jobs in `outputs/runs/<job16>/`.
- **FR-006** Optional VRAM sampling with `--sample-vram`.
- **FR-007** Docs: README/quickstart for native Windows commands; existing `bridge` CLI unchanged.

## Success Criteria *(mandatory)*
- **SC-001** Offline E2E produces a 129-frame movie from the YAML alone (fake GPU).
- **SC-002** Rerun issues 0 `/prompt`.
- **SC-003** Missing profiles → exit 6 with 0 write requests.

## Assumptions
Real end-to-end acceptance requires owner-installed models and bounded GPU approval; not claimed here.
