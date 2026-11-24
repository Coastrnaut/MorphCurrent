# Implementation Plan: Local music analysis and sync

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
New `audio.py`: `load_mono(path)` (wave module or FFmpeg → 11,025 Hz s16 mono), `onset_envelope` (hop 256, RMS flux, half-wave rectified), `estimate_tempo` (autocorrelation 60–200 BPM, confidence, half/double), `track_beats` (phase that maximises onset sum, then grid), `downbeat_phase` (bar of 4, max energy), `analyze_audio`. `sync_report(storyboard, analysis|None)`. Schema `Audio.licensed`. CLI `audio-analyze`, `audio-sync`.

## Technical Context
Python stdlib (`wave`, `array`, `math`); FFmpeg for non-WAV. Tests synthesise WAVs with the `wave` module.

## Constitution Check
II (local only, licence acknowledgement, no fetch) PASS · I (confidence + alternatives, manual override) PASS · IV/V (plan hash unchanged without audio) PASS · VII PASS.

## a reference music visualizer reference (owner request, 2026-11-24)
The owner pointed to the local a reference music visualizer checkout (a local reference checkout, LGPL-2.1) as a worked example. `audio_bands.py` reimplements its music-visualizer-style band loudness independently in Python (same bands, relative-to-long-average semantics and frame-rate-adjusted decays; no code copied, MIT licence preserved) and adds `audio-visualize` (bass/mid/treble timeline PNG with beats and bridge boundaries).

## Complexity Tracking
None.
