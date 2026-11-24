# Feature Specification: Local music analysis, beats and frame-accurate sync

**Logical ledger ID**: F15 · **Feature Directory**: `specs/015-local-audio-beat-mapping` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F15 Local music analysis: BPM, beats, onsets and downbeats with confidence, half/double tempo alternatives, licensed local file guard, manual override and frame-accurate bridge timing with drift report"

## Gap analysis
| Exists | Gap |
|---|---|
| Storyboard `audio.bpm` (manual), `beat_offset_seconds`, `synchronization`; `timeline.py` beats→4n+1 frames with timing error; F09 mux with offset | No analysis of a real file; BPM must be typed; no confidence or half/double-tempo warning; no licence acknowledgement; no cumulative drift report against actual beat times |

## Clarifications

### Session 2026-11-24 (US5)

Resolved autonomously from docs/MUSIC_SYNC.md and the existing band semantics:

- Q: How are events detected and scored? → A: onset strength = positive spectral flux per frame divided by the track's median flux; onset events are local maxima (±3 frames) above max(median + 1.5 × median absolute deviation, 3 × the median flux) (the 3× floor added during implementation: noise alone passed the MAD test and pulled anchors on near-silent tracks), scored min(1, onset / 12); section starts score 1.0; peaks of smoothed volume (`vol_att`, local maxima ±8 frames, above 1.1) score min(1, `vol_att` − 1); a downbeat adds +0.25 only when a supplied beat map is marked verified or has confidence ≥ 0.5.
- Q: What does the planner optimize? → A: anchors on grid frames g (multiples of 4); a grid point's score is the strongest event within ±2 frames; total = Σ anchor scores − 1.5 × Σ |L − preferred| / 64 over bridges (calibrated during implementation on the Mozart recording: un-normalized scores up to 3 with weight 0.5 packed 129 bridges averaging 45.5 frames, ~1.6× the GPU cost; normalized scores ≤ 1 with weight 1.5 keep bridges near the preferred length while still moving anchors onto strong events), maximized by dynamic programming over allowed lengths 33–81.
- Q: When is a bridge called bass-heavy, treble-heavy, building or settling? → A: bass-heavy when mean `bass_att` ≥ 1.15 and exceeds mean `treb_att` by ≥ 0.10 (treble-heavy symmetric); building when `vol_att` rises by > 0.15 from the first to the last quarter of the bridge, settling when it falls by > 0.15; otherwise steady.
- Q: How is the warp computed? → A: weight w = max(`vol_att`, 0.2) per frame, relative speed = w / mean(w) clamped to [0.5, 2] and renormalized (repeat 5×); cumulative progress maps output frame times to source frame positions with both ends pinned.

## User Scenarios & Testing *(mandatory)*
### US1 - Analyse a local track (P1)
`audio-analyze FILE` decodes locally (WAV directly, other formats via FFmpeg) and reports duration, BPM with confidence, half/double alternatives, beat times, onset times and a downbeat phase guess.
**Acceptance**: synthetic click tracks at 90/120/140 BPM → BPM within ±1; beat times within ±30 ms; offset start (0.37 s) detected; silence → `no_beat_detected` with confidence 0; missing file → error; stereo and 22.05/44.1/48 kHz handled.

### US2 - Licensed-file guard and manual override (P1)
A storyboard with `audio.file` must set `audio.licensed: true` (owner acknowledgement) or planning fails; `audio.bpm` and `beat_offset_seconds` stay authoritative overrides. Remote URLs refused.

### US3 - Beat-accurate timing and drift report (P1)
`audio-sync STORYBOARD` (offline) compares each bridge boundary (cumulative `(L−1)/fps`) to the nearest analysed (or grid) beat/downbeat, reporting per-boundary error and cumulative drift in ms and frames; flags boundaries off by more than one frame.
**Acceptance**: 120 BPM, 16 fps, 8-beat bridges → 0 ms drift; 90 BPM 8 beats → 5.333 s requested vs 81 frames (5.0 s) → error reported, flagged.

### US4 - Classical-music analysis (P1, owner request 2026-11-24)
Classical recordings have soft onsets, wide dynamics, rubato and little percussion; the click-track analyzer gave Mozart 40/I 203 BPM at confidence 0.30. Rework modelled on a reference music visualizer's (historical) `BeatDetect` energy-statistics approach (Patin): log-spaced sub-band energies relative to a running history, log-compressed; local tempo curve with a perceptual prior (octave errors); dynamic-programming beat tracking that follows tempo drift; phrase/section boundaries from loudness/brightness novelty. **One analyzer for every kind of music — no style switch** (owner direction): the same pipeline must pass the click-track and the classical-style tests.
**Acceptance**: synthetic soft-attack notes with an accelerando 90→110 BPM → beats within ±60 ms, tempo curve rising; *pp*→*ff* swell → onsets in the quiet part; loud/quiet/loud sections → boundaries within ±1.5 s; existing click-track tests unchanged; real Mozart 40/I result recorded honestly.

### US5 - Layered music synchronization foundation (P1, owner request 2026-11-24)
A real-time music visualizer stays in sync with any song without a reliable beat grid, because it follows self-normalized band energies and onsets rather than tempo (`docs/MUSIC_SYNC.md`). The author gets the same foundation for the film: (1) an **audio feature track** — per video frame (default 16 fps), bass/mid/treble energy relative to each band's own long-term level with fast and smoothed (attack/release) versions and overall volume, plus spectral change (flux), onset strength and brightness, plus song sections — saved once per song as a hashed record tied to the audio file's checksum and the analysis settings; (2) an **event-locked anchor plan** — anchor times chosen on scored musical events (onset peaks, section starts, energy peaks; downbeats only as an optional boost when a verified or confident beat map is supplied), on the 4-frame grid, with every bridge 33–81 frames long (4n+1) and near a preferred length, covering the whole song, and still sensible when beat detection is unreliable; (3) **per-bridge character** words from band energy (bass-heavy, treble-heavy, building, settling) recorded with the plan; (4) an **energy-warp time map** for each bridge so the morph's progress follows the music's cumulative energy, with both anchors pinned to their times and playback speed kept within 0.5×–2× (computed now; applied by F25).
**Acceptance**: a synthetic track with clear accents at known times → anchors land on those accents (±2 frames) with valid bridge lengths; a synthetic track with no steady beat (irregular accents) still yields a full-coverage plan; identical audio and settings → identical feature-track hash and plan; a bass-heavy passage is described as bass-heavy and a crescendo as building; every warp map starts and ends at the bridge's anchor frames, is monotone, and stays within 0.5×–2×; the real Mozart recording produces a recorded plan.

### Edge Cases
Very short file (< 4 s) → low confidence; a song shorter than one minimum bridge cannot be planned (clear error); silence-only stretches get no events, so bridges there default to the preferred length; a song end that falls between grid points is covered by holding the final anchor; tempo outside 60–200 → folded with alternatives listed; video-only storyboards unaffected.

## Requirements *(mandatory)*
- **FR-001** Analysis is local and offline (FFmpeg decode only); never fetches or uploads audio.
- **FR-002** (revised for US4) Onset strength from log-spaced sub-band energies relative to a primed ~1.3 s running history (Patin-style); one global tempo octave (summed autocorrelation × prior, sub-multiple check), local tempo within ±25%; DP beat tracking that always links; BPM from median inter-beat interval; window-centre time stamps; confidence = mean local autocorrelation.
- **FR-003** `Audio.licensed` boolean; `file` set without `licensed: true` → validation error; URLs rejected.
- **FR-004** Drift report: per boundary planned time, nearest beat, error (ms, frames), cumulative; `>1 frame` flagged.
- **FR-005** Storyboards without audio produce identical plan hashes (no new fields in tasks).
- **FR-006** (US5) Feature track per video frame: relative bass/mid/treb (+ smoothed `_att`), vol, spectral flux, onset strength, brightness; sections; recorded with the audio SHA-256, settings and a content hash; identical inputs → identical hash.
- **FR-007** (US5) Event-locked planner: candidates = onset peaks, section starts, smoothed-energy peaks (+ downbeat boost only when a verified/confident beat map is given); anchors on the 4-frame grid; bridge lengths 33–81 frames (4n+1); preferred length configurable (default 65); maximizes event strength at anchors with a penalty for distance from the preferred length; first anchor at the start, last anchor at or after the song end minus one grid step; no reliance on tempo.
- **FR-008** (US5) Per-bridge character descriptors from mean band energies and the energy trend, deterministic.
- **FR-009** (US5) Energy-warp map per bridge: monotone, endpoints pinned, local speed clamped to 0.5×–2×.
- **FR-010** (US5) CLI `audio-features FILE --out` and `sync-plan FEATURES --out`; offline, ASCII-safe output; refuse to overwrite.

## Success Criteria *(mandatory)*
- **SC-001** Click tracks at 90/120/140 BPM detected within ±1 BPM.
- **SC-002** Drift report exact for the sample storyboard (0 ms at 120 BPM).
- **SC-003** Real owner-licensed track sync: BLOCKED until the owner supplies one.
- **SC-004** (US5) Anchors land within ±2 frames of synthetic accents in 100% of test cases; plans cover the full song with 100% valid bridge lengths; warp maps 100% within bounds.
- **SC-005** (US5) The Mozart recording's feature track and plan are produced in under one minute and recorded.

## Assumptions
US5 plans are proposals for F32/F37; GPU rendering and audio muxing stay with those features and owner approval.
Pure-Python DSP on 11,025 Hz mono is fast enough for multi-minute tracks (seconds). Real music is harder than clicks; confidence is reported, and manual override is always available.
