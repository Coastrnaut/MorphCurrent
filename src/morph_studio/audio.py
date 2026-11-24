"""Local music analysis and beat-accurate timing reports (F15).

Audio is decoded locally (WAV via ``wave``, anything else via FFmpeg) to 11,025 Hz
mono. Onset strength is the half-wave-rectified frame-energy flux; tempo comes from
its autocorrelation over 60–200 BPM; beats are the grid phase that best matches the
onsets. Results carry a confidence and half/double-tempo alternatives — real music is
harder than click tracks, and the storyboard's manual ``bpm``/offset always wins.
Nothing is fetched or uploaded.
"""
from __future__ import annotations

import array
import math
import shutil
import subprocess
import wave
from pathlib import Path

from .media import ProbeUnavailable

SR = 11025
HOP = 256
MIN_BPM, MAX_BPM = 60.0, 200.0


class AudioError(ValueError):
    pass


def _check_local(path: str | Path) -> Path:
    text = str(path)
    if "://" in text:
        raise AudioError("audio must be a local file, not a URL")
    p = Path(path)
    if not p.is_file():
        raise AudioError(f"audio file not found: {p}")
    return p


def load_mono(path: str | Path) -> list[float]:
    """Mono float samples at 11,025 Hz."""
    return load_mono_at(path, SR)


def load_mono_at(path: str | Path, rate: int) -> list[float]:
    """Mono float samples at ``rate`` Hz (WAV read directly when it already matches)."""
    p = _check_local(path)
    if p.suffix.lower() == ".wav":
        with wave.open(str(p), "rb") as w:
            if w.getsampwidth() == 2 and w.getframerate() == rate and w.getnchannels() == 1:
                data = array.array("h", w.readframes(w.getnframes()))
                return [s / 32768.0 for s in data]
    executable = shutil.which("ffmpeg")
    if not executable:
        raise ProbeUnavailable("ffmpeg not found on PATH (needed to resample/convert audio)")
    done = subprocess.run([executable, "-hide_banner", "-nostdin", "-v", "error", "-i", str(p),
                           "-ac", "1", "-ar", str(rate), "-f", "s16le", "-"],
                          capture_output=True, timeout=600, shell=False, check=False)
    if done.returncode != 0:
        raise AudioError(f"could not decode {p.name}: {done.stderr.decode(errors='replace')[:200]}")
    data = array.array("h")
    data.frombytes(done.stdout[: len(done.stdout) // 2 * 2])
    return [s / 32768.0 for s in data]


def onset_envelope(samples: list[float]) -> list[float]:
    energies = []
    for start in range(0, len(samples) - HOP + 1, HOP):
        frame = samples[start:start + HOP]
        energies.append(math.sqrt(sum(x * x for x in frame) / HOP))
    flux = energies[:1] + [max(0.0, energies[i] - energies[i - 1]) for i in range(1, len(energies))]
    peak = max(flux, default=0.0)
    return [f / peak for f in flux] if peak > 0 else flux


def estimate_tempo(env: list[float]) -> dict:
    fps = SR / HOP
    # Smooth spikes so beat periods that are not whole frames still correlate (±2 frames).
    kernel = (0.25, 0.5, 1.0, 0.5, 0.25)
    env = [sum(kernel[k + 2] * env[i + k] for k in range(-2, 3) if 0 <= i + k < len(env))
           for i in range(len(env))]
    mean = sum(env) / len(env) if env else 0.0
    centred = [e - mean for e in env]
    energy = sum(c * c for c in centred)
    if energy <= 1e-12:
        return {"bpm": None, "confidence": 0.0, "status": "no_beat_detected", "alternatives": []}
    lo, hi = int(fps * 60 / MAX_BPM), int(math.ceil(fps * 60 / MIN_BPM))
    scores = {}
    for lag in range(max(1, lo), min(hi, len(centred) - 1) + 1):
        scores[lag] = sum(centred[i] * centred[i + lag] for i in range(len(centred) - lag)) / energy
    best_lag = max(scores, key=scores.get)
    # tempo-octave correction: accented bars make 2x/3x the beat period score highest;
    # prefer the shortest sub-multiple whose score is close to the best.
    for divisor in (4, 3, 2):
        sub = round(best_lag / divisor)
        near = [l for l in (sub - 1, sub, sub + 1) if l in scores]
        if near:
            cand = max(near, key=scores.get)
            if scores[cand] >= 0.6 * scores[best_lag]:
                best_lag = cand
                break
    # parabolic refinement for sub-frame lag precision
    lag = float(best_lag)
    if best_lag - 1 in scores and best_lag + 1 in scores:
        a, b, c = scores[best_lag - 1], scores[best_lag], scores[best_lag + 1]
        denom = a - 2 * b + c
        if denom:
            lag += 0.5 * (a - c) / denom
    bpm = 60.0 * fps / lag
    confidence = max(0.0, min(1.0, scores[best_lag]))
    if confidence < 0.1:
        return {"bpm": None, "confidence": round(confidence, 3), "status": "no_beat_detected", "alternatives": []}
    alternatives = [round(b, 2) for b in (bpm / 2, bpm * 2) if MIN_BPM / 2 <= b <= MAX_BPM * 2]
    return {"bpm": round(bpm, 2), "confidence": round(confidence, 3), "status": "ok",
            "alternatives": alternatives}


def track_beats(env: list[float], bpm: float, duration: float) -> tuple[list[float], float]:
    """Beat grid at ``bpm`` whose phase best matches the onsets; returns (beats, offset)."""
    fps = SR / HOP
    period = 60.0 / bpm
    steps = 200
    scores = []
    for k in range(steps):
        phase = period * k / steps
        score, t = 0.0, phase
        while t < duration:
            idx = int(t * fps)  # frame containing time t
            if idx < len(env):
                score += env[idx]
            t += period
        scores.append(score)
    # Many phases fall in the same onset frame and tie; take the middle of the best run
    # (circularly) instead of its first member, which would bias beats early.
    best = max(scores)
    tied = [k for k, s in enumerate(scores) if s >= best - 1e-9]
    if tied[0] == 0 and tied[-1] == steps - 1:  # run wraps around the period boundary
        tied = [k - steps if k > steps // 2 else k for k in tied]
    best_phase = (period * (sum(tied) / len(tied)) / steps) % period
    if best_phase > period - 1.0 / fps:  # a beat a few ms before t=0 is the beat at t=0
        best_phase = 0.0
    beats, t = [], best_phase
    while t < duration:
        beats.append(round(t, 4))
        t += period
    return beats, round(best_phase, 4)


def downbeat_phase(env: list[float], beats: list[float], beats_per_bar: int = 4) -> int:
    """Index (0..3) of the beat in each bar with the most onset energy — a guess, not certainty."""
    fps = SR / HOP
    sums = [0.0] * beats_per_bar
    for i, b in enumerate(beats):
        idx = int(b * fps)
        if idx < len(env):
            sums[i % beats_per_bar] += env[idx]
    return max(range(beats_per_bar), key=lambda k: sums[k])


def analyze_audio(path: str | Path) -> dict:
    samples = load_mono(path)
    duration = len(samples) / SR
    env = onset_envelope(samples)
    tempo = estimate_tempo(env)
    result = {"file": str(path), "duration_s": round(duration, 3), "sample_rate": SR,
              "method": "energy-flux onsets + autocorrelation tempo (heuristic)", **tempo}
    if tempo["bpm"] is None:
        result.update(beats=[], offset_s=None, downbeat_index=None)
        return result
    beats, offset = track_beats(env, tempo["bpm"], duration)
    fps = SR / HOP
    onsets = [round(i / fps, 3) for i in range(1, len(env) - 1)
              if env[i] > 0.3 and env[i] >= env[i - 1] and env[i] > env[i + 1]]
    result.update(beats=beats, offset_s=offset, onsets=onsets[:2000],
                  downbeat_index=downbeat_phase(env, beats))
    if duration < 4:
        result["warning"] = "short file; tempo confidence is limited"
    return result


def sync_report(storyboard, analysis: dict | None = None) -> dict:
    """Bridge boundaries vs beats: per-boundary error and cumulative drift (offline)."""
    from .timeline import compile_timeline
    bridges = compile_timeline(storyboard)
    fps = storyboard.render.generation_fps
    if analysis and analysis.get("beats"):
        beats, source = analysis["beats"], f"analysis of {analysis.get('file')}"
    else:
        bpm, offset = storyboard.audio.bpm, storyboard.audio.beat_offset_seconds
        total = sum((b.frames - 1) / fps for b in bridges) + 60.0 / bpm
        n = int(total * bpm / 60.0) + 2
        beats, source = [offset + i * 60.0 / bpm for i in range(n)], f"storyboard grid {bpm} BPM"
    boundaries, t, planned_beats = [], 0.0, 0.0
    frame_ms = 1000.0 / fps
    for b in bridges:
        t += (b.frames - 1) / fps
        planned_beats += b.requested_seconds
        nearest = min(beats, key=lambda x: abs(x - t)) if beats else None
        target = (beats[0] if beats else 0.0) + planned_beats
        error_ms = round((t - target) * 1000, 1)
        boundaries.append({"after": f"{b.from_anchor}->{b.to_anchor}", "time_s": round(t, 4),
                           "target_s": round(target, 4),
                           "nearest_beat_s": round(nearest, 4) if nearest is not None else None,
                           "error_ms": error_ms, "error_frames": round(error_ms / frame_ms, 2),
                           "flag": abs(error_ms) > frame_ms})
    return {"beat_source": source, "fps": fps, "boundaries": boundaries,
            "cumulative_drift_ms": boundaries[-1]["error_ms"] if boundaries else 0.0,
            "flagged": [x["after"] for x in boundaries if x["flag"]]}
