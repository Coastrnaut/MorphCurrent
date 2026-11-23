# Windows 11 native-only setup (Python automation)

This short checklist is intentionally secondary to [WINDOWS_DEVELOPMENT.md](WINDOWS_DEVELOPMENT.md).

There is **no** WSL, Linux installation, GPU passthrough, Docker Linux backend or PowerShell scripting in MorphCurrent's supported development workflow.

1. Verify `python --version` (>= 3.11); the `py` launcher is optional. Install Git for Windows, Python 3.11+, Windows FFmpeg/FFprobe, current RTX A6000 Windows driver and native Windows ComfyUI (Portable NVIDIA or dedicated Python environment).
2. Clone repository to `C:\\GIT\\MorphCurrent` and open folder in **Claude Desktop > Code**.
3. In Windows Terminal or Command Prompt, run `python scripts/windows/initialize.py`.
4. Run `python scripts/windows/speckit.py --status`, install/upgrade official Spec Kit CLI if absent or outdated, then `python scripts/windows/speckit.py --init` to create or repair the existing Claude integration using `--script py`. Verify with `python scripts/windows/speckit.py --verify`; the helper moves the unused PowerShell fallback to ignored backup.
5. Run `python scripts/windows/launch_comfyui.py --install-root C:\\AI\\ComfyUI_windows_portable` (adjust to your actual installed path), then `python scripts/windows/check.py --check-comfy`.
6. Verify PyTorch CUDA availability from **ComfyUI's own Python**. Export real API-format workflows and validate node IDs.
7. Paste `docs/CLAUDE_DESKTOP_ONESHOT.md` into Claude Desktop Code.

These scripts never install model weights/drivers automatically or force `--highvram`. Run only one initial GPU job at a time and record actual benchmarks.
