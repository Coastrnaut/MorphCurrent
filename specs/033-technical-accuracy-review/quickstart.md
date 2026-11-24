# Quickstart: F33

1. `accuracy-negatives configs\sequences\engineering-film.yaml` — expect pass for 96 anchors + 95 bridges.
2. `accuracy-checklist configs\sequences\engineering-film.yaml` — 96 entries with concept context.
3. `accuracy-impact configs\sequences\engineering-film.yaml --reject telegraph-sounder` — the rest of the Signal chain, its bridges and the final movie; nothing outside the act.
4. On the real organic-machines run: `accuracy-status configs\sequences\organic-machines.yaml --run outputs\runs\run-ba2d9dbedb6189be` — 3 pending until the owner reviews (`accuracy-review ... --run ...`).
