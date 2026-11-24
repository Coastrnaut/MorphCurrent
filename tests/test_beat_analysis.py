"""F15: the single analyzer must also handle classical-style material (no style switch)."""
from __future__ import annotations

import array
import math
import random
import wave
from pathlib import Path

from morph_studio.audio import analyze_audio

SR = 11025


def write_wav(path: Path, samples: list[float]) -> Path:
    peak = max(1e-9, max(abs(s) for s in samples))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(array.array("h", [int(s / peak * 30000) for s in samples]).tobytes())
    return path


def bowed_notes(onsets: list[float], seconds: float, *, gains=None, attack=0.06, release=0.35,
                pitches=(196.0, 247.0, 294.0, 392.0), floor=0.01) -> list[float]:
    """Soft-attack harmonic notes (no clicks) on each onset, plus a quiet noise floor."""
    rng = random.Random(3)
    out = [floor * rng.uniform(-1, 1) for _ in range(int(seconds * SR))]
    for k, t0 in enumerate(onsets):
        f = pitches[k % len(pitches)]
        g = gains[k] if gains else 1.0
        start = int(t0 * SR)
        for i in range(int((attack + release) * SR)):
            n = start + i
            if n >= len(out):
                break
            t = i / SR
            env = (t / attack) if t < attack else math.exp(-(t - attack) / (release / 3))
            tone = sum(math.sin(2 * math.pi * f * h * (n / SR)) / h for h in (1, 2, 3))
            out[n] += 0.3 * g * env * tone
    return out


def accelerando(start_bpm: float, end_bpm: float, seconds: float) -> list[float]:
    times, t = [], 0.0
    while t < seconds:
        times.append(t)
        bpm = start_bpm + (end_bpm - start_bpm) * (t / seconds)
        t += 60.0 / bpm
    return times


def test_soft_attacks_with_accelerando_are_tracked(tmp_path):
    truth = accelerando(90, 110, 24.0)
    result = analyze_audio(write_wav(tmp_path / "a.wav", bowed_notes(truth, 24.5)))
    assert result["status"] == "ok"
    assert 90 <= result["bpm"] <= 110
    # Soft attacks have no sharp physical start: compare with the attack midpoint and allow
    # one 16-fps video frame (62.5 ms). Every beat after warm-up must follow the rubato.
    late = [b for b in result["beats"] if b > 3.0]
    errors = [min(abs(b - (t + 0.03)) for t in truth) for b in late]
    assert late and sum(e < 0.0625 for e in errors) / len(errors) >= 0.9, errors
    curve = result["tempo_curve"]
    assert curve[-1]["bpm"] > curve[0]["bpm"]  # tempo rises


def test_quiet_passage_onsets_are_not_lost(tmp_path):
    truth = [i * 0.5 for i in range(40)]  # 120 BPM, 20 s
    gains = [0.03 + 0.97 * (k / 39) ** 2 for k in range(40)]  # pp -> ff swell (~30 dB)
    result = analyze_audio(write_wav(tmp_path / "s.wav", bowed_notes(truth, 20.5, gains=gains)))
    early = [b for b in result["beats"] if 2.0 < b < 8.0]  # the quiet part
    assert len(early) >= 10 and abs(result["bpm"] - 120) <= 2


def test_sections_found_at_dynamic_changes(tmp_path):
    truth = [i * 0.5 for i in range(int(60 / 0.5))]
    gains = [1.0 if t < 20 or t >= 40 else 0.08 for t in truth]  # loud / quiet / loud
    result = analyze_audio(write_wav(tmp_path / "d.wav", bowed_notes(truth, 60.5, gains=gains)))
    times = [s["t"] for s in result["sections"]]
    assert any(abs(t - 20) <= 1.5 for t in times) and any(abs(t - 40) <= 1.5 for t in times), times
