# Implementation Plan: Generated anchors → Wan bridges

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
New `pipeline.py` with `run_bridge_stage(dag_plan, anchor_jobs, client, runs_root, …)` building `BridgeRequest`s from DAG tasks and verified anchor files, executed by the unchanged `plan_bridge`/`run_bridge`.

## Technical Context
Python 3.11+; tests reuse `FakeComfy` (SaveVideo path) and inject a probe (ffprobe cannot decode fake MP4 bytes).

## Constitution Check
III PASS (real Wan export/profile only; nothing guessed) · IV/V PASS (shared B SHA asserted) · II PASS (consent passthrough, gate) · VII PASS (`bridge` CLI untouched).

## Design
`BridgeStageResult{jobs: {task_id: BridgeJob}, blocked: {task_id: reason}, stopped_at}`; `bridge_request_for(task, start, end, profile)`.

## Complexity Tracking
None.
