# Development

Supported environment: **native Windows 11**, Python 3.11+, NVIDIA GPU, ComfyUI Portable on `127.0.0.1:8188`. All helper scripts are Python (no PowerShell/Bash scripts, WSL or containers). The `py.exe` launcher is optional; use `python`.

## Layout

```text
C:\AI\ComfyUI_windows_portable\   ComfyUI with its own embedded Python + PyTorch (model runtime)
C:\GIT\MorphCurrent\
  .venv\                          controller environment (no PyTorch)
  src\morph_studio\               package
  tests\                          offline tests (fake ComfyUI)
  workflows\  configs\            ComfyUI API exports, binding profiles, storyboards
  specs\  .specify\               Spec Kit specs (F01–F13 existing; F14–F40 proposed)
  outputs\                        run artifacts (gitignored)
```

Keep the two Python environments separate: never install PyTorch into `.venv`, and check CUDA with ComfyUI's own interpreter (`python_embeded\python.exe`).

## Setup

```cmd
cd /d C:\GIT
git clone https://github.com/Coastrnaut/MorphCurrent.git
cd MorphCurrent
python scripts\windows\initialize.py
.venv\Scripts\python.exe -m morph_studio.cli doctor --skip-comfy
```

`initialize.py` creates `.venv`, installs the package with dev extras and runs the offline tests. It never touches drivers, ComfyUI or model files. Install and start ComfyUI with [COMFYUI_SETUP.md](COMFYUI_SETUP.md).

## Tests

```cmd
.venv\Scripts\python.exe -m pytest -m "not integration and not gpu"
set MORPHCURRENT_COMFY_URL=http://127.0.0.1:8188
.venv\Scripts\python.exe -m pytest -m integration
```

Offline tests use a stateful fake ComfyUI (`tests/fake_comfy.py`) and real FFmpeg for clip tests. `integration` only reads `/object_info`. CI (Windows, no GPU) proves portability, not model output.

## Spec Kit

The 40-feature roadmap (F31–F40: five-minute engineering film track) and true F01–F10 GPU evidence are in [SPECKIT_FEATURE_LEDGER.md](SPECKIT_FEATURE_LEDGER.md). F11–F13 already have real specs and implementation slices; F14–F40 must be created one at a time with real spec/plan/tasks/implementation artifacts. The [Claude Desktop one-shot](CLAUDE_DESKTOP_ONESHOT.md) is **paste-only**: copy its entire contents into Claude Desktop Code, no trimming of wrappers required.


Spec Kit is installed with the Python script backend (`.specify/integration.json`: `script=py`); the Claude skills are `speckit-specify`, `-plan`, `-tasks`, `-analyze`, `-implement`, etc.

```cmd
python scripts\windows\speckit.py --status
python scripts\windows\speckit.py --verify
```

Do not run bare `specify init` on Windows (it defaults to PowerShell scripts); `speckit.py --repair` restores the Python backend with a backup in `.local/`. New features: `python .specify\scripts\python\create_new_feature.py --json --number N --short-name SLUG "description"`. Check existing `specs/001`–`013` and any concurrent new directories; capture the script-returned real spec path. Do not reinitialize an already valid Spec Kit.

## Conventions

- Typed Python, `pathlib`, subprocess argument lists (`shell=False`); never put storyboard text into commands or URLs.
- ComfyUI URL must be loopback; fail closed on graph hash, node, model or output drift.
- Commit only on the currently owner-authorized branch (usually `main`); no AI co-author trailers. Record measured results in [PROGRESS.md](PROGRESS.md).
- Never commit weights, generated media, `outputs/` or credentials. Text files are LF (`.gitattributes`).
