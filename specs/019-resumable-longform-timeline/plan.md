# Implementation Plan: F19 long-form sequencing

**Branch**: `019-resumable-longform-timeline` | **Spec**: [spec.md](spec.md)

## Summary
New pure module `src/morph_studio/longform.py` (stage identities, plan diff, chapter index, FFmpeg metadata, proxy storyboard, storage estimate/report, disk preflight). Schema adds optional `Anchor.chapter`; DAG records it only when set. `render` gains a disk preflight (`--min-free-gb`). CLI: `plan-diff`, `timeline`, `storage`.

## Technical Context
Python 3.11, pydantic, PyYAML; FFmpeg only in E2E tests (skipped if absent). No ComfyUI contact. Storage estimates from measured artifacts: anchor PNG 0.42–0.49 MB at 832×480 (≈1.2 B/px, use 2.0), 65-frame bridge MP4 0.73–1.38 MB (≈0.053 B/frame·px, use 0.1); ×2 for ComfyUI's own output copy.

## Constitution Check
Local-only ✔; Python-only ✔; no GPU in tests ✔; preserves hashes ✔; preflight refuses before any submission ✔.

## Design
- Identity fields — anchor: method, positive/negative prompt, seed, width, height, profile; bridge: frames, fps, width, height, seed, positive/negative prompt, candidates, profile. Timing-only fields (requested_seconds) are excluded because the job cache ignores them.
- Diff reason: `direct` if own fields differ, else `upstream:<first changed dependency>`.
- Chapter index: anchor time t_k = Σ_{i<k}(L_i−1)/F; chapter spans first→last anchor; FFMETADATA1 with TIMEBASE=1/1000.
- Preflight: `needed = Σ uncached estimates × 2`; refuse if `free − needed < reserve`.
