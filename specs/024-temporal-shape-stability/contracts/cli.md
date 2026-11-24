# Contract: F24 CLI

| Command | Output | Exit |
|---|---|---|
| `continuity CLIP [--metrics]` | ContinuityReport JSON | 0 no flags, 13 flags |
| `continuity-eval [--labels configs/qa_labels.json]` | EvaluationReport JSON (skips missing local clips, says so) | 0 |
| `repair-propose RUN_DIR BRIDGE_TASK --out FILE` | writes RepairProposal JSON (refuses overwrite); prints it | 0 |
| `repair-compare ORIGINAL REPAIRED` | RepairComparison JSON | 0 candidate improvement, 14 otherwise |

All offline, ASCII-safe output; nothing renders.
