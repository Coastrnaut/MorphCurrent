# CLI contract: F34

| Command | Output | Exit |
|---|---|---|
| `look-check STORYBOARD [--language L] [--look NAME]` | JSON look report | 0 ok; 1 mismatches; 2 bad definition/look |
| `look-drift STORYBOARD --run R [--language L]` | JSON drift report | 0 no flags; 1 flags |
| `look-test [--storyboard S] [--act A] [--count N] [--out-dir D] [--language L]` | JSON {files} | 0; 2 refusal (exists, unknown act) |
| `film-storyboard ... [--language L] [--look NAME]` | as F32 | as F32 |

Defaults: language `configs/film/visual-language.yaml`, storyboard `configs/sequences/engineering-film.yaml`, act `spark`, count 5, out-dir `outputs/look-test`.
