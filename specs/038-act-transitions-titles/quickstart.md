# Quickstart: F38

```powershell
.venv\Scripts\python.exe -m morph_studio.cli titles-check --vertical
```

```powershell
.venv\Scripts\python.exe -m morph_studio.cli act-boundaries
```

```powershell
.venv\Scripts\python.exe -m morph_studio.cli titles-render outputs\animatic\engineering-film.mp4 outputs\titles\engineering-film-titled.mp4
```

Expected: all 7 overlays fit both areas (the opening card shrinks for 9:16); boundaries at anchors 18/28/38/67 with proposals 18→13, 38→43, 67→70 and none for 28; the titled copy has the same frame count and duration as the input, and the input hash is unchanged.

Tests: `.venv\Scripts\python.exe -m pytest tests/test_titles.py -q`.
