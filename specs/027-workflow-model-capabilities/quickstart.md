# Quickstart: F27

1. Offline registry — expect three entries with status `offline-unverified`:

   `.venv\Scripts\python.exe -m morph_studio.cli registry`

2. Live, read-only (ComfyUI running) — expect three `ready` entries and exit 0:

   `.venv\Scripts\python.exe -m morph_studio.cli registry --live --models-root C:\AI\ComfyUI_windows_portable\ComfyUI\models --strict`

3. Preview — expect verdict `compatible` with no changes:

   `.venv\Scripts\python.exe -m morph_studio.cli registry-diff configs\profiles\wan22_flf2v.binding.json configs\profiles\wan22_flf2v.binding.json`

4. Selection/rollback against a temporary `--selection` file: without `--approve` exit 2 and no file written; with it, the history grows; `registry-rollback` restores the default.
