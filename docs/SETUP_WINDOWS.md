# Windows 11 / WSL setup checklist

Target: NVIDIA RTX A6000 (48 GiB), local ComfyUI at 127.0.0.1:8188, Claude Desktop Code and a clone of this repository.

1. Install NVIDIA drivers compatible with the chosen ComfyUI/PyTorch stack. Verify `nvidia-smi`; in WSL verify GPU passthrough and that the Linux Python environment uses CUDA, not a CPU-only Torch build.
2. Install Python 3.11+ and FFmpeg with `ffprobe` in PATH. Check `python --version`, `ffmpeg -version`, `ffprobe -version`.
3. Clone `https://github.com/Coastrnaut/MorphCurrent.git` and open folder in Claude Desktop **Code**.
4. In the project folder, create a local `.venv`, then `python -m pip install -e ".[dev]"` and `python -m pytest`.
5. Confirm ComfyUI on localhost. Do **not** expose it to LAN/public Internet. If ComfyUI runs inside WSL, verify Windows can reach port 8188 intentionally and without opening external interfaces.
6. Inspect installed checkpoints and actual ComfyUI `/object_info` node names. Compare official FLF2V docs and ComfyUI implementation versions; install missing weights only after reviewing sources/license/space/cost.
7. Save **API Format** workflows to `workflows/`, populate verified binding profiles, use CLI `health`.
8. Use the one-shot in `docs/CLAUDE_DESKTOP_ONESHOT.md`; have Claude run offline tests first, then a consented single GPU smoke test.
9. Optional Spec Kit: verify `uv` and `specify --help`; run Claude integration from official docs. Avoid `--force` on existing spec files. Document actual command versions.

Avoid blanket `--highvram` or forced FP16 settings until benchmarks show they fit. The two 14B FP16 experts by themselves exceed the A6000 capacity.
