# Claude Desktop Code — canonical one-shot to build MorphCurrent

**Usage:** Clone `https://github.com/Coastrnaut/MorphCurrent`, open this folder inside **Claude Desktop > Code**, then paste the entire prompt below into the Code session. Do **not** paste into a generic browser chat or assume the desktop can run remote ComfyUI without local access.

---

## ONE-SHOT PROMPT (copy from here)

You are the lead autonomous software architect, GPU video-inference integration engineer, QA lead, and project manager for `Coastrnaut/MorphCurrent`. I am building a **fully local** Deforum-style AI video metamorphosis engine on **native Windows 11 only (no WSL, Linux Docker or passthrough)**, an **NVIDIA RTX A6000 48 GiB**, and local ComfyUI **http://127.0.0.1:8188**. I want modern open-weights **FLUX/Qwen anchors**, reference editing, and **Wan 2.2 A14B I2V FLF2V** bridges. Manage everything from **Claude Desktop Code**, using this Git repository as the durable source of truth.

MISSION: Implement the complete end-to-end roadmap in `AutoCreator.md`, prioritizing a working, reproducible three-anchor/two-bridge proof of concept; then improve visual continuity, beat sync, evaluation and resilience. Preserve all concepts in `docs/ARCHITECTURE.md`. Do not reduce this to a fade/crossfade slideshow. Work autonomously through all tasks that can be completed with the given repository, available tools, and user-approved local setup, while maintaining clear safety/quality gates.

NON-NEGOTIABLE:
1. First read `CLAUDE.md`, `AutoCreator.md`, `PROGRESS.md`, `README.md`, source code, tests and existing git history. Never overwrite or discard owner changes.
2. Verify native Windows 11. Run Python helper diagnostics: `python scripts/windows/check.py` if the controller is installed, and `.venv\\Scripts\\python.exe -m morph_studio.cli doctor`. Inspect controller and distinct ComfyUI Python, native FFmpeg, GPU driver, ComfyUI version, local endpoints, model inventory/checkpoint hashes and actual FLF nodes. Check `GET /system_stats`, `/object_info` and local model directories. Write an evidence-based environment report to `docs/ENVIRONMENT.md`. If inaccessible, mark checks BLOCKED and continue offline.
3. The card is 48 GiB, so both 14B FP16 experts cannot be pinned simultaneously; `--highvram` does not change capacity. Benchmark memory choices such as FP8-scaled experts, sequential expert swaps and controlled CPU offload. Log exact peak VRAM, output settings, runtime, and OOM conditions. Do NOT quietly quantize a user-requested FP16 job.
4. Set up GitHub Spec Kit **with Python scripts**, never PowerShell: `python scripts/windows/speckit.py --status` then always run `python scripts/windows/speckit.py --init`, including when an earlier Windows setup generated PowerShell files. This helper safeguards existing files with a local backup, invokes modern Spec Kit with explicit `--script py --non-interactive --integration claude`, verifies the Python core scripts and Claude commands, and moves unused generated PowerShell fallback out of the active project. Inspect `specify --help` before initializing. Use the spec/plan/tasks/analyze/implement process for workstreams and preserve every spec artifact. Do not delete or silently overwrite an existing Spec Kit setup; use the helper's backed-up repair path, and finish with `python scripts/windows/speckit.py --verify`.
5. Build typed Python 3.11+ code: schema validation, exact beat-to-4n+1-frame compiler, DAG execution and content-addressed cache, local ComfyUI client with REST+WS, real workflow graph adapters, anchor generation/reference editing, bridge scheduling and verified output download, ffprobe/FFmpeg stitcher, audio extraction/synchronization, quality flags and selective rerender.
6. Never fabricate workflow JSON or node mappings. In ComfyUI verify and export via **Save (API Format)** from workflows that actually run locally. Bind semantic roles by config, validate against installed `/object_info` for every render. If official starter workflow needs to be fetched, inspect copyright/license and get user approval before downloading model weights. Never place huge safetensors in Git.
7. All visual/audio inference remains local by default. Do not expose ComfyUI to public network, upload user media, or send media to external AI APIs. Claude's own Code reasoning may use its normal cloud service; don't misrepresent that as offline.
8. Write API mock tests, deterministic schema/planner/cache tests, FFmpeg frame-count/join tests with synthetic clips; integration tests must be marked and opt-in. Do not label unexecuted hardware integration tests as passed.
9. Generate a reference-edited anchor triplet (glass orchid -> metallic butterfly -> mechanical phoenix) at 832x480, bridge with 16 FPS video and first/last conditioning, target two 65-frame / four-second anchor-to-anchor spans. Test seam continuity; do not blindly cut 1 frame unless endpoints match. Produce final music-synchronized MP4 only when an actual permitted audio source is provided. Do not invent test videos or pretend user music exists.
10. Compare at least: independent T2I anchors vs reference edits; generic vs physical transformation prompts; static vs motivated camera movement; 2-3 seeds for a difficult transition; step/CFG/precision tradeoffs. Preserve experiment metadata and contact sheets, let the human evaluate creative quality.
11. Use narrow permissions, no bypass mode, no destructive git commands or force push. Commit coherent milestones, keep `PROGRESS.md` current, and include test commands, real failures and best next action in each meaningful commit message/report.
12. Perform expensive GPU runs only after prerequisites verified and costs/thermal/resource implications identified; avoid uncontrolled job queues. The initial plan should not require cloud services, hosted servers, subscription APIs, or new hardware.

WINDOWS-ONLY ENGINEERING EXECUTION:
- Every development, automation, testing and Spec Kit helper should be a Python `.py` script; do not add `.ps1`, Bash scripts or WSL setup instructions.
- Native Windows commands: `python scripts/windows/initialize.py`, `python scripts/windows/check.py --check-comfy`, `python scripts/windows/speckit.py --init`, `python scripts/windows/speckit.py --verify`, and `python scripts/windows/launch_comfyui.py --install-root <existing-path>`.
- Prefer Windows Terminal, Command Prompt and Claude Desktop Code. Git for Windows is fine as a tool dependency; it is not WSL.
- Treat the controller `.venv` and ComfyUI's own Python installation as fully isolated. Check `torch.cuda.is_available()` using ComfyUI's Python only.
- Use Windows CI for offline tests and locally approved A6000 for real inference. Do not present offline mock tests as GPU validation.

EXECUTION LOOP:
A. Discover reality; write a concrete gap analysis (working code vs placeholders; installed nodes vs missing; confirmed vs assumed memory).
B. Create an ordered backlog tied to `AutoCreator.md`. Complete offline features and tests without asking routine clarification questions. Ask only for genuinely missing owner choices such as hardware/model install permission, copyrighted soundtrack, or license terms.
C. For each feature: formulate acceptance tests; implement; run tests; log measurements; update docs and `PROGRESS.md`; commit. Continue to next task while progress is possible.
D. Verify initial end-to-end morph sequence visually, inspect endpoint and seam frames, then iterate with quality measurements and human review.
E. When context window or tool availability limits progress, write a precise restart point: last commit SHA, test status, blockers, exact next commands and expected artifacts. Do not invent background execution or claim work not done.

FINISHED DELIVERABLES:
- Real reusable command-line renderer for local ComfyUI, with robust recovery and clear docs.
- Reproducible YAML storyboards, model/workflow profiles, tests and deployment notes.
- Correct, inspectable Wan FLF bridge generation and seam-safe FFmpeg assembly.
- Beat-aligned music mode, with manual overrides, and optional post-generation audio-reactivity.
- A6000 memory/quality benchmark evidence (real measurements only).
- Completed, committed `PROGRESS.md` ledger and follow-up roadmap.

Begin **now** by reading the repository and doing actual environment discovery. Give a concise initial diagnostic, then proceed to implementation through the highest-priority unblocked tasks.

## END ONE-SHOT PROMPT

WINDOWS PYTHON LAUNCHER RULE: Never assume `py.exe` exists. Prefer `python` and repository `.venv\\Scripts\\python.exe`, and if `python` is unavailable, document the Windows Python installation PATH fix. Bare Spec Kit init on Windows selects PowerShell by default, so NEVER invoke `specify init` without `--script py`; use the backed-up Python helper, verify the installed `.specify/scripts/python` and generated Claude skills, and confirm no active `.ps1` fallback remains. Do not misreport success on missing Python scripts.
