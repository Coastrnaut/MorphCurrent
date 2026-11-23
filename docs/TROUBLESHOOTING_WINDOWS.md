# Native Windows 11 troubleshooting

All examples assume Windows Terminal / Command Prompt using Python. No WSL, PowerShell scripts or GPU passthrough.

| Symptom | Diagnosis / resolution |
|---|---|
| `py` not recognized | Install the official Windows Python launcher, or run the script with a native Python 3.11+ executable. The controller requires Python >= 3.11. |
| `python -m venv` fails | Inspect installation permissions, antivirus interference, PATH and available disk space; ensure working in a writable native Windows directory. |
| `ModuleNotFoundError: morph_studio` | Run `py -3 scripts/windows/initialize.py` and invoke the controller through `.venv\Scripts\python.exe`. |
| `ffmpeg` or `ffprobe` missing | Install a trusted Windows build and add the directory containing `ffmpeg.exe` and `ffprobe.exe` to Windows PATH; restart the terminal and rerun doctor. |
| `nvidia-smi` fails | Verify Windows NVIDIA RTX A6000 driver, GPU visibility in Device Manager and conflicting processes; restart after driver changes when necessary. |
| `torch.cuda.is_available()` false | Run the check using **ComfyUI's** embedded/dedicated Python, inspect its torch build, installed CUDA-enabled wheel and NVIDIA driver; installing torch in the controller won't help. |
| `launch_comfyui.py` cannot find entrypoint | Pass the folder containing either `ComfyUI\main.py` + `python_embeded\python.exe` for Portable, or `main.py` for manual. Review `--dry-run`. |
| Port 8188 already in use | Another ComfyUI process may be running. Inspect processes and check the existing localhost endpoint; do not start a second instance blindly. Or select another localhost `--port` and matching controller URL. |
| `/object_info` lacks Wan FLF node | Check ComfyUI revision and nodes; do not fabricate class types or IDs. Export the actual working API graph after controlled installation. |
| CUDA out of memory | Check GPU usage, resolution, frame count, activations, FP8 availability, staged/offloaded experts. Two FP16 14B experts alone exceed 48 GiB; `--highvram` is not a workaround. |
| `specify` not found | Install current official `specify-cli` and verify it is on PATH; then `py -3 scripts/windows/speckit.py --status`. |
| Spec Kit init offers PowerShell or Bash | Use core command `specify init --here --integration claude --script py`, or the repository's `speckit.py --init`. If a third-party extension lacks Python templates, record incompatibility; do not silently switch. |
| Git shows widespread line-ending changes | Check Git `core.autocrlf` and `.gitattributes`, retain LF for Python/YAML/JSON/Markdown; avoid broad line-ending-only commits. |
| Windows path length issue | Use short repository/model roots where practical (`C:\GIT`, `C:\AI`) and review Windows long-path configuration rather than truncating files. |
| Video output exists already | FFmpeg wrapper defaults to `-n`; explicit overwrite only when authorized. |
| Claude Desktop cannot find tools | Verify local Code tab project folder, Git for Windows installation, Python executable and PATH; do not add WSL as workaround. |

**Evidence-based reporting:** Log actual Windows version, driver, ComfyUI Python path, graph node IDs, checkpoint hashes, VRAM usage and FFmpeg version. When a prerequisite is absent, mark BLOCKED and complete offline Python tests first.
