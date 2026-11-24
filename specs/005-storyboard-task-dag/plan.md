# Implementation Plan: Storyboard task DAG

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
New pure module `dag.py`: `compile_plan(storyboard, profiles, repo_root) -> dict` reusing `timeline.compile_timeline` and `derived_seed`; `dag` CLI. Schema gains a multiple-of-16 check.

## Technical Context
Python 3.11+; no I/O except existence checks of local profile files; pytest.

## Constitution Check
I PASS (requirements show missing profiles) · II PASS (no network) · III PASS (no node IDs in the DAG; profiles referenced by path) · IV PASS (explicit seeds, plan hash) · V PASS (B single task shared by two bridges; 4n+1; (L−1)/F) · VII PASS (`plan`/`validate` untouched).

## Design / Data model
Task: `{id, kind: anchor|bridge|final, depends_on[], ...}`; anchor fields per FR-002, bridge per FR-003, final per FR-004. Plan: `{schema: 1, storyboard, storyboard_sha256, plan_sha256, order[], tasks{}, requirements{text_to_image, reference_edit, wan_flf2v: {profile, exists}}}`. `plan_sha256` = SHA-256 of canonical JSON of `tasks` + `order` + requirement profile paths (not existence, not time).

Contract: `contracts/dag-cli.md`.

## Complexity Tracking
None.
