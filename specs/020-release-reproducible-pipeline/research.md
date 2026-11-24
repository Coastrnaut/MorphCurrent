# Research: F20

## R1 Stage identity for comparison
- **Decision**: compare by stage key (`anchor:<id>`, `bridge:<a>-><b>`, `final:movie`) using hashes recorded in each run's manifest (`image_sha256`, `video_sha256`) and, for the final movie, the hash of the file in `<run>/final/`. Re-hash files on disk to detect post-hoc corruption.
- **Rationale**: manifests already store content hashes; re-hashing confirms the bytes still match.
- **Alternatives**: compare job ids (equal ids imply equal inputs, not equal outputs — rejected).

## R2 Frame comparison
- **Decision**: reuse `qa.decode_gray_frames` (FFmpeg, area-scaled gray) and report the max mean absolute per-frame difference; "visually equivalent" ≤ 1.0 with equal frame counts. Informational only.

## R3 Audit sources
- Workflow pins: each `configs/profiles/*.binding.json` → `workflow` + `workflow_sha256` vs `graph_sha256(load_api_workflow(...))`. Test profiles (`test_*`) are skipped when their workflow is absent.
- Tracked files: `git ls-files -z` (subprocess list, `shell=False`); if git is unavailable, walk the tree excluding ignored dirs and report a warning.
- Media provenance: same-stem `.json` with a `license` field and a source (`source`, `work` or `url`).
- Model hashes: parse the `docs/MODELS.md` table rows `| … | folder | file | sha |`; list them, never hash weights.

## R4 Archive format
- **Decision**: zip (stdlib), members `run/<run-name>/…` and `jobs/<job-id>/…` plus `SHA256SUMS.json` (`{path: sha256}`); restore extracts into `<dest>.part-<random>` then renames, refusing if any target exists or a member path is absolute/contains `..`.

## R5 Acceptance matrix
- **Decision**: parse the ledger table rows `| **Fnn** | dir | deps | priority | status |`; evidenced = status starts with GPU-VERIFIED/COMPLETE/OFFLINE-PASS without "pending"/"partial"; unresolved otherwise; release-ready only when all F01–F20 are evidenced with no pending gate.
