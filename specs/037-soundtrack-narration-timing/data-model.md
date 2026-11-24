# Data model: F37

- **Sync report**: `rows` [{anchor, event, target_s, actual_s, error_frames}], `mean_abs_error`, `max_abs_error`, `drift_frames`, `gate` bool.
- **Warp report**: `rows` [{bridge, frames, min_speed, max_speed, pinned, flags}], `ok`.
- **Animatic record** (`<out>.animatic.json`): `cuts` [{anchor, frame, seconds, source: still | card}], `duration_s`, `expected_s`, `audio` {path, sha256, offset_s} | null, `measured` {duration_s, frames, audio}, `ok`.
- **Cue**: `index`, `start_s`, `end_s`, `text` (SRT `HH:MM:SS,mmm`).
- **Narration script** (YAML): `lines` [{text, at | t, duration}]; check result `lines` [{index, start_s, end_s, text, flags}], `gaps` [{after, seconds}], `ok`.
- **Beat map** (JSON): `downbeats` [s], `verified` bool, `verified_by`, `verified_on`, `corrections` [{index, from, to}].
