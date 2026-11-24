"""F30: versioned delivery presets, verification, codec fallback, crop safe area, final acceptance view."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from morph_studio import cli
from morph_studio import delivery as dv
from morph_studio import release as rel
from morph_studio.cache import sha256_file

from conftest import REPO

needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                                  reason="ffmpeg/ffprobe not installed")


def clip(path: Path, frames: int = 17, audio: bool = False, subject: str = "centre") -> Path:
    """832x480 16 fps clip: dark background with a bright box (the subject) centred or at the left edge."""
    x = {"centre": 366, "left": 4}[subject]
    vf = f"drawbox=x={x}:y=190:w=100:h=100:color=white:t=fill"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x101010:size=832x480:rate=16:duration={frames / 16}"]
    if audio:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=330:duration={frames / 16}", "-c:a", "aac", "-shortest"]
    cmd += ["-vf", vf, "-frames:v", str(frames), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)]
    subprocess.run(cmd, check=True)
    return path


def tone(path: Path, seconds: float) -> Path:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
                    str(path)], check=True)
    return path


# --- foundational ---------------------------------------------------------------------------------

def test_presets_and_recipes():
    assert set(dv.PRESETS) == {"landscape-1080p", "vertical-1080x1920", "square-1080", "video-only-1080p",
                               "licensed-audio-1080p", "hires-1440p", "smooth-24fps-1080p"}
    sums = {name: dv.recipe_sha256(name) for name in dv.PRESETS}
    assert len(set(sums.values())) == 7 and sums == {name: dv.recipe_sha256(name) for name in dv.PRESETS}
    assert dv.crop_rect(832, 480, "9:16") == (270, 480, 281, 0)
    assert dv.crop_rect(832, 480, "1:1") == (480, 480, 176, 0)
    with pytest.raises(dv.DeliveryError, match="valid"):
        dv.recipe("cinema-4k")


def test_safe_area():
    centre = {"centroid": [0.5, 0.5], "extent": [0.1, 0.2]}
    edge = {"centroid": [0.06, 0.5], "extent": [0.1, 0.2]}
    assert dv.safe_area(centre, 832, 480, "9:16") == "inside"
    assert dv.safe_area(edge, 832, 480, "9:16") == "outside"
    assert dv.safe_area({}, 832, 480, "9:16") == "unknown"


# --- US1 ------------------------------------------------------------------------------------------

@needs_ffmpeg
def test_deliver_formats(tmp_path):
    src = clip(tmp_path / "movie.mp4", audio=True)
    before = sha256_file(src)
    out = dv.deliver(src, tmp_path / "out", ["landscape-1080p", "vertical-1080x1920", "square-1080", "hires-1440p",
                                             "smooth-24fps-1080p"])
    assert not out["errors"]
    sizes = {r["preset"]: (r["output"]["width"], r["output"]["height"]) for r in out["results"]}
    assert sizes == {"landscape-1080p": (1920, 1080), "vertical-1080x1920": (1080, 1920),
                     "square-1080": (1080, 1080), "hires-1440p": (2560, 1440), "smooth-24fps-1080p": (1920, 1080)}
    for r in out["results"]:
        assert r["verification"]["passed"], r["verification"]
        assert r["recipe_sha256"] == dv.recipe_sha256(r["preset"])
        rec = json.loads(Path(r["output"]["path"] + ".delivery.json").read_text(encoding="utf-8"))
        assert rec["output"]["sha256"] == sha256_file(Path(r["output"]["path"]))
        assert rec["output"]["audio"] is True  # copied
    smooth = next(r for r in out["results"] if r["preset"] == "smooth-24fps-1080p")
    assert abs(smooth["output"]["fps"] - 24) < 1e-6 and smooth["fps_step"] == "blend 16->24"
    already = dv.deliver_one(Path(smooth["output"]["path"]), tmp_path / "out3", "smooth-24fps-1080p")
    assert already["fps_step"] == "none (already 24 fps)" and already["verification"]["passed"]
    assert sha256_file(src) == before
    again = dv.deliver(src, tmp_path / "out2", ["landscape-1080p"])
    assert again["results"][0]["recipe_sha256"] == out["results"][0]["recipe_sha256"]
    with pytest.raises(FileExistsError):
        dv.deliver_one(src, tmp_path / "out", "landscape-1080p")


@needs_ffmpeg
def test_audio_policies(tmp_path):
    src = clip(tmp_path / "m.mp4", frames=32, audio=True)
    r = dv.deliver_one(src, tmp_path / "o", "video-only-1080p")
    assert r["output"]["audio"] is False and r["verification"]["passed"]
    music = tone(tmp_path / "music.wav", 5)
    r = dv.deliver_one(src, tmp_path / "o", "licensed-audio-1080p", audio=music, audio_licensed=True, audio_offset=0.5)
    assert r["output"]["audio"] is True and r["verification"]["passed"], r["verification"]
    assert abs(r["output"]["audio_duration_s"] - r["output"]["duration_s"]) <= 1 / 16 + 0.03
    assert r["audio_source"]["offset_s"] == 0.5
    with pytest.raises(dv.DeliveryError, match="licensed"):
        dv.deliver_one(src, tmp_path / "o2", "licensed-audio-1080p", audio=music, audio_licensed=False)
    short = tone(tmp_path / "short.wav", 1)
    with pytest.raises(dv.DeliveryError, match="shorter"):
        dv.deliver_one(src, tmp_path / "o3", "licensed-audio-1080p", audio=short, audio_licensed=True)


@needs_ffmpeg
def test_encoder_fallback_and_mismatch(tmp_path, monkeypatch):
    src = clip(tmp_path / "m.mp4")
    monkeypatch.setattr(dv, "available_encoders", lambda: {"mpeg4", "aac"})
    r = dv.deliver_one(src, tmp_path / "o", "landscape-1080p")
    assert r["encoder"]["fallback"] is True and r["output"]["codec"] == "mpeg4" and r["verification"]["passed"]
    monkeypatch.undo()
    check = dv.verify({"width": 1920, "height": 1080, "fps": 16, "codec": "h264", "audio": False, "duration_s": 1.0,
                       "frame_s": 1 / 16},
                      {"width": 1920, "height": 1072, "fps": 16, "codec": "h264", "audio": True, "duration_s": 1.2})
    assert not check["passed"] and {m["key"] for m in check["mismatches"]} == {"height", "audio", "duration_s"}


@needs_ffmpeg
def test_refusals_continue(tmp_path):
    big = tmp_path / "big.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=size=2560x1440:rate=16:duration=0.2",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(big)], check=True)
    out = dv.deliver(big, tmp_path / "o", ["landscape-1080p", "hires-1440p", "nope"])
    assert [r["preset"] for r in out["results"]] == ["hires-1440p"]
    errors = {e["preset"]: e["error"] for e in out["errors"]}
    assert "larger" in errors["landscape-1080p"] and "valid" in errors["nope"]


# --- US2 ------------------------------------------------------------------------------------------

@needs_ffmpeg
def test_crop_safe_area_reported(tmp_path):
    centre = dv.deliver_one(clip(tmp_path / "c.mp4"), tmp_path / "o", "vertical-1080x1920")
    assert centre["crop"]["anchors"] == {"first": "inside", "last": "inside"} and "warning" not in centre["crop"]
    sq = dv.deliver_one(clip(tmp_path / "c2.mp4"), tmp_path / "o", "square-1080")
    assert sq["crop"]["anchors"]["first"] == "inside"
    left = dv.deliver_one(clip(tmp_path / "l.mp4", subject="left"), tmp_path / "o", "vertical-1080x1920")
    assert left["crop"]["anchors"]["first"] == "outside" and "warning" in left["crop"]
    assert Path(left["output"]["path"]).is_file()


# --- US3 ------------------------------------------------------------------------------------------

LEDGER = REPO / "docs/SPECKIT_FEATURE_LEDGER.md"


def test_acceptance_through():
    m30 = rel.acceptance_matrix(LEDGER, through=30)
    assert len(m30["rows"]) == 30 and m30["rows"][-1]["feature"] == "F30"
    assert len(rel.acceptance_matrix(LEDGER, through=40)["rows"]) == 40
    assert len(rel.acceptance_matrix(LEDGER, all_features=True)["rows"]) == 40
    assert len(rel.acceptance_matrix(LEDGER)["rows"]) == 20


def test_release_check_real_and_synthetic(tmp_path, monkeypatch):
    real = rel.release_check(LEDGER, REPO, through=30)
    assert real["ready_for_owner_review"] is False and real["reasons"]
    assert "owner approval" in real["note"]
    ledger = tmp_path / "ledger.md"
    ledger.write_text("\n".join(f"| **F{i:02d}** | x | y | P1 | **OFFLINE-PASS** — evidence |" for i in range(1, 41)),
                      encoding="utf-8")
    monkeypatch.setattr(rel, "audit_repo", lambda root=".": {"errors": 0, "warnings": 0, "checks": []})
    ok = rel.release_check(ledger, tmp_path, through=30)
    assert ok["ready_for_owner_review"] is True and ok["reasons"] == [] and "owner approval" in ok["note"]
    source = (REPO / "src/morph_studio/release.py").read_text(encoding="utf-8")
    assert "git tag" not in source and '"tag"' not in source


# --- CLI ------------------------------------------------------------------------------------------

@needs_ffmpeg
def test_cli(tmp_path, capsys):
    src = clip(tmp_path / "m.mp4")
    assert cli.main(["deliver", str(src), "--preset", "landscape-1080p", "--out-dir", str(tmp_path / "o")]) == 0
    capsys.readouterr().out.encode("ascii")
    assert cli.main(["deliver", str(src), "--preset", "landscape-1080p", "--preset", "square-1080",
                     "--out-dir", str(tmp_path / "o")]) == 2  # first exists, second still delivered
    assert (tmp_path / "o" / "m_square-1080.mp4").is_file()
    capsys.readouterr()
    assert cli.main(["deliver", "--list-presets"]) == 0
    assert len(json.loads(capsys.readouterr().out)["presets"]) == 7
    assert cli.main(["acceptance", "--through", "30"]) == 0
    assert len(json.loads(capsys.readouterr().out)["rows"]) == 30
    assert cli.main(["release-check"]) == 1
    assert json.loads(capsys.readouterr().out)["ready_for_owner_review"] is False
