# Data model: F24

- **FrameMetrics**: `frame`, `occupancy`, `overlap_prev` (IoU with previous mask, null for frame 0), `parts`, `background_change` (null for frame 0), `centre` [x, y] or null, `colour` [r, g, b] or null, `unreliable`.
- **ContinuityFlag**: `type` ∈ {shape_substitution, topology_change, background_change, motion_jump, colour_jump}, `frames` [first, last], measured values (`overlap`, `parts`, `change`, `step`, `threshold`).
- **ContinuityReport**: `frames`, `threshold`, `flags`, `metrics` (optional), `method: heuristic`.
- **EvaluationReport**: per clip: labelled defects with `hit` / `miss` and matching detector, `false_flags` on clean windows; per-kind recall; `thresholds` echo.
- **RepairProposal**: `bridge`, `clip_sha256`, `flags`, `refinements` [text], `intermediate_anchor` {at_frame, first_frames, second_frames} or null, `controlled_comparison` {same seed, length, endpoints; only prompt/anchor changed}, `status: proposed — owner review`.
- **RepairComparison**: `frames` (both), `endpoints` {start_mad, end_mad, unchanged}, `removed`, `persisting`, `new`, `verdict` ∈ {candidate improvement — needs owner review, no improvement, endpoint regression, not comparable}.
