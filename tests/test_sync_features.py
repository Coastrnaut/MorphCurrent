"""F15 US5: audio feature track, event-locked anchors, bridge character and energy warp."""
from __future__ import annotations

import array
import json
import math
import random
import wave
from pathlib import Path

import pytest

from morph_studio import cli
from morph_studio.audio_bands import BAND_SR
from morph_studio.sync_features import (bridge_character, energy_warp, events, plan_anchors, sync_plan,
                                        track_record)

ACCENTS = [2.5, 5.3, 9.1, 12.4, 15.0, 18.9]


def write_wav(path: Path, seconds: float, accents: list[float], seed: int = 3) -> Path:
    rng = random.Random(seed)
    n = int(seconds * BAND_SR)
    data = [0.01 * (rng.random() * 2 - 1) for _ in range(n)]
    for t in accents:
        start = int(t * BAND_SR)
        for i in range(int(0.18 * BAND_SR)):
            if start + i >= n:
                break
            decay = math.exp(-i / (0.05 * BAND_SR))
            data[start + i] += decay * (0.5 * math.sin(2 * math.pi * 70 * i / BAND_SR) + 0.35 * (rng.random() * 2 - 1))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(BAND_SR)
        w.writeframes(array.array("h", [max(-32767, min(32767, int(s * 32767))) for s in data]).tobytes())
    return path


@pytest.fixture(scope="module")
def accent_track(tmp_path_factory):
    path = write_wav(tmp_path_factory.mktemp("a") / "accents.wav", 22.0, ACCENTS)
    return path, track_record(path, fps=16)


# --- feature track ----------------------------------------------------------------------------------

def test_feature_track_fields_and_hash(accent_track):
    path, rec = accent_track
    assert rec["fps"] == 16 and len(rec["frames"]) == 352 and len(rec["audio_sha256"]) == 64
    row = rec["frames"][40]
    for key in ("t", "bass", "mid", "treb", "bass_att", "mid_att", "treb_att", "vol", "vol_att", "flux",
                "onset", "brightness"):
        assert key in row
    onset_peaks = sorted(range(len(rec["frames"])), key=lambda k: rec["frames"][k]["onset"])[-6:]
    for t in ACCENTS:  # the six strongest onsets sit on the accents
        assert any(abs(k / 16 - t) <= 2 / 16 for k in onset_peaks), t
    assert track_record(path, fps=16)["content_sha256"] == rec["content_sha256"]  # deterministic


# --- events and planner -----------------------------------------------------------------------------

def test_events_and_beatmap_boost(accent_track):
    _, rec = accent_track
    ev = events(rec)
    onset_times = [e["frame"] / 16 for e in ev if e["kind"] == "onset"]
    assert all(any(abs(o - t) <= 2 / 16 for o in onset_times) for t in ACCENTS)
    base = {e["frame"]: e["score"] for e in ev}
    boosted = events(rec, beatmap={"verified": True, "downbeats": [ACCENTS[2]]})
    hit = next(e for e in boosted if e["kind"] == "downbeat")
    assert hit["score"] == 0.25
    assert events(rec, beatmap={"verified": False, "confidence": 0.2, "downbeats": [ACCENTS[2]]}) == ev
    assert base  # sanity


def test_plan_lands_on_accents(accent_track):
    _, rec = accent_track
    plan = plan_anchors(rec, events(rec))
    frames = [a["frame"] for a in plan["anchors"]]
    assert frames[0] == 0 and frames[-1] >= len(rec["frames"]) - 1 - 4
    lengths = [b - a + 1 for a, b in zip(frames, frames[1:])]
    assert all(33 <= L <= 81 and (L - 1) % 4 == 0 for L in lengths), lengths
    for t in ACCENTS:
        assert any(abs(f / 16 - t) <= 2 / 16 for f in frames), (t, frames)


def test_irregular_and_edge_cases(tmp_path):
    rng = random.Random(9)
    times, t = [], 1.0
    while t < 28:
        t += rng.uniform(0.4, 3.5)
        times.append(round(t, 2))
    rec = track_record(write_wav(tmp_path / "irregular.wav", 30.0, times), fps=16)
    plan = plan_anchors(rec, events(rec))
    frames = [a["frame"] for a in plan["anchors"]]
    assert frames[0] == 0 and frames[-1] >= len(rec["frames"]) - 5
    assert all(33 <= b - a + 1 <= 81 for a, b in zip(frames, frames[1:]))
    silent = track_record(write_wav(tmp_path / "silent.wav", 12.0, []), fps=16)
    lengths = [b["frames"] for b in sync_plan(silent)["bridges"]]
    assert lengths and all(abs(L - 65) <= 16 for L in lengths)  # near preferred where nothing happens
    with pytest.raises(ValueError, match="shorter than one bridge"):
        plan_anchors(track_record(write_wav(tmp_path / "tiny.wav", 1.0, []), fps=16), [])
    odd = sync_plan(track_record(write_wav(tmp_path / "odd.wav", 10.3, [5.0]), fps=16))
    assert odd["coverage"]["hold_s"] >= 0 and odd["coverage"]["last_anchor_s"] <= odd["coverage"]["song_s"] + 0.25


# --- character and warp -----------------------------------------------------------------------------

def synthetic(n, **series):
    frames = []
    for k in range(n):
        row = {"t": k / 16, "bass": 1, "mid": 1, "treb": 1, "bass_att": 1.0, "mid_att": 1.0, "treb_att": 1.0,
               "vol": 1, "vol_att": 1.0, "flux": 0, "onset": 0, "brightness": 0.2}
        for key, fn in series.items():
            row[key] = fn(k)
        frames.append(row)
    return {"fps": 16, "frames": frames}


def test_bridge_character():
    assert "bass-heavy" in bridge_character(synthetic(65, bass_att=lambda k: 1.4), 0, 64)
    assert "treble-heavy" in bridge_character(synthetic(65, treb_att=lambda k: 1.4), 0, 64)
    assert "building" in bridge_character(synthetic(65, vol_att=lambda k: 0.8 + 0.6 * k / 64), 0, 64)
    assert "settling" in bridge_character(synthetic(65, vol_att=lambda k: 1.4 - 0.6 * k / 64), 0, 64)
    assert bridge_character(synthetic(65), 0, 64) == ["steady"]


def test_energy_warp_bounds():
    track = synthetic(81, vol_att=lambda k: 3.0 if 20 <= k <= 30 else 0.1)
    warp = energy_warp(track, 0, 80)
    m = warp["map"]
    assert m[0] == 0.0 and m[-1] == 80.0 and len(m) == 81
    assert all(b >= a for a, b in zip(m, m[1:]))  # monotone
    steps = [b - a for a, b in zip(m, m[1:])]
    assert 0.5 - 1e-6 <= min(steps) and max(steps) <= 2.0 + 1e-6
    assert warp["max_speed"] > 1.5 and warp["min_speed"] < 0.9  # surges fast (capped 2x), calm slower
    flat = energy_warp(synthetic(33), 0, 32)
    assert all(abs(s - 1) < 1e-6 for s in (b - a for a, b in zip(flat["map"], flat["map"][1:])))


# --- plan + CLI ------------------------------------------------------------------------------------

def test_sync_plan_and_cli(accent_track, tmp_path, capsys):
    path, rec = accent_track
    plan = sync_plan(rec)
    assert plan["track_sha256"] == rec["content_sha256"] and len(plan["bridges"]) == len(plan["anchors"]) - 1
    assert all({"frames", "character", "warp"} <= set(b) for b in plan["bridges"])
    assert sync_plan(rec)["plan_sha256"] == plan["plan_sha256"]
    feats = tmp_path / "f.json"
    assert cli.main(["audio-features", str(path), "--out", str(feats)]) == 0
    assert cli.main(["audio-features", str(path), "--out", str(feats)]) == 2  # no overwrite
    out = tmp_path / "plan.json"
    assert cli.main(["sync-plan", str(feats), "--out", str(out)]) == 0
    printed = capsys.readouterr().out
    printed.encode("ascii")
    saved = json.loads(out.read_text(encoding="utf-8"))
    assert saved["plan_sha256"] == plan["plan_sha256"]
