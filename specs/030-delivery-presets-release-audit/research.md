# Research: F30

- **Decision**: Recipe checksum covers the preset definition, recipe version and encode settings, not source-dependent sizes. **Rationale**: "same preset → same checksum" across runs and sources; source-specific filters are still recorded in the record. **Alternatives**: hashing the full ffmpeg argv — rejected (changes with paths).
- **Decision**: Reuse `interpolate.convert(method="blend")` for the 24 fps step and `finishing.geometry/chain` for fit. **Rationale**: one implementation of each behaviour (F25/F26 evidence carries over).
- **Decision**: Crop = centre crop at full height to the target aspect, then Lanczos scale. **Rationale**: deterministic and honest; reframing beyond centre crops is a later creative decision flagged by the safe-area report.
- **Decision**: Safe area = 5% inset of the crop window (same margin as F23 `camera.crop_check`), generalized to any aspect: crop width fraction = min(1, H·a/W).
- **Decision**: Encoder fallback detected from `ffmpeg -encoders`; MPEG-4 Part 2 is built into every FFmpeg. Verification expects `h264` or `mpeg4` accordingly.
- **Decision**: Licensed audio: input seek by offset, `-t` to the picture duration, AAC; refuse when the probed audio duration minus offset is shorter than the picture by more than one frame. **Rationale**: no silent padding (music continuity).
- **Decision**: `release_check` reports `ready_for_owner_review` only when every F01–F30 row is evidenced and the audit has 0 errors; it never tags. **Rationale**: ledger rule "never declare release complete solely from tests".
