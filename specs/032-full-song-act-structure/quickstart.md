# Quickstart: F32

1. Generate the film storyboard:
   `.venv\Scripts\python.exe -m morph_studio.cli film-storyboard --out configs\sequences\engineering-film.yaml`
   → 96 anchors, 95 transitions, 5 acts, 5 text-to-image anchors.
2. Dry run report: `film-report configs\sequences\engineering-film.yaml` → per-act frames/seconds, total unique frames, coverage vs 358.8 s, labelled GPU hours.
3. Existing storyboards unchanged: `plan configs\sequences\organic-machines.yaml` still gives plan `ba2d9dbe…`.
