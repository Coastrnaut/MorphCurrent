# Quickstart — F02

Offline:
```cmd
.venv\Scripts\python.exe -m pytest -m "not integration and not gpu"
.venv\Scripts\python.exe -m morph_studio.cli workflow-check
```
After the owner approves a model set and exports a graph (procedure in `docs/MODELS.md`):
```cmd
.venv\Scripts\python.exe -m morph_studio.cli workflow-inspect workflows\01_anchor_t2i.json
.venv\Scripts\python.exe -m morph_studio.cli workflow-check --profile configs\profiles\anchor_t2i.binding.json
```
Expected: inspect reports `ok: true`, no cloud nodes, all model literals installed; workflow-check `ok: true` with the capability contract satisfied.
