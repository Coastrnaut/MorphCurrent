# Research: F36

- **Decision**: Linear-in-frames interpolation between measured bridge lengths at the same size. **Rationale**: F29 measured 65 → 81 frames costing 489 → 658 s (≈ 10.5 s/frame), consistent with Wan cost scaling roughly with frame count at fixed resolution. **Alternatives**: pixel×frame scaling from one reference (old F11 extrapolation) — kept only as a fallback.
- **Decision**: Pin seeds in batch storyboards. **Rationale**: bridge seeds derive from the transition index, which changes in a sub-storyboard; pinning reproduces the full plan's tasks so jobs are content-identical and cached. **Alternatives**: render the whole film with caps only — loses per-act approval and act-contained batches.
- **Decision**: Include referenced parent anchors from earlier batches in a batch storyboard unchanged. **Rationale**: their tasks are identical to the full plan's, so their jobs are cache hits; this keeps reference edits valid without re-rendering.
- **Decision**: Estimate-vs-actual uses leave-one-out history. **Rationale**: comparing a job with a history containing itself would bias the ratio toward 1.
- **Decision**: Duplicate submissions detected by repeated `prompt_id` across job records. **Rationale**: each ComfyUI submission yields a unique prompt id; a repeat means a double submission (the crash-safe submit logic should make this impossible).
