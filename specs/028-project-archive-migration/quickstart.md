# Quickstart: F28

1. Export with run provenance, no media:
   `.venv\Scripts\python.exe -m morph_studio.cli project-export configs\sequences\organic-machines.yaml --run outputs\runs\run-ba2d9dbedb6189be --out %TEMP%\om.mcproj.zip`
2. Inspect — expect `ok: true`, `media_included: false`:
   `.venv\Scripts\python.exe -m morph_studio.cli project-inspect %TEMP%\om.mcproj.zip`
3. Import into a second directory — expect `plan_matches: true`:
   `.venv\Scripts\python.exe -m morph_studio.cli project-import %TEMP%\om.mcproj.zip --dest %TEMP%\om-restored`
4. Repeat step 3 — expect exit 2 (destination not empty).
5. Old F20 backup: `project-inspect` on a `run-backup` zip reports `format: 0 → 1`.
