# Research: F39 batch review

## R1 Matching runs to the film
- Decision: a run contributes every stage whose id (`anchor:<id>`, `bridge:<a>-><b>`) exists in the compiled film plan; batch storyboards use the film's ids, so batches, reruns and the full film all match. Runs of other storyboards contribute nothing.
- Alternative: match by storyboard name prefix (breaks for renamed batches).

## R2 Versions
- Decision: a version is a distinct media hash (`video_sha256` for bridges, `image_sha256` for anchors) of a verified stage; ordered by the first manifest (`created_at`) that recorded it; cache hits in later runs add nothing. Media path from the job dir (`job.json` outputs), as in the review UI.

## R3 Decisions
- Decision: film log JSONL, append-only, entries pinned to a version hash; older per-run `review.json` decisions are imported (read-only) and pinned to that run's version. Latest entry by time wins; stale if its version ≠ current.

## R4 Rerender closure
- Decision: rejected anchors → add anchors whose task has `conditioned_on_parent` and a reference already in the set (plan order is topological, as in F33 `accuracy.impact`); bridges with `from` or `to` in the set; plus rejected bridges.
- Seeds: queued stages get `derived_seed(master, "<task>:rerender:<n>")` with n = existing versions, so the rerender yields a new version; other stages keep their pinned film seeds and are cache hits.
- Segment: contiguous anchors from the first queued stage's act start to the last queued stage, like F36 batches.

## R5 Media aids
- Decision: sheet = for each rendered bridge, frames at 0, middle, last (`-ss` seeks, scaled to 160 px high), tiled 3 per row with FFmpeg `tile`/`hstack`/`vstack`; labels in the record JSON (no drawn text needed). Compare = `scale=-2:240` both, `hstack`, `tpad` the shorter clip.

## R6 UI
- Decision: reuse `review_ui` server and CSRF token; act page lists bridges in review order with `<video>` elements served through the existing media allowlist; tiny inline script maps A/R/N to form posts.
