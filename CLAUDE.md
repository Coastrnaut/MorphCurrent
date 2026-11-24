# CLAUDE.md — MorphCurrent autonomous engineering instructions

**Project:** `Coastrnaut/MorphCurrent`, native Windows 11, Python 3.11+, isolated ComfyUI Portable on `http://127.0.0.1:8188`, RTX A6000 48 GiB.  
**Primary goal:** generate **both first and last anchor images automatically through local ComfyUI**, then generate true Wan 2.2 first/last-frame morph clips and stitch a reproducible movie.  
**Spec Kit scope:** ten features F01–F10 in [`docs/SPECKIT_FEATURE_LEDGER.md`](docs/SPECKIT_FEATURE_LEDGER.md).  
**Claude one-shot:** paste *whole* contents of [`docs/CLAUDE_DESKTOP_ONESHOT.md`](docs/CLAUDE_DESKTOP_ONESHOT.md) into Claude Desktop Code (that file is only the prompt, no wrapper).

## On every new session (mandatory)

1. Read latest repo HEAD, `git status` and diffs. Read this file, `README.md`, `AutoCreator.md`, `.specify/memory/constitution.md`, `docs/SPECKIT_FEATURE_LEDGER.md`, `docs/FULL_PIPELINE_DESIGN.md`, `PROGRESS.md`, real API workflow/binding configs, source/tests. Never discard existing work or reset the owner's branch.
2. Record reality: existing Wan 2.2 15-node API export + pinned profile, `bridge.py`/CLI, user manual FLF2V runs MC-FLF2V-001/002, first programmatic run MC-FLF2V-003. Its output matched the owner's manual video frame-by-frame, **not** a general creative-quality acceptance; peak VRAM still NOT MEASURED. Anchor T2I and reference-edit workflow exports are **absent** until locally captured.
3. **Read-only** inspect live ComfyUI `/queue`, `/history`, `/system_stats`, `/object_info` if safely accessible. If GPU occupied, **do not** start/restart models/ComfyUI, hash large checkpoints, change launch flags, interrupt others or queue additional inference. Offline code/tests/specs can proceed.
4. Verify installed Python Spec Kit via `python scripts/windows/speckit.py --status` and `--verify`; do NOT re-run `--init` if already valid. Inspect installed skill names. Reconcile latest active spec mapping in ledger and `PROGRESS.md`.
5. Pick highest-priority unblocked F01–F10, write real Spec Kit spec/plan/tasks, write failing tests when practical, implement and validate; update ledger with actual commands, evidence and commits.

## System boundaries: local GPU, permission and licensing

- No remote user media or inference upload, no public ComfyUI listener, no cloud dependency for the video/image generation. Claude Code's own cloud reasoning is a distinct matter.
- No new GPU-heavy jobs, model checkpoint downloads, custom-node installers, changed ComfyUI launch flags, blanket permissions, queue clearing or disruptive cleanup without **explicit bounded owner approval**. Prior smoke-render consent does not cover later renders. Never terminate/interrupt an ongoing job except the specific MorphCurrent-owned prompt ID after explicit instruction.
- RTX A6000 48 GiB: two full FP16 Wan 14B experts cannot both be guaranteed resident; prefer existing verified FP8 I2V workflow, monitor actual available VRAM, schedule anchor T2I/edit and Wan video model usage **sequentially**. `--highvram` does not create capacity.
- No WSL, Linux VM, Docker Linux/passthrough, PowerShell `.ps1` or Bash project scripts. Python automation only. Do not assume optional `py.exe` launcher; use `python`/`.venv\Scripts\python.exe`. Keep controller isolated from ComfyUI's embedded `python_embeded\python.exe` CUDA/PyTorch.
- No committing weights, generated video, private raw images/audio, environment files, credentials or multi-GB artifacts. Only owner-authorized small public example anchors may be committed (already present).

## Spec Kit feature lifecycle and source-of-truth

- `.specify` already exists. `script=py` in `.specify/integration.json`; installed skills live under `.claude/skills/speckit-*/SKILL.md`. Use real specify → clarify (when necessary) → plan/research → tasks → analyze → implement. Detect actual invocation rather than guessing `/speckit.*` from other Spec Kit releases. No ceremonial empty `spec.md` or invented CLI success.
- F01–F10 are **logical ledger IDs**. Real `specs/<NNN>-slug/` prefix must be collision-free; installed `create_new_feature.py --help` supports `--number` and `--short-name`, and may automatically renumber collisions. Record the returned directory and active spec. Do **one active feature at a time**, preserving all existing files and branches.
- Each feature must have verifiable requirements and acceptance tests; record plan, mock test outputs, hardware/consent evidence (or BLOCKED) and a coherent commit SHA. Update `PROGRESS.md` and feature ledger on every durable milestone. Do not mark GPU verification COMPLETE based on CI or prior unrelated render.
- `CLAUDE.md` + `.specify/memory/constitution.md`: binding rules; `docs/SPECKIT_FEATURE_LEDGER.md`: ten feature scope; `PROGRESS.md`: measured evidence; real ComfyUI exports/profile: node truth; source/tests: implemented behavior.

## Preserve and extend existing architecture

- Reuse `src/morph_studio/comfy_client.py`, `workflow_adapter.py`, `bridge.py`, `schema.py`, `timeline.py`, `media.py` and `stitcher.py`. Existing `bridge --confirm-gpu`, upload, job resume, targeted cancel, graph SHA and ffprobe checking are regression baselines. Never rewrite `03_wan22_flf2v.json` or hardcode guessed node IDs to match an intended model.
- Before automatic anchor generation, acquire real **local** T2I and reference-edit image workflow API exports (`workflows/01_anchor_t2i.json`, `02_anchor_edit.json`) and semantic bindings, inspect model license and validate nodes/choices against `/object_info`. No image model is known installed simply because Wan 2.2 video renders. Model downloads require owner approval.
- Generate A by real local T2I, B by actual image-to-image/reference-edit of A and C of B. Optional independent-T2I fallback is explicit, never silently masquerades as reference editing. The exact B image SHA must be shared by bridges A→B and B→C. All anchor and bridge stages have immutable source hashes, prompts, seeds, graph/model identity and atomic manifests.
- For Wan lengths `L=4n+1`, anchor timestamp separation `(L-1)/F`; joined 65+65 shared-boundary accepted bridges = 129 unique frames if endpoint images match. Validate actual boundary frames before deduplication; do not use xfade as fake metamorphosis. Music is optional and only owner-authorized/licensed.
- Quality tests: decoded endpoint fidelity, subject placement, mid-morph collapse/flare, optical discontinuity, freezes, blur and manual creative approval. MC-FLF2V-001/003 are evidence, not a blanket quality pass. The continuity prompt in `docs/RENDER_BASELINE_001.md` is a candidate experiment.

## Engineering and completion standards

- Typed Python 3.11+, `pathlib`, no `shell=True`, clean semantics and mocked REST tests. Local API allows loopback only; do not inject unsafe prompts into shell paths or HTTP URLs. Fail closed on graph/node/input/hash drift and missing model outputs.
- Default pipeline command must support a truly side-effect-free `--dry-run`, explicit bounded `--confirm-gpu`, resume without double-submit, safe `--status` and one GPU job at a time. Store runs in gitignored `outputs/runs`; immutable artifacts, protected `.part` downloads and user-facing errors.
- Test offline via `python -m pytest -m "not integration and not gpu"`; dedicated `-m integration` read-only on owner machine; GPU tests only opt-in. CI proves code portability, not A6000 video quality.
- Complete only after end-to-end YAML→**Comfy-generated A,B,C**→two Wan bridge MP4s→verified seam→final movie plus manifest/contact sheet, plus reproducible second run, human review and documented model/license gates. If blocked, finish safe offline work and state the exact missing step.
- Every commit should identify changed Fxx, tests/observations, artifact hashes (where appropriate), retained behavior and next feature. Avoid force-push, destructive git commands, unreviewed license changes and pretending to work asynchronously.
