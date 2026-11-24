# Quickstart: F37

1. `sync-report configs\sequences\engineering-film.yaml` → 96 anchors, max error 0, drift 0, gate passed.
2. `warp-report` → 95 bridges pinned, speeds within 0.5–2.
3. `animatic configs\sequences\engineering-film.yaml` → `outputs\animatic\engineering-film.mp4` (cards, no audio) lasting the song length; add `--audio <licensed track> --audio-licensed` for the listening review.
4. `captions configs\sequences\engineering-film.yaml` → 96-cue SRT.
5. `click-track <beatmap.json> --music <track>` → listening preview; `beatmap-verify <beatmap.json> --owner <name>` after corrections.
