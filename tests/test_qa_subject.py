"""F16 subject-aware QA detectors on synthetic clips; calibration harness."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from morph_studio import cli
from morph_studio.geometry import H, W
from morph_studio.qa import analyze_clip
from morph_studio.qa_subject import analyze_subject, calibrate, detect_subject_defects, frame_metrics

BG, FG = (8, 8, 12), (150, 180, 230)
needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


def frame(cx=0.5, cy=0.5, w=0.3, h=0.5, sharp=True):
    px = [BG] * (W * H)
    x0, x1 = int((cx - w / 2) * W), int((cx + w / 2) * W)
    y0, y1 = int((cy - h / 2) * H), int((cy + h / 2) * H)
    for y in range(max(0, y0), min(H, y1)):
        for x in range(max(0, x0), min(W, x1)):
            # sharp: checkerboard texture; blurred: flat colour
            px[y * W + x] = FG if not sharp or (x + y) % 2 else (90, 110, 160)
    return px


def clip(frames_spec):
    return frame_metrics([frame(**spec) for spec in frames_spec])


def test_clean_morph_has_no_subject_flags():
    specs = [dict(w=0.30 + 0.002 * i) for i in range(33)]
    assert detect_subject_defects(clip(specs)) == []


def test_collapse_detected_in_window():
    specs = [dict() for _ in range(33)]
    for i in range(12, 20):
        specs[i] = dict(w=0.08, h=0.2)
    flags = detect_subject_defects(clip(specs))
    collapse = [f for f in flags if f["type"] == "subject_collapse"]
    assert collapse and collapse[0]["frames"][0] in range(11, 14) and collapse[0]["frames"][1] in range(18, 21)


def test_drift_detected():
    specs = [dict() for _ in range(33)]
    for i in range(10, 22):
        specs[i] = dict(cx=0.75)
    assert any(f["type"] == "subject_drift" for f in detect_subject_defects(clip(specs)))


def test_blur_detected():
    specs = [dict() for _ in range(33)]
    for i in range(14, 22):
        specs[i] = dict(sharp=False)
    assert any(f["type"] == "blur_dip" for f in detect_subject_defects(clip(specs)))


def _write_clip(path: Path, specs) -> Path:
    data = b"".join(bytes(c for px in frame(**s) for c in px) for s in specs)
    subprocess.run(["ffmpeg", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "16",
                    "-i", "-", "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv444p", str(path)],
                   input=data, check=True, shell=False)
    return path


@needs_ffmpeg
def test_real_encoded_clip_and_qa_merge(tmp_path):
    specs = [dict() for _ in range(25)]
    for i in range(8, 15):
        specs[i] = dict(w=0.06, h=0.15)
    path = _write_clip(tmp_path / "c.mp4", specs)
    assert any(f["type"] == "subject_collapse" for f in analyze_subject(path)["flags"])
    report = analyze_clip(path)
    assert report["status"] == "flagged" and any(f["type"] == "subject_collapse" for f in report["flags"])


@needs_ffmpeg
def test_calibration_harness(tmp_path, capsys):
    bad = _write_clip(tmp_path / "bad.mp4", [dict() if not 8 <= i < 15 else dict(w=0.06, h=0.15) for i in range(25)])
    clean = _write_clip(tmp_path / "clean.mp4", [dict() for _ in range(25)])
    labels = tmp_path / "labels.json"
    labels.write_text(json.dumps({"kinds": ["subject_collapse", "subject_drift", "blur_dip"], "clips": [
        {"clip": "bad.mp4", "defects": [{"kind": "subject_collapse", "frames": [8, 14]}]},
        {"clip": "clean.mp4", "defects": []},
        {"clip": "missing.mp4", "defects": []}]}), encoding="utf-8")
    report = calibrate(labels, tmp_path)
    assert report["summary"]["subject_collapse"] == {"tp": 1, "fn": 0, "fp": 0, "precision": 1.0, "recall": 1.0}
    assert report["clips"][2]["status"].startswith("skipped")
    assert cli.main(["qa-calibrate", str(labels), "--repo-root", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)["summary"]["subject_collapse"]["recall"] == 1.0
