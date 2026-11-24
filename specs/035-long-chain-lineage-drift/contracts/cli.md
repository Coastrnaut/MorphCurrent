# CLI contract: F35

| Command | Output | Exit |
|---|---|---|
| `lineage STORYBOARD [--config C]` | JSON lineage report | 0 within limit; 1 over limit |
| `lineage-drift STORYBOARD --run R [--config C]` | JSON drift curve | 0 no flags; 1 flags |
| `lineage-propose STORYBOARD [--run R] [--out O] [--config C]` | JSON proposals (+ written file) | 0; 2 refusal (output exists) |
| `lineage-shared --run R` | JSON shared-anchor results | 0 all match; 1 mismatch/unchecked |

Default config `configs/film/lineage.yaml`; default proposal path `outputs/proposals/<name>.reanchored.yaml`. ASCII output.
