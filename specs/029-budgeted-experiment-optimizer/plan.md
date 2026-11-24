# Implementation Plan: Structured Local A/B Experiments and Quality-vs-Cost Optimization (F29)

**Branch**: `029-budgeted-experiment-optimizer` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/029-budgeted-experiment-optimizer/spec.md`

## Summary

New `src/morph_studio/experiment.py`:

- **Definition** (pydantic, YAML): `name`, `subject` {start_image, end_image, positive_prompt, negative_prompt?, profile (default Wan production)}, `controls` {setting: value}, `factors` {setting: [values]}, `seeds` list or `seed_count` + `master_seed`, `budget` {max_runs?, max_gpu_s?, max_frames?}, `early_stop` {consecutive_flagged: N}? . `ALLOWED = {seed, length, width, height, positive_prompt, negative_prompt, fps, profile}`; leakage check; seeds only from the block.
- **`effective_defaults(profile)`**: literal values at the profile's bound nodes in the exported graph (width/height/length/fps) for estimates and baseline reporting; constraint checks via `registry.build_entry` (`length_rule`, object_info constraints when supplied) plus the hard rules (length ≥ 5 and (L−1) % 4 == 0, width/height % 16 == 0, fps > 0, profile capability `wan_flf2v`).
- **`design(defn, history)`** → candidates: baseline (controls, first seed) then `itertools.product` over sorted factor names × seeds; `candidate_id = sha256(canonical effective settings incl. image hashes)[:16]`; dedupe; per-candidate `estimate_s` (median `exec_s` of history entries with same kind/width/height/frames, else `None` "NO DATA"); budget pass in order marking `deferred` with `limit` (runs / gpu_s (estimates only when known) / frames).
- **Runner** `run(defn, out_dir, executor, *, confirm_gpu)`: loads `results.jsonl`; for each non-deferred candidate in order: skip done (reused), skip early-stopped level, check budget against measured totals, call `executor(candidate, submit=confirm_gpu)` → outcome dict, append. `bridge_executor(url, runs_root)` builds `BridgeRequest` → `plan_bridge(request, object_info)` → `run_bridge(..., submit=...)`, reads job record (execution seconds, output path, frames/size via probe, verification) and runs `qa.analyze_clip` for flags. Without confirmation outcome status is `validated` (not counted as done).
- **Ratings** `rate(out_dir, candidate_id, score, note)` → `ratings.json` (atomic write).
- **Analysis** `report(defn, out_dir)` → dict + Markdown: per factor level summaries, mismatches (`frames != requested length`), unrated, Pareto set (maximize rating; minimize runtime, memory, size over dimensions measured for all rated candidates), totals, caveat.
- CLI: `experiment-plan DEF [--history]`, `experiment-run DEF [--confirm-gpu] [--url] [--runs-root]`, `experiment-rate DEF CANDIDATE SCORE [--note]`, `experiment-report DEF`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: stdlib, pydantic, PyYAML (existing); `bridge` (BridgeRequest, plan_bridge, run_bridge), `perf.load_history`, `timeline.derived_seed`, `registry`, `qa.analyze_clip`, `media.probe_video`

**Storage**: `outputs/experiments/<name>-<def8>/` (results.jsonl append-only, ratings.json, report.md/json); bridge jobs in the runs root

**Testing**: pytest with real Wan profile/workflow, tmp images, a stand-in executor; no ComfyUI

**Target Platform**: native Windows 11

**Project Type**: CLI tool / library module

**Performance Goals**: planning < 1 s

**Constraints**: one GPU job at a time, idle queue (inherited from `run_bridge`), `--confirm-gpu`, no change to approved outputs, only real bindable inputs

**Scale/Scope**: tens of candidates per experiment

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | Measured timings only; NO DATA instead of guesses; observational caveat | PASS |
| II Local, consent | Loopback ComfyUI via existing bridge jobs; `--confirm-gpu`; idle queue | PASS |
| III Graph contracts | Factors limited to profile-bound roles, validated against real constraints | PASS |
| IV Immutable artifacts | Content-addressed jobs reused; append-only results; approved outputs untouched | PASS |
| V Physical morph | Length 4n+1, shared anchors unchanged (subject images fixed) | PASS |
| VI Spec Kit | Full workflow + converge | PASS |
| VII Compatibility | New module and commands only | PASS |
| VIII Loopback UIs | N/A | N/A |
| IX Owner gates | Ratings and the choice are the owner's; GPU batch bounded by budget | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/029-budgeted-experiment-optimizer/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/cli.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/morph_studio/experiment.py   # new
src/morph_studio/cli.py          # + experiment-* commands
tests/test_experiment.py         # new
configs/experiments/             # example definition (data)
```

**Structure Decision**: single module plus CLI wiring, matching F20–F28.

## Complexity Tracking

None.
