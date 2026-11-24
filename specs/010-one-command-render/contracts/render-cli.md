# CLI contract — `morphcurrent render`

```
python -m morph_studio.cli render STORYBOARD.yaml --dry-run
python -m morph_studio.cli render STORYBOARD.yaml [--confirm-gpu] [--accept-heuristics] [--allow-busy-queue]
       [--sample-vram] [--t2i-profile P] [--edit-profile P] [--bridge-profile P] [--runs-root outputs/runs]
python -m morph_studio.cli render --status RUN_DIR
```
| Exit | Meaning |
|---|---|
| 0 | dry run printed; or validated without consent; or complete |
| 6 | BLOCKED (missing profile / unverified dependency) |
| 7 | awaiting human review (`morphcurrent review RUN_DIR bridge:<a>-><b> approved`) |
| 5 | a stage failed (see manifest) |
| 2 | invalid input / error |
