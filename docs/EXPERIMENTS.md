# Experiments

Rendered media is not committed (Git ignores `.mp4`); hashes identify the files.

| ID | Date | What | Settings | Result | Evidence |
|---|---|---|---|---|---|
| MC-FLF2V-001 | 2026-11-23 | Owner's manual Wan 2.2 FLF2V, orchid → butterfly with a hand-prepared anchor pair (since removed from the repo) | 640 × 368, 49 frames, 16 fps (3.0625 s); seed recovered later from `/history`: 1091897826965482, 20 steps (10/10), CFG 4, euler/simple | Faithful endpoints; petals clip out of frame and wings distort at 0.75–1.5 s | MP4 SHA-256 `a638f6e1d58d876670ddc72c0bb773f9f6c83d93076ac3a9403c41618823120c`; VRAM/time NOT MEASURED |
| MC-FLF2V-002 | 2026-11-23 | Owner's manual run of the exported graph with the continuity prompt below | 640 × 368, 65 frames, 16 fps (4.0625 s); seed 844823683741909 | Not visually reviewed | ComfyUI `/history` prompt `160616bb…` |
| MC-FLF2V-003 | 2026-11-24 | First MorphCurrent-dispatched bridge (`bridge --confirm-gpu`), same graph and seed as 002 | as 002 | Decoded frames identical to 002 (PSNR ∞, SSIM 1.000). Petals collapse ~frames 24–40, bright wing flare ~48. `qa` heuristics raise **no flags** on it | MP4 SHA-256 `2d145e6b563fb2b7ccf75412fae7522e3bb5446c6363eec0cac779b13647843c`; 234 s execution; peak VRAM NOT MEASURED |
| MC-RUN-001 | 2026-11-24 | **First full MorphCurrent storyboard render** (`render organic-machines.yaml --confirm-gpu --sample-vram`): generated orchid (Qwen-Image T2I) → butterfly (Qwen edit of orchid) → phoenix (edit of butterfly), then 2 Wan bridges | 832 × 480; anchors 20 steps CFG 4, seeds 101/102/103; bridges 65 frames, 16 fps, seeds 201/202, storyboard prompts | All 5 stages verified; both bridges use the identical butterfly (SHA-256 `4c70fc98…2760`). Anchors 19 s / 52 s / 49 s, bridges 497 s / 495 s (~8 min each at 832×480 vs 4 min at 640×368). Orchid→butterfly: real petal-to-wing morph, but the subject drifts right and blurs mid-way (~frames 32–48) before resolving. Butterfly→phoenix: butterfly shrinks to a small blurred figure (~frame 16), then a side-on walking phoenix appears; reads close to a cut. The phoenix anchor is side-on rather than frontal, which makes that transition hard. `qa` heuristics: no flags on either (again missed visible problems). Owner approved both bridges; joined `final/movie.mp4`: 129 frames, 832×480, 16 fps, 8.0625 s, seam boundary diff 0.96 (anchor diffs 1.56 / 1.19, tolerance 8), no crossfade, SHA-256 `d94633da8403eccdb910d08b779d5a8e5e5aafbf26161dfe99714ee28e83d583` | `outputs/runs/run-cefb16ae1db47f4d/`; sampled VRAM (all processes): baseline 46,992 MiB, peak 48,080 MiB of 49,140, 2,041 samples at 0.5 s |
| MC-RUN-002 | 2026-11-24 | Phoenix fix: storyboard phoenix re-prompted frontal/centered/wings-spread with a negative prompt (side view, walking, off-center); butterfly→phoenix bridge prompt changed from rising orbit to a static front-facing transformation | as MC-RUN-001; orchid, butterfly and orchid→butterfly reused (no re-render) | New phoenix (`148c0638…5844`, 54.1 s execution) is frontal and symmetric with wings matching the butterfly's span. New bridge (`896df441…7aa5`, 497 s) stays centered and continuous; wings fold inward ~frames 32–40 before opening into feathers, no cut. Owner pre-approved both bridges; joined movie 129 frames, 832×480, 8.0625 s, seam diff 1.02 (anchor 1.56 / 1.20), no crossfade, SHA-256 `ce687958c40bd8d94b25ac28820ebf0ca5bddb53d86908ba4c052c74b80f99ab` | `outputs/runs/run-ba2d9dbedb6189be/`; sampled VRAM (all processes) baseline 35,604 MiB, peak 47,838 MiB |
| MC-RUN-003 | 2026-11-24 | **Reproducibility check**: same storyboard as MC-RUN-002 rendered from scratch into a fresh runs root (`--runs-root outputs/repro --accept-heuristics`), nothing reusable | as MC-RUN-002 | All 5 stages recomputed (anchors 20.2 / 51.8 / 49.9 s, bridges 496.0 / 494.1 s, same as the original) and **byte-identical**: orchid `500bee50…`, butterfly `4c70fc98…`, phoenix `148c0638…`, bridges `b3b57d0c…` / `896df441…`, final movie `ce687958…` (PSNR ∞, SSIM 1.000 on all clips). New movie name `organic-machines_20261124-160448Z_ba2d9dbe.mp4`, 129 frames, seam diff 1.02 | `outputs/repro/run-ba2d9dbedb6189be/`; sampled VRAM baseline 35,449, peak 48,056 MiB (all processes) |

Frame-identical reproduction (003 vs 002) proves determinism of the dispatcher, not creative quality.

## Continuity prompt (candidate, used in 002/003)

> A translucent glass orchid transforms continuously into an intricate mechanical butterfly. Every crystal petal gradually bends, folds, and reshapes into a matching silver and blue glass wing, remaining fully inside the frame. The flower's center develops into a detailed metallic butterfly body. All components remain physically connected throughout the transformation. Smooth gradual changes, stable centered composition, fixed camera, consistent lighting, no disappearing petals, no sudden cuts or abrupt changes.

001 changed prompt and length together, so it is an artistic iteration, not a controlled comparison. For controlled tests, change one variable at a time and keep model, resolution, sampler, steps and seed fixed.

## Ideas not yet run

Reference edit vs independent T2I anchors; prompt-only and length-only comparisons; seed sweeps (3 candidates); camera motion prompts; 832 × 480 vs 640 × 368 bridges; cold vs warm reruns with sampled VRAM.

## F11–F30 proposed verification experiments (none executed in this update)

| Features | Controlled comparison or acceptance | Evidence needed |
|---|---|---|
| F11 / F17 | Warm/cold stage run with separate external GPU load recorded | Stage latency + sampled whole-GPU VRAM with coverage, no guessed per-process usage |
| F12 / F13 / F23 / F24 | Same first/last anchors, seed and steps; vary framing or correspondence prompt one factor at a time | Contact sheets, geometry/framing windows, owner-rated motion quality |
| F14 / F19 | One morph versus multi-hop intermediate-anchor ladder; short vs multi-scene | SHA-identical shared endpoints, frame/PTS count and verified seam integrity |
| F15 | User-owned/licensed 90/120/140 BPM synthetic or real music with manual override | Beat-offset error, soundtrack mux PTS and final duration |
| F16 / F29 | Blind-held-out labelled quality windows and bounded seed/prompt A/B | Detection recall/false positives, run caps, honest Pareto runtime results |
| F18 / F21 / F22 | Same YAML via CLI and local UI/brief + style library | Editable generated plan, approvals, determinism and private asset handling |
| F25 / F26 / F30 | Native 16 fps vs approved interpolated/upscaled/cropped delivery | Decode/ffprobe counts, seam/subject integrity, audio sync and visual review |
| F27 / F28 | Hash-pinned profile migration and project archive restore | Safe failure/rollback, no private asset leakage or external model download |

Existing **MC-RUN-003** from-scratch exact-byte reproducibility is already a verified result in the table above. These new studies are future tests, not outcomes.
