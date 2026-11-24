---
description: "Task list for F21 style packs and asset collections"
---

# Tasks: F21

- [X] T001 [P] [US1] Tests: inheritance, negative merge, cycle/unknown parent, slug safety, hash in tests/test_styles.py
- [X] T002 [US1] `StylePack`, `load_pack`, `resolve_pack`, `pack_sha256`, `style_text` in src/morph_studio/styles.py
- [X] T003 [US2] Schema `Style.pack`, `Anchor.style_override`; DAG applies packs; three-scene + hash tests
- [X] T004 [US3] `check_assets` (missing/changed/unsafe) + tests; `library/` gitignored
- [X] T005 CLI `style-list`, `style-show`, `style-check`; example engineering packs
- [X] T006 Suite, ledger, PROGRESS, commit

## Phase 2: Convergence

- [X] T007 Report a style-pack size advisory in `render --dry-run` when the pack's advisory size differs from the storyboard render size (outside the plan hash; render size unchanged) in src/morph_studio/render.py with a test in tests/test_styles.py per Edge case "pack size is advisory" (partial)
- [X] T008 Evaluate all nine constitution v2.0.0 principles in the Constitution Check of specs/021-style-packs-asset-library/plan.md per Constitution (partial)
