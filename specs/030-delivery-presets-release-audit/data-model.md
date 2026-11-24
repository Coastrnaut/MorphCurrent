# Data model: F30

## Preset (recipe version 1)
`name`, `target` [w, h], `geometry` fit | crop, `aspect` (crop only, e.g. "9:16"), `fps` null | 24, `audio` copy | drop | licensed.

## Delivery record (`<out>.delivery.json`)
`preset`, `recipe_version`, `recipe_sha256`, `steps` [str], `input` {path, sha256, width, height, fps, frames, duration_s, audio}, `output` {path, sha256, width, height, fps, codec, frames, duration_s, audio, audio_duration_s}, `encoder` {video, fallback: bool, audio}, `expected` {...}, `verification` {passed, mismatches [{key, expected, measured}]}, `crop` {rect, anchors: {first, last: inside | outside | unknown}, warning?}, `audio_source` {path, sha256, offset_s, licensed}?, `seconds`, `device` "CPU (FFmpeg)".

## Acceptance row / release check
Row: `feature`, `status`, `evidenced`, `gate`. Release check: `through`, `evidenced`, `unresolved`, `audit` {errors, warnings}, `ready_for_owner_review`, `reasons` [str], `note`.
