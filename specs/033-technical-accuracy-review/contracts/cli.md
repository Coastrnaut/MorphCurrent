# CLI contract: F33

| Command | Output | Exit |
|---|---|---|
| `accuracy-checklist STORYBOARD [--bank B]` | JSON per-anchor checklist with concept context | 0 |
| `accuracy-review STORYBOARD ANCHOR --verdict accurate\|reject\|waive (--sha256 H \| --image F \| --run R) [--fail ITEM ...] [--note T] [--reviewer N] [--log L]` | JSON recorded verdict | 0; 2 refusal |
| `accuracy-negatives STORYBOARD` | JSON text-free check | 0 pass; 1 missing |
| `accuracy-impact STORYBOARD --reject A [--reject B ...]` | JSON impact + regeneration seeds | 0; 2 unknown anchor |
| `accuracy-status STORYBOARD [--run R] [--log L]` | JSON status | 0 gate passed; 1 not passed |

Default log `outputs/reviews/<storyboard name>.accuracy.jsonl`. ASCII output.
