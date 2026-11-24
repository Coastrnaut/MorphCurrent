# Quickstart: F34

1. `film-storyboard --out configs\sequences\engineering-film.yaml` (default look applied) then `look-check configs\sequences\engineering-film.yaml` → ok for 191 stages.
2. `look-drift configs\sequences\organic-machines.yaml --run outputs\runs\run-ba2d9dbedb6189be` → one act, colour stats, geometry flags.
3. `look-test` → `outputs\look-test\copper-to-silicon.yaml` and `steel-accent.yaml`; owner renders both (bounded GPU) and records the choice in `selected`.
