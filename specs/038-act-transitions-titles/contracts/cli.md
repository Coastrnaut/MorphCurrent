# CLI contract: F38

All output ASCII; exit codes 0 ok, 1 flags, 2 refusal.

- `titles-check [--titles configs/film/titles.yaml] [--storyboard configs/sequences/engineering-film.yaml] [--vertical] [--json]`
  Resolves overlays and runs the safe-area check. Overlaps and clipping are warnings (exit 0); a flagged block exits 1.
- `titles-render MOVIE OUT [--titles ...] [--storyboard ...] [--vertical]`
  Renders a new file and prints the record JSON. Exit 2 on a missing font or movie, empty text, or an existing output.
- `act-boundaries [--storyboard ...] [--sync-plan configs/film/sync-plan.json] [--window 6] [--json]`
  One line per boundary (or JSON). Exit 0; exit 2 on an anchor-count mismatch.
