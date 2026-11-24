# Quickstart — F11

```cmd
.venv\Scripts\python.exe -m pytest -m "not integration and not gpu"
.venv\Scripts\python.exe -m morph_studio.cli estimate configs\sequences\organic-machines.yaml
.venv\Scripts\python.exe -m morph_studio.cli perf-report outputs\repro\run-ba2d9dbedb6189be
```
Expected: estimate ≈ 20/52/50 s anchors + ≈495 s bridges (ESTIMATED from MC-RUN history); perf-report for MC-RUN-003 shows per-stage execution times equal to the job records, VRAM summary from the run (no timestamped samples exist for pre-F11 runs → window peaks NOT MEASURED).

GPU benchmark matrix (owner approval required): one sampled `render --confirm-gpu --sample-vram` into a fresh root at 832×480 (cold models) and immediately again into another fresh root (warm), plus a 640×368 variant storyboard.
