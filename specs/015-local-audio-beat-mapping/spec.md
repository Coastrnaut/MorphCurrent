# Feature Specification: Local music analysis, beats and frame-accurate sync

**Logical ledger ID**: F15 · **Feature Directory**: `specs/015-local-audio-beat-mapping` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F15 Local music analysis: BPM, beats, onsets and downbeats with confidence, half/double tempo alternatives, licensed local file guard, manual override and frame-accurate bridge timing with drift report"

## Gap analysis
| Exists | Gap |
|---|---|
| Storyboard `audio.bpm` (manual), `beat_offset_seconds`, `synchronization`; `timeline.py` beats→4n+1 frames with timing error; F09 mux with offset | No analysis of a real file; BPM must be typed; no confidence or half/double-tempo warning; no licence acknowledgement; no cumulative drift report against actual beat times |

## User Scenarios & Testing *(mandatory)*
### US1 - Analyse a local track (P1)
`audio-analyze FILE` decodes locally (WAV directly, other formats via FFmpeg) and reports duration, BPM with confidence, half/double alternatives, beat times, onset times and a downbeat phase guess.
**Acceptance**: synthetic click tracks at 90/120/140 BPM → BPM within ±1; beat times within ±30 ms; offset start (0.37 s) detected; silence → `no_beat_detected` with confidence 0; missing file → error; stereo and 22.05/44.1/48 kHz handled.

### US2 - Licensed-file guard and manual override (P1)
A storyboard with `audio.file` must set `audio.licensed: true` (owner acknowledgement) or planning fails; `audio.bpm` and `beat_offset_seconds` stay authoritative overrides. Remote URLs refused.

### US3 - Beat-accurate timing and drift report (P1)
`audio-sync STORYBOARD` (offline) compares each bridge boundary (cumulative `(L−1)/fps`) to the nearest analysed (or grid) beat/downbeat, reporting per-boundary error and cumulative drift in ms and frames; flags boundaries off by more than one frame.
**Acceptance**: 120 BPM, 16 fps, 8-beat bridges → 0 ms drift; 90 BPM 8 beats → 5.333 s requested vs 81 frames (5.0 s) → error reported, flagged.

### Edge Cases
Very short file (< 4 s) → low confidence; tempo outside 60–200 → folded with alternatives listed; video-only storyboards unaffected.

## Requirements *(mandatory)*
- **FR-001** Analysis is local and offline (FFmpeg decode only); never fetches or uploads audio.
- **FR-002** Onset strength from frame energy flux; tempo by autocorrelation over 60–200 BPM; beats by phase alignment to onsets; confidence = normalised autocorrelation peak.
- **FR-003** `Audio.licensed` boolean; `file` set without `licensed: true` → validation error; URLs rejected.
- **FR-004** Drift report: per boundary planned time, nearest beat, error (ms, frames), cumulative; `>1 frame` flagged.
- **FR-005** Storyboards without audio produce identical plan hashes (no new fields in tasks).

## Success Criteria *(mandatory)*
- **SC-001** Click tracks at 90/120/140 BPM detected within ±1 BPM.
- **SC-002** Drift report exact for the sample storyboard (0 ms at 120 BPM).
- **SC-003** Real owner-licensed track sync: BLOCKED until the owner supplies one.

## Assumptions
Pure-Python DSP on 11,025 Hz mono is fast enough for multi-minute tracks (seconds). Real music is harder than clicks; confidence is reported, and manual override is always available.
