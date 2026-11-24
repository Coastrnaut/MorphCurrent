# CLI contract — F11

```
python -m morph_studio.cli perf-report RUN_DIR [--models-cache outputs/model_hashes.json]
python -m morph_studio.cli estimate STORYBOARD [--history configs/perf_history.json] [--extrapolate]
python -m morph_studio.cli render STORYBOARD --confirm-gpu --sample-vram   # now also writes RUN_DIR/vram_samples.json
```
Both new commands read local files only (no network, no GPU) and print JSON. Exit 0 on success, 2 on missing/invalid input.
