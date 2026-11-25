# CLI contract: F40

Common: `--storyboard configs/sequences/engineering-film.yaml`, `--runs-root outputs/runs`, `--log` (F39 film log). ASCII; exit 0 ok, 1 attention needed, 2 refusal.

- `film-assemble [--preview] [--audio FILE --audio-licensed] [--offset S] [--out MP4]` — writes the master and record; exit 2 with the blocker list when blocked.
- `film-deliver MASTER [--preset NAME ...] [--out-dir DIR] [--audio FILE --audio-licensed]` — exit 1 if any preset failed.
- `film-provenance ASSEMBLY_JSON [--out JSON]` — exit 1 if incomplete.
- `film-gates [--ledger docs/SPECKIT_FEATURE_LEDGER.md] [--accepted configs/film/accepted-blockers.yaml] [--json]` — exit 1 if any F31–F40 row is unresolved.
