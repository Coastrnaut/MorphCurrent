# Data model — F01

## GateDecision
| Field | Type | Rule |
|---|---|---|
| allowed | bool | true only when `reasons` is empty |
| reasons | list[str] | codes: `consent`, `queue_busy`, `cloud_node` (with detail text) |
| queue_running / queue_pending | int | from `GET /queue` |
| cloud_nodes | list[str] | `"<node_id> (<class>)"` |

## BaselineReport (JSON, schema 1)
- `schema`, `generated_at` (UTC ISO), `morphcurrent_version`
- `repository`: `head`, `branch`, `dirty_files` (int) or `unknown`
- `comfyui`: `status` (`ok`/`unreachable`/`skipped`), `version`, `argv`, `devices[{name, vram_total, vram_free}]`, `vram_label: "snapshot (not peak)"`
- `queue`: `running[]`, `pending[]` prompt IDs, `gpu_busy`
- `inventory`: role → installed filenames (`checkpoints`, `diffusion_models`, `text_encoders`, `vae`, `loras`), `sha256: "NOT MEASURED"`
- `cloud_api_node_classes` (int count; local-only policy rejects them)
- `profiles`: per `configs/profiles/*.binding.json`: `profile`, `workflow`, `ok`, `errors`, `warnings`
- `capabilities`: `text_to_image`, `reference_edit`, `wan_flf2v` → `{status: available|blocked, reason}`
- `gpu_snapshot`: nvidia-smi `memory_used_mib`, `memory_total_mib`, `label: "snapshot (not peak)"` or `unavailable`
- `peak_vram: "NOT MEASURED"`
