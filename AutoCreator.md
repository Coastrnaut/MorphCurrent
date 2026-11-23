# AutoCreator — MorphCurrent staged autonomous engineering roadmap

## Mission
Develop a reproducible, **local** Deforum-style continuous-morph video system operated from Claude Desktop Code on **native Windows 11 only**, without WSL or GPU passthrough, with an NVIDIA RTX A6000 (48 GiB) and ComfyUI REST/WebSocket.

This is a feature-by-feature engineering contract. Read `CLAUDE.md` and `docs/ARCHITECTURE.md` before doing work. Preserve this ledger and keep actual progress in `PROGRESS.md`.

## Creative acceptance standard
A passing output should show an uninterrupted, intentional *physical metamorphosis*: discernible subject structures mutate over time while camera, palette and composition evolve coherently; endpoints are faithful to anchor images; segment joins don't flash, freeze or jump. Crossfades between unrelated images are **not** a pass.

## Workstreams

### W0. Reproducible environment and dependency audit
- Inspect Windows 11 host, Git for Windows, Python 3.11+, controller .venv, distinct ComfyUI Python, native FFmpeg, ffprobe, CUDA in ComfyUI, GPU utilization and models; no WSL.
- Record manifest of GPU architecture, driver, ComfyUI revision, custom nodes and checkpoint SHA256/precision/licenses.
- Enforce no model downloads or untrusted custom-node installation without owner approval.
- Establish CI-offline unit tests and local hardware-only test markers.
- Profile FP8, staged FP16 or offload without assuming FP16 fits in 48 GiB; record OOM events as data.
**Gate:** clean offline test run, inventory or explicit missing-prerequisites report.

### W1. Deterministic storyboard compiler
- Pydantic v2 schema: anchors, transition graph, defaults, visual continuity contract, seeds, beat timeline, reference IDs, model profiles.
- Validate IDs, monotonic timing, no missing refs, output dimensions, valid 4n+1 frame lengths and constraints.
- Compile into content-addressed DAG with immutable run manifest and stable seed derivation (master seed + content ID).
- Add previews and CLI plan/validate/dry-run.
**Gate:** a 3-anchor storyboard compiles into two contiguous, beat-timed transitions with reproducible manifests.

### W2. Model and workflow binding
- Obtain actual API-format export for reference-guided anchor generation and Wan 2.2 FLF2V.
- Map semantic fields to node ID and input (e.g. seed, width, height, text, start_image, end_image, length, output).
- Validate node `class_type` and input schemas against ComfyUI `/object_info`.
- Fail with actionable diagnostics for missing custom nodes/weights; no hardcoded guessed IDs.
**Gate:** deterministic graph patch tests and real API validation.

### W3. Anchor synthesis and continuity
- Generate first anchor via T2I; next anchor via reference editing when model permits.
- Keep palette, lighting, subject center, silhouette, perspective, focal length and aspect ratio compatible.
- Add optional semantic geometry/material correspondence planner and low-res contact-sheet approval.
- Record source prompts/negative prompts/ref weights/seed/model IDs.
**Gate:** anchor pairs available as reproducible image files with a continuity review.

### W4. Video bridge generation
- Upload start/end anchors; patch a verified Wan 2.2 FLF2V workflow; submit `/prompt`, follow `/ws`, poll `/history/{prompt_id}` after completion.
- Implement bounded retry, timeout, persistent job registry, clean cancellation and artifact verification.
- One GPU render at a time initially; grouped model scheduling avoids thrashing.
- Experiment direct metamorphosis, camera passage and intermediate anchors; compare steps, CFG, sampler and precision with fixed inputs.
**Gate:** real local clip with observed endpoint fidelity, motion quality and logged VRAM.

### W5. Seam-safe video and beat-driven audio
- Analyze audio onset, beat grid and sections; allow manual BPM/downbeat correction.
- Generate 4n+1 frames per bridge from a beat duration; define explicit duration approximation/retime policy.
- Probe codecs/frame rates/dimensions, normalize clips, compare boundaries, drop only true duplicate frames, test join for jumps.
- FFmpeg compose without shell injection; optionally interpolate later, preserve audio offset, mux final master.
**Gate:** three anchors yield continuous, correctly timed MP4 with recorded seam scores and no forced dissolve.

### W6. Automated quality and selective rerender
- Generate contact sheets and temporal diagnostics for blur, freeze, flicker, color delta, perceptual seam gap, motion direction and endpoint fidelity.
- Rank candidates with metrics plus manual review; avoid overclaiming objective scores.
- Rerender only failed clip DAG nodes, reusing stable anchors and successful bridges.
**Gate:** one failed bridge requeued without invalidating unrelated work.

### W7. Creative expansion
- LLM-compiled physical transformation prompts and optional *local LLM* backend.
- Adaptive intermediate anchor insertion for high semantic/visual distance.
- Loop mode, soundtrack controls for camera speed/color/glow, multiple delivery resolutions, preview/proxy rendering.
- Pluggable video models and benchmark profiles after Wan baseline; license/compatibility gating.
**Gate:** user-facing sequence recipe reproducible across two clean runs.

### W8. Reliability and production polish
- Native Windows paths, Unicode and long-path handling, Python-only setup/launch/diagnostics/Spec Kit helpers, importable package, CLI help, structured logs and ignored assets.
- Resumable interrupted jobs, snapshot/version migration, content hash cache, optional metrics dashboards.
- End-to-end acceptance documentation and re-render instructions.
**Gate:** clean-machine setup instructions and demonstrable local pipeline.

## Sequencing / engineering discipline
1. Write acceptance tests for each stage before runtime integration.
2. Use stable, small changes and update `PROGRESS.md` after each batch.
3. Provide reviewable experiment tables rather than choosing the fastest preset without visual evidence.
4. For any limitation, mark BLOCKED and do not invent test results.
5. Do not force-push or bypass branches/protections; request human action only for true permissions, hardware or licensed downloads.

## Spec Kit workflow (when installed)
Check `specify --help`. Prefer the repository Python helper `py -3 scripts/windows/speckit.py --status` and `--init` to set up `specify init --here --integration claude --script py`, after checking for existing `.specify` and avoiding destructive reinitialization. Follow with Claude's installed `/speckit.constitution` (or equivalent), `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.analyze`, `/speckit.implement` for successive workstreams. CLI/skills naming can change; inspect installed version rather than asserting syntax blindly.

## Handoff one-shot
The full copy/paste autonomous instruction is maintained in `docs/CLAUDE_DESKTOP_ONESHOT.md`. It is the canonical one-shot. Start it from Claude Desktop Code in the cloned repo.

## W0-W8 native Windows requirements
1. Development scripts must be Python, not PowerShell or Bash; no GPU passthrough, WSL, Linux Docker or native Linux installations.
2. Windows Python `.venv\\Scripts\\python.exe` is an orchestration environment only. Detect and respect ComfyUI Portable's embedded Python or a manual ComfyUI-specific venv.
3. The standard entry points are `py -3 scripts/windows/initialize.py`, `check.py`, `launch_comfyui.py`, `speckit.py`. Keep them safe, idempotent where possible and testable without GPU.
4. Spec Kit generated automation must be `--script py`. If the installed CLI/extension lacks Python script routing, report the limitation rather than silently switching to .ps1 or .sh.
5. Test on Windows GitHub Actions Python 3.11/3.12; use the Windows local A6000 only for separately approved smoke/benchmark jobs. Never conflate CI offline success with validated CUDA video rendering.
6. `doctor --strict` provides a readiness gate: host/tooling only with `--skip-comfy`; GPU + ComfyUI when used without it. Record both failure and success evidence in `PROGRESS.md`.
