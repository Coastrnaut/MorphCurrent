"""F09 seam-verified joining on real FFmpeg synthetic clips."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from morph_studio.media import probe_video
from morph_studio.qa import decode_gray_frames
from morph_studio.stitcher import SeamError, build_join_command, join_verified

pytestmark = pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                                reason="ffmpeg/ffprobe not installed")
W, H = 64, 36


def ramp_clip(path: Path, start: int, end: int, frames: int = 17, fps: int = 16) -> Path:
    data = b"".join(bytes([round(start + (end - start) * i / (frames - 1))]) * (W * H) for i in range(frames))
    subprocess.run(["ffmpeg", "-v", "error", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}",
                    "-r", str(fps), "-i", "-", "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv420p",
                    str(path)], input=data, check=True, shell=False)
    return path


def test_matching_seam_joins_to_2L_minus_1(tmp_path):
    a = ramp_clip(tmp_path / "ab.mp4", 30, 120)
    b = ramp_clip(tmp_path / "bc.mp4", 120, 210)
    report = join_verified([a, b], tmp_path / "movie.mp4", fps=16)
    assert report["frames"] == 33 and report["measured"]["frame_count"] == 33
    assert report["crossfade"] is False and all(s["match"] for s in report["seams"])
    frames = decode_gray_frames(tmp_path / "movie.mp4")
    assert len(frames) == 33
    assert abs(frames[0][0] - 30) <= 3 and abs(frames[16][0] - 120) <= 3 and abs(frames[-1][0] - 210) <= 3
    assert not (tmp_path / "movie.part.mp4").exists()
    assert "xfade" not in " ".join(report["ffmpeg_args"])
    assert probe_video(tmp_path / "movie.mp4")["fps"] == 16


def test_mismatched_seam_is_refused(tmp_path):
    a = ramp_clip(tmp_path / "ab.mp4", 30, 120)
    b = ramp_clip(tmp_path / "bc.mp4", 180, 220)
    with pytest.raises(SeamError, match="do not match"):
        join_verified([a, b], tmp_path / "movie.mp4", fps=16)
    assert not list(tmp_path.glob("movie*"))


def test_size_mismatch_refused(tmp_path, monkeypatch):
    a = ramp_clip(tmp_path / "ab.mp4", 30, 120)
    b = ramp_clip(tmp_path / "bc.mp4", 120, 210, fps=24)
    with pytest.raises(SeamError, match="size/fps"):
        join_verified([a, b], tmp_path / "movie.mp4", fps=16)


def _streams(path: Path) -> list[str]:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "json",
                          str(path)], capture_output=True, text=True, check=True).stdout
    return [s["codec_type"] for s in json.loads(out)["streams"]]


def test_video_only_and_audio_variants(tmp_path):
    a = ramp_clip(tmp_path / "ab.mp4", 30, 120)
    b = ramp_clip(tmp_path / "bc.mp4", 120, 210)
    silent = join_verified([a, b], tmp_path / "silent.mp4", fps=16)
    assert _streams(tmp_path / "silent.mp4") == ["video"] and silent["audio"] is None
    tone = tmp_path / "tone.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=5",
                    str(tone)], check=True)
    with_audio = join_verified([a, b], tmp_path / "music.mp4", fps=16, audio=tone, audio_offset=0.5)
    assert sorted(_streams(tmp_path / "music.mp4")) == ["audio", "video"]
    assert with_audio["measured"]["frame_count"] == 33
    assert with_audio["measured"]["duration_s"] == pytest.approx(33 / 16, abs=0.1)
    with pytest.raises(ValueError, match="local file"):
        join_verified([a, b], tmp_path / "x.mp4", fps=16, audio=Path("https://example.com/a.mp3"))


def test_audio_command_requires_duration():
    with pytest.raises(ValueError, match="video_seconds"):
        build_join_command([Path("a.mp4"), Path("b.mp4")], Path("o.mp4"), fps=16,
                           verified_matching_endpoints=True, audio=Path("a.wav"))
