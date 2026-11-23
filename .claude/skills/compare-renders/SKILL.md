---
name: compare-renders
description: Compare morph clip candidates under identical inputs and log visible defects, seam mismatches, and actual performance.
---
# Compare renders

1. Keep anchors, seed family, prompt and duration fixed for controlled comparisons, varying one parameter at a time.
2. Generate contact sheets and endpoint comparisons from real media; report missing files clearly.
3. Record precision, checkpoint hash, steps, CFG, sampler, execution time, peak VRAM, resolution and frames.
4. Flag blur, freeze, scene-cut, dissolve, style drift, mismatched endpoints, camera discontinuities.
5. Annotate metrics vs human creative judgment separately in `PROGRESS.md`; choose winners only after video review.
