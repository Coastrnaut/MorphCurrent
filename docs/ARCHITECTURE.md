# MorphCurrent architecture — design contracts and tradeoffs

## Logical graph
```
Sequence YAML + assets + local audio
  -> validation / beat analysis / creative continuity planning
  -> immutable DAG of anchor generation/editing tasks
  -> Wan 2.2 FLF2V bridge tasks (anchor N -> anchor N+1)
  -> inspection + candidate scoring + optional rerender
  -> seam-aware FFmpeg conform / audio sync / final export
```

## Components
- `schema.py`: strict Pydantic creative schema, stable IDs and transitions.
- `timeline.py`: beat/BPM-to-Wan frame planning; exact rational clock.
- `comfy_client.py`: local REST + WS, timeouts, history/errors, image upload/download, node discovery.
- `workflow_adapter.py`: semantic bindings from `configs/profiles/*.binding.json` for real API-format JSON; validates node classes, inputs, links, installed model choices and value ranges against `/object_info`; hash-pins the graph and fails closed on drift.
- `bridge.py`: one FLF2V bridge job: content-addressed job dir, persisted state machine (planned → uploaded → validated → submitting → submitted → completed → downloaded → verified), client-chosen prompt IDs for crash-safe resume, targeted cancel, ffprobe verification via `media.py`. GPU submission only with explicit consent (`--confirm-gpu`).
- `manifest.py`, `scheduler.py`, `cache.py` (to build): immutable content-addressed artifacts with crash recovery.
- `audio_analysis.py` (to build): librosa-derived beat/onset/envelopes + manual override.
- `quality.py` (to build): perceptual seam, blur/freeze/flow, endpoint fidelity and contact sheets.
- `stitcher.py` (to build): FFprobe checks, frame normalize, zero/one-frame seam dedupe, timestamp integrity, mux.

## ComfyUI contract
GET `/system_stats`, GET `/object_info`, POST `/upload/image`, POST `/prompt` with `{"prompt": API_GRAPH, "client_id": ID}`, WS `/ws?clientId=ID`, GET `/history/{prompt_id}`, GET `/view?filename=...&subfolder=...&type=...`.
Actual API format is a dictionary of node IDs to `{"class_type": "...", "inputs": {...}}`. UI-formatted workflow JSON is *not* directly queueable. Use authenticated/trusted localhost; default deny non-loopback endpoints. Verify runtime `object_info` before dispatch, and make `/history` + files authoritative after WS completion. Persist prompt ID and poll for recovery after lost WS.

## Model memory tradeoffs
Wan 2.2 A14B I2V high-noise + low-noise experts each have ~14B parameters. Two full FP16 sets exceed A6000 48 GiB with no activation budget. `--highvram` is not an OOM workaround. Benchmark:
- sequential FP16 expert residency/offload;
- FP8 scaled experts and text encoder with measured quality;
- CPU offload as explicit fallback;
- separate anchor stage and video stage.
Keep single GPU job by default, record CUDA allocated/reserved memory, actual clip latency and output fidelity. Do not assert weights/precision or quantization efficacy without checkpoint inspection.

## Morph quality contracts
1. Preserve compatible silhouette, subject centroid, color palette, lighting and camera between anchors, preferably reference editing.
2. Transition prompt specifies temporal actions, shape/material correspondences, camera movement, stable shot and explicit no-cut/no-fade constraint.
3. Modes: direct morph, camera-passage morph, optional intermediate-anchor ladder. Selection heuristic must be overruled by preview review.
4. Generate 2-3 seeds for difficult pairs; flag blur/freeze/endpoint mismatch. Metrics aren't a replacement for visual inspection.
5. Don't automatically use dissolve/xfade: that destroys true material transformation.

## Frame mathematics and seam policies
Wan FLF latent lengths commonly use `L = 4n + 1`. For anchor-to-anchor **timestamp span** at generation FPS F, use `T = (L - 1) / F`. For 120 BPM, 8 beats = 4 seconds; F=16 gives L=65.
For N bridges with identical frame sizes/fps and exact shared-anchor endpoints, concatenation **removes the duplicate first endpoint** from each later bridge. Total frames = 1 + sum(L_i - 1). A 2-bridge 65/65 example gives 129 unique frames at 16 FPS, with anchor timestamp span 8s. File playback PTS and audio mux length must be explicitly conformed for delivery; frame count / fps differs by the final frame interval.
Before trimming: inspect boundary histogram/perceptual differences and optical flow. If mismatch, flag, rerender or use narrowly scoped repair; naive 2-4-frame overlap risks skipping endpoint conditions. Use frame-accurate FFmpeg filters with explicit PTS resets and offline golden tests.
For incompatible beat durations, choose nearest L, insert an intermediate bridge, or retime *deliberately*; record timing residual and never silently drift against music.

## YAML storyboard and profiles
Human edits only the creative YAML (style, anchors, continuity cues, transitions, beat structure). Low-level Comfy node maps and model checkpoint filenames live in `configs/profiles/`. The compiled DAG and run metadata belong in `outputs/runs/<runid>/manifest.json` and must not be versioned.
Hashes must cover (at minimum) source storyboard/profile content, reference image bytes, source music analysis version, checkpoint IDs+SHA256, ComfyUI revision and API workflow JSON, generation parameters, processing code version, output profile, and prior-node hashes. Changing postprocessing doesn't need to invalidate raw video bridges.

## Resilience, security and testing
- localhost only by default; never allow a storyboard to supply arbitrary HTTP endpoints or shell fragments.
- HTTP request timeout/retry with backoff; WS can disconnect. Only confirmed history/output files imply success.
- API error and node errors produce actionable diagnostics; persist state on every transition.
- No shell=True. Use FFmpeg argument arrays and namespaced output locations.
- Unit tests offline: parser, graph validation, frame math, deterministic manifests, seam dedupe, API mocks.
- Gated integration tests against a local ComfyUI, hardware benchmark suite, human video-quality review.
- Outputs/media, weights, API tokens and logs with sensitive environment details are excluded from Git.

## Sources
https://docs.comfy.org/development/comfyui-server/comms_routes
https://github.com/Comfy-Org/ComfyUI/blob/master/script_examples/websockets_api_example.py
https://docs.comfy.org/tutorials/video/wan/wan2_2
https://code.claude.com/docs/en/settings

## Sole supported runtime: Windows 11 native
- Controller: Python >=3.11 virtual environment at `.venv\\Scripts\\python.exe`; no controller torch dependency.
- Model runtime: native Windows ComfyUI Portable NVIDIA (isolated `python_embeded\\python.exe`) or manual Windows ComfyUI (dedicated `.venv\\Scripts\\python.exe`); torch/CUDA are installed here, not in controller.
- All helper automation is Python under `scripts/windows/`. The Spec Kit preferred generated script type is **`py`**, selected with `--script py`. No PowerShell or Bash development scripts, WSL, passthrough or Linux containers.
- Windows subprocesses use direct argument lists and `shell=False`. FFmpeg is from native Windows PATH; output overwrite is denied by default.
- ComfyUI always binds to `127.0.0.1` by default; no remote GPU server or exposed API.
- Device diagnostics are non-destructive and do not require CUDA to be installed in the controller environment. Native Windows GitHub Actions covers offline tests only.
- See `docs/WINDOWS_DEVELOPMENT.md` and `docs/TROUBLESHOOTING_WINDOWS.md`.

### Spec Kit Python-only invariant
Bare `specify init` defaults to PowerShell on Windows, so the repository's Python helper supplies `--script py --non-interactive --integration claude` explicitly. Upstream may also unpack `.specify/scripts/powershell/` as a fallback even when Python is selected. The helper verifies real Python core scripts, checks generated Claude `speckit-*` skills/commands for .ps1 references, normalizes `python3` invocations to Windows `python`, and moves the unused fallback into a gitignored backup. It detects/fixes existing PowerShell-initialized `.specify` under `--init` or `--repair` with a backup before force-merging. A known July 2026 CLI packaging issue omitted Python scripts in some versions; a missing `.py` fails verification and requires upgrade, not silently returning to PowerShell.

## Image-generation-to-morph extension (ten-feature program, 2026-11-24)

The preceding system describes the existing bridge, planner and intended DAG. **As of MC-FLF2V-003, the single-pair Wan bridge is actually running and verified on the owner's GPU; automatic local anchor image generation is not yet implemented.** The canonical new design is [FULL_PIPELINE_DESIGN.md](FULL_PIPELINE_DESIGN.md), and its exact ten-feature implementation gates are [SPECKIT_FEATURE_LEDGER.md](SPECKIT_FEATURE_LEDGER.md).

Pipeline stages: `Storyboard → real locally-exported ComfyUI T2I graph (first anchor A) → real locally-exported reference-edit graph (B from A, C from B) → existing validated Wan FLF2V bridge(A,B), bridge(B,C) → local QA → verified shared-anchor seam → FFmpeg final MP4`. A fallback independent T2I endpoint is **explicitly chosen**, not silently called reference editing. Do not add fake `01_anchor_t2i.json` or `02_anchor_edit.json` until installed-model runs and `/object_info` validate them.

GPU stages execute serially by default with explicit per-run consent, persistent stage/parent hashes, and no interference with ongoing owner ComfyUI work. Peak VRAM requires a real opt-in sampler, not a stationary `/system_stats vram_free` snapshot. Output B is the *same byte sequence* in adjacent bridges. For 2×65-frame / 16-FPS successful bridges the expected **unique** frame count is 129 only when the B boundary is verified duplicated. Keep audio optional.

`CLAUDE.md` and `.specify/memory/constitution.md` now point to the ten-feature program. The only canonical pasteable agent instruction is the **entire file** `docs/CLAUDE_DESKTOP_ONESHOT.md`; it includes no wrapper.
