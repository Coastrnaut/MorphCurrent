# Implementation Plan: Local music analysis and sync

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
New `audio.py`: `load_mono(path)` (wave module or FFmpeg → 11,025 Hz s16 mono), `onset_envelope` (hop 256, RMS flux, half-wave rectified), `estimate_tempo` (autocorrelation 60–200 BPM, confidence, half/double), `track_beats` (phase that maximises onset sum, then grid), `downbeat_phase` (bar of 4, max energy), `analyze_audio`. `sync_report(storyboard, analysis|None)`. Schema `Audio.licensed`. CLI `audio-analyze`, `audio-sync`.

## Technical Context
Python stdlib (`wave`, `array`, `math`); FFmpeg for non-WAV. Tests synthesise WAVs with the `wave` module.

## Constitution Check
II (local only, licence acknowledgement, no fetch) PASS · I (confidence + alternatives, manual override) PASS · IV/V (plan hash unchanged without audio) PASS · VII PASS.

## Reference visualizer (owner request, 2026-11-24)
The owner pointed to a local reference music visualizer as a worked example. `audio_bands.py` implements music-visualizer-style band loudness independently in Python (same bands, relative-to-long-average semantics and frame-rate-adjusted decays; no code copied, MIT licence preserved) and adds `audio-visualize` (bass/mid/treble timeline PNG with beats and bridge boundaries).

## US5 — Layered synchronization foundation (2026-11-24)

**Summary.** New `src/morph_studio/sync_features.py`: `feature_track(samples, fps=16)` reuses `audio_bands.band_levels` for relative bass/mid/treb (+`_att`) and `vol` at the video frame rate, adds spectral flux (positive magnitude change on the same 1024-point windows), onset strength (flux / median flux), brightness (spectral centroid as a fraction of Nyquist), plus `vol_att` (mean of the `_att` bands) and sections from `beat_analysis.sections`; `track_record(path, fps)` adds audio SHA-256, settings and a content hash. `events(track, beatmap=None)` scores candidates per the spec Clarifications. `plan_anchors(track, events, min=33, max=81, preferred=65)` is a DP over 4-frame grid points. `bridge_character(track, a, b)` and `energy_warp(track, a, b)` per bridge. `sync_plan(track_record, beatmap=None, ...)` assembles anchors, bridges (frames, character, warp summary + map) and a coverage report. CLI `audio-features FILE --out [--fps]`, `sync-plan FEATURES --out [--preferred] [--beatmap]`.

**Technical context.** Pure Python + existing FFmpeg decode (`audio.load_mono_at`); deterministic JSON (sorted keys) for hashing; ~5,800 frames for a 6-minute song at 16 fps.

**Constitution check (v2.0.2).** I evidence: synthetic accent tests + real Mozart record, heuristics labelled · II local only, no fetch/upload · III no graph change · IV feature track and plan hashed, inputs recorded · V 4n+1 lengths, 4-frame grid, no drift, anchors pinned in warps · VI full Spec Kit + converge · VII existing analyzers unchanged · VIII n/a · IX plans are proposals; GPU/mux stay owner-gated. PASS.

**Design artifacts.** Data shapes and CLI contract are in this section: FeatureTrack {audio_sha256, fps, settings, frames[{t,bass,mid,treb,*_att,vol,vol_att,flux,onset,brightness}], sections, content_sha256}; SyncPlan {track_sha256, anchors[{frame,t,event,score}], bridges[{from_frame,to_frame,frames,character,warp:{min_speed,max_speed,map}}], coverage{song_s, last_anchor_s, hold_s}, plan_sha256}. Exit 0; refuse overwrite (exit 2).

## Complexity Tracking
None.
