# Data model: F38

## Titles definition (`configs/film/titles.yaml`)
- `version: 1`, `font` (path; must exist when rendering), `defaults` {fade_s 0.5, color white}
- `opening` {text, start_s 0, duration_s 5, size 0.10, y 0.45}
- `acts` {duration_s 4, size 0.08, y 0.80, text: {act_id: text}} — default text = act title from `configs/film/acts.yaml`
- `lower_thirds`: list of {text, start_s | anchor, duration_s, size 0.05, y 0.88}
- `end` {text, duration_s 5, size 0.10, y 0.45}
- Validation: text non-empty after strip; duration > 0; fade ≤ duration/2; 0 < size ≤ 0.3; 0 < y < 1.

## Overlay (resolved)
`id`, `kind` (opening|act|lower_third|end), `text`, `start_s`, `end_s`, `fade_s`, `size` (fraction), `y`, `anchors` [{index, id, frame, t}], `notes` (deferred, clipped).

## Safe-area result
`id`, `area` (16:9 | 9:16), `fits`, `size_px`, `size_used_px`, `width_px`, `limit_px`, `flagged`.

## Recipe
{`version`, `width`, `height`, `fps`, `font_sha256`, `overlays` [{id, text, start_s, end_s, fade_s, size_px, y}], `filter`, `encoder`} → `recipe_sha256` = sha256 of canonical JSON.

## Render record (`<out>.titles.json`)
{`input`, `input_sha256`, `output`, `recipe`, `recipe_sha256`, `probe_in`, `probe_out`, `overlays`, `warnings`}.

## Boundary proposal
`act`, `anchor`, `anchor_id`, `t`, `event`, `section_anchor`, `offset`, `proposal` (str|null).
