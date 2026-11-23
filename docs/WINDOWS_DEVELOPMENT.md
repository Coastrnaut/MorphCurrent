# Native Windows 11 development standard — Python-only automation

**Supported execution environment: Windows 11 native, NVIDIA RTX A6000 (48 GiB), ComfyUI at 127.0.0.1:8188, Claude Desktop Code.** No WSL, GPU passthrough, Docker Linux containers or Linux VM. All repo automation helpers are Python 3.11+ scripts, including GitHub Spec Kit initialization. No project PowerShell or Bash scripting.

## 1. Suggested layout

```text
C:\AI\ComfyUI_windows_portable\
    python_embeded\python.exe       # official Portable: ComfyUI's OWN torch/CUDA environment
    ComfyUI\main.py
    ComfyUI\models\
C:\GIT\MorphCurrent\
    .venv\Scripts\python.exe       # Python controller, does NOT install ComfyUI/torch
    scripts\windows\*.py
    workflows\
    configs\
    outputs\                      # ignored by Git
```

Manual Windows ComfyUI is equally valid: `C:\AI\ComfyUI\main.py` plus `C:\AI\ComfyUI\.venv\Scripts\python.exe`. Keep controller and model runtime fully isolated. Paths above are **examples only**.

## 2. Install Windows prerequisites (one time)

- NVIDIA Windows RTX A6000 driver; verify from Windows Terminal with `nvidia-smi`.
- Git for Windows, Python 3.11+ Windows installer (`python.exe` on PATH; the optional `py.exe` launcher is not required), native FFmpeg + FFprobe in PATH.
- Claude Desktop app, **Code** tab pointed at clone. Git for Windows may be used internally by Claude Code; that does not require WSL.
- One native Windows **ComfyUI Portable NVIDIA** or manual ComfyUI installation with a compatible CUDA-enabled PyTorch and dependencies. For an RTX A6000, use the [standard RTX Portable archive](https://github.com/Comfy-Org/ComfyUI/releases/latest/download/ComfyUI_windows_portable_nvidia.7z), documented as Python 3.13 / CUDA 13.0 as of 2026-11-23 (versions may change). **Do not choose** the GTX 10-series CUDA 12.6 legacy archive, and do not install both alternatives unnecessarily. See [ComfyUI Portable instructions](COMFYUI_PORTABLE_WINDOWS.md).
- For Spec Kit, install `uv` and official `specify-cli` separately using reviewed instructions (`uv tool install specify-cli` if appropriate). Use a recent release with the Python script backend. Do not run download/install commands automatically from inside this repository.

The Windows CUDA Toolkit is not automatically required merely to run a compatible prebuilt CUDA-enabled PyTorch wheel; specific extensions/custom nodes may have their own build requirements.

## 3. Bootstrap MorphCurrent from Windows Terminal (Command Prompt tab)

First check `python --version` and `where.exe python`. If Python is not on PATH, install an official Python 3.11+ distribution and reopen the shell. No `py.exe` launcher is needed.

```text
cd C:\GIT
git clone https://github.com/Coastrnaut/MorphCurrent.git
cd MorphCurrent
python scripts/windows/initialize.py
python scripts/windows/check.py
.venv\Scripts\python.exe -m morph_studio.cli doctor --skip-comfy
```

`initialize.py` creates the local controller `.venv`, installs this package + its developer tests, runs offline pytest, and emits an environment diagnostic. It does **not** touch NVIDIA drivers, global pip packages, model files or ComfyUI's environment.

## 4. GitHub Spec Kit with Python-generated scripts

```text
python scripts/windows/speckit.py --status
python scripts/windows/speckit.py --init
```

The second command, only if `.specify` does not exist and the installed CLI supports the options, invokes:

```text
specify init --here --integration claude --script py
```

**Important:** Running bare `specify init` on Windows selects PowerShell by default. Even with `--script py`, Spec Kit may also install PowerShell fallback files. The repository's `speckit.py --init` is a **verified repair** command, not a simple CLI pass-through: it snapshots existing `.specify` and generated Claude commands under ignored `.local/spec-kit-backups/`, safely regenerates in Python mode if needed using `--force --non-interactive`, checks `.specify/scripts/python/` for all expected core files, normalizes Claude's generated `python3` calls for Windows, and moves `.specify/scripts/powershell/` into the ignored backup **after** Python references pass verification. Run `python scripts/windows/speckit.py --verify` and confirm the final result. If verification fails, the fallback is preserved and no successful initialization is claimed.

Older 2026 `specify-cli` releases had a packaging bug that omitted the Python scripts despite `--script py`; this was fixed upstream (issue #3665). Upgrade the installed CLI and rerun `python scripts/windows/speckit.py --repair` if the Python files are missing. Check whether any third-party extensions support Python variants; no silent switches to `.ps1` or `.sh`.

After initialization, use whichever `/speckit.*` or `/speckit-*` commands the installed Claude integration actually provides. Run constitution → specify → clarify → plan → tasks → analyze → implement; inspect version-specific command names rather than guessing.

References:
- https://github.github.com/spec-kit/quickstart
- https://github.github.com/spec-kit/overview/core.html
- https://github.com/github/spec-kit

## 5. Download, extract, and start ComfyUI natively

Follow [COMFYUI_PORTABLE_WINDOWS.md](COMFYUI_PORTABLE_WINDOWS.md) to download the official archive and extract under `C:\AI\ComfyUI_windows_portable` (the extracted folder should directly contain `ComfyUI\main.py` and `python_embeded\python.exe`). If ComfyUI is already running, reuse it; do not start a second server.

For Portable at the example path:

```text
python scripts/windows/launch_comfyui.py --install-root C:\AI\ComfyUI_windows_portable
```

For a manual Windows installation:

```text
python scripts/windows/launch_comfyui.py --install-root C:\AI\ComfyUI --distribution manual
```

Use `--dry-run` to inspect resolved executable and arguments. The launcher binds only `127.0.0.1`, port `8188` (adjustable via `--port`), and defaults to ComfyUI's normal memory manager. A deliberate experiment can add `--memory-mode highvram` or `--memory-mode lowvram`, never by default. **`--highvram` does not fit both FP16 14B experts into 48 GiB.**

Portable CUDA verification **must use Portable's embedded Python**:

```text
C:\AI\ComfyUI_windows_portable\python_embeded\python.exe -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

For manual ComfyUI, substitute that installation's own `.venv\Scripts\python.exe`. Testing `import torch` inside `C:\GIT\MorphCurrent\.venv` is not meaningful: the controller intentionally does not require PyTorch.

## 6. Safe offline and live checks

```text
python scripts/windows/check.py
.venv\Scripts\python.exe -m morph_studio.cli doctor --skip-comfy
python scripts/windows/check.py --check-comfy
.venv\Scripts\python.exe -m morph_studio.cli doctor --strict
```

`doctor --strict` only asserts basic native Windows host/tool, NVIDIA visibility and ComfyUI health; it **does not** prove model weights or actual video inference work. Next export working **Save (API Format)** anchor and FLF2V workflows; inspect real node IDs via `/object_info` and run one controlled bridge smoke test through Claude's implementation milestones.

## 7. Windows engineering conventions

- Pathlib and Unicode/space-safe arguments for subprocesses, `shell=False`, no shell pipelines required. Do not interpolate storyboard content into commands.
- All setup/test/launch/Spec Kit helpers are Python; no PowerShell/Bash script entrypoints. Native Windows Terminal/Command Prompt is the recommended shell interface.
- Windows-only GitHub Actions tests Python 3.11/3.12 offline; CI has no GPU and cannot certify any Wan/FLUX model execution.
- Never install uncontrolled custom nodes/model weights; inventory checkpoint SHA256, licenses, versions and real memory strategies.
- Never auto-upload media, expose ComfyUI beyond loopback or overwrite output videos without explicit permission.
- Windows paths can include spaces and non-ASCII characters; do not assume C: or a specific user profile path.
- Use `.gitattributes` to keep repository text in LF even on Windows; `.venv`, GPU outputs and model weights stay out of version control.

See [troubleshooting](TROUBLESHOOTING_WINDOWS.md), [architecture](ARCHITECTURE.md) and [canonical Claude one-shot](CLAUDE_DESKTOP_ONESHOT.md).

For an existing repository initialized in PowerShell mode, run `python scripts/windows/speckit.py --status`, `python scripts/windows/speckit.py --init`, then `python scripts/windows/speckit.py --verify`. Backup files are intentionally excluded from Git; inspect them before any manual deletion.
