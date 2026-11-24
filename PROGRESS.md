# PROGRESS — MorphCurrent

> Date: 2026-11-23. This document is a ledger, not a promise. Only mark a stage complete when its acceptance gate is demonstrated.

## Current snapshot
- [x] Repository created by owner; initial engineering scaffold committed via connected GitHub workflow (after initial setup).
- [x] Architecture and Claude Desktop engineering handoff documented.
- [x] Native Windows 11-only Python setup/launch/Spec Kit helpers and doctor CLI authored; Windows-only CI configured (check job status for results).
- [x] Offline storyboard / timing and local ComfyUI client starter included.
- [ ] Workflow exports from user's installed ComfyUI verified.
- [ ] A6000 environment and model inventory verified.
- [ ] First two-anchor video bridge rendered and inspected.
- [ ] Continuous three-anchor seam and beat sync validated.
- [ ] Benchmark tables and quality regression suite completed.

## Milestone sequence
M0 — Native Windows environment discovery, independent controller/ComfyUI Python, Python-only Spec Kit, pinned dependencies, Windows CI/offline contract tests.
M1 — Model inventory, real ComfyUI API workflows and semantic node adapters.
M2 — Reference-guided anchors with immutable artifact manifests.
M3 — Wan 2.2 FLF2V video bridge scheduling, retries, error tracking, VRAM benchmarking.
M4 — Seam inspection / FFmpeg chain, beat-aligned durations and audio mux.
M5 — Automatic transition planning, intermediate anchors, multi-candidate quality review.
M6 — Higher resolution + frame interpolation + resumable multi-song render jobs.

## Experiment ledger
| ID | Date | Change | Resolution | Steps/CFG/Seed | VRAM/time | Quality observation | Evidence |
|---|---|---|---|---|---|---|---|
| pending | — | No GPU trials yet | — | — | NOT MEASURED | NOT REVIEWED | — |

## First run checklist
- Require native Windows 11, no WSL. Log NVIDIA driver, GPU VRAM, CUDA and PyTorch versions from ComfyUI's **own Python environment**.
- Log `ComfyUI --version` or Git commit, API availability, node types, models and checkpoint hashes.
- Export verified API-format anchor and Wan FLF2V workflows (do not substitute UI-format JSON).
- Record exact model license, precision, loading policy, and `--highvram` configuration.
- Run `python scripts/windows/check.py`, storyboard validation and planning CLI; use `doctor --skip-comfy` before attempting GPU health.
- Benchmark 832x480 65-frame 16fps clips before attempting 720p.
- Log all blockers rather than fabricating success.

## Windows Python launcher / Spec Kit repair hardening (2026-11-23)
- [x] Replace all repository setup commands using the optional `py.exe` launcher with `python` and make VS Code task execution use `python`.
- [x] Upgrade Python Spec Kit initialization to handle existing PowerShell-mode installs; preserve backed-up files, verify actual `.py` core scripts and Claude command references, and move generated PowerShell fallback out of the active tree.
- [ ] On the owner's Windows host, run `python --version`, `python scripts/windows/speckit.py --init`, then `python scripts/windows/speckit.py --verify` and record actual CLI version and results.
- [ ] Real local CUDA/ComfyUI inference remains untested; do not confuse Windows CI unit tests with A6000 evidence.

## Example FLF2V anchor pair generated (2026-11-23)

- [x] Two matched 16:9 Glass Orchid → Metallic Butterfly endpoint images created from original AI-generated artwork, manually composed/cropped for consistent framing and stored as small JPEG fixtures in `assets/anchors/`.
- [x] Documented the positive transformation prompt, manual ComfyUI first/last-frame loading and Python-only optional staging helper (`docs/ANCHOR_EXAMPLES.md`).
- [ ] Owner still needs to copy or upload these images in the local running ComfyUI and complete a short Wan 2.2 I2V/FLF2V smoke render.
- [ ] Save and validate the real ComfyUI API-format workflow. No GPU video inference was performed or claimed by this commit.
