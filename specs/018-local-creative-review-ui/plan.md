# Implementation Plan: Local Creative Review Experience (F18)

**Branch**: `018-local-creative-review-ui` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/018-local-creative-review-ui/spec.md`

## Summary

A strictly-loopback local review page (`morphcurrent review-ui`) over existing run manifests: runs index, run page (stage states, anchors, contact sheet, playable clips with QA flags, reviews, final movie), approve/reject/pending forms writing `review.json` through the same `qa.record_review` the CLI uses, and a read-only plan view. Stdlib HTTP server; no scripts, no external assets, no GPU/ComfyUI code path. Design choice and threat model in [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.11+ (controller `.venv`)

**Primary Dependencies**: stdlib only (`http.server`, `html`, `secrets`, `mimetypes`, `urllib.parse`); reuses `run_manifest`, `qa`, `dag`, `perf`, `longform`, `schema`

**Storage**: existing files: `outputs/runs/run-*/manifest.json`, `review.json`, job dirs (`job.json`, PNG/MP4)

**Testing**: pytest; pure page-builder tests plus a live server on an ephemeral loopback port driven by `http.client`

**Target Platform**: native Windows 11, browser on the same machine

**Project Type**: CLI tool with an optional local page

**Performance Goals**: run page < 1 s for a 3-anchor run (SC-005)

**Constraints**: loopback only; no new dependencies; no request logs; no involuntary rendering

**Scale/Scope**: single operator; runs of up to ~150 stages (five-minute film)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence before claims | Tests for parity, security and missing media; owner walkthrough stays open | PASS |
| II Native Windows, privacy, GPU consent | Python only, loopback bind, no upload/telemetry; no GPU action reachable | PASS |
| III Real graph contracts, test-first | No graph touched; tests before handler code | PASS |
| IV Immutable artifacts, crash safety | Read-only over artifacts; only `review.json` written (atomic, existing function) | PASS |
| V Physical metamorphosis/timing | Plan view reuses `chapter_index` timing; nothing altered | PASS |
| VI Forty-feature lifecycle | Logical F18 → `specs/018-…`; ledger updated on completion | PASS |
| VII Source compatibility and hygiene | CLI `review` unchanged and authoritative; no media committed; no AI trailers | PASS |
| VIII Loopback-only local interfaces | Loopback bind, Host check, form token + Origin, allowlisted media, escaping, no external resources, no request logs, no render path | PASS |
| IX Owner gates and autonomous progress | No GPU, download or destructive action; owner walkthrough (T017) is the only owner gate | PASS |

Post-design re-check: PASS (no new violations; Complexity Tracking empty).

## Project Structure

### Documentation (this feature)

```text
specs/018-local-creative-review-ui/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/http-routes.md
├── contracts/cli-review-ui.md
├── checklists/requirements.md
└── tasks.md            # /speckit-tasks
```

### Source Code (repository root)

```text
src/morph_studio/
├── review_ui.py        # NEW: run_view, list_runs, page builders, apply_review, handler, make_server
└── cli.py              # + review-ui subcommand
tests/
└── test_review_ui.py   # NEW
```

**Structure Decision**: single project; one new module plus a CLI subcommand, matching existing feature modules.

## Complexity Tracking

None.
