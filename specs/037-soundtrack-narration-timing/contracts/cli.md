# CLI contract: F37

| Command | Output | Exit |
|---|---|---|
| `sync-report STORYBOARD [--plan P]` | JSON sync report | 0 gate passed; 1 failed; 2 count mismatch |
| `warp-report [--plan P]` | JSON warp report | 0 ok; 1 flags |
| `animatic STORYBOARD [--run R] [--audio F --audio-licensed] [--offset S] [--plan P] [--out O]` | JSON animatic record | 0 ok; 1 probe mismatch; 2 refusal |
| `captions STORYBOARD [--bank B] [--out O]` | JSON {out, cues} | 0 |
| `narration-check SCRIPT STORYBOARD [--out O]` | JSON check | 0 ok; 1 flags; 2 unknown anchor |
| `click-track BEATMAP [--music F] [--out O]` | JSON {out, clicks} | 0 |
| `beatmap-verify BEATMAP --owner NAME [--correct I=T ...] [--out O]` | JSON beat map | 0; 2 refusal |

Defaults: plan `configs/film/sync-plan.json`; outputs under `outputs/`. ASCII output.
