# Quickstart: F35

1. `lineage configs\sequences\engineering-film.yaml` → per-act max depths 17/9/9/28/28, over limit 12 → exit 1.
2. `lineage-propose configs\sequences\engineering-film.yaml` → re-anchor points inside Spark, Logic and Scale; proposed file in `outputs\proposals\`; `lineage` on it → max depth ≤ 12.
3. `lineage-drift configs\sequences\organic-machines.yaml --run outputs\runs\run-ba2d9dbedb6189be` → 3-point curve.
4. `lineage-shared --run outputs\runs\run-ba2d9dbedb6189be` → 2/2 bridges match.
