"""F15 local beat analysis on synthetic click tracks; licence guard; sync drift report."""
from __future__ import annotations

import array
import json
import math
import shutil
import wave
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from morph_studio import cli
from morph_studio.audio import AudioError, analyze_audio, sync_report
from morph_studio.dag import compile_plan
from morph_studio.schema import Storyboard, load_storyboard

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "configs/sequences/organic-machines.yaml"


def click_track(path: Path, bpm: float, seconds: float = 20.0, rate: int = 11025, channels: int = 1,
                offset: float = 0.0, accent_every: int = 4) -> Path:
    n = int(seconds * rate)
    data = [0.0] * n
    period, k, t = 60.0 / bpm, 0, offset
    while t < seconds:
        start = int(t * rate)
        amp = 0.9 if k % accent_every == 0 else 0.5
        for i in range(int(0.03 * rate)):  # 30 ms decaying 1 kHz click
            if start + i < n:
                data[start + i] += amp * math.exp(-i / (0.006 * rate)) * math.sin(2 * math.pi * 1000 * i / rate)
        t += period
        k += 1
    pcm = array.array("h", [int(max(-1, min(1, s)) * 32000) for s in data for _ in range(channels)])
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    return path


@pytest.mark.parametrize("bpm", [90, 120, 140])
def test_click_track_tempo_and_beats(tmp_path, bpm):
    result = analyze_audio(click_track(tmp_path / "c.wav", bpm))
    assert result["status"] == "ok" and abs(result["bpm"] - bpm) <= 1.0, result["bpm"]
    period = 60.0 / bpm
    for k, beat in enumerate(result["beats"][:20]):
        assert abs(beat - k * period) < 0.03
    assert result["confidence"] > 0.3


def test_offset_and_downbeat(tmp_path):
    result = analyze_audio(click_track(tmp_path / "c.wav", 120, offset=0.37))
    assert abs(result["offset_s"] - 0.37) < 0.03
    assert result["downbeat_index"] == 0  # accented first beat of each bar


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg needed for resampling")
@pytest.mark.parametrize("rate,channels", [(44100, 2), (48000, 1), (22050, 2)])
def test_other_rates_and_stereo(tmp_path, rate, channels):
    result = analyze_audio(click_track(tmp_path / "c.wav", 120, seconds=12, rate=rate, channels=channels))
    assert abs(result["bpm"] - 120) <= 1.0


def test_silence_and_missing_file(tmp_path):
    silent = tmp_path / "s.wav"
    with wave.open(str(silent), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(11025)
        w.writeframes(b"\x00\x00" * 11025 * 5)
    result = analyze_audio(silent)
    assert result["status"] == "no_beat_detected" and result["confidence"] == 0.0 and result["beats"] == []
    with pytest.raises(AudioError, match="not found"):
        analyze_audio(tmp_path / "missing.wav")
    with pytest.raises(AudioError, match="URL"):
        analyze_audio("https://example.com/song.mp3")


def test_licence_guard_and_plan_hash():
    data = yaml.safe_load(SAMPLE.read_text(encoding="utf-8"))
    data["audio"]["file"] = "music/track.wav"
    with pytest.raises(ValidationError, match="licensed"):
        Storyboard.model_validate(data)
    data["audio"]["licensed"] = True
    assert Storyboard.model_validate(data).audio.licensed
    data["audio"]["file"] = "https://example.com/a.mp3"
    with pytest.raises(ValidationError, match="local file"):
        Storyboard.model_validate(data)
    plan = compile_plan(load_storyboard(SAMPLE), repo_root=REPO)
    assert plan["plan_sha256"] == "ba2d9dbedb6189beaef6c39a8e5e2a06caef260a2729620c7e8ffa1071bb4bdf"


def test_sync_report_exact_at_120_bpm():
    report = sync_report(load_storyboard(SAMPLE))
    assert report["cumulative_drift_ms"] == 0.0 and report["flagged"] == []
    assert [b["time_s"] for b in report["boundaries"]] == [4.0, 8.0]


def test_sync_report_flags_110_bpm_rounding():
    data = yaml.safe_load(SAMPLE.read_text(encoding="utf-8"))
    data["audio"]["bpm"] = 110  # 8 beats = 4.364 s; nearest Wan length 69 frames = 4.25 s
    report = sync_report(Storyboard.model_validate(data))
    first = report["boundaries"][0]
    assert first["time_s"] == 4.25 and first["flag"] and round(first["error_ms"]) == -114
    assert len(report["flagged"]) == 2


def test_sync_with_analysis_and_cli(tmp_path, capsys):
    track = click_track(tmp_path / "c.wav", 120, seconds=12)
    report = sync_report(load_storyboard(SAMPLE), analyze_audio(track))
    assert report["beat_source"].startswith("analysis") and abs(report["cumulative_drift_ms"]) < 30
    assert cli.main(["audio-analyze", str(track)]) == 0
    assert abs(json.loads(capsys.readouterr().out)["bpm"] - 120) <= 1
    assert cli.main(["audio-sync", str(SAMPLE), "--audio", str(track)]) == 0
    assert cli.main(["audio-analyze", str(tmp_path / "nope.wav")]) == 2
