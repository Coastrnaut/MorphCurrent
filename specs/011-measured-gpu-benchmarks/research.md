# Research — F11

- **Per-process VRAM on Windows**: `nvidia-smi --query-compute-apps` returned `[N/A]` used memory for every process on this machine (WDDM, observed 2026-11-24), so only whole-GPU `memory.used` is available. Decision: whole-GPU only, baseline-subtracted "rise during stage" reported as an upper bound on MorphCurrent usage *if* other processes were steady, explicitly caveated.
- **Stage window**: job events `submitted` → `completed` (UTC, 1 s resolution) bound GPU execution; widen ±1 s. ComfyUI `execution_seconds` (from `/history` timestamps, ms) is the authoritative execution duration.
- **Gap threshold**: 3× nominal interval (0.5 s default → 1.5 s) to tolerate scheduler jitter.
- **Historical data** (from docs/EXPERIMENTS.md / job records): MC-FLF2V-003 640×368×65 bridge 234.0 s; MC-RUN-001 832×480: anchors 18.7/51.7/49.5 s, bridges 497.2/494.6 s; MC-RUN-002 phoenix 49.9 s (reported 50 s), bridge 496.8 s; MC-RUN-003 anchors 20.2/51.8/49.9 s, bridges 496.0/494.1 s.
- **Estimator**: median of matching history (kind + width + height + frames, and method for anchors). Extrapolation only on request: exec × (w·h·frames)/(w0·h0·frames0) — known to under/over-estimate, labelled.
