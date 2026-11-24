"""F15 visualizer-style band loudness, hits and timeline PNG (synthetic audio)."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from morph_studio import cli
from morph_studio.audio_bands import (BAND_SR, band_hits, band_levels, fft_magnitudes,
                                      render_timeline_png)
from morph_studio.media import inspect_image

REPO = Path(__file__).resolve().parents[1]


def tone_bursts(freq: float, bpm: float, seconds: float = 6.0, rate: int = BAND_SR,
                burst_s: float = 0.08, floor: float = 0.02) -> list[float]:
    """Quiet broadband noise floor plus smooth (raised-cosine) bursts at ``freq`` on each beat.

    Hard on/off gating would splatter energy into every band; real music also has a
    floor in every band, which keeps the long-term averages meaningful.
    """
    import random
    rng = random.Random(7)
    period = 60.0 / bpm
    out = []
    for i in range(int(seconds * rate)):
        t = i / rate
        phase = t % period
        env = 0.5 - 0.5 * math.cos(2 * math.pi * phase / burst_s) if phase < burst_s else 0.0
        out.append(0.8 * env * math.sin(2 * math.pi * freq * t) + floor * rng.uniform(-1, 1))
    return out


def test_fft_peak_bin():
    n = 1024
    mags = fft_magnitudes([math.sin(2 * math.pi * 64 * i / n) for i in range(n)])
    assert max(range(len(mags)), key=mags.__getitem__) == 64


def test_bass_kicks_raise_bass_not_treble():
    levels = band_levels(tone_bursts(60.0, 120), fps=30)
    late = [r for r in levels if r["t"] > 2.0]  # past the long-average warm-up
    assert max(r["bass"] for r in late) > 1.3
    assert max(r["treb"] for r in late) < 1.3
    hits = band_hits(levels)
    late_hits = [h for h in hits if h > 2.0]
    gaps = [b - a for a, b in zip(late_hits, late_hits[1:])]
    assert gaps and all(abs(g - 0.5) < 0.07 for g in gaps)  # one hit per beat at 120 BPM


def test_hihat_raises_treble():
    levels = band_levels(tone_bursts(9000.0, 120), fps=30)
    late = [r for r in levels if r["t"] > 2.0]
    assert max(r["treb"] for r in late) > 1.3 and max(r["bass"] for r in late) < 1.3


def test_values_hover_around_one_for_steady_sound():
    steady = [0.5 * math.sin(2 * math.pi * 200 * i / BAND_SR) for i in range(BAND_SR * 4)]
    late = [r for r in band_levels(steady, fps=30) if r["t"] > 2.5]
    assert all(0.9 < r["bass"] < 1.1 and 0.9 < r["bass_att"] < 1.1 for r in late)


def test_timeline_png(tmp_path):
    levels = band_levels(tone_bursts(60.0, 120, seconds=3), fps=30)
    out = render_timeline_png(levels, tmp_path / "t.png", beats=[0.5, 1.0], boundaries=[1.5])
    assert inspect_image(out) == {"format": "png", "width": len(levels) * 2, "height": 180}
    with pytest.raises(FileExistsError):
        render_timeline_png(levels, out)


def test_cli_audio_visualize(tmp_path, capsys):
    import array
    import wave
    wav = tmp_path / "k.wav"
    samples = tone_bursts(60.0, 120, seconds=9)
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(BAND_SR)
        w.writeframes(array.array("h", [int(s * 32000) for s in samples]).tobytes())
    out = tmp_path / "viz.png"
    assert cli.main(["audio-visualize", str(wav), "--out", str(out),
                     "--storyboard", str(REPO / "configs/sequences/organic-machines.yaml")]) == 0
    report = json.loads(capsys.readouterr().out)
    assert out.is_file() and report["boundaries_s"] == [4.0, 8.0] and report["bass_hits_s"]
