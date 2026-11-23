# Real ComfyUI API exports required

DO NOT commit a made-up runnable workflow or machine-specific model paths.

When ComfyUI is running with the correct models and nodes, load a known working workflow, choose **Save (API Format)**, and save files as:

- `01_anchor_t2i.json` — compatible local text-to-image anchor workflow
- `02_anchor_edit.json` — compatible local reference-based image editing workflow
- `03_wan22_flf2v.json` — working Wan 2.2 first-last-frame workflow

The default official FLF2V ComfyUI tutorial is:
https://docs.comfy.org/tutorials/video/wan/wan2_2

Verify that node `WanFirstLastFrameToVideo` and both correct Wan 2.2 I2V experts are available, not just that some Wan node is installed. Real graph exports are reproducible input artifacts and can be versioned **only after inspecting for sensitive local paths**.

NOTE: Workflow JSON is model/version-sensitive. The semantic workflow adapter will reject nonexistent bindings instead of guessing.

Runtime: native Windows 11 ComfyUI only. Export API graphs on the actual Windows instance; never invent paths or node IDs. Python helpers in scripts/windows/ handle setup and launch; no WSL or PowerShell scripts.
