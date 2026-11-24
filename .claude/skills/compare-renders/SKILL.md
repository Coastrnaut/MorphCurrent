---
name: compare-renders
description: Compare morph clip candidates under identical inputs and log visible defects, seam mismatches, and actual performance.
---
# Compare renders

1. Keep anchors, seed family, prompt and duration fixed for controlled comparisons, varying one parameter at a time.
2. Generate contact sheets and endpoint comparisons from real media; report missing files clearly.
3. Record precision, checkpoint hash, steps, CFG, sampler, execution time, peak VRAM, resolution and frames.
4. Flag blur, freeze, scene-cut, dissolve, style drift, mismatched endpoints, camera discontinuities.
5. Annotate metrics vs human creative judgment separately in `docs/PROGRESS.md`; choose winners only after video review.

Windows-only: invoke existing Python .py helpers in scripts/windows/; do not use WSL, .ps1 or .sh. Keep ComfyUI's Python separate from the controller venv. Spec Kit generated scripts must use --script py.

Use `python scripts/windows/speckit.py --init` to initialize/repair Python-only Spec Kit, and `--verify` to validate installed scripts and Claude command references. The optional Windows `py.exe` launcher is not required. Do not execute generated `.ps1` scripts.
