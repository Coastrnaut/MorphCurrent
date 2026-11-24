# MorphCurrent Constitution

## Core Principles

### I. Factual evidence before completion claims

Source files, real API exports, local `/object_info`, recorded `/history`, hashes, verified outputs
and committed tests establish what works. Status MUST distinguish DOCUMENTED, MOCKED, LOCALLY
VALIDATED (OFFLINE-PASS), GPU-VERIFIED, VISUALLY ACCEPTED and BLOCKED. Offline tests do not verify
NVIDIA inference; a successful clip proves neither peak VRAM nor artistic acceptability; QA
heuristics reporting no flags is not creative acceptance. Preserve MC-FLF2V-001/002/003,
MC-RUN-001/002/003 (byte-identical fresh-root repeat) and BENCH-001 evidence. Unavailable metrics
are recorded as **NOT MEASURED**.

### II. Native Windows, local-only inference, GPU consent

The sole runtime is **native Windows 11** with Python 3.11+ automation in an isolated controller
`.venv`, a separate ComfyUI Portable environment and a loopback-only ComfyUI server
(`127.0.0.1:8188`). No PowerShell `.ps1`, Bash scripts, WSL, Linux containers or reliance on
`py.exe`. All image/video inference is local; no public media upload, hosted model inference,
tracking or cloud API nodes. GPU work requires `--confirm-gpu`, an idle queue, one job at a time and
targeted cancellation only; never interrupt, clear or restart another job. Model downloads or
installations always need explicit owner consent.

### III. Real ComfyUI graph contracts, test-first

Executable workflows MUST be real `Save (API Format)` exports with hash-pinned semantic binding
profiles validated against live `/object_info` before dispatch. Never invent node IDs, model
filenames or speculative graphs. Acceptance criteria and offline tests (fake ComfyUI, synthetic
media) precede implementation; GPU checks are separately gated. Fail closed on version drift,
missing models, malformed media and unverified outputs.

### IV. Immutable content-addressed artifacts and safe resume

Every anchor image and bridge clip is an immutable job keyed by content: input bytes, patched graph,
model/workflow identity, prompts, seed and dimensions — never by prompt, seed or filename alone.
Records carry hashes, parent dependencies, prompt IDs, stage state and provenance. Resume MUST NOT
double-submit GPU work; partial writes use temporary files and atomic replace. A cross-process run
lock, job/GPU-time budgets and disk preflight guard long batches.

### V. Genuine physical metamorphosis, shared anchors and timing

Both endpoint images are generated in ComfyUI; anchor B derives from A, C from B, and the same bytes
of B serve both adjacent bridges. Independent T2I fallback is explicit, never presented as a
reference edit. Prefer physically continuous transformation over cuts or dissolves. Wan lengths are
`L = 4n+1` with `(L−1)/FPS` anchor spacing; seams are joined only after verified duplicate removal.
Changing a reference-edited image invalidates its transitive descendant edits and every dependent
bridge. Music is optional, owner-licensed and tracked with provenance.

### VI. Forty logical features, numerical order, full Spec Kit workflow

The program is the forty logical features F01–F40 in `docs/SPECKIT_FEATURE_LEDGER.md`. Completed
F01–F10 specs and code are never recreated; F11–F13 have implemented slices and F14–F40 follow.
Features are implemented **in numerical order, lowest
unfinished number first**; an owner- or GPU-gated remainder does not block moving to the next
number. Every new feature MUST run the installed Spec Kit skills in order — `speckit-specify` →
`speckit-clarify` → `speckit-plan` → `speckit-tasks` → `speckit-analyze` → `speckit-implement` — and
then `speckit-converge` in a loop (fix findings, implement appended tasks, rerun) until nothing
remains except owner/GPU-gated tasks. Hand-written substitutes for skill outputs are not allowed.
Map logical IDs to verified, non-colliding `specs/NNN-slug/` directories.

### VII. Source compatibility and repository hygiene

Preserve existing CLI behavior, plan hashes, regression tests, repo history and owner work; add
regression tests before incompatible changes. Use typed Python, `pathlib`, subprocess argument
lists with `shell=False` and minimal permissions. Never commit `.safetensors`, generated media, run
manifests, private media or credentials (the only committed media is owner-approved,
licence-tracked music). Work is committed directly on `main` and pushed; no force-push without an
explicit owner request. Commits and pull requests MUST NOT carry AI co-author trailers or
"Generated with" attributions.

### VIII. Loopback-only local interfaces

Any local UI binds only to loopback addresses, rejects non-loopback Host headers, protects
state-changing requests with a per-session token and origin check, serves only allowlisted
artifacts, escapes all displayed text, loads no external resources and writes no request logs. A UI
never renders, cancels or contacts ComfyUI; the CLI remains authoritative and fully functional.

### IX. Owner gates and autonomous progress

Work proceeds autonomously through all remaining features without waiting for prompts. Pause only
for decisions that are the owner's: new GPU batches beyond an approved bounded scope, model
downloads/installs, destructive or irreversible actions, and creative approvals — then continue
other unblocked work. Five-minute film production follows P0 offline plan → P1 authorized pilot →
P2 one reviewed act → P3 whole-film batches. Engineering facts are recorded separately from
artistic metaphors.

## Technology & Safety Constraints

- Hardware baseline: one RTX A6000 (48 GiB); ComfyUI's own model cache (~35 GB) is not a per-model
  peak.
- Reuse existing modules (`anchors`, `bridge`, `pipeline`, `dag`, `render`, `run_manifest`,
  `workflow_adapter`, `qa`, `stitcher`, `timeline`, `provenance`, `vram`, `perf`, `scheduler`,
  `longform`) rather than parallel reimplementations.
- New third-party dependencies require justification in the feature plan; stdlib is preferred.
- LGPL or otherwise incompatible reference code (e.g. a reference music visualizer) is studied for ideas only, never
  copied.

## Development Workflow & Quality Gates

- Session start: inspect git status, HEAD and upstream; read-only check ComfyUI queue state; verify
  Spec Kit with `scripts/windows/speckit.py --status/--verify`.
- Gate per feature: offline suite `.venv\Scripts\python.exe -m pytest -m "not integration and not
  gpu"` green; analyze has no CRITICAL/HIGH findings; converge loop clean; ledger row and
  `docs/PROGRESS.md` entry record actual outputs, hashes and missing permissions; one coherent
  commit pushed to `main`.
- At context limits, leave an exact handoff in `docs/PROGRESS.md`.

## Governance

This constitution and `CLAUDE.md` are the non-negotiable rules; authority order is: `CLAUDE.md` +
this constitution → `docs/SPECKIT_FEATURE_LEDGER.md` (scope and gates) → `docs/PROGRESS.md`
(measured status; newest dated evidence wins over stale early entries) → real workflow exports and
profiles → code and tests. Amendments are made through `speckit-constitution` in a separate
committed change that states the version bump and reconciles `CLAUDE.md` and the ledger.
Versioning: MAJOR for removed or redefined principles, MINOR for added or materially expanded
guidance, PATCH for clarifications. Every feature plan's Constitution Check MUST evaluate each
principle above; consent and test gates are never bypassed to meet a schedule.

**Version**: 2.0.0 | **Ratified**: 2026-11-24 | **Last Amended**: 2026-11-24
