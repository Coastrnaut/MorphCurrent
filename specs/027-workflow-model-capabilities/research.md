# Research: F27

- **Decision**: Build entries on the existing workflow_adapter checks (hash, capability contract, node-in-graph, object_info presence) instead of a new validator. **Rationale**: one source of truth for graph checks (Principle III). **Alternatives**: separate schema — rejected (drift).
- **Decision**: Classify problems by running the checks separately (hash → stale-hash; class absent from object_info → missing-node; capability/role/node-in-graph/parse errors → contract-error; cloud class → cloud-node) rather than parsing message strings. **Rationale**: robust classification.
- **Decision**: Model roles from loader input names: `unet_name` → diffusion, `clip_name*` → text encoder (or CLIP vision on `CLIPVisionLoader`), `vae_name` → VAE, `ckpt_name` → checkpoint, `lora_name` → LoRA, `model_name` on `UpscaleModelLoader` → upscaler. **Rationale**: matches ComfyUI core loaders used in the real exports.
- **Decision**: Model presence is checked only when `--models-root` is given (else `present: null`); weights are never hashed here (`models-hash` stays the opt-in tool). **Rationale**: CLAUDE.md forbids casual hashing of enormous weights.
- **Decision**: Catalogue as JSON data mirrored from MODELS.md, with a test asserting every SHA-256 in the MODELS.md table appears in it. **Rationale**: machine-readable plus drift guard.
- **Decision**: Verdict rules per Clarifications; a changed numeric constraint compares object_info min/max/step for each bound role when both entries have constraints.
- **Decision**: Selection file written atomically (`.part` + `os.replace`); history entries never edited; rollback appends a rollback entry restoring the `previous` of the latest effective selection.
