# Quickstart — F01 validation

```cmd
cd /d C:\GIT\MorphCurrent
.venv\Scripts\python.exe -m pytest -m "not integration and not gpu"
.venv\Scripts\python.exe -m morph_studio.cli baseline --skip-comfy
.venv\Scripts\python.exe -m morph_studio.cli baseline
.venv\Scripts\python.exe -m morph_studio.cli workflow-check
```

Expected:
1. All offline tests pass (83 pre-existing + new F01 tests).
2. `--skip-comfy` prints repository facts, `comfyui.status = "skipped"`.
3. Live run prints queue state, `capabilities.text_to_image.status = "blocked"` while no image model/profile exists, `wan_flf2v = "available"`; ComfyUI queue is unchanged afterwards.
4. `workflow-check` still `ok: true` for the Wan profile (it has no cloud nodes).
