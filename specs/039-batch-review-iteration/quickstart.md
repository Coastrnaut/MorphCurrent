# Quickstart: F39

```powershell
.venv\Scripts\python.exe -m morph_studio.cli film-review-status
```

```powershell
.venv\Scripts\python.exe -m morph_studio.cli film-act-sheet spark
```

```powershell
.venv\Scripts\python.exe -m morph_studio.cli film-review-approve-act spark
```

```powershell
.venv\Scripts\python.exe -m morph_studio.cli film-rerender-queue
```

Expected before the pilot: 191 stages, all missing. After `spark-b01` renders: its anchors and bridges show as verified with one version each; the act sheet shows one row per rendered bridge.

Tests: `.venv\Scripts\python.exe -m pytest tests/test_batch_review.py -q`.
