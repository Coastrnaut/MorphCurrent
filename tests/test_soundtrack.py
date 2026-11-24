"""F37: sync report, warp report, animatic, captions, narration timing, click track and beat-map verification."""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import wave
from pathlib import Path

import pytest
import yaml

from morph_studio import cli
from morph_studio import soundtrack as st
from morph_studio.media import probe_video

from conftest import REPO

FILM = REPO / "configs/sequences/engineering-film.yaml"
PLAN = REPO / "configs/film/sync-plan.json"
needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="ffmpeg missing")


def mini(tmp_path, frames=(33, 37, 33)) -> tuple[Path, Path]:
    ids = ["a", "b", "c", "d"]
    chapters = ["one", "one", "two", "two"]
    sb = {"schema_version": 1, "name": "mini", "render": {"anchor_profile": "anchor_t2i", "bridge_profile": "wan22_flf2v"},
          "style": {"description": "x"},
          "anchors": [{"id": k, "prompt": k, "chapter": c} for k, c in zip(ids, chapters)],
          "transitions": [{"from": ids[i], "to": ids[i + 1], "frames": f, "prompt": "m"} for i, f in enumerate(frames)]}
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "mini.yaml"
    path.write_text(yaml.safe_dump(sb), encoding="utf-8")
    anchors, frame = [], 0
    for i in range(4):
        anchors.append({"frame": frame, "t": frame / 16, "event": ["section", "onset", "energy_peak", "onset"][i]})
        if i < 3:
            frame += [33, 37, 33][i] - 1
    plan = {"fps": 16.0, "anchors": anchors,
            "bridges": [{"frames": f, "warp": {"map": [j * (f - 1) / (f - 1) for j in range(f)]}} for f in (33, 37, 33)],
            "coverage": {"hold_s": 0.5, "last_anchor_s": frame / 16, "song_s": frame / 16 + 0.5}}
    pp = tmp_path / "plan.json"
    pp.write_text(json.dumps(plan), encoding="utf-8")
    return path, pp


def tone(path: Path, seconds: float) -> Path:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency=330:duration={seconds}",
                    str(path)], check=True)
    return path


# --- US1 ------------------------------------------------------------------------------------------

def test_sync_report_synthetic(tmp_path):
    sb, plan = mini(tmp_path)
    rep = st.sync_report(sb, plan)
    assert [r["error_frames"] for r in rep["rows"]] == [0, 0, 0, 0] and rep["gate"]
    assert rep["rows"][1]["event"] == "onset"
    bad, _ = mini(tmp_path / "x", frames=(37, 37, 33))
    rep = st.sync_report(bad, plan)
    assert [r["error_frames"] for r in rep["rows"]] == [0, 4, 4, 4]
    assert rep["drift_frames"] == 4 and not rep["gate"]
    short = json.loads(plan.read_text())
    short["anchors"] = short["anchors"][:3]
    p2 = tmp_path / "p2.json"
    p2.write_text(json.dumps(short))
    with pytest.raises(st.SoundtrackError, match="4"):
        st.sync_report(sb, p2)


def test_sync_report_real_film():
    rep = st.sync_report(FILM, PLAN)
    assert len(rep["rows"]) == 96 and rep["gate"] and rep["max_abs_error"] == 0 and rep["drift_frames"] == 0


# --- US2 ------------------------------------------------------------------------------------------

def test_warp_report(tmp_path):
    rep = st.warp_report(PLAN)
    assert len(rep["rows"]) == 95 and rep["ok"]
    assert all(r["pinned"] and 0.5 - 1e-6 <= r["min_speed"] and r["max_speed"] <= 2 + 1e-6 for r in rep["rows"])
    plan = json.loads(PLAN.read_text())
    plan["bridges"][0]["warp"]["map"][-1] -= 1
    plan["bridges"][1]["warp"]["map"][5] = plan["bridges"][1]["warp"]["map"][4] + 3
    p = tmp_path / "w.json"
    p.write_text(json.dumps(plan))
    bad = st.warp_report(p)
    assert not bad["ok"] and "unpinned" in bad["rows"][0]["flags"] and "speed" in " ".join(bad["rows"][1]["flags"])


# --- US3 ------------------------------------------------------------------------------------------

@needs_ffmpeg
def test_animatic_cards_no_audio(tmp_path):
    sb, plan = mini(tmp_path)
    out = tmp_path / "a.mp4"
    rec = st.animatic(sb, out, plan=plan)
    p = probe_video(out)
    expected = (32 + 36 + 32) / 16 + 0.5  # picture + tail hold
    assert abs(p["duration_s"] - expected) <= 1 / 16 + 1e-6 and rec["ok"]
    assert rec["audio"] is None and rec["measured"]["audio"] is False
    assert [c["frame"] for c in rec["cuts"]] == [0, 32, 68, 100] and {c["source"] for c in rec["cuts"]} == {"card"}
    with pytest.raises(FileExistsError):
        st.animatic(sb, out, plan=plan)


@needs_ffmpeg
def test_animatic_still_and_audio(tmp_path):
    sb, plan = mini(tmp_path)
    runs = tmp_path / "runs"
    run = runs / "run-x"
    run.mkdir(parents=True)
    job = runs / "job0"
    (job / "outputs").mkdir(parents=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=red:size=832x480", "-frames:v", "1",
                    str(job / "outputs" / "a.png")], check=True)
    (job / "job.json").write_text(json.dumps({"image": {"local_path": "outputs/a.png"}}), encoding="utf-8")
    (run / "manifest.json").write_text(json.dumps({"order": ["anchor:b"], "stages": {
        "anchor:b": {"state": "verified", "job_dir": "outputs/runs/job0"}}}), encoding="utf-8")
    music = tone(tmp_path / "m.wav", 12)
    with pytest.raises(st.SoundtrackError, match="licensed"):
        st.animatic(sb, tmp_path / "u.mp4", plan=plan, audio=music)
    rec = st.animatic(sb, tmp_path / "b.mp4", plan=plan, run_dir=run, audio=music, licensed=True, offset=1.0)
    assert [c["source"] for c in rec["cuts"]] == ["card", "still", "card", "card"]
    assert rec["measured"]["audio"] is True and rec["ok"]
    assert abs(rec["measured"]["audio_duration_s"] - rec["expected_s"]) <= 0.1


# --- US4 ------------------------------------------------------------------------------------------

def test_captions_roundtrip(tmp_path):
    cues = st.captions(FILM, REPO / "configs/concepts/engineering-film.yaml")
    assert len(cues) == 96 and all(a["end_s"] <= b["start_s"] + 1e-9 for a, b in zip(cues, cues[1:]))
    out = tmp_path / "c.srt"
    st.srt_write(cues, out)
    back = st.srt_parse(out)
    assert [(c["start_s"], c["text"]) for c in back] == [(round(c["start_s"], 3), c["text"]) for c in cues]
    assert "towering thunderstorm" in back[0]["text"]


def test_narration_check(tmp_path):
    sb, _ = mini(tmp_path)
    script = tmp_path / "n.yaml"
    script.write_text(yaml.safe_dump({"lines": [
        {"text": "It begins with a storm.", "at": "a", "duration": 3},
        {"text": "Overlapping line.", "t": 2.0, "duration": 1},
        {"text": "Charge is stored.", "at": "c", "duration": 2},
        {"text": "Too late.", "t": 6.5, "duration": 2}]}), encoding="utf-8")
    rep = st.narration_check(script, sb, tmp_path / "n.srt")
    flags = {l["index"]: l["flags"] for l in rep["lines"]}
    assert "overlap" in flags[2] and "past_end" in flags[4] and not rep["ok"]
    assert rep["gaps"] and Path(rep["srt"]).is_file()
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump({"lines": [{"text": "x", "at": "zzz", "duration": 1}]}), encoding="utf-8")
    with pytest.raises(st.SoundtrackError, match="zzz"):
        st.narration_check(bad, sb, tmp_path / "b.srt")


# --- US5 ------------------------------------------------------------------------------------------

def test_click_track_and_verify(tmp_path):
    bm = tmp_path / "beats.json"
    bm.write_text(json.dumps({"downbeats": [0.5, 1.0, 1.5, 2.25], "verified": False}), encoding="utf-8")
    out = tmp_path / "click.wav"
    rep = st.click_track(bm, out)
    assert rep["clicks"] == 4
    with wave.open(str(out)) as w:
        rate = w.getframerate()
        data = w.readframes(w.getnframes())
    import struct
    samples = struct.unpack(f"<{len(data) // 2}h", data)
    for t in (0.5, 1.0, 1.5, 2.25):
        i = int(round(t * rate))
        assert max(abs(s) for s in samples[i:i + 200]) > 1000
    assert max(abs(s) for s in samples[int(0.7 * rate):int(0.9 * rate)]) == 0
    verified = tmp_path / "beats.verified.json"
    before = bm.read_bytes()
    data = st.verify_beatmap(bm, verified, owner="owner", corrections={3: 2.0})
    assert data["verified"] and data["verified_by"] == "owner" and data["downbeats"][3] == 2.0
    assert bm.read_bytes() == before
    with pytest.raises(st.SoundtrackError, match="owner"):
        st.verify_beatmap(bm, tmp_path / "x.json", owner=" ")
    with pytest.raises(st.SoundtrackError, match="increasing"):
        st.verify_beatmap(bm, tmp_path / "y.json", owner="o", corrections={1: 0.2})


@needs_ffmpeg
def test_click_track_with_music(tmp_path):
    bm = tmp_path / "beats.json"
    bm.write_text(json.dumps({"downbeats": [0.5, 1.0]}), encoding="utf-8")
    rep = st.click_track(bm, tmp_path / "mix.wav", music=tone(tmp_path / "m.wav", 2))
    assert Path(rep["out"]).is_file() and rep["music"]


# --- CLI ------------------------------------------------------------------------------------------

@needs_ffmpeg
def test_cli(tmp_path, capsys):
    assert cli.main(["sync-report", str(FILM)]) == 0
    assert json.loads(capsys.readouterr().out)["gate"] is True
    assert cli.main(["warp-report"]) == 0
    capsys.readouterr()
    sb, plan = mini(tmp_path)
    assert cli.main(["sync-report", str(sb), "--plan", str(plan)]) == 0
    capsys.readouterr()
    assert cli.main(["animatic", str(sb), "--plan", str(plan), "--out", str(tmp_path / "a.mp4")]) == 0
    capsys.readouterr()
    assert cli.main(["captions", str(sb), "--out", str(tmp_path / "c.srt")]) == 0
    capsys.readouterr().out.encode("ascii")


def test_cli_narration_click_verify(tmp_path, capsys):
    sb, _ = mini(tmp_path)
    script = tmp_path / "n.yaml"
    script.write_text(yaml.safe_dump({"lines": [{"text": "a", "at": "a", "duration": 9}]}), encoding="utf-8")
    assert cli.main(["narration-check", str(script), str(sb), "--out", str(tmp_path / "n.srt")]) == 1  # past end
    capsys.readouterr()
    bad = tmp_path / "b.yaml"
    bad.write_text(yaml.safe_dump({"lines": [{"text": "a", "at": "nope", "duration": 1}]}), encoding="utf-8")
    assert cli.main(["narration-check", str(bad), str(sb), "--out", str(tmp_path / "b.srt")]) == 2
    bm = tmp_path / "beats.json"
    bm.write_text(json.dumps({"downbeats": [0.5, 1.0, 1.5]}), encoding="utf-8")
    assert cli.main(["click-track", str(bm), "--out", str(tmp_path / "c.wav")]) == 0
    assert json.loads(capsys.readouterr().out)["clicks"] == 3
    assert cli.main(["beatmap-verify", str(bm), "--owner", "owner", "--correct", "2=1.75",
                     "--out", str(tmp_path / "v.json")]) == 0
    assert json.loads(capsys.readouterr().out)["downbeats"] == [0.5, 1.0, 1.75]
    assert cli.main(["beatmap-verify", str(bm), "--owner", " ", "--out", str(tmp_path / "w.json")]) == 2
