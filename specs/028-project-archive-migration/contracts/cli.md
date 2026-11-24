# CLI contract: F28

| Command | Output | Exit |
|---|---|---|
| `project-export STORYBOARD --out P [--run DIR] [--include-media] [--include-audio] [--repo-root R]` | JSON `{out, members, bytes, plan_sha256, media_included, excluded, redactions}` | 0; 2 refused (exists, weights, audio without media) |
| `project-inspect P` | JSON inspection report | 0 ok; 2 unsafe/corrupt |
| `project-import P --dest D [--models-root M]` | JSON readiness report | 0 restored; 2 refused (inspection failed, destination not empty) |

ASCII output (`ensure_ascii`). No network access.
