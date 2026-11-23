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
- Git for Windows, Python 3.11+ Windows installer (including `py.exe` launcher), native FFmpeg + FFprobe in PATH.
- Claude Desktop app, **Code** tab pointed at clone. Git for Windows may be used internally by Claude Code; that does not require WSL.
- One native Windows **ComfyUI Portable NVIDIA** or manual ComfyUI installation with a compatible CUDA-enabled PyTorch and dependencies. Do **not** install both unnecessarily.
- For Spec Kit, install `uv` and official `specify-cli` separately using reviewed instructions (`uv tool install specify-cli` if appropriate). Use a recent release with the Python script backend. Do not run download/install commands automatically from inside this repository.

The Windows CUDA Toolkit is not automatically required merely to run a compatible prebuilt CUDA-enabled PyTorch wheel; specific extensions/custom nodes may have their own build requirements.

## 3. Bootstrap MorphCurrent from Windows Terminal (Command Prompt tab)

```text
cd C:\GIT
git clone https://github.com/Coastrnaut/MorphCurrent.git
cd MorphCurrent
py -3 scripts/windows/initialize.py
py -3 scripts/windows/check.py
.venv\Scripts\python.exe -m morph_studio.cli doctor --skip-comfy
```

`initialize.py` creates the local controller `.venv`, installs this package + its developer tests, runs offline pytest, and emits an environment diagnostic. It does **not** touch NVIDIA drivers, global pip packages, model files or ComfyUI's environment.

## 4. GitHub Spec Kit with Python-generated scripts

```text
py -3 scripts/windows/speckit.py --status
py -3 scripts/windows/speckit.py --init
```

The second command, only if `.specify` does not exist and the installed CLI supports the options, invokes:

```text
specify init --here --integration claude --script py
```

`--script py` is **intentional**. Spec Kit supports Bash, PowerShell and Python core automation; MorphCurrent requires the Python variant. Check whether each installed Spec Kit extension also honors Python script selection. If an extension still references a Bash/PowerShell template, report the incompatibility and keep core script execution on Python; do not silently substitute .ps1/.sh. Preserve any existing `.specify` configuration, never force-reinitialize.

After initialization, use whichever `/speckit.*` or `/speckit-*` commands the installed Claude integration actually provides. Run constitution → specify → clarify → plan → tasks → analyze → implement; inspect version-specific command names rather than guessing.

References:
- https://github.github.com/spec-kit/quickstart
- https://github.github.com/spec-kit/overview/core.html
- https://github.com/github/spec-kit

## 5. Start ComfyUI natively

For Portable at the example path:

```text
py -3 scripts/windows/launch_comfyui.py --install-root C:\AI\ComfyUI_windows_portable
```

For a manual Windows installation:

```text
py -3 scripts/windows/launch_comfyui.py --install-root C:\AI\ComfyUI --distribution manual
```

Use `--dry-run` to inspect resolved executable and arguments. The launcher binds only `127.0.0.1`, port `8188` (adjustable via `--port`), and defaults to ComfyUI's normal memory manager. A deliberate experiment can add `--memory-mode highvram` or `--memory-mode lowvram`, never by default. **`--highvram` does not fit both FP16 14B experts into 48 GiB.**

Portable CUDA verification **must use Portable's embedded Python**:

```text
C:\AI\ComfyUI_windows_portable\python_embeded\python.exe -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

For manual ComfyUI, substitute that installation's own `.venv\Scripts\python.exe`. Testing `import torch` inside `C:\GIT\MorphCurrent\.venv` is not meaningful: the controller intentionally does not require PyTorch.

## 6. Safe offline and live checks

```text
py -3 scripts/windows/check.py
.venv\Scripts\python.exe -m morph_studio.cli doctor --skip-comfy
py -3 scripts/windows/check.py --check-comfy
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
