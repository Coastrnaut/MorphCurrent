# Quickstart: validate F20

1. `.venv\Scripts\python.exe -m pytest tests/test_release.py -q` → all pass.
2. `.venv\Scripts\python.exe -m morph_studio.cli run-compare outputs\runs\run-ba2d9dbedb6189be outputs\runs\run-cefb16ae1db47f4d` → every verified stage identical (MC-RUN-001 vs MC-RUN-003 evidence), verdict reported.
3. `.venv\Scripts\python.exe -m morph_studio.cli audit` → 0 errors; Wan and Qwen model hashes listed from `docs/MODELS.md`.
4. `... run-backup outputs\runs\run-ba2d9dbedb6189be --out %TEMP%\run.zip` then `... run-restore %TEMP%\run.zip --runs-root %TEMP%\restored` → then `run-compare` original vs restored → reproduced.
5. `... acceptance` → 20 rows; `release_ready` false while gates are pending.

See [contracts/cli.md](contracts/cli.md).
