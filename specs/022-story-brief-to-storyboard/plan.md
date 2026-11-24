# Implementation Plan: Brief to storyboard

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
New `brief.py`: `Brief` model and `plan_storyboard(brief) -> (storyboard dict, preview dict)` (preview: scene ids, frames/seconds per bridge, span, residual, unique frames); the CLI `brief-plan BRIEF --out FILE [--history] [--llm]` validates and compiles the storyboard, adds the F11 estimate and blocked profiles, and refuses `--llm` (disabled extension point). Example brief: `configs/briefs/engineering-pilot.yaml` (8 scenes, ~32 s) for the F31–F40 film pilot.

## Constitution Check
Re-evaluated against constitution v2.0.0:

| Principle | Status |
|---|---|
| I Evidence | PASS — prompts are templates for owner review; estimates labelled (NO DATA for unmeasured lengths) |
| II Local inference, GPU consent | PASS — offline; `--llm` refused (no hosted inference; only a future local owner-enabled endpoint) |
| III Graph contracts, test-first | PASS — no model or node names generated; output validated by `Storyboard` and `compile_plan` |
| IV Immutable artifacts, safe resume | PASS — writes a new file only; never overwrites |
| V Physical morph timing | PASS — 4n+1 lengths, reference-edit lineage, physical-metamorphosis choreography |
| VI Forty features / Spec Kit | PASS — retroactive converge loop under v2.0.0 |
| VII Compatibility and hygiene | PASS — output filename chosen by the user, never derived from brief text |
| VIII Loopback UIs | N/A |
| IX Owner gates | PASS — creative approval stays with the owner before any render |

## Complexity Tracking
None.
