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

## First actual manual video baseline (MC-FLF2V-001)

- **Observed:** user-rendered `ComfyUI_00002_.mp4`, 640×368 H.264, 49 frames at 16 FPS, encoded duration 3.0625 seconds (3.0 seconds endpoint timestamp span). This differs from the earlier suggested 640×360 setting.
- **Qualitative results:** identifiable flower→butterfly progression, visually faithful endpoints, generally stable dark background; temporary petal clipping and stretched/irregular wing geometry around 0.75–1.5 s.
- **Unknown:** exact positive/negative prompts used in the MP4, seed, sampler, steps/CFG, checkpoint hashes, ComfyUI version, peak VRAM and elapsed GPU render time; do not retroactively invent metadata.
- **Next experiment:** MC-FLF2V-002 proposes a more physically explicit continuity prompt and 65 frames, retaining 640×368 and 16 FPS; full trial design, provenance and exact prompt are in [`RENDER_BASELINE_001.md`](RENDER_BASELINE_001.md).
- **Causal attribution:** changing prompt **and** length at the same time is an artistic iteration, not a controlled estimate of either change's effect. Separate prompt-only and duration-only A/B tests with fixed captured seeds and sampler settings for rigorous comparisons.

## Quality gates
No silent OOM/offload; no generic xfade; no stitched jump or duplicate freeze; no missing endpoint; no unverifiable experiment entries.

## Native Windows experiment capture
Record native Windows 11 build, NVIDIA Windows driver, distinct ComfyUI Python version, actual CUDA PyTorch support, FFmpeg.exe version, and whether ComfyUI used default/--highvram/offload. Python helpers must be used rather than WSL/PowerShell wrappers. Windows CI is not an A6000 benchmark.

## Future automated anchor-to-video trial matrix

The feature program uses the following **future** controlled tests (not results). Requirements and execution gates live in [SPECKIT_FEATURE_LEDGER.md](SPECKIT_FEATURE_LEDGER.md).

| Trial | Intervention | Fixed variables | Expected evidence |
|---|---|---|---|
| E9 | reference-edit B-from-A vs independent T2I B with shared style cues | A image, target description, dimensions, geometry/lighting goals | output image SHA, seeds, scene compatibility, human approval |
| E10 | storyboard direct A→B vs automatically generated A/B→Wan bridge | same Wan binding/seed/frames/CFG, input pair recorded | actual graph/profile validation, video ffprobe, endpoint fidelity |
| E11 | rerender only flawed bridge B→C | A/B/C byte hashes, approved A→B video | no extra A/bridge A→B GPU submissions, changed B→C candidate |
| E12 | 2×65-frame seam and optional audio | saved bridge decoded frames, 16 FPS | 129 unique frames only when B duplicate proven; PTS and soundtrack offsets recorded |
| E13 | cold vs warm run/restart | same storyboard, graph/model identity and seed | immutable manifest, same content hashes, zero duplicate GPU submission on complete rerun |

Keep manual MC-FLF2V-001 and programmatic MC-FLF2V-003 baseline observations separate from any new anchor-model tests. Peak VRAM measurement must use actual sampled GPU evidence; no inferring from `vram_free` snapshots.
