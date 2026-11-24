# Implementation Plan: Intermediate anchors and ladders

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
New `ladder.py`: `prompt_distance`, `transition_risk`, `risk_report(storyboard, anchor_images?)`, `propose_ladder(storyboard_dict, from, to, steps, history, max_new, max_gpu_s)`. CLI `ladder-risk STORYBOARD [--run RUN_DIR]` and `ladder-propose`.

## Technical Context
Pure Python + existing `timeline`, `dag`, `perf.estimate`, `geometry`. YAML via PyYAML (`sort_keys=False`).

## Constitution Check
I (risk heuristic, proposal requires review) PASS · II (no GPU) PASS · IV (new file, input untouched) PASS · V (linear storyboard keeps shared-anchor/seam rules) PASS.

## Complexity Tracking
None.
