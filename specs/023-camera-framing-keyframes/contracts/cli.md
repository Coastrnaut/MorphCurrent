# Contract: `morphcurrent camera-check`

```text
morphcurrent camera-check STORYBOARD [--run RUN_DIR] [--repo-root .]
```

JSON: `{transitions: [...satisfiability + clause/label], anchors: [...framing/crops], verdict: ok|issues|pending_anchors}`.
Exit 0 when ok or pending anchors; 12 when any transition is unsatisfiable or any anchor is off target / outside a crop. `unknown` and `not_verifiable` are reported but do not fail. Offline; no ComfyUI contact.
