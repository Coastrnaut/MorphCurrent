---
description: "Task list for F18 Local Creative Review Experience"
---

# Tasks: Local Creative Review Experience (F18)

**Input**: Design documents from `specs/018-local-creative-review-ui/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/
**Tests**: requested by the spec (parity, injection, missing media, security, accessibility) — written before implementation.

## Phase 1: Setup

- [X] T001 Create test module with a synthetic-run fixture (manifest, job dirs with job.json + PNG/MP4, contact sheet, review.json) in tests/test_review_ui.py

## Phase 2: Foundational

- [X] T002 Implement media allowlist helpers (`_token`, `_job_dir` = runs_root / basename(job_dir), `_inside`, `_job_media` from job.json `image.local_path` or `video` output `local_path`) and `UiError` in src/morph_studio/review_ui.py
- [X] T003 Implement shared page shell `_page` (escape all values with `html.escape`; no scripts; inline CSS only; visible focus outline) in src/morph_studio/review_ui.py

## Phase 3: User Story 1 — Inspect a render run in one place (P1) 🎯 MVP

**Goal**: runs index and run page with stage states, anchors, contact sheet, playable clips + QA flags, blocked reasons, final movie.
**Independent test**: synthetic Orchid→Butterfly→Phoenix run shows 3 anchors, 2 clips, QA flags, final; a deleted clip shows "missing".

- [X] T004 [P] [US1] Tests: `run_view` stages/media/missing media; `list_runs` skips corrupt manifests; run page contains video/img tags and QA flags; unknown/malformed run name raises `UiError`; every input/button/video has a label or aria-label and no positive tabindex (FR-011) in tests/test_review_ui.py
- [X] T005 [US1] Implement `run_view` (RunView/StageView per data-model.md; `media_missing` for verified stages whose file is gone) and `list_runs` in src/morph_studio/review_ui.py
- [X] T006 [US1] Implement `render_index` (empty state "No runs yet.") and `render_run_page` (labelled native controls, `aria-label` per section/video) in src/morph_studio/review_ui.py

## Phase 4: User Story 2 — Approve or reject clips from the page (P1)

**Goal**: approved/rejected/pending + note written exactly like `morphcurrent review`.
**Independent test**: page decision == CLI decision; anchors/unknown tasks/bad decisions refused.

- [X] T007 [P] [US2] Tests: UI/CLI parity (same `review.json` entry fields), refusal of anchor task, unknown task and bad decision, note truncated to "≤ 500 chars"; decision recorded via CLI appears on the next page view (FR-012) in tests/test_review_ui.py
- [X] T008 [US2] Implement `apply_review` (task must be a bridge of the run; decision in `approved|rejected|pending`; reuse `qa.record_review`) in src/morph_studio/review_ui.py
- [X] T009 [P] [US2] Security tests on a live server (ephemeral 127.0.0.1 port): foreign Host → 403; missing/invalid csrf → 403; foreign Origin → 403; >10 kB form → 413; traversal / unknown media token → 404; Range 206/416; security headers present; non-loopback `make_server` host refused in tests/test_review_ui.py
- [X] T010 [US2] Implement HTTP handler per contracts/http-routes.md (GET/HEAD/POST, Host check, CSRF + Origin, 303 redirect with message, Range responses, no request logging) and `make_server` (loopback only, IPv6 family for ::1) in src/morph_studio/review_ui.py

## Phase 5: User Story 3 — Inspect a storyboard plan before rendering (P2)

**Goal**: read-only plan view with anchors, timing, chapters, transitions, profile availability, estimate.
**Independent test**: sample storyboard shows 0 s / 4 s / 8 s and two 65-frame transitions; markup in prompts is escaped.

- [X] T011 [P] [US3] Tests: plan page content for configs/sequences/organic-machines.yaml; `<script>` in a prompt rendered inert; default storyboard discovery from configs/sequences/*.yaml in tests/test_review_ui.py
- [X] T012 [US3] Implement `plan_summary`, `render_plan_page` and `default_storyboards(repo_root)` in src/morph_studio/review_ui.py
- [X] T013 [US3] Add `review-ui` subcommand per contracts/cli-review-ui.md (exit 2 on non-loopback host) in src/morph_studio/cli.py

## Phase 6: Polish & Cross-Cutting

- [X] T014 [P] Test that review_ui imports no ComfyUI client/render module (no involuntary rendering), the handler writes no request log (FR-013) and the run page renders < 1 s in tests/test_review_ui.py
- [X] T015 Run full offline suite; update docs/ARCHITECTURE.md, README.md command list, docs/SPECKIT_FEATURE_LEDGER.md and docs/PROGRESS.md
- [X] T016 Run speckit-converge loop until clean; commit and push

## Blocked / owner

- [ ] T017 Owner walkthrough: plan, inspect and approve Orchid→Butterfly→Phoenix locally (acceptance gate)

## Dependencies

Setup → Foundational → US1 → US2 (needs run_view) → US3 (independent of US2) → Polish.

## Parallel examples

- US1: T004 tests alongside T002/T003 review.
- US2: T007 and T009 test authoring in parallel.
- US3: T011 can be written while T010 is implemented.

## Implementation strategy

MVP = US1 (read-only inspection). Then US2 (decisions + security), US3 (plan view), polish and converge.

## Phase 7: Convergence

- [X] T018 Resolve final movie and contact sheet inside runs_root/<run>/ by basename (manifests store cwd-relative paths) and test a UI started with a different runs root in src/morph_studio/review_ui.py, tests/test_review_ui.py per FR-003, FR-007 (partial)
- [X] T019 Add Constitution v2.0.0 principles VIII and IX to the Constitution Check in specs/018-local-creative-review-ui/plan.md per plan: Constitution Check (partial)
- [X] T020 Test that a corrupt review.json or manifest yields an error page, not a crash, in tests/test_review_ui.py per Edge case "corrupt manifest/review file" (partial)
