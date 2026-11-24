# CLI contract: F32

| Command | Output | Exit |
|---|---|---|
| `film-storyboard --plan P --bank B --acts A --out O [--audio F]` | JSON `{out, anchors, bridges, acts, text_to_image, plan_sha256}` | 0; 2 refusal (counts, bridge range, existing output, bad acts) |
| `film-report STORYBOARD [--plan P] [--history H]` | JSON film report | 0; 2 invalid storyboard |

Defaults: `--plan configs/film/sync-plan.json`, `--bank configs/concepts/engineering-film.yaml`, `--acts configs/film/acts.yaml`, `--history configs/perf_history.json`. ASCII output; no GPU.
