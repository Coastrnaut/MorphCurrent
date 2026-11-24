"""F26: geometric HD finishing, identity check, colour match and gated generative upscalers."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from morph_studio import cli
from morph_studio.cache import sha256_file
from morph_studio.finishing import (FinishError, chain, finish, geometry, require_owner_approval,
                                    upscale_models)
from morph_studio.media import probe_video

from conftest import REPO

needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                                  reason="ffmpeg/ffprobe not installed")


def clip(path: Path, size="832x480", frames=17, extra_vf=None, audio=False) -> Path:
    vf = ["-vf", extra_vf] if extra_vf else []
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=size={size}:rate=16:duration={frames / 16}"]
    if audio:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=330:duration={frames / 16}", "-c:a", "aac", "-shortest"]
    cmd += [*vf, "-frames:v", str(frames), "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv444p", str(path)]
    subprocess.run(cmd, check=True)
    return path


# --- geometry ---------------------------------------------------------------------------------------

def test_geometry():
    fit = geometry(832, 480, "1080p", "fit")
    assert (fit["scaled_w"], fit["scaled_h"], fit["pad_x"], fit["pad_y"]) == (1872, 1080, 24, 0)
    fill = geometry(832, 480, "1080p", "fill")
    assert (fill["scaled_w"], fill["scaled_h"], fill["crop_x"], fill["crop_y"]) == (1920, 1108, 0, 14)
    q = geometry(832, 480, "1440p", "fit")
    assert (q["scaled_w"], q["scaled_h"], q["pad_x"]) == (2496, 1440, 32)
    vf = chain(fit, denoise=True, deblock=True, sharpen=True, gains=(1.0, 0.9, 1.1))
    assert vf.index("hqdn3d") < vf.index("scale=") < vf.index("pad=") < vf.index("unsharp")
    assert "lanczos" in vf and "deblock" in vf and "colorchannelmixer" in vf
    assert "hqdn3d" not in chain(fit)


# --- US1 / US2 --------------------------------------------------------------------------------------

@needs_ffmpeg
@pytest.mark.parametrize("mode", ["fit", "fill"])
def test_finish_1080p(tmp_path, mode):
    src = clip(tmp_path / "src.mp4")
    before = sha256_file(src)
    out = tmp_path / f"out_{mode}.mp4"
    rec = finish(src, out, target="1080p", mode=mode, sharpen=True)
    p = probe_video(out)
    assert (p["width"], p["height"]) == (1920, 1080) and p["frame_count"] == 17
    assert abs(p["duration_s"] - probe_video(src)["duration_s"]) <= 1 / 16 + 1e-6
    assert rec["identity"]["passed"], rec["identity"]
    for key in ("chain", "codec", "colour_space", "bit_depth", "seconds", "device"):
        assert key in rec
    assert rec["steps"] == {"denoise": False, "deblock": False, "sharpen": True}
    assert sha256_file(src) == before
    assert json.loads(Path(str(out) + ".finish.json").read_text(encoding="utf-8"))["output"]["sha256"] == sha256_file(out)
    with pytest.raises(FileExistsError):
        finish(src, out, target="1080p", mode=mode)


@needs_ffmpeg
def test_refusals_and_audio(tmp_path):
    big = clip(tmp_path / "big.mp4", size="2560x1440", frames=3)
    with pytest.raises(FinishError, match="larger"):
        finish(big, tmp_path / "x.mp4", target="1080p", mode="fit")
    src = clip(tmp_path / "a.mp4", audio=True)
    out = tmp_path / "a1080.mp4"
    finish(src, out, target="1080p", mode="fit", denoise=True, deblock=True)
    streams = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0",
                              str(out)], capture_output=True, text=True).stdout.split()
    assert "audio" in streams


@needs_ffmpeg
def test_identity_fails_for_altered_output(tmp_path):
    src = clip(tmp_path / "src.mp4")
    rec = finish(src, tmp_path / "dark.mp4", target="1080p", mode="fit", gains=(0.5, 0.5, 0.5), clamp=False)
    assert not rec["identity"]["passed"] and rec["identity"]["first_mad"] > 4


# --- US3 --------------------------------------------------------------------------------------------

@needs_ffmpeg
def test_colour_match(tmp_path):
    from morph_studio.qa_subject import decode_rgb_frames
    neutral = clip(tmp_path / "neutral.mp4")
    anchor = tmp_path / "anchor.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(neutral), "-frames:v", "1", str(anchor)], check=True)
    cast = clip(tmp_path / "cast.mp4", extra_vf="colorchannelmixer=rr=0.85:bb=1.15")
    out = tmp_path / "matched.mp4"
    rec = finish(cast, out, target="1080p", mode="fill", match_anchor=anchor)
    gains = rec["colour_gains"]
    assert all(0.8 <= g <= 1.25 for g in gains) and gains[0] > 1.0 and gains[2] < 1.0

    def mean_rgb(path):
        px = decode_rgb_frames(path)[0]
        return [sum(p[i] for p in px) / len(px) for i in range(3)]
    target, before_m, after_m = mean_rgb(neutral), mean_rgb(cast), mean_rgb(out)
    dist = lambda a, b: sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5  # noqa: E731
    assert dist(after_m, target) < dist(before_m, target)


# --- US4 --------------------------------------------------------------------------------------------

def test_generative_models_gated(tmp_path):
    folder = tmp_path / "models" / "upscale_models"
    folder.mkdir(parents=True)
    (folder / "RealESRGAN_x2plus.pth").write_bytes(b"x")
    (folder / "put_esrgan_and_other_upscale_models_here").write_bytes(b"")
    assert upscale_models(tmp_path) == ["RealESRGAN_x2plus.pth"]
    with pytest.raises(FinishError, match="owner"):
        require_owner_approval("RealESRGAN_x2plus.pth")


# --- CLI --------------------------------------------------------------------------------------------

@needs_ffmpeg
def test_cli(tmp_path, capsys):
    src = clip(tmp_path / "src.mp4")
    assert cli.main(["finish", str(src), "--target", "1080p", "--mode", "fit", "--out", str(tmp_path / "o.mp4")]) == 0
    capsys.readouterr().out.encode("ascii")
    assert cli.main(["finish", "--list-models", "--comfy-root", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)["models"] == []
    assert cli.main(["finish", str(src), "--target", "1080p", "--out", str(tmp_path / "o.mp4")]) == 2  # exists


def test_module_has_no_comfy_client():
    source = (REPO / "src/morph_studio/finishing.py").read_text(encoding="utf-8")
    assert "comfy_client" not in source and "httpx" not in source
