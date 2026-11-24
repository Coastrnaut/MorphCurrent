# Troubleshooting

All examples assume Windows Terminal / Command Prompt using Python. No WSL, PowerShell scripts or GPU passthrough.

| Symptom | Diagnosis / resolution |
|---|---|
| `'py' is not recognized` | No action needed if `python --version` reports Python 3.11+. Use `python scripts/windows/initialize.py` and `python scripts/windows/speckit.py --status`. The Windows launcher `py.exe` is optional. If `python` also fails, install Python 3.11+ and reopen Command Prompt. |
| `python -m venv` fails | Inspect installation permissions, antivirus interference, PATH and available disk space; ensure working in a writable native Windows directory. |
| `ModuleNotFoundError: morph_studio` | Run `python scripts/windows/initialize.py` and invoke the controller through `.venv\Scripts\python.exe`. |
| `ffmpeg` or `ffprobe` missing | Install a trusted Windows build and add the directory containing `ffmpeg.exe` and `ffprobe.exe` to Windows PATH; restart the terminal and rerun doctor. |
| `nvidia-smi` fails | Verify Windows NVIDIA RTX A6000 driver, GPU visibility in Device Manager and conflicting processes; restart after driver changes when necessary. |
| `torch.cuda.is_available()` false | Run the check using **ComfyUI's** embedded/dedicated Python, inspect its torch build, installed CUDA-enabled wheel and NVIDIA driver; installing torch in the controller won't help. |
| `launch_comfyui.py` cannot find entrypoint | ComfyUI Portable should be extracted to `C:\AI\ComfyUI_windows_portable`, containing `ComfyUI\main.py` and `python_embeded\python.exe`. Check for an extra nested extraction folder. Pass the actual parent directory and try `--dry-run`. See [COMFYUI_SETUP.md](COMFYUI_SETUP.md). |
| Port 8188 already in use | Another ComfyUI process may be running. Inspect processes and check the existing localhost endpoint; do not start a second instance blindly. Or select another localhost `--port` and matching controller URL. |
| Wan 2.2 loader does not list an I2V FP8 file | Confirm `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` and `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` are in `models\diffusion_models`, and `umt5_xxl_fp8_e4m3fn_scaled.safetensors` is in `models\text_encoders`; refresh or restart ComfyUI. Do not select T2V models as replacements for I2V checkpoints. |
| `/object_info` lacks Wan FLF node | Check ComfyUI revision and nodes; do not fabricate class types or IDs. Export the actual working API graph after controlled installation. |
| CUDA out of memory | Check GPU usage, resolution, frame count, activations, FP8 availability, staged/offloaded experts. Two FP16 14B experts alone exceed 48 GiB; `--highvram` is not a workaround. |
| `specify` not found | Install current official `specify-cli` and verify it is on PATH; then `python scripts/windows/speckit.py --status`. |
| Spec Kit created PowerShell `.ps1` files | Windows defaults to PowerShell for bare `specify init`, and even `--script py` can install an unused PowerShell fallback. Run `python scripts/windows/speckit.py --init` to repair an existing setup; check `--verify`. The helper backs up old managed files and moves the generated fallback out of `.specify/scripts/`. Do not delete existing user work manually. |
| Git shows widespread line-ending changes | Check Git `core.autocrlf` and `.gitattributes`, retain LF for Python/YAML/JSON/Markdown; avoid broad line-ending-only commits. |
| Windows path length issue | Use short repository/model roots where practical (`C:\GIT`, `C:\AI`) and review Windows long-path configuration rather than truncating files. |
| Video output exists already | FFmpeg wrapper defaults to `-n`; explicit overwrite only when authorized. |


**Evidence-based reporting:** Log actual Windows version, driver, ComfyUI Python path, graph node IDs, checkpoint hashes, VRAM usage and FFmpeg version. When a prerequisite is absent, mark BLOCKED and complete offline Python tests first.
| ComfyUI panel says installed models are missing | The panel can be stale; press its ↻ button or reload the tab. `GET http://127.0.0.1:8188/models/<folder>` is authoritative. Sizes there are GiB. |
| `render` exits 6 (blocked) | A required profile/workflow is missing; the JSON lists which. See [MODELS.md](MODELS.md). |
| `render` exits 7 | Waiting for review: inspect the clips/contact sheet, then `morphcurrent review RUN_DIR bridge:<a>-><b> approved` and rerun the same command. |
| `workflow-check` reports a hash mismatch | The workflow file was re-exported or edited; re-verify the profile's node IDs and update `workflow_sha256` (see MODELS.md). |
