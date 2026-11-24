# Music synchronization strategy

Owner direction (2026-11-24): classic real-time music visualizers work with **any** song regardless of
beat detection; study how such a visualizer turns audio into visual data and build a deeper
synchronization strategy on those ideas (ideas only — no code is copied).

## 1. How a real-time music visualizer turns audio into visual data

| Stage | What happens (per rendered frame) | Why it matters |
|---|---|---|
| PCM ring buffer | The most recent ~576 samples per channel, normalized to a common amplitude scale | Works from raw audio; no file metadata, tempo or score needed |
| Waveform alignment | Each new waveform is shifted to best match the previous frame's | Shapes driven by the waveform stay stable instead of jittering |
| Spectrum | Damped (lightly low-passed) samples → windowed FFT (sine envelope) → magnitude with a log-scale equalization → 512 bins, mono = mean of L/R | A perceptually balanced spectrum every frame |
| Bands | bass / mid / treble = sum of the first, second and third sixth of the spectrum | Three coarse "energies" anyone can map to motion |
| **Relative loudness** | Each band divided by its own long-term average (slow decay ≈ 0.992 per 1/30 s; faster in the first ~50 frames) → ≈ 1.0 is "normal for this song", < 0.7 quiet, > 1.3 loud | **Self-normalizing**: the same mapping works for any level, genre or mix |
| Two speeds | `bass` = instantaneous relative value; `bass_att` = attack/release average (fast rise 0.2, slower fall 0.5 per 1/30 s), all rates corrected for actual fps; `vol` = mean of the three | Sharp response *and* a smooth envelope from the same signal |
| Mapping | Preset equations map these (plus `time`, `frame`, `progress`, spectrum and waveform arrays) continuously to zoom, warp, rotation, colour, shapes and per-pixel motion; `q` variables carry state | Motion follows **energy**, not a beat grid — so rubato, rhythm-free and live music all "sync" |
| Discrete events | A *hard cut* fires when `vol` rises by more than a sensitivity between frames (a transient), rate-limited by a minimum interval; otherwise presets change by timed soft blends | Onsets — not tempo — are the only events it needs |

**Lesson:** synchronization does not require a correct beat grid. It needs (a) a self-normalized,
multi-speed **energy envelope** per band, (b) **onsets** as event candidates, and (c) a continuous
**mapping** from those signals to motion — with beats as an optional refinement when they are reliable.

## 2. What MorphCurrent can and cannot control

Wan FLF2V generates each bridge from two fixed endpoint images; per-frame motion inside a bridge
cannot be steered live like a visualizer preset. MorphCurrent can control: **where anchors fall** (time),
**how long each bridge is** (4n+1 frames, 33–81), **what each bridge's prompt asks for** (character and
intensity), the **playback timing of generated frames** (retiming with interpolation, F25) and
**finishing effects** after generation (F26/F40). The strategy uses every one of these levers.

## 3. Layered synchronization strategy

All layers are driven by one **audio feature track**, computed locally once per song and hashed into
the plan: per video frame (16 fps, re-sampled for delivery fps) — `bass`, `mid`, `treb`, their `_att`
envelopes and `vol` in the relative-to-own-average sense; spectral **flux** (positive spectral change),
**onset strength**, spectral **centroid/brightness**; plus song-level **sections** (F15 novelty) and,
optionally, an owner-verified beat/downbeat map.

1. **Structure (minutes).** Sections from novelty → acts and chapters (F32/F38). Works for any music.
2. **Anchor timing (seconds) — event-locked, beat-optional.** Candidate anchor times are scored
   events: onset peaks (the visualizer's transient-cut idea, made offline and more precise), section starts,
   energy peaks of `vol_att`, and downbeats **only when** the beat map is owner-verified or beat
   confidence is high. A dynamic program picks the anchor sequence that maximizes total event strength
   at anchors subject to bridge lengths 33–81 frames (4n+1) and a preferred length; anchor frames
   are snapped to the 4-frame grid (≤ 2-frame error, no cumulative drift). With no reliable beats it
   still works — like a real-time visualizer.
3. **Bridge character (per bridge).** Mean and peak band envelopes over each bridge map
   deterministically to prompt descriptors: bass-heavy → massive, slow, weighty transformation;
   treble-heavy → fine, glittering, crystalline detail; rising `vol_att` → building, accelerating;
   falling → settling, calming. Recorded in the plan; a prompt-only approximation (no audio enters Wan).
4. **Energy-warped timing (frames) — the visualizer coupling.** Inside each bridge, playback progress
   follows the music's energy: the cumulative `vol_att` over the bridge's time span defines a monotone
   time map so the morph moves faster when the music surges and slower when it calms, with both
   anchor frames pinned to their exact times. Speed is clamped to 0.5×–2× and realized with
   timestamp-preserving frame interpolation (F25). The generated frames are untouched; the warp is a
   versioned, reversible finishing step.
5. **Finishing pulses (frames, optional).** Subtle, owner-tuned, local post effects driven by the
   envelopes (e.g. ≤ 3% scale pulse on `bass_att`, glow on `treb`), applied after the seam-verified
   join and never to the frames used for seam verification. Labelled as effects, not generated content.

**Verification:** an anchor/event report (target event, actual frame time, error), a warp report
(speed range, endpoint pinning), the animatic (stills at anchor times + music) and the energy-warped
preview, and owner listening review. Every artifact records the feature-track hash.

## 4. Mapping to features

- **F15 (extended now):** the audio feature track (`audio-features`) and the event-locked anchor
  planner (`sync-plan`) — the foundation every later layer uses.
- **F25:** energy-warped retiming with pinned anchors and interpolation.
- **F32:** acts from sections; storyboard timing from `sync-plan`; beat map as optional refinement.
- **F37:** verification (event report, warp report), animatic, audio mux, narration, captions.
- **F26/F40:** optional finishing pulses; delivery checks.
