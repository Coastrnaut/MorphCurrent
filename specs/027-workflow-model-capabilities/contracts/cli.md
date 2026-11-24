# CLI contract: F27

| Command | Output | Exit |
|---|---|---|
| `registry [--profiles DIR] [--object-info FILE \| --live] [--models-root DIR] [--strict]` | JSON `{offline, entries: [...]}` | 0; 1 with `--strict` and any non-ready entry |
| `registry-diff CURRENT CANDIDATE [--object-info FILE]` | JSON preview | 0 (verdict in output); 2 unreadable profile |
| `registry-select --profile P --approve [--note T] (--object-info FILE \| --live) [--models-root DIR] [--selection FILE]` | JSON `{selected, active, history_length}` | 0; 2 refusal |
| `registry-rollback --capability C [--selection FILE]` | JSON `{capability, active}` | 0; 2 nothing to roll back |

All output is ASCII (`ensure_ascii`). `--live` is a read-only GET `/object_info` on 127.0.0.1:8188.
