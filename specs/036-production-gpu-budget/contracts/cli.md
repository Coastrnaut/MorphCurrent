# CLI contract: F36

| Command | Output | Exit |
|---|---|---|
| `history-ingest [--runs-root R] [--history H]` | JSON {added, skipped, total} | 0; 2 malformed history |
| `prod-budget STORYBOARD [--history H] [--max-batch-s S] [--max-jobs N] [--cold-s C]` | JSON budget | 0 |
| `prod-approve STORYBOARD --act A [--note T] [--owner O] [--revoke]` | JSON approval record | 0; 2 unknown act |
| `prod-batch STORYBOARD --act A [--out-dir D] [caps]` | JSON {files, batches} | 0; 2 not approved / exists |
| `prod-status STORYBOARD [--runs-root R] [--history H]` | JSON status | 0 ok; 1 flags or duplicates |

ASCII output. Batches are rendered with the existing `render <batch.yaml> --confirm-gpu [--max-gpu-s S]`.
