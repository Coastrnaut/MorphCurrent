# Contract: F20 CLI

| Command | Behaviour | Exit |
|---|---|---|
| `run-compare RUN_A RUN_B [--frames]` | JSON RunComparison | 0 reproduced, 10 differs/incomplete |
| `replay STORYBOARD --reference RUN --runs-root EMPTY_DIR [--confirm-gpu] [--frames]` | refuses a non-empty runs root; without `--confirm-gpu` validates only; with it renders then compares | as `render` when not complete; else as `run-compare` |
| `audit [--repo-root .]` | JSON AuditReport | 0 no errors, 11 errors |
| `run-backup RUN --out ARCHIVE.zip [--allow-missing-jobs]` | refuses existing archive; refuses missing jobs unless allowed | 0 / 2 |
| `run-restore ARCHIVE.zip --runs-root DEST` | verifies every checksum; refuses unsafe paths and existing targets | 0 / 2 |
| `acceptance [--all]` | JSON matrix of F01–F20 (or F01–F40) | 0 |

No command tags releases, uploads, or contacts ComfyUI except `replay --confirm-gpu`.
