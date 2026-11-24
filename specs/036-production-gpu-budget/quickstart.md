# Quickstart: F36

1. `history-ingest` → adds the measured F29 bridges (65 and 81 frames) and other verified jobs once.
2. `prod-budget configs\sequences\engineering-film.yaml` → per-act GPU hours with labels; batches ≤ 2 h each.
3. `prod-approve configs\sequences\engineering-film.yaml --act spark --note "pilot act"` then `prod-batch configs\sequences\engineering-film.yaml --act spark` → batch storyboards in `outputs\production\engineering-film\`.
4. Owner renders each batch: `render outputs\production\engineering-film\spark-b01.yaml --confirm-gpu`.
5. `prod-status configs\sequences\engineering-film.yaml` → progress, ETA, ratios, zero duplicates.
