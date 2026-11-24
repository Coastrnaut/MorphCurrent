# PROGRESS — MorphCurrent

> Date: 2026-11-23. This document is a ledger, not a promise. Only mark a stage complete when its acceptance gate is demonstrated.

## Current snapshot
- [x] Repository created by owner; initial engineering scaffold committed via connected GitHub workflow (after initial setup).
- [x] Architecture and Claude Desktop engineering handoff documented.
- [x] Native Windows 11-only Python setup/launch/Spec Kit helpers and doctor CLI authored; Windows-only CI configured (check job status for results).
- [x] Offline storyboard / timing and local ComfyUI client starter included.
- [ ] Workflow exports from user's installed ComfyUI verified.
- [ ] A6000 environment and model inventory verified.
- [x] First two-anchor FLF2V video bridge **manually** rendered by owner, uploaded, and qualitatively inspected — see `docs/RENDER_BASELINE_001.md`. Automated MorphCurrent rendering and quantitative GPU benchmarking remain unverified.
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
| MC-FLF2V-001 | 2026-11-23 local | Owner manual Wan 2.2 Orchid → Butterfly, uploaded MP4 | **640×368**, 49 frames, 16 FPS; 3.0625 s | Steps/CFG/seed **UNKNOWN** | VRAM/time **NOT MEASURED** | Faithful anchors; transitory petal clipping and distorted wings at 0.75–1.5 s | `docs/RENDER_BASELINE_001.md`; MP4 SHA-256 `a638f6e1d58d876670ddc72c0bb773f9f6c83d93076ac3a9403c41618823120c` |

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
- [x] Owner reports successful local Wan 2.2 FLF2V smoke render; uploaded `ComfyUI_00002_.mp4` was inspected. See `docs/RENDER_BASELINE_001.md` for measured video metadata and limitations.
- [ ] Save and validate the real ComfyUI API-format workflow. The owner performed a **manual** GPU video render; no programmatic MorphCurrent render or measured VRAM/time is claimed.

## First video baseline and next trial (2026-11-23)

- [x] Reviewed owner-uploaded 49-frame H.264 baseline at 640×368 / 16 FPS, with hash, endpoint fidelity and mid-transition issues documented in `docs/RENDER_BASELINE_001.md`.
- [ ] MC-FLF2V-002: evaluate the new continuity-oriented positive prompt and a 65-frame trial; **not yet rendered**.
- [ ] Export user-run ComfyUI FLF2V graph as `workflows/03_wan22_flf2v.json`, capture sampler/seed and actual model names, and validate `/object_info` before API integration.
