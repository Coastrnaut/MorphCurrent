---
name: benchmark-vram
description: Benchmark RTX A6000 model residency, memory peaks and generation speed with explicit quality comparisons.
---
# Benchmark VRAM

1. Inspect GPU and ComfyUI state and available VRAM; avoid interfering with other workloads.
2. Baseline one render configuration and model hash. Test `--highvram` only if local launch behavior is understood and owner approves changes.
3. Measure FP8-scaled experts, staged FP16 and offload as distinct, not interchangeable policies.
4. Report peak allocated/reserved GPU memory, wall time, OOM, model load frequency and image/video quality.
5. Never claim full dual-14B FP16 residency in 48 GiB. Store measurements in an experiment CSV and explain quality tradeoffs.

Windows-only: invoke existing Python .py helpers in scripts/windows/; do not use WSL, .ps1 or .sh. Keep ComfyUI's Python separate from the controller venv. Spec Kit generated scripts must use --script py.
