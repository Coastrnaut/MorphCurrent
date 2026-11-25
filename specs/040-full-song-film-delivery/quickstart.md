# Quickstart: F40

```powershell
.venv\Scripts\python.exe -m morph_studio.cli film-gates
```

```powershell
.venv\Scripts\python.exe -m morph_studio.cli film-assemble
```

Before rendering, `film-assemble` refuses with 95 blockers (every bridge missing) and `film-gates` lists the open owner gates. After all acts are rendered and approved:

```powershell
.venv\Scripts\python.exe -m morph_studio.cli film-assemble --audio <licensed track> --audio-licensed
```

```powershell
.venv\Scripts\python.exe -m morph_studio.cli film-deliver outputs\film\<master>.mp4
```

```powershell
.venv\Scripts\python.exe -m morph_studio.cli film-provenance outputs\film\<master>.assembly.json
```

Tests: `.venv\Scripts\python.exe -m pytest tests/test_film_delivery.py -q`.
