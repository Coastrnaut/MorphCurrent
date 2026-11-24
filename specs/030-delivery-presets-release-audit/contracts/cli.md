# CLI contract: F30

| Command | Output | Exit |
|---|---|---|
| `deliver INPUT --preset P [--preset P ...] --out-dir D [--audio F --audio-licensed] [--audio-offset S]` | JSON `{results: [{preset, out, passed, mismatches, crop, encoder}], errors: [{preset, error}]}` | 0 all verified; 5 some failed verification; 2 any refusal (others still delivered) |
| `deliver --list-presets` | JSON presets with recipe checksums | 0 |
| `acceptance [--through 20\|30\|40] [--all]` | JSON matrix | 0 |
| `release-check [--through 30]` | JSON `{ready_for_owner_review, reasons, note, ...}` | 0 ready for owner review; 1 not ready |

ASCII output. No tagging, no network.
