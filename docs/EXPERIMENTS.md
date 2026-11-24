# Experiments

Rendered media is not committed (Git ignores `.mp4`); hashes identify the files.

| ID | Date | What | Settings | Result | Evidence |
|---|---|---|---|---|---|
| MC-FLF2V-001 | 2026-11-23 | Owner's manual Wan 2.2 FLF2V, orchid → butterfly example anchors | 640 × 368, 49 frames, 16 fps (3.0625 s); seed recovered later from `/history`: 1091897826965482, 20 steps (10/10), CFG 4, euler/simple | Faithful endpoints; petals clip out of frame and wings distort at 0.75–1.5 s | MP4 SHA-256 `a638f6e1d58d876670ddc72c0bb773f9f6c83d93076ac3a9403c41618823120c`; VRAM/time NOT MEASURED |
| MC-FLF2V-002 | 2026-11-23 | Owner's manual run of the exported graph with the continuity prompt below | 640 × 368, 65 frames, 16 fps (4.0625 s); seed 844823683741909 | Not visually reviewed | ComfyUI `/history` prompt `160616bb…` |
| MC-FLF2V-003 | 2026-11-24 | First MorphCurrent-dispatched bridge (`bridge --confirm-gpu`), same graph and seed as 002 | as 002 | Decoded frames identical to 002 (PSNR ∞, SSIM 1.000). Petals collapse ~frames 24–40, bright wing flare ~48. `qa` heuristics raise **no flags** on it | MP4 SHA-256 `2d145e6b563fb2b7ccf75412fae7522e3bb5446c6363eec0cac779b13647843c`; 234 s execution; peak VRAM NOT MEASURED |

Frame-identical reproduction (003 vs 002) proves determinism of the dispatcher, not creative quality.

## Continuity prompt (candidate, used in 002/003)

> A translucent glass orchid transforms continuously into an intricate mechanical butterfly. Every crystal petal gradually bends, folds, and reshapes into a matching silver and blue glass wing, remaining fully inside the frame. The flower's center develops into a detailed metallic butterfly body. All components remain physically connected throughout the transformation. Smooth gradual changes, stable centered composition, fixed camera, consistent lighting, no disappearing petals, no sudden cuts or abrupt changes.

001 changed prompt and length together, so it is an artistic iteration, not a controlled comparison. For controlled tests, change one variable at a time and keep model, resolution, sampler, steps and seed fixed.

## Example anchor fixtures

`assets/anchors/01_glass_orchid.jpg` and `02_metallic_butterfly.jpg` (1280 × 720) are the hand-prepared pair used for 001–003 and remain regression fixtures for the bridge. They are **not** generated anchors. To try them in the ComfyUI UI:

```cmd
python scripts\windows\stage_example_anchors.py --install-root C:\AI\ComfyUI_windows_portable --dry-run
python scripts\windows\stage_example_anchors.py --install-root C:\AI\ComfyUI_windows_portable
```

The script only copies the two JPGs into `ComfyUI\input\` and refuses to overwrite different files.

## Ideas not yet run

Reference edit vs independent T2I anchors; prompt-only and length-only comparisons; seed sweeps (3 candidates); camera motion prompts; 832 × 480 vs 640 × 368 bridges; cold vs warm reruns with sampled VRAM.
