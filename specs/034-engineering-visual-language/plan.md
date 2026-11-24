# Implementation Plan: Engineering Visual Language (F34)

**Branch**: `034-engineering-visual-language` (committed on `main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/034-engineering-visual-language/spec.md`

## Summary

- **Data**: `configs/film/visual-language.yaml` — `version`, `status: draft`, `base_pack: engineering-noir`, `default_look`, `selected: null`, `geometry {centroid_max: 0.08, scale_ratio: [0.75, 1.33]}`, `drift {act_spread_max: 60, boundary_jump_max: 70}`, `looks {name: {acts: {act_id: {palette, lighting, camera}}}}`.
- **New `src/morph_studio/look.py`**:
  - `load_language(path, act_ids)` → validated dict (acts covered, ≥ 2 colours, camera ∈ {static, slow_push, slow_pull}, adjacent acts share a colour — case/space-insensitive); `choose(language, look=None)` → (name, look, "owner-selected" | "default (not owner-selected)").
  - `apply_look(storyboard_dict, look)` → sets anchor `style_override {palette, lighting}` by chapter and transition `choreography.camera` by the start anchor's act (existing negatives kept).
  - `look_check(plan, look)` → per stage mismatches (anchor prompt contains every palette colour and lighting; `style_sha256` constant per act; bridge prompt contains `prompt_compiler.CAMERA[camera]`).
  - `drift_report(storyboard, run_dir, language)` → anchors' files via `release._stage_files`, `geometry.image_geometry` (mean_colour, centroid, extent); per-act mean/spread; boundary jumps; centroid offset; neighbour extent ratio; missing anchors.
  - `look_test(storyboard_dict, language, act, count, out_dir)` → two storyboards (one per look) for the first `count` anchors of `act` (first anchor forced to text-to-image).
- **`film.py`**: `build_storyboard(..., language=None, look=None)` applies the chosen look; `write_storyboard` / CLI `film-storyboard --language/--look`; regenerate the checked-in film storyboard with the default look.
- **CLI**: `look-check STORYBOARD [--language] [--look]`, `look-drift STORYBOARD --run R [--language]`, `look-test [--storyboard] [--act] [--count] [--out-dir]`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: existing `styles` (overrides), `prompt_compiler.CAMERA`, `dag.compile_plan`, `geometry.image_geometry`, `release._stage_files`, `film`

**Storage**: YAML in `configs/film/`; test storyboards in `outputs/look-test/`

**Testing**: pytest (film storyboard, synthetic runs with generated PNGs via FFmpeg-free PIL-less approach: write tiny PPM→PNG with FFmpeg if available, else skip)

**Target Platform**: native Windows 11

**Project Type**: library + CLI + data

**Performance Goals**: look check < 2 s; drift on 96 anchors < 30 s

**Constraints**: prompt-level only; no GPU; deterministic

**Scale/Scope**: 5 acts, 96 anchors

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I Evidence | Drift measured from renders; prompts treated as hypotheses | PASS |
| II Local, consent | No GPU; A/B render is owner-run | PASS |
| III Graph contracts | Uses existing style override and choreography paths | PASS |
| IV Immutable artifacts | Deterministic plan; regenerated storyboard committed | PASS |
| V Physical morph | Geometry targets (centred, scale band) reported | PASS |
| VI Spec Kit | Full workflow + converge | PASS |
| VII Compatibility | Other storyboards untouched | PASS |
| VIII Loopback UIs | N/A | N/A |
| IX Owner gates | Look selection is the owner's | PASS |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/034-engineering-visual-language/
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
configs/film/visual-language.yaml   # new
src/morph_studio/look.py            # new
src/morph_studio/film.py            # apply look
src/morph_studio/cli.py             # look-* commands, film-storyboard --look
configs/sequences/engineering-film.yaml  # regenerated
tests/test_look.py                  # new
```

**Structure Decision**: one module plus generator option.

## Complexity Tracking

None.
