# Workflow profiles

Profiles supply low-level **actual** ComfyUI node bindings independently of the creative sequence YAML.

- Start from `wan22_flf2v.binding.example.json`; replace `REPLACE_AFTER_API_EXPORT` with real node IDs and input names.
- Save the full executable API graph under `workflows/`, not just UI-format workflow JSON.
- Check `GET /object_info` against node classes and fields before dispatch.
- Model filenames and hashes are environment-specific and should be discovered from the local installation.
- For hard scientific comparisons, version exact model hash, inference dtype and UI revision in a run manifest.
- This repository includes **no guessed runnable bindings**, no `.safetensors` weights, and no guaranteed compatible custom nodes.

Profiles are design inputs. A real GPU render requires validated local exports.
