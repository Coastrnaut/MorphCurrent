"""Local music analysis and beat-accurate timing reports (F15).

Audio is decoded locally (WAV via ``wave``, anything else via FFmpeg) to 11,025 Hz
mono and analysed by ``beat_analysis`` — one pipeline for any kind of music
(Patin-style sub-band onsets, tempo curve, DP beat tracking, sections).
The storyboard's manual ``bpm``/offset always wins. Nothing is fetched or uploaded.
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


def analyze_audio(path: str | Path) -> dict:
    """Tempo, beats, downbeat, tempo curve and sections — one analyzer for any music."""
    from .beat_analysis import analyze_samples
    samples = load_mono(path)
    duration = len(samples) / SR
    result = {"file": str(path), "duration_s": round(duration, 3), "sample_rate": SR,
              **analyze_samples(samples)}
    if duration < 8:
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
