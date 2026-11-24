# CLI contract — `morphcurrent baseline`

```
python -m morph_studio.cli baseline [--url http://127.0.0.1:8188] [--skip-comfy]
                                    [--object-info FILE] [--out FILE] [--strict]
```

- Stdout: BaselineReport JSON (see data-model.md).
- `--out`: also writes the JSON; refuses if FILE exists (exit 2).
- `--skip-comfy`: no HTTP at all; `comfyui.status = "skipped"`.
- `--object-info FILE`: use a saved snapshot instead of `GET /object_info` (other GETs still made unless `--skip-comfy`).
- Exit codes: 0 report produced; 3 with `--strict` when ComfyUI unreachable or the Wan profile fails validation; 2 usage/IO error.
- HTTP methods used: GET only (`/system_stats`, `/queue`, `/object_info`).

# Library contract — `morph_studio.gates`

- `cloud_nodes(graph, object_info) -> list[str]`
- `check_gpu_gate(*, consent: bool, queue: dict, graph: dict | None = None, object_info: dict | None = None, allow_busy_queue: bool = False) -> GateDecision`
