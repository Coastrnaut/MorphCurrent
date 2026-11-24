# CLI contract: F31

| Command | Output | Exit |
|---|---|---|
| `concepts-check [--bank P] [--plan SYNC_JSON \| --target N]` | JSON check report | 0 valid; 1 problems |
| `concepts-list [--bank P] [--json]` | numbered lines (or JSON) | 0 |

Default bank `configs/concepts/engineering-film.yaml`; default target 96 (current Mozart sync plan anchors). ASCII output.
