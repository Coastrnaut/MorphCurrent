# CLI contract: F29

| Command | Output | Exit |
|---|---|---|
| `experiment-plan DEF [--history FILE]` | JSON `{experiment, out_dir, candidates, deferred, estimated_total_s}` | 0; 2 invalid definition |
| `experiment-run DEF [--confirm-gpu] [--url U] [--runs-root R] [--history FILE]` | JSON `{ran, reused, skipped, stopped, measured_exec_s}` | 0; 2 refusal |
| `experiment-rate DEF CANDIDATE SCORE [--note T]` | JSON rating | 0; 2 unknown candidate / bad score |
| `experiment-report DEF` | writes report.md + report.json; prints JSON summary | 0 |

ASCII output. Without `--confirm-gpu` the run validates candidates only.
