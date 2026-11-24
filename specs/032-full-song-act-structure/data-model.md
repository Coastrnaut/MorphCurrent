# Data model: F32

## Transition (extended)
`from`, `to`, `duration_beats` (optional) **xor** `frames` (optional; 4n+1, 5..render.max_bridge_frames), `seed?`, `prompt`, existing optional fields.

## Act definition (`configs/film/acts.yaml`)
`version`; `acts`: [{`id` slug, `title`, `eras` [era names]}] — five acts, every era exactly once, eras contiguous and in bank order.

## Film storyboard (`configs/sequences/engineering-film.yaml`)
Standard storyboard: `render` 832×480, 16 fps, delivery 24, `max_bridge_frames` 81, `master_seed` 31415; `style.pack` engineering-noir; `audio` none or {file, licensed: true}; 96 anchors (`chapter` = act id; first per act `text_to_image`, others `reference_edit` of the previous); 95 transitions with `frames`. Header comment: sync plan hash, track hash, bank version/status, acts file.

## Film report
`storyboard`, `plan_sha256`, `acts`: [{id, title, anchors, bridges, frames, seconds, boundary_event}], `totals` {anchors, bridges, unique_frames, seconds}, `coverage` {last_anchor_s, tail_hold_s, song_s, matches}, `gpu` {total_hours, label, per_act_hours, stages_extrapolated, stages_estimated}, `note`.
