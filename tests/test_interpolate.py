"""F25: delivery frame-rate conversion with provenance, anchor alignment, cut fallback and energy warps."""
from __future__ import annotations

import json
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path

import pytest

from morph_studio import cli
from morph_studio.cache import sha256_file
from morph_studio.interpolate import anchor_alignment, apply_warp, convert, warp_times
from morph_studio.media import probe_video
from morph_studio.qa import decode_gray_frames

from conftest import REPO

pytestmark = pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                                reason="ffmpeg/ffprobe not installed")
W, H = 64, 48


def gray_clip(path: Path, levels: list[int], audio: bool = False) -> Path:
    raw = b"".join(bytes([lv]) * (W * H) for lv in levels)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}", "-r", "16",
           "-i", "-"]
    if audio:
        cmd += ["-f", "lavfi", "-t", f"{len(levels) / 16}", "-i", "sine=frequency=440:sample_rate=48000",
                "-c:a", "aac", "-shortest"]
    cmd += ["-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv444p", str(path)]
    subprocess.run(cmd, input=raw, check=True)
    return path


def ramp(n=65):
    return [min(255, 4 * k) for k in range(n)]


def means(path: Path) -> list[float]:
    return [sum(f) / len(f) for f in decode_gray_frames(path)]


# --- US1 / US2 --------------------------------------------------------------------------------------

def test_convert_blend_keeps_duration_and_original(tmp_path):
    src = gray_clip(tmp_path / "src.mp4", ramp())
    before = sha256_file(src)
    out = tmp_path / "out24.mp4"
    rec = convert(src, out, fps=24, method="blend")
    assert rec["method_used"] == "blend" and rec["ok"]
    assert abs(rec["output"]["duration"] - rec["input"]["duration"]) <= 1 / 24 + 1e-6
    assert rec["input"]["sha256"] == before == sha256_file(src)  # original untouched
    side = json.loads(Path(str(out) + ".interp.json").read_text(encoding="utf-8"))
    assert side["output"]["sha256"] == sha256_file(out) and "framerate" in side["filter"] and side["tool_version"]
    assert probe_video(out)["fps"] == 24
    with pytest.raises(FileExistsError):
        convert(src, out, fps=24, method="blend")


@pytest.mark.parametrize("fps, method", [(30, "repeat"), (48, "motion"), (60, "blend")])
def test_other_rates_and_methods(tmp_path, fps, method):
    src = gray_clip(tmp_path / "src.mp4", ramp(33))
    rec = convert(src, tmp_path / f"o{fps}.mp4", fps=fps, method=method)
    assert rec["ok"] and abs(rec["output"]["duration"] - rec["input"]["duration"]) <= 1 / fps + 1e-6


def test_audio_is_carried_over(tmp_path):
    src = gray_clip(tmp_path / "a.mp4", ramp(33), audio=True)
    out = tmp_path / "a24.mp4"
    convert(src, out, fps=24, method="repeat")
    streams = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0",
                              str(out)], capture_output=True, text=True).stdout.split()
    assert "audio" in streams


def test_anchor_alignment():
    for fps in (24, 48, 60):
        report = anchor_alignment(Fraction(2), fps)
        assert len(report) == 9 and all(r["exact"] for r in report)
    thirty = anchor_alignment(Fraction(2), 30)
    assert sum(r["exact"] for r in thirty) == 5
    assert all(r["offset_s"] <= 0.5 / 30 + 1e-9 for r in thirty)


# --- US3 --------------------------------------------------------------------------------------------

def test_hard_cut_falls_back_to_repeat(tmp_path):
    src = gray_clip(tmp_path / "cut.mp4", [30] * 32 + [220] * 33)
    rec = convert(src, tmp_path / "cut24.mp4", fps=24, method="blend")
    assert rec["method_requested"] == "blend" and rec["method_used"] == "repeat"
    assert "hard cut" in rec["fallback"] and "32" in rec["fallback"]


# --- US4 --------------------------------------------------------------------------------------------

def fast_middle_map(n=65):
    speeds = [0.6] * 20 + [1.8] * 24 + [0.6] * 20  # 64 steps
    scale = (n - 1) / sum(speeds)
    m, pos = [0.0], 0.0
    for s in speeds:
        pos += s * scale
        m.append(pos)
    m[-1] = float(n - 1)
    return m


def test_warp_times_inverse():
    m = fast_middle_map()
    t = warp_times(m)
    assert t[0] == 0.0 and abs(t[-1] - 64) < 1e-9 and all(b > a for a, b in zip(t, t[1:]))
    identity = warp_times([float(i) for i in range(65)])
    assert all(abs(a - i) < 1e-9 for i, a in enumerate(identity))


def test_apply_warp(tmp_path):
    src = gray_clip(tmp_path / "ramp.mp4", ramp())
    out = tmp_path / "warped.mp4"
    rec = apply_warp(src, fast_middle_map(), out)
    assert rec["frames_in"] == rec["frames_out"] == 65 and rec["endpoints_ok"]
    a, b = means(src), means(out)
    assert abs(a[0] - b[0]) <= 3 and abs(a[-1] - b[-1]) <= 3
    early, middle = b[16] - b[0], b[40] - b[24]
    assert middle > early * 1.5  # progress faster where the music surges
    ident = apply_warp(src, [float(i) for i in range(65)], tmp_path / "ident.mp4")
    assert max(abs(x - y) for x, y in zip(a, means(tmp_path / "ident.mp4"))) <= 3 and ident["endpoints_ok"]
    with pytest.raises(ValueError, match="one entry per source frame"):
        apply_warp(src, [0.0, 64.0], tmp_path / "bad.mp4")


# --- CLI --------------------------------------------------------------------------------------------

def test_cli(tmp_path, capsys):
    src = gray_clip(tmp_path / "src.mp4", ramp())
    assert cli.main(["interpolate", str(src), "--fps", "24", "--method", "blend", "--out", str(tmp_path / "c.mp4")]) == 0
    capsys.readouterr().out.encode("ascii")
    mp = tmp_path / "map.json"
    mp.write_text(json.dumps(fast_middle_map()), encoding="utf-8")
    assert cli.main(["warp-apply", str(src), "--map", str(mp), "--out", str(tmp_path / "w.mp4")]) == 0
    plan = {"bridges": [{"warp": {"map": fast_middle_map()}}]}
    pf = tmp_path / "plan.json"
    pf.write_text(json.dumps(plan), encoding="utf-8")
    assert cli.main(["warp-apply", str(src), "--plan", str(pf), "--bridge", "0", "--out", str(tmp_path / "w2.mp4")]) == 0
    assert cli.main(["warp-apply", str(src), "--map", str(mp), "--out", str(tmp_path / "w.mp4")]) == 2  # exists


def test_module_has_no_comfy_client():
    source = (REPO / "src/morph_studio/interpolate.py").read_text(encoding="utf-8")
    assert "comfy_client" not in source and "httpx" not in source


def test_frozen_stretch_stays_frozen(tmp_path):
    levels = [40] * 16 + [120] * 17  # second half is one held image
    out = tmp_path / "held24.mp4"
    convert(gray_clip(tmp_path / "held.mp4", levels), out, fps=24, method="blend")
    m = means(out)
    held = m[len(m) // 2 + 3:]  # well inside the held stretch
    assert max(held) - min(held) <= 1.0  # no invented motion
