# Implementation Plan: Physical correspondence and prompt orchestration

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
`schema.Choreography` + `Transition.choreography`; new `prompt_compiler.py`; `dag.py` uses it; `pipeline.bridge_request_for` passes the negative; CLI `prompt-preview [--variants]`.

## Technical Context
Pure Python; tests: golden strings, plan-hash regression against the committed storyboard, fake-ComfyUI graph check.

## Constitution Check
I (no motion guarantees; GPU A/B gated) PASS · III (patches existing bound role `negative_prompt` only) PASS · IV/V (plan hash unchanged without choreography; shared B untouched) PASS · VII PASS.

## Template (deterministic)
Positive: `<base prose>` · `Correspondences: a becomes b; c becomes d.` · `Sequence: first p1, then p2, finally pN.` · camera sentence · `The subject stays centered` (if keep_centered) `and keeps the same size` (if keep_scale) · `One continuous shot with no cuts, dissolves or crossfades.`
Negative defaults: `cut, scene change, dissolve, crossfade, flash, sudden replacement, subject leaves frame, collapsing shapes, extra limbs, blurry` + user negatives (dedup, order kept).

## Complexity Tracking
None.
