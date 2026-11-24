# Feature Specification: Long-form sequencing, edit invalidation and storage limits (F19)

**Feature Branch**: `019-resumable-longform-timeline` (work committed on `main` per owner rule)
**Created**: 2026-11-24
**Status**: Offline slice
**Input**: Ledger F19 — scale from the 8-second demonstration to many scenes and multi-minute songs without blind giant GPU batches.

## User Scenarios & Testing

### User Story 1 — Know exactly what an edit will re-render (P1)
The owner edits one scene of a long storyboard and, before spending GPU, sees which stages stay cached and which must re-run, and why (direct change vs. upstream lineage).

**Acceptance**: 1) Editing the last anchor's prompt marks that anchor and its one incoming bridge for re-run; everything else is cached. 2) Editing a reference-edit parent marks every descendant edit and every bridge touching them (lineage rule). 3) Changing only a bridge prompt re-runs only that bridge. 4) The prediction matches the prompts actually submitted by a resumed render (fake ComfyUI).

### User Story 2 — Chapters and a final index (P1)
The owner groups anchors into chapters and gets a timestamp index (anchor and chapter start/end in the final movie) plus an FFmpeg chapter-metadata file.

**Acceptance**: chapter ids are optional and must be contiguous; without chapters the plan hash is unchanged; anchor k starts at Σ(L−1)/F of earlier bridges.

### User Story 3 — Storage accounting and disk preflight (P1)
Before GPU work, the render estimates bytes for uncached stages and refuses if free disk would drop below a reserve. A report summarizes bytes per job kind in the runs root.

**Acceptance**: preflight refuses with a clear message (no prompt submitted) when free space is insufficient; cached stages cost nothing.

### User Story 4 — Scale and restart (P1)
2-, 10- and 50-anchor storyboards compile deterministically in dependency order; a 10-anchor render interrupted at random points by job budgets finishes with exactly one submission per stage.

### Edge cases
Renamed anchor with identical content (identity follows content and dependencies); removed scenes reported as `removed`; inserted scene invalidates only the bridges around it; proxy previews use a separate plan identity and never reuse full-resolution artifacts.

## Requirements
- **FR-001** Stage identity = hash of the inference-relevant task fields + profiles + identities of dependencies (Merkle).
- **FR-002** `plan-diff OLD NEW` lists unchanged / rerun (direct | upstream:<task>) / added / removed and counts GPU stages to re-run.
- **FR-003** Optional `anchors[].chapter`; contiguous; recorded on the anchor task only when set.
- **FR-004** `timeline STORYBOARD [--ffmetadata FILE] [--write-proxy FILE]` prints the index; proxy storyboard at 640×368 (measured fastest size, BENCH-001) with `-proxy` name suffix.
- **FR-005** `storage_report(runs_root)`; `render` disk preflight for `--confirm-gpu` runs with `--min-free-gb` (default 2).
- **FR-006** No GPU work in tests; existing plan hashes unchanged (sample `ba2d9dbe…`).

## Success Criteria
- **SC-001** Predicted re-run set equals actual new submissions in E2E edit tests.
- **SC-002** 50-anchor plan compiles in < 2 s; random-restart E2E has zero duplicate submissions.
- **SC-003** Offline suite green.

## Out of scope (owner/GPU gated)
Owner-approved bounded multi-scene GPU render with resume (acceptance gate); UI for reorder (F18).
