# Quickstart: F30

1. Deliver the MC-RUN movie in landscape and vertical — expect two verified files, records with recipe checksums, vertical crop safe-area report:
   `.venv\Scripts\python.exe -m morph_studio.cli deliver outputs\runs\run-ba2d9dbedb6189be\final\<movie>.mp4 --preset landscape-1080p --preset vertical-1080x1920 --out-dir %TEMP%\deliver`
2. List presets: `deliver --list-presets`.
3. Acceptance through F30: `acceptance --through 30` — 30 rows.
4. Release check: `release-check` — expect exit 1 (owner-gated items remain) with reasons; nothing is tagged.
