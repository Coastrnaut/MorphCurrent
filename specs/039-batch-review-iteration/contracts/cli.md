# CLI contract: F39

Common options: `--storyboard configs/sequences/engineering-film.yaml`, `--runs-root outputs/runs`, `--log` (default `outputs/reviews/<film>.batch-review.jsonl`). ASCII output; exit 0 ok, 1 attention needed, 2 refusal.

- `film-review-status [--act ACT] [--json]` — per-act totals and one line per stage in review order. Exit 1 when any stage is rejected or stale.
- `film-review STAGE {approved,rejected,pending} [--note N] [--reviewer owner]` — append one decision. Exit 2 for an unknown/unrendered stage or bad decision.
- `film-review-approve-act ACT [--reviewer owner]` — bulk-approve eligible bridges; prints the count.
- `film-rerender-queue [--write OUT] [--json]` — queue and estimate; `--write` writes a rerender storyboard (exit 2 if it exists).
- `film-act-sheet ACT [--out PNG]` — act contact sheet; exit 1 if no bridge of the act is rendered.
- `film-compare STAGE [--a SHA] [--b SHA] [--out MP4]` — side-by-side of two versions (default: the last two); exit 2 if fewer than two versions.
