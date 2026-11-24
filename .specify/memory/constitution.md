# MorphCurrent — Spec Kit engineering constitution

**Version:** 1.0.0  
**Effective:** 2026-11-24  
**Scope:** every future `specs/` feature; read with `CLAUDE.md` and `docs/SPECKIT_FEATURE_LEDGER.md`.

This replaces the unfilled stock constitution template. Historical feature work, working code and run evidence remain preserved and are not implicitly invalidated.

## I. Factual evidence before completion claims

Source files, real API exports, local `/object_info`, recorded `/history`, hashes, verified outputs and committed tests establish what actually works. Always distinguish DOCUMENTED, MOCKED, LOCALLY VALIDATED, GPU-VERIFIED, VISUALLY ACCEPTED and BLOCKED. Offline CI does not verify local NVIDIA inference; a successful clip does not prove peak VRAM or artistic acceptability. Preserve MC-FLF2V-001, 002 and 003 observations.

## II. Native Windows, privacy, GPU consent

Sole supported runtime is **native Windows 11**, Python 3.11+ automation, an isolated ComfyUI Portable Python/Torch environment and a loopback-only local ComfyUI server. No PowerShell `.ps1` scripts, WSL, Linux containers or assumed `py.exe`. No remote inference/media upload, custom-node/model installation, expensive GPU jobs or disruption of the owner's ongoing run without explicit permission. Read-only discovery and offline work may continue while the GPU is busy. Prior GPU approval is not blanket consent.

## III. Real ComfyUI graph contracts, test-first

Executable image and Wan workflows **must** be real `Save (API Format)` exports. Never invent node IDs or model filenames, or pretend a missing image model exists. Semantic binding profiles are hash-pinned and validated against the installed ComfyUI `/object_info`. For each feature document acceptance criteria and write offline tests/mocks before separately gated local/GPU checks. Fail closed on version drift, missing model, malformed media and unverified output.

## IV. Immutable artifacts, crash safety and observability

Every generated image and bridge video must have immutable source bytes, content hash, model/workflow identity, positive/negative prompts, seed, dimensions, parent dependencies, stage result, job ID and provenance. Resume must not double-submit GPU work. Never cache solely by prompt/seed/filename. Guard partial downloads and overwrites; record unavailable metrics as **NOT MEASURED**. No `.safetensors`, generated videos, user music/media or credentials in Git.

## V. Genuine physical metamorphosis, shared anchors and timing

A full system generates **both endpoint images** inside ComfyUI; any independent T2I fallback is explicit and is not misrepresented as reference editing. Adjacent bridges must share byte-identical anchor B. Prefer physically continuous transformations over cuts/dissolves, honor Wan 4n+1 frames and `(L-1)/FPS` anchor time, verify seam duplicate removal, use optional (never mandatory) owner-licensed soundtrack and human qualitative review.

## VI. Ten actual Spec Kit feature lifecycles

Execute exactly ten *logical* features F01–F10 from `docs/SPECKIT_FEATURE_LEDGER.md`, sequentially respecting dependencies. Check installed Python Spec Kit/Claude skill names; use **real** specify → clarify if needed → plan/research → tasks → analyze → implement. Map logical IDs to actual nonconflicting `specs/NNN-slug/` names; never overwrite prior specs or promise unique 001–010 prefixes. Update `PROGRESS.md` with evidence and a commit for each coherent step. A blocked GPU gate is not COMPLETE.

## VII. Source compatibility and governance

Preserve existing Wan bridge, repo history, local dirty state, tests and working CLI; add regression tests before incompatible changes. Use typed Python, `pathlib`, subprocess argument lists (`shell=False`), private localhost networking and minimal permissions. Amend this constitution through a separate reviewed/committed change that states migration and reconciles `CLAUDE.md` plus the feature ledger. Do not bypass test/consent gates to satisfy a schedule.

**Authority order:** `CLAUDE.md` and this constitution (non-negotiable safety), `docs/SPECKIT_FEATURE_LEDGER.md` (ten feature scope/gates), `PROGRESS.md` (measured status), real workflow exports/profiles (executable node truth), code/tests (actual implemented behavior).
