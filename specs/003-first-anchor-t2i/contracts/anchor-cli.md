# CLI contract — `morphcurrent anchor`

```
python -m morph_studio.cli anchor --profile PROFILE.json (--prompt TEXT | --prompt-file F) --seed N
       [--negative TEXT] [--width W --height H] [--reference IMG] [--method text_to_image|independent_t2i|reference_edit]
       [--runs-root outputs/runs] [--confirm-gpu] [--retry] [--allow-busy-queue] [--timeout S]
python -m morph_studio.cli anchor --resume JOB_DIR [--confirm-gpu]
python -m morph_studio.cli anchor-status JOB_DIR
```
Exit 0: `validated` (no consent), `downloaded`, `verified`. Exit 5: other states. Exit 2: errors. Without `--confirm-gpu` nothing is queued.
