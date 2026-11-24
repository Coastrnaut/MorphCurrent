# Onboard automatic first/last image generation in ComfyUI

**Why this is needed:** The existing Wan 2.2 FLF2V workflow consumes **two supplied still images**. It does **not** automatically generate the glass orchid, metallic butterfly or mechanical phoenix. The existing repo successfully submitted the Wan video stage, but its `workflows/01_anchor_t2i.json` and `workflows/02_anchor_edit.json` have **not** yet been exported and the required image-generation checkpoint licenses/installations have not been verified.

This guide is for **Spec Kit F02–F04** in [`SPECKIT_FEATURE_LEDGER.md`](SPECKIT_FEATURE_LEDGER.md). Follow native Windows Python-only development. Do not install a new image model or restart ComfyUI while an owner's GPU smoke render is active.

**Current decision record and measured state:** [`ANCHOR_MODEL_DECISION.md`](ANCHOR_MODEL_DECISION.md) (F02; no image weights installed as of 2026-11-24). Use `morphcurrent baseline` for the live state and `morphcurrent workflow-inspect <export>` before writing a binding profile.

## 1. Inspect the local environment first (read-only)

From **Windows Command Prompt**, with `C:\GIT\MorphCurrent` checked out:

~~~cmd
cd /d C:\GIT\MorphCurrent
python scripts\windows\check.py --check-comfy
python scripts\windows\speckit.py --verify
.venv\Scripts\python.exe -m morph_studio.cli workflow-check
~~~

Inspect `http://127.0.0.1:8188/object_info` and model folders under `C:\AI\ComfyUI_windows_portable\ComfyUI\models` to identify real T2I and image-edit nodes/weights. Read and record installed model names, file type, license, ComfyUI revision and memory demands without disrupting a running video job. The Wan VAE/UMT5/FP8 I2V files are **video** dependencies and do not certify a separate image-generation pipeline.

## 2. Select compatible local image workflows

For **first anchor A**, choose an installed or owner-approved text-to-image model with a valid ComfyUI graph, controllable prompt/seed/dimensions, and an image output. FLUX- or Qwen-Image-family workflows are *candidates*, not asserted installed models; evaluate each against available RTX A6000 48 GiB and model license/terms. Favor an image model and resolution aligned with the Wan video workflow (compositions centered, dark backgrounds, stable subject scale). Check required text encoders/VAEs for this **specific** T2I model rather than assuming the Wan video components can be reused.

For **anchor B from A** (and C from B), prefer a real **reference image editing or image-to-image** model/workflow. Its graph must accept an image reference and a target-concept prompt. If only T2I is available, a **consciously selected** `independent_t2i` fallback can generate a separate target image using shared style/composition cues; it is less reliable for structural consistency and is **not** called reference editing. Do not auto-switch a storyboard-declared `reference_edit` anchor to T2I without consent. Mark reference-edit capability BLOCKED until actual model graph works.

Avoid simultaneous residency of heavy image and Wan 14B diffusion models; schedule T2I/edit, then video in separate sequential stages. Download new model weights/custom nodes only with owner permission, after checking official sources, hashes and licensing. There is no validated model download URL to commit until such a model is actually chosen.

## 3. Prove and export two real API graphs

When the user has authorized an image-model test and the current queue is idle:

- Load a T2I image template **with the actual installed model**, enter the Orchid prompt, set a stable seed and target dimensions, then render one image successfully. Export **Save (API Format)** to `workflows/01_anchor_t2i.json`.
- Load a reference-edit template with the Orchid image as input, enter the Butterfly target and seed, then render one visually compatible image. Export **Save (API Format)** to `workflows/02_anchor_edit.json`.
- For each graph, read actual `class_type`, node ID, `inputs` and output mappings, and validate against `GET /object_info`. Build a **new independent** semantic binding profile for that graph under `configs/profiles/`. Include hash assertions similar to the known-good `wan22_flf2v.binding.json`. Do not duplicate/video node mappings by name without validating them.
- Export only after a successful manual image-generation smoke test. Do not create an empty placeholder with fake nodes. Inspect the exported JSON for absolute private paths and remove only nonexecuting sensitive UI metadata; if changes affect the executable graph, recompute graph hash and revalidate.

## 4. Target semantics for source-code implementation

| Role | T2I workflow | Reference-edit workflow |
|---|---|---|
| `positive_prompt` | Desired subject A | Target B with change instructions |
| `negative_prompt` | Optional negative if model supports it | Optional negative if supported |
| `seed` | Stable deterministic seed | Stable edited-anchor seed |
| `width`, `height` | Image output geometry, validated schema | Image output geometry if exposed |
| `reference_image` | Not present | MUST exist and point to A's uploaded bytes |
| `model_choice` | Actual installed image checkpoint if changeable | Actual installed edit checkpoint if changeable |
| `output` | Real SaveImage/image history node | Real SaveImage/image history node |

Roles are design targets; **no node IDs or class types are specified here** because these graphs have not yet been obtained. Copy exactly what the installed ComfyUI exposes, validate types/ranges/choice lists, and fail closed if the workflow does not support a role.

## 5. Automated quality and provenance contract

A generated anchor should be stored as immutable PNG/JPEG plus image SHA256, prompt, seed, parent/reference SHA (for edited anchors), graph SHA, checkpoint SHA if measured, dimensions, creation timestamp and the actual ComfyUI `/history` result. The first and last anchor must have matching intended subject position/camera/palette/lighting without forced recoloring of originals. Subject appearance is judged with contact sheets and human review, not an ungrounded score.

Once A and B are generated, feed them as real image files into existing `src/morph_studio/bridge.py`; preserve the verified Wan API export, FP8 model choices and queue guard. The same B output bytes must appear in both neighboring bridge jobs. The full acceptance test is storyboard YAML → generated orchid A, edited butterfly B, edited phoenix C → two Wan clips → final movie and manifest, with *no* manually supplied endpoint images.

## 6. If blocked, state the exact missing prerequisite

Use a checklist such as: `T2I model absent`, `edit model absent`, `model license not reviewed`, `checkpoint file missing`, `not enough VRAM`, `ComfyUI queue busy`, `API-format export missing`, `node schema mismatch`, `owner GPU approval required`. Complete mocked tests and dry-run planning without a GPU where possible. Do not call an image-model feature complete until locally validated output exists.

For canonical end-to-end contracts see [`FULL_PIPELINE_DESIGN.md`](FULL_PIPELINE_DESIGN.md), and for the ten-feature implementation gates see [`SPECKIT_FEATURE_LEDGER.md`](SPECKIT_FEATURE_LEDGER.md).
