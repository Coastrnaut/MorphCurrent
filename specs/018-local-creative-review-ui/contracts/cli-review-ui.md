# Contract: `morphcurrent review-ui`

```text
morphcurrent review-ui [--runs-root outputs/runs] [--host 127.0.0.1] [--port 8765]
                       [--storyboard PATH ...] [--repo-root .]
```

- Plan view lists `configs/sequences/*.yaml` plus each `--storyboard`.
- Non-loopback `--host` → exit 2 with an error naming the allowed hosts; nothing is bound.
- Prints `Review UI: http://<host>:<port>/ (Ctrl+C to stop)`; serves until interrupted; exit 0.
- `morphcurrent review RUN TASK DECISION [--note]` is unchanged and writes the identical entry.
