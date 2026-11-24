# Workflow profiles

Profiles supply low-level **actual** ComfyUI node bindings independently of the creative sequence YAML.

- `wan22_flf2v.binding.json` binds the real export `workflows/03_wan22_flf2v.json` (validated against ComfyUI 0.46.0 `/object_info` on 2026-11-23). It pins the graph's canonical hash, so a re-export fails `workflow-check` until every binding is re-verified and the hash updated.
- Check with `python -m morph_studio.cli workflow-check` (live) or add `--object-info tests/fixtures/object_info_wan22_flf2v.json` (offline). Produce a patched graph with `workflow-patch --set seed=42 --set length=81 --out <new file>`; it never submits to ComfyUI.
- `assertions` record literals the bindings depend on (for example the low-noise sampler adds no noise, so its seed is intentionally unbound).
- Save the full executable API graph under `workflows/`, not just UI-format workflow JSON.
- Check `GET /object_info` against node classes and fields before dispatch.
- Model filenames and hashes are environment-specific and should be discovered from the local installation.
- For hard scientific comparisons, version exact model hash, inference dtype and UI revision in a run manifest.
- This repository includes **no guessed bindings** (every node ID comes from a real export), no `.safetensors` weights, and no guaranteed compatible custom nodes.

Profiles are design inputs. A real GPU render requires validated local exports.

Target platform: native Windows 11, RTX A6000, local ComfyUI (Portable embedded Python or manual dedicated venv). Prefer Windows path-neutral model names in workflows; controller .venv is never the model runtime. Spec Kit automation uses Python scripts.

## Planned image-generation bindings

The current Wan profile is **real and verified**. Text-to-image and reference-edit profiles are **not yet present**. Their respective real local API exports must first be validated against ComfyUI's `/object_info` and then hash pinned with semantic bindings for prompt/negative/seed/dimensions/reference image and *image* outputs. Do not reuse Wan node IDs, invent installed image weights, or commit placeholder runnable graphs. See [docs/ANCHOR_MODEL_ONBOARDING.md](../../docs/ANCHOR_MODEL_ONBOARDING.md) and [the ten-feature ledger](../../docs/SPECKIT_FEATURE_LEDGER.md).
