# Experimental design: reproduce visual quality, not anecdotes

## Baseline
- Triplet: orchid -> butterfly -> phoenix, consistent color, lighting, composition.
- Candidate resolution: 832 x 480, 16 FPS, 65 frames/bridge, 120 BPM x 8 beats/bridge.
- Real endpoint span: 4s/bridge; output deduped total: 129 frames (8s anchor timestamp span).
- No fake quality metrics or hardware benchmarks.

## Controlled matrix
| Trial | Change | Hold constant | Measure |
|---|---|---|---|
| E1 | independent vs reference-edited anchors | same anchors' prompts, resolution | silhouette, palette, start/end match |
| E2 | generic vs physically explicit prompt | anchor bitmaps, seed, model, steps | blur, cut/fade, semantic morph |
| E3 | static vs moving camera prompt | same anchors, sampler | optical flow, motion continuity |
| E4 | varying seed, 3 candidates | all else | repeatability, quality variance |
| E5 | FP8 scaled vs staged FP16 | resolution, steps, prompt | peak VRAM, elapsed, visual comparison |
| E6 | seam handling | same decoded bridge outputs | duplicate removal, color delta, motion |
| E7 | beat grid vs rounded Wan frames | fixed audio | beat residual / drift |
| E8 | optional intermediate anchor | same endpoints | recognizable continuous transformation |

Every trial must have unique ID, time, model hashes, dtype, workflow hash, ComfyUI commit, step/CFG/sampler, seeds, resolution, frame count, time, peak VRAM, evaluator notes and artifact paths.

## Quality gates
No silent OOM/offload; no generic xfade; no stitched jump or duplicate freeze; no missing endpoint; no unverifiable experiment entries.
