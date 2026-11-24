# Research: F37

- **Decision**: Animatic at 16 fps via an ffconcat list of still images with exact durations, then `fps=16:round=near`. **Rationale**: same technique as F25 warp-apply; cuts land on frame boundaries because durations are whole frames. **Alternatives**: rendering every frame as a PNG — slower, same result.
- **Decision**: Placeholder cards are plain colour fields (FFmpeg `color` source) with no text. **Rationale**: constitution/owner rule — no model- or tool-rendered text in pictures; subjects are named in the SRT track instead.
- **Decision**: Click track synthesized with the stdlib `wave` module (exact sample placement), music mixed with FFmpeg `amix` when given. **Rationale**: precise click times without depending on FFmpeg filter syntax for hundreds of delays.
- **Decision**: Sync error measured in frames against the plan's target times; drift = last error − first error. **Rationale**: matches the F32/F15 gate definition (no cumulative error).
- **Decision**: Warp speed = map delta per output frame (source frames advanced per output frame). **Rationale**: the F15 warp map is source-frame position per output frame; its derivative is playback speed.
