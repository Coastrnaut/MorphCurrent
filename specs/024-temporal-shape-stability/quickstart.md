# Quickstart: validate F24

1. `.venv\Scripts\python.exe -m pytest tests/test_continuity.py -q` → all pass.
2. `... continuity outputs\runs\9785f0ae3ba196df\outputs\bridge_00001_.mp4` → flags with windows (MC-RUN-001 orchid→butterfly).
3. `... continuity-eval` → per-kind recall and false flags on the labelled real clips (honest misses listed).
4. `... repair-propose outputs\runs\run-ba2d9dbedb6189be bridge:orchid->butterfly --out %TEMP%\repair.json` → refinements and optional intermediate anchor for owner review.
5. `... repair-compare ORIGINAL.mp4 REPAIRED.mp4` → removed/persisting/new defects, endpoint check, capped verdict.
