# CLAUDE.md — MorphCurrent engineering constitution

You are working in **Coastrnaut/MorphCurrent**, a local video-generation orchestration engine targeting an **RTX A6000 48 GiB**, **native Windows 11 only**, and ComfyUI at `http://127.0.0.1:8188`.

## Session start (mandatory)
1. Read `README.md`, `AutoCreator.md`, `docs/ARCHITECTURE.md`, `PROGRESS.md`, this file and git status/diff.
2. Inspect the live ComfyUI `GET /system_stats` and `GET /object_info` only if localhost is reachable; otherwise explicitly mark hardware checks BLOCKED and develop/test offline.
3. Enforce native Windows 11 for local development (no WSL, Linux containers or passthrough). Inspect Windows Python, native FFmpeg, ComfyUI's separate Python environment, NVIDIA driver and installed nodes/checkpoints. Run `python -m morph_studio.cli doctor` where possible.
4. Pick the next uncompleted, testable milestone; establish baseline tests before editing.
5. Write an execution plan to `PROGRESS.md`; update measured results, commands, artifacts and next steps afterward.

## Non-negotiable rules
- **Only local ComfyUI inference**. No remote prompt/image/audio upload or public server endpoint without explicit owner approval. Claude Desktop itself may use cloud reasoning.
- Do not download weights, install arbitrary custom nodes, change ComfyUI launch flags, delete user media, or make costly GPU runs without checking prerequisites and recording user consent as appropriate.
- FP16 `high_noise + low_noise` 14B models do **not** both fit fully resident in 48 GiB. Benchmark FP8 vs staged FP16 and optional offload; `--highvram` is not unlimited VRAM. Avoid concurrent anchor+video model residency.
- Treat API-exported ComfyUI workflows as authoritative; **never invent node IDs or pretend placeholders can render**. Validate `class_type`, input names and model filenames against `/object_info`.
- Never edit original anchor files in place. Outputs are immutable per render manifest hash. Support resume after partial failures.
- Never cache only by seed, prompt or filename; incorporate workflows, node maps, precision, model hashes, reference images and output settings.
- Distinguish numerical metrics from human creative judgments; automated CLIP/LPIPS scores are heuristics, not quality proof.
- Do not use FFmpeg `xfade` as the default for metamorphosis; don't trim endpoints without checking seam similarity. Preserve the audio track and exact beat positions.
- Avoid GPL-only model/code redistribution when licenses conflict; inventory all model and custom-node terms. Honor original music rights.
- Windows 11 **native only**: no WSL, Linux VM, Linux Docker backend or GPU passthrough. Use Python scripts for setup, testing, ComfyUI launch and **Spec Kit**; path-safe `pathlib`, subprocess argument arrays, `shell=False`, no hardcoded `C:\\` paths in library code.
- Prefer incremental, typed Python code with focused pytest coverage, with integration tests clearly marked and never run on a real GPU by surprise.
- No blanket shell permissions or uncontrolled installers in `.claude/settings.json`. Do not author .ps1 scripts or embed Windows PowerShell automation. Never store credentials or bypass permission prompts.

## Development flow
Feature: requirements -> design -> code -> unit tests -> mocked API integration -> ComfyUI smoke tests -> A6000 benchmarks -> quality review -> documentation -> git commit.
For native Windows Spec Kit use `py -3 scripts/windows/speckit.py --status` then, if new, `--init`. Enforce official `specify init --here --integration claude --script py`; preserve existing setup and flag incompatible third-party extensions. If GitHub Spec Kit is installed, use `/speckit.constitution`, `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.analyze`, `/speckit.implement` in that order as appropriate. Detect the actual integration commands and don't invent them.
Prefer self-contained branches/commits with concrete acceptance evidence; keep main functional and do not force-push.

## Definitions of done
- Unit tests passing and lint/type checks configured.
- Change verified against real exported ComfyUI node schemas for any rendering code.
- All run flags, seed/precision data, FFmpeg invocation and model/version identifiers logged.
- `PROGRESS.md` and relevant docs updated.
- Never describe a storyboard plan or fake workflow as completed render.

## Offline and failure behavior
If ComfyUI or weights aren't available, do not block all work. Complete offline client mocks, schema, timing planner, job persistence and FFmpeg tests and clearly identify what needs on-machine verification. Fail closed on missing node bindings rather than silently choosing a node.

## Native Windows engineering experience
- Read `docs/WINDOWS_DEVELOPMENT.md`. Use `py -3 scripts/windows/initialize.py` and `py -3 scripts/windows/check.py` from native Windows Terminal / Command Prompt, not `.ps1` or WSL shell scripts.
- Do not install ComfyUI / torch into controller `.venv\\Scripts\\python.exe`. ComfyUI Portable has its own `python_embeded\\python.exe` and manual ComfyUI has its own `.venv`; verify CUDA in the latter environment, not the controller.
- Prefer `py -3 scripts/windows/launch_comfyui.py --install-root <path>` with loopback bind and default VRAM mode. The script supports `--dry-run` and opt-in `--memory-mode highvram`; do not change running ComfyUI settings unexpectedly.
- Use `python -m morph_studio.cli doctor --skip-comfy` for offline host checks and `doctor` only when ComfyUI is available. CI runs on Windows runners and has **no A6000 GPU**.
- Only supported automation scripting language for new infrastructure helpers is Python 3.11+. Git for Windows may underlie Claude Code's command tool but do not write .sh/.ps1 project scripts.
- Prevent automatic output overwrites and avoid destructive cleanup; default FFmpeg joining uses `-n` unless overwrite was explicitly requested.
