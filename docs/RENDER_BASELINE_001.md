# Experiment MC-FLF2V-001 — first successful Orchid → Butterfly video bridge

**Status:** Observed successful user-run ComfyUI FLF2V video, qualitative inspection complete. **Not** an automated MorphCurrent render or measured A6000 performance benchmark.
**Session date:** 2026-11-23 (owner's local time).

## Evidence and provenance

- Source artifact: user-uploaded `ComfyUI_00002_.mp4`, reviewed in this session. Generated video is **not committed** (Git ignores `.mp4`).
- SHA-256 of uploaded MP4: `a638f6e1d58d876670ddc72c0bb773f9f6c83d93076ac3a9403c41618823120c`.
- The owner confirmed that the ComfyUI render succeeded; reviewed video shows the sampled orchid-to-butterfly transformation.
- Frame metadata measured with `ffprobe` on **this uploaded MP4**, rather than inferred from a template:

| Item | Verified value |
| --- | --- |
| Codec | H.264 |
| Display width × height | **640 × 368** (not 640 × 360) |
| Frame rate | **16 FPS** |
| Frames | **49** (valid 4n+1) |
| Encoded duration | **3.0625 seconds** (= 49/16) |
| First to last frame timestamp span | **3.0 seconds** (= (49-1)/16) |
| File size | **641,366 bytes** |

**Evidence limits:** The exact seed, source workflow's sampler, step count, CFG, schedule split, ComfyUI Git revision, precise model hashes/versions, prompt text **actually embedded in that run**, host driver, peak VRAM, GPU run time and negative prompt **were not retrieved from the uploaded MP4**. Do not infer that the previous example prompt was actually used, or that all expected checkpoint filenames were loaded. Export the real API JSON before making reproducibility claims.

## Qualitative inspection of sampled video frames

Reviewed a contact sheet sampled every four frames (0, 4, ... 48) and side-by-side endpoint comparisons in the conversation; these review images are not included in Git.

- **Frame 0 / 0.00 s:** glass orchid is recognizable and aligns closely with its provided first anchor.
- **Frames 12–24 / 0.75–1.50 s:** upper petals move upward and partially extend outside the visible frame; transient thin/elongated butterfly anatomy and wing distortion.
- **Frames 28–36 / 1.75–2.25 s:** recognizable butterfly structure emerges; some shapes remain irregular or thin before resolving.
- **Frames 44–48 / 2.75–3.00 s:** blue-silver mechanical wings resolve; the last frame is visually close to the selected last anchor.
- The background, overall composition and lighting remain generally consistent, and no obvious hard edit/cut was observed in the sampled frames. The motion is still **not fully smooth**; do not mislabel a sampled-frame review as a frame-by-frame quantitative evaluation.

**Milestone interpretation:** A **manual two-anchor ComfyUI FLF2V smoke test** passed. A verified API-format export, headless MorphCurrent submission, numerical quality gates, three-anchor stitching and reproducible VRAM/timing benchmarks are **still pending**.

## Preserved original example prompt (prior to this run)

From [`ANCHOR_EXAMPLES.md`](ANCHOR_EXAMPLES.md); retained as the example's original suggested prompt rather than a claim about the MP4's unknown actual node inputs:

> A luminous translucent glass orchid slowly transforms into an intricate mechanical butterfly. Crystalline flower petals gracefully unfold into polished silver and blue glass butterfly wings. The flower's glowing center reshapes into a delicate mechanical butterfly body, while the slender stem remains aligned. Smooth continuous metamorphosis, fixed front-facing camera, the same dark background and cinematic studio lighting, no cuts, no jumps, no sudden composition changes.

## Proposed controlled experiment MC-FLF2V-002 — stronger continuity

**New positive prompt (copy into the ComfyUI positive `CLIP Text Encode` node):**

> A translucent glass orchid transforms continuously into an intricate mechanical butterfly. Every crystal petal gradually bends, folds, and reshapes into a matching silver and blue glass wing, remaining fully inside the frame. The flower's center develops into a detailed metallic butterfly body. All components remain physically connected throughout the transformation. Smooth gradual changes, stable centered composition, fixed camera, consistent lighting, no disappearing petals, no sudden cuts or abrupt changes.

**Test plan:**

1. First save a copy of the *actual working* ComfyUI graph and export its **API format** to `workflows/03_wan22_flf2v.json` after reviewing it for machine paths/secrets. Capture original seed, model names, high-/low-noise sampler steps, CFG, scheduler, precision and node IDs. Do not fabricate any.
2. Use the same **two anchor images**, both FP8 I2V diffusion experts, VAE and UMT5 text encoder previously selected in the local successful workflow. Confirm the actual loaded filenames from the exported graph.
3. Preserve the baseline's observed **640 × 368** resolution and **16 FPS**. Change frame count from **49 to 65** (valid 4n+1), giving 4.0 seconds between anchor timestamps, **4.0625 seconds encoded duration** at 16 FPS.
4. Replace only the **positive** prompt with the one above; keep negative prompt, seed and sampler/steps/CFG/scheduler settings the same **when explicitly captured**. If the current workflow uses randomized seeds, pin and record a seed for repeatable comparisons.
5. Note that **duration and prompt change together** in this proposed artistic iteration: improvement cannot be scientifically attributed to either variable alone. For a controlled E2 prompt comparison, render both original and revised prompts at **65 frames** with all other fields fixed; for a frame-count-only comparison, retain identical prompt with 49 vs 65 frames.
6. Render one clip, preserve the original 49-frame MP4, record output checksum, export frames or a contact sheet, and compare first/last fidelity, petal motion leaving frame, temporary wing distortion, jumps and full subject visibility at equal stages of the transition.
7. Measure peak VRAM, wall-clock render time and recorded model state **on the Windows A6000 host**, only when available; do not invent results or mark MC-FLF2V-002 complete until inspected.

## Integration handoff

- **Immediate blocker:** Need the owner's **real working ComfyUI API-format workflow export**. The MP4 does not contain authoritative executable node IDs.
- Keep `assets/anchors/01_glass_orchid.jpg` and `assets/anchors/02_metallic_butterfly.jpg` immutable; source samples are committed already.
- In Claude Desktop Code, read `CLAUDE.md`, `AutoCreator.md`, `docs/ARCHITECTURE.md`, `PROGRESS.md`, and this report. Inspect the real exported JSON and `/object_info`, patch semantic inputs, add mocked API/unit tests, then attempt a separately approved GPU integration smoke test.
- Never add checkpoints, generated videos, raw local user data or unverified nodes to Git. Native Windows Python only; no PowerShell or WSL.
