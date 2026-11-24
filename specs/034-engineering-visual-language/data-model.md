# Data model: F34

## Visual language (`configs/film/visual-language.yaml`)
`version`, `status` draft | approved, `base_pack`, `default_look`, `selected` null | look name, `geometry` {centroid_max, scale_ratio [lo, hi]}, `drift` {act_spread_max, boundary_jump_max}, `looks` {name: {description, acts: {act_id: {palette [≥2], lighting, camera static | slow_push | slow_pull}}}}.

## Look report
`look`, `selection` owner-selected | default, `stages` checked, `mismatches` [{stage, problem}], `ok`.

## Drift report
`acts` [{id, anchors, measured, mean_colour, spread, spread_flag}], `boundaries` [{from_act, to_act, from_anchor, to_anchor, jump, flag}], `off_centre` [{anchor, offset}], `scale_jumps` [{from, to, ratio}], `missing` [anchor], `ok`.
