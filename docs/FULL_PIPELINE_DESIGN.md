# MorphCurrent — full local anchor-to-video system design

**Scope:** new end-to-end architecture for generating both source images **inside ComfyUI**, then rendering Wan 2.2 I2V first/last-frame transitions automatically. Detailed implementation and acceptance tests are in [SPECKIT_FEATURE_LEDGER.md](SPECKIT_FEATURE_LEDGER.md). This is a design target, not an assertion that T2I/edit workflows have been installed.

## Baseline: reuse existing working infrastructure

- `workflows/03_wan22_flf2v.json`: real validated ComfyUI API graph.
- `configs/profiles/wan22_flf2v.binding.json`: real node mappings (positive/negative prompts, image inputs, size, frame length, fps, seed, output), graph SHA pin and high/low-noise assertions.
- `src/morph_studio/bridge.py`: resumable, hash-based single bridge dispatcher with explicit `--confirm-gpu`, image upload, queue controls, history polling, download and ffprobe verification.
- The first programmatic GPU render MC-FLF2V-003 produced 65 frames, 640×368 @16 FPS, 4.0625 seconds. Decoded frames matched the owner's second manual render exactly, but *artistic quality and peak VRAM are not yet certified*.
- `schema.py`, `timeline.py`, YAML samples and Windows CI already exist. Do not replace them with a second engine.

## Complete dependency graph

~~~text
User YAML storyboard (and optional owner-provided licensed music)
          |
          v
Preflight & no-GPU DAG plan
          |
          v
Local ComfyUI API-format T2I graph 01 + real semantic profile
          |
          +----> Anchor A: T2I orchid ---- SHA(A) ---+
          |                                         |
          v                                         v
Reference edit API graph 02 (or explicit T2I fallback)  Wan FLF2V(A,B)
          |
          +----> Anchor B: butterfly ---- SHA(B) ---+--- shared BYTE-IDENTICAL anchor B
          |                                         |
          v                                         v
Reference edit B -> Anchor C: phoenix ---- SHA(C) --- Wan FLF2V(B,C)
                                                    |
                                     QA / candidate selection
                                                    |
                                 verified shared-endpoint join
                                                    |
                                   optional licensed music
                                                    |
                    final MP4 + images + manifests + contact sheet
~~~

The generated **end image** of one bridge is the generated **start image** of the next. This must use the *same bytes*, not a regenerated lookalike.

## Workflow acquisition and verified semantic adapters

| Workflow | Existing? | Inputs | Output |
|---|---|---|---|
| Wan FLF2V `03_wan22_flf2v.json` | **Yes** (validated) | real first/last images, two FP8 I2V experts, UMT5, Wan 2.1 VAE, prompts, seed, 4n+1 frames | MP4 |
| Anchor T2I `01_anchor_t2i.json` | **No** — must export after a successful local image-model run | prompt, negative/style, image dimensions, seed, model | verified PNG/JPG |
| Anchor reference editing `02_anchor_edit.json` | **No** — must export after model/node verification | parent anchor bytes, target prompt, reference-strength if exposed, seed | verified PNG/JPG |

Only a real ComfyUI **Save (API Format)** graph can be submitted. Keep new workflow bindings separate in `configs/profiles/`, pin canonical graph hashes, and validate classes/required inputs/model choices against `/object_info`. If no compatible image/edit model is installed, report **BLOCKED** and request explicit permission for model acquisition. Do not manufacture missing nodes or silently use the old example images to satisfy an auto-generation acceptance test.

A candidate text-to-image family such as FLUX/Qwen is a **research option**, not proof of an installed model. Choose using actual local model support, license, VRAM/precision and quality. A reference edit model is preferred for shape consistency. An alternate `independent_t2i` mode can create both endpoints with shared style and human review but must be opt-in and labeled *not* reference editing.

## Data contracts and manifest

A storyboard contains: ordered anchor definitions (`id`, subject prompt, negative/optional style, generation method, reference id, seed), ordered transitions (`from`, `to`, physical morph motion prompt, seed, length or beat duration), render profile and optional local audio. Validate unique IDs, no missing/cyclic reference, actual format/dimensions, 4n+1 frame count and rational beat time.

Root job manifest at ignored `outputs/runs/<run-id>/manifest.json` will carry:

- Repo commit, app/library version, storyboard hash and DAG contract version.
- ComfyUI version/observed schema, T2I/edit/Wan workflow SHA, profile/hash, model filename, **model SHA256 if actually measured** (otherwise unverified state), runtime/precision.
- Anchor A/B/C actual byte hash, generation parent hash, prompt/negative prompt/seed, image dimensions and staged local paths.
- Each bridge's A/B image hashes, model/workflow hashes, seed, prompt, 4n+1 length, fps, selected candidate, `/prompt` ID, history execution/error, output checksum, ffprobe frames and time base.
- Consent and queue state; observations/metrics distinguish measured peak VRAM from generic `vram_free` snapshots. Atomic stage transitions and `.part` files avoid partial corruption.
- QA/contact-sheet review state, seam decisions, final FFmpeg arguments/manifest and authorized music provenance.

Cache keys are content hashes of source **bytes**, model hashes, workflows, code version and parameters; filenames alone are insufficient. Reuse verified stages after crash/resume. Do not download weights or share media remotely. One GPU task at a time initially: especially avoid simultaneous anchor model plus two Wan I2V 14B experts in A6000 48 GiB.

## Timing and joining

Wan first/last-frame latency uses `L = 4n+1`. For fps `F`, the **anchor timestamp separation** is `(L-1)/F`; a video container with L decoded frames has nominal duration `L/F`. At F=16 and L=65 this means 4.0s between anchors vs 4.0625s container length. Two 65-frame bridges with matching shared B collapse to **129 distinct frames**, 8.0s A→C timestamp span and 129/16 = 8.0625s nominal playback. Do not let an audio mux silently drift; express delivery duration/PTS policy explicitly. Deduplicate boundary frames **only if actual decoded images agree**. Do not use generic `xfade` instead of a physical morph.

## Video quality and scientific controls

- Examine actual first/middle/last frames, framing/clipping, endpoints, flash/cut, subject stability, blur/freeze and structural progression. Heuristic image metrics assist, but do not prove artistic quality.
- MC-FLF2V-001: apparent petal escape/distortion around 0.75–1.5 s. MC-FLF2V-003: identical decoded frames to manual 002 (PSNR infinity, SSIM 1.000) and visible mid-sequence collapse/flare from sampling. This does **not** demonstrate prompt improvement; see `docs/RENDER_BASELINE_001.md` for the revised *candidate* positive prompt.
- A valid prompt comparison holds resolution, model, sampler, steps and recorded seed constant; length-only comparison holds the prompt. If both change, describe as an artistic iteration, not a controlled causal experiment.
- Automatic QA flags bad candidates; human review can veto/approve. Selective rerender only the affected bridge while preserving verified anchors and neighbors.

## Operator UX and gates

The following commands are **future targets** (not implemented on this baseline):

~~~cmd
cd /d C:\GIT\MorphCurrent
.venv\Scripts\python.exe -m morph_studio.cli render configs/sequences/organic-machines.yaml --dry-run
.venv\Scripts\python.exe -m morph_studio.cli render configs/sequences/organic-machines.yaml --confirm-gpu
.venv\Scripts\python.exe -m morph_studio.cli render --resume outputs\runs\<actual-run-id>
~~~

Preserve the **existing** `bridge` CLI. A dry run cannot upload, post prompts, change ComfyUI configuration or start models. Every expensive run requires explicit consent and should print expected image-model/Wan stages, queue occupancy and bounded job count. When owner already running a GPU smoke test, do read-only discovery and offline code only.

### Validation ladder

1. **Offline:** Spec Kit constitution, schemas, DAG, mocked ComfyUI calls, cache, injected retry failures, FFmpeg synthetic input, security and predictable CLI.
2. **Read-only local:** installed `/object_info` choices and model/graph compatibility; safe localhost health/queue check.
3. **Owner-approved GPU image:** T2I first anchor and reference edit second anchor, independent results with checked output bytes.
4. **Owner-approved bounded GPU bridge:** generated A/B → proven Wan bridge. Confirm endpoint fidelity and frame metadata.
5. **Owner-approved E2E:** generated A/B/C, two bridges, seam-safe final MP4, manifest, quality review and optional authorized soundtrack.
6. **Clean rerun:** same inputs reuse outputs; interrupted run resumes without duplicate GPU jobs. Windows CI proves offline code only.

Keep the actual feature implementation flow and evidence in `docs/SPECKIT_FEATURE_LEDGER.md` and `PROGRESS.md`.
