# Quickstart — F03

Offline: `.venv\Scripts\python.exe -m pytest -m "not integration and not gpu"` (anchor tests use a fake ComfyUI).

GPU (BLOCKED until `configs/profiles/anchor_t2i.binding.json` exists from a real export, and the owner approves this render):
```cmd
.venv\Scripts\python.exe -m morph_studio.cli anchor --profile configs\profiles\anchor_t2i.binding.json --prompt-file prompt.txt --seed 101 --width 832 --height 480
.venv\Scripts\python.exe -m morph_studio.cli anchor --resume outputs\runs\<id> --confirm-gpu
```
Expected: first command `validated`, nothing queued; second `verified` with a PNG of 832×480 and its SHA-256 in `job.json`.
