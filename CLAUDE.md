# CLAUDE.md — MorphCurrent engineering constitution

You are working in **Coastrnaut/MorphCurrent**, a local video-generation orchestration engine targeting an **RTX A6000 48 GiB** and ComfyUI at `http://127.0.0.1:8188`.

## Session start (mandatory)
1. Read `README.md`, `AutoCreator.md`, `docs/ARCHITECTURE.md`, `PROGRESS.md`, this file and git status/diff.
2. Inspect the live ComfyUI `GET /system_stats` and `GET /object_info` only if localhost is reachable; otherwise explicitly mark hardware checks BLOCKED and develop/test offline.
3. Detect OS, Python, FFmpeg, ComfyUI revision and installed nodes/checkpoints; do not assume models are present or `--highvram` was used.
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
- Make all operations usable on Windows and/or WSL; safe path handling, subprocess argument arrays, no shell=True, no hardcoded C:\\ paths.
- Prefer incremental, typed Python code with focused pytest coverage, with integration tests clearly marked and never run on a real GPU by surprise.
- No generic unlimited Bash allowances in `.claude/settings.json`. Never store secrets or credentials. Do not bypass permission prompts.

## Development flow
Feature: requirements -> design -> code -> unit tests -> mocked API integration -> ComfyUI smoke tests -> A6000 benchmarks -> quality review -> documentation -> git commit.
If GitHub Spec Kit is installed, use `/speckit.constitution`, `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.analyze`, `/speckit.implement` in that order as appropriate. Detect the actual integration commands and don't invent them.
Prefer self-contained branches/commits with concrete acceptance evidence; keep main functional and do not force-push.

## Definitions of done
- Unit tests passing and lint/type checks configured.
- Change verified against real exported ComfyUI node schemas for any rendering code.
- All run flags, seed/precision data, FFmpeg invocation and model/version identifiers logged.
- `PROGRESS.md` and relevant docs updated.
- Never describe a storyboard plan or fake workflow as completed render.

## Offline and failure behavior
If ComfyUI or weights aren't available, do not block all work. Complete offline client mocks, schema, timing planner, job persistence and FFmpeg tests and clearly identify what needs on-machine verification. Fail closed on missing node bindings rather than silently choosing a node.
