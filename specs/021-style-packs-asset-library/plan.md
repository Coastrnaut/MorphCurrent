# Implementation Plan: Style packs and asset collections

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
New `styles.py` (`StylePack` model, `load_pack`, `resolve_pack`, `pack_sha256`, `style_text`, `apply_override`, `check_assets`); schema: `Style.pack`, `Anchor.style_override`; `dag.compile_plan` uses packs when set; CLI `style-list/show/check`. Example packs: `configs/styles/engineering-noir.yaml` (+ `engineering-noir-power.yaml` extending it) for the F31–F40 film.

## Constitution Check
Re-evaluated against constitution v2.0.0:

| Principle | Status |
|---|---|
| I Evidence | PASS — no silent prompt rewriting; pack size advisory is reported by `render --dry-run`, never applied |
| II Local inference, GPU consent | PASS — reference assets stay in the local gitignored `library/`; nothing fetched |
| III Graph contracts, test-first | PASS — prompt text only; no graph changes |
| IV Immutable artifacts, safe resume | PASS — resolved pack SHA-256 joins the plan identity; asset hashes checked read-only |
| V Physical morph timing | PASS — unaffected |
| VI Forty features / Spec Kit | PASS — retroactive converge loop under v2.0.0 |
| VII Compatibility and hygiene | PASS — no-pack storyboards keep their plan hash; assets never committed |
| VIII Loopback UIs | N/A |
| IX Owner gates | PASS — licences recorded per asset; no downloads |

## Complexity Tracking
None.
