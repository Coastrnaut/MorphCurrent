# Example Wan 2.2 FLF2V anchors — Glass Orchid → Metallic Butterfly

These two **generated** sample assets provide a consistent pair of still frames for
the first MorphCurrent Wan 2.2 I2V **first-frame/last-frame** video test.
They were derived from the two panels of a single original generated image,
with labels/borders removed and matched framing against the same dark
studio background. Both Git-tracked JPEG files are **1280 × 720 (16:9)**.

| Role | Image in repository | ComfyUI input node |
| --- | --- | --- |
| Starting frame (A) | `assets/anchors/01_glass_orchid.jpg` | First **Load Image** |
| Ending frame (B) | `assets/anchors/02_metallic_butterfly.jpg` | Second / last **Load Image** |

No model weights, licensed stock images, or generated videos are committed.
The original high-quality PNG copies can also be downloaded from the conversation
where these sample images were created; the JPEGs are compressed to keep Git history small.

## Stage into your already-installed ComfyUI (Python only)

ComfyUI normally loads user-uploaded images from its `ComfyUI/input` folder.
The files in `C:\GIT\MorphCurrent\assets\anchors` will not automatically appear
in the **Load Image** dropdown until uploaded or staged.

From native **Windows Command Prompt**:

```cmd
cd /d C:\GIT\MorphCurrent
git pull
python scripts\windows\stage_example_anchors.py --install-root C:\AI\ComfyUI_windows_portable --dry-run
python scripts\windows\stage_example_anchors.py --install-root C:\AI\ComfyUI_windows_portable
```

The script checks for the expected Portable layout; it **does not** install
anything or start/stop ComfyUI. It copies only two small example files to:

```text
C:\AI\ComfyUI_windows_portable\ComfyUI\input\01_glass_orchid.jpg
C:\AI\ComfyUI_windows_portable\ComfyUI\input\02_metallic_butterfly.jpg
```

If a destination exists with identical bytes, it is left untouched. If a
destination conflicts, the operation fails before copying anything; only use
`--overwrite` after reviewing the conflict. You can alternatively upload each
file using ComfyUI's **Load Image** node without using the script.

## Configure a first video smoke test

1. In ComfyUI, open the **Wan 2.2 14B FLF2V** graph.
2. In the **first Load Image** node choose `01_glass_orchid.jpg`.
3. In the **last Load Image** node choose `02_metallic_butterfly.jpg`.
4. In the **positive CLIP Text Encode** prompt box paste the motion prompt below.
5. Keep the workflow's current negative prompt and compatible sampler settings
   for the first experiment. Start with **640 × 360**, **49 frames**, **16 fps**
   if the graph supports those settings. 49 is a valid 4n+1 frame count.
6. Run **one** video, inspect first/middle/last frames, and measure VRAM.
   If the test fails, capture the console errors, model names, memory usage
   and graph settings; do not silently change precision or loading policy.
7. Only after success, export **Save (API Format)** to
   `workflows/03_wan22_flf2v.json` and verify actual node IDs
   against the running ComfyUI `/object_info` endpoint.

**Positive motion prompt:**

> A luminous translucent glass orchid slowly transforms into an intricate
> mechanical butterfly. Crystalline flower petals gracefully unfold into
> polished silver and blue glass butterfly wings. The flower's glowing center
> reshapes into a delicate mechanical butterfly body, while the slender stem
> remains aligned. Smooth continuous metamorphosis, fixed front-facing camera,
> the same dark background and cinematic studio lighting, no cuts, no jumps,
> no sudden composition changes.

**Negative prompt:** Leave the existing example's default unchanged for
the initial smoke test.

### Model paths used by this workflow

- `models\vae\wan_2.1_vae.safetensors`
- `models\text_encoders\umt5_xxl_fp8_e4m3fn_scaled.safetensors`
- `models\diffusion_models\wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors`
- `models\diffusion_models\wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors`

See [ComfyUI Portable setup](COMFYUI_PORTABLE_WINDOWS.md) for exact `C:\AI` paths
and instructions. User has since reported a successful **manual** FLF2V render and uploaded the video for inspection. See [baseline MC-FLF2V-001 and proposed continuity prompt](RENDER_BASELINE_001.md). The example's original prompt above remains preserved for comparison. Actual exported node graph, selected seed/sampler, checkpoint identities and programmatic MorphCurrent integration still require verification.

## After the first smoke test

The user's 49-frame video was reviewed: orchid and butterfly endpoints matched closely, while some petals rose partially out of frame and butterfly wings were temporarily distorted in the middle. **Do not overwrite this initial example prompt**. Use [MC-FLF2V-001 review and MC-FLF2V-002 revised prompt](RENDER_BASELINE_001.md) for the 65-frame candidate experiment.
