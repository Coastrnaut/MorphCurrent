"""F24: temporal continuity diagnostics, honest evaluation, repair proposals and controlled comparison."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from morph_studio import cli
from morph_studio.continuity import (COMPARE_VERDICT_OK, compare_repair, detect_continuity, evaluate,
                                     frame_metrics, propose_repair)

from conftest import REPO

W, H = 128, 74
BG, FG = (8, 8, 16), (220, 220, 220)
needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


def frame(rects, bg=BG, colour=FG):
    """rects: list of (cx, cy, w, h) in frame fractions."""
    px = [bg] * (W * H)
    for cx, cy, w, h in rects:
        x0, x1 = int((cx - w / 2) * W), int((cx + w / 2) * W)
        y0, y1 = int((cy - h / 2) * H), int((cy + h / 2) * H)
        for y in range(max(0, y0), min(H, y1)):
            for x in range(max(0, x0), min(W, x1)):
                px[y * W + x] = colour
    return px


def smooth(n=33):
    return [frame([(0.45 + 0.1 * k / (n - 1), 0.5, 0.2 + 0.15 * k / (n - 1), 0.5)]) for k in range(n)]


def between(a, b, n=33):
    """Smooth morph from rect a to rect b (cx, cy, w, h)."""
    return [frame([tuple(a[i] + (b[i] - a[i]) * k / (n - 1) for i in range(4))]) for k in range(n)]


def kinds(flags):
    return {f["type"] for f in flags}


def window(flags, kind):
    return next(f["frames"] for f in flags if f["type"] == kind)


# --- US1 --------------------------------------------------------------------------------------------

def test_smooth_morph_has_no_flags():
    assert detect_continuity(smooth())["flags"] == []


def test_shape_substitution():
    frames = [frame([(0.5, 0.5, 0.4, 0.4)])] * 16 + [frame([(0.5, 0.5, 0.06, 0.9)])] * 17
    report = detect_continuity(frames)
    flag = next(f for f in report["flags"] if f["type"] == "shape_substitution")
    assert abs(flag["frames"][0] - 16) <= 2 and flag["overlap"] < 0.45


def test_topology_change():
    one = frame([(0.5, 0.5, 0.4, 0.5)])
    four = frame([(0.3, 0.3, 0.1, 0.15), (0.7, 0.3, 0.1, 0.15), (0.3, 0.7, 0.1, 0.15), (0.7, 0.7, 0.1, 0.15)])
    report = detect_continuity([one] * 10 + [four] * 5 + [one] * 10)
    flag = next(f for f in report["flags"] if f["type"] == "topology_change")
    assert flag["frames"] == [10, 14] and flag["parts"] == 4


def test_background_flash():
    frames = [frame([(0.5, 0.5, 0.3, 0.4)])] * 25
    frames[12] = frame([(0.5, 0.5, 0.3, 0.4)], bg=(60, 60, 60))
    report = detect_continuity(frames)
    assert "background_change" in kinds(report["flags"])
    assert 11 <= window(report["flags"], "background_change")[0] <= 13


def test_motion_and_colour_jumps():
    teleport = [frame([(0.3, 0.5, 0.2, 0.3)])] * 12 + [frame([(0.7, 0.5, 0.2, 0.3)])] * 12
    assert "motion_jump" in kinds(detect_continuity(teleport)["flags"])
    switch = [frame([(0.5, 0.5, 0.3, 0.4)])] * 12 + [frame([(0.5, 0.5, 0.3, 0.4)], colour=(240, 160, 160))] * 12
    flags = detect_continuity(switch)["flags"]
    assert kinds(flags) == {"colour_jump"} and abs(window(flags, "colour_jump")[0] - 12) <= 2


def test_unreliable_and_short_clips():
    frames = smooth(17)
    frames[8] = [(250, 250, 250)] * (W * H)  # full white: mask unreliable
    report = detect_continuity(frames)
    assert report["excluded_frames"] == [8] and report["flags"] == []
    assert detect_continuity(smooth(5))["frames"] == 5
    metrics = frame_metrics(smooth(5))
    assert metrics[0]["overlap_prev"] is None and metrics[1]["parts"] == 1


# --- US2 --------------------------------------------------------------------------------------------

def test_evaluate_reports_hits_and_misses(tmp_path):
    clips = {"a.mp4": [frame([(0.5, 0.5, 0.4, 0.4)])] * 16 + [frame([(0.5, 0.5, 0.06, 0.9)])] * 17,
             "b.mp4": smooth()}
    labels = {"schema": 1, "clips": [
        {"id": "swap", "clip": "a.mp4", "defects": [{"kind": "shape_substitution", "frames": [14, 18]}]},
        {"id": "subtle", "clip": "b.mp4", "defects": [{"kind": "subject_collapse", "frames": [10, 20]}]},
        {"id": "gone", "clip": "missing.mp4", "defects": [{"kind": "subject_drift", "frames": [1, 5]}]}]}
    path = tmp_path / "labels.json"
    path.write_text(json.dumps(labels), encoding="utf-8")
    report = evaluate(path, tmp_path, decode=lambda p: clips[Path(p).name])
    rows = {r["id"]: r for r in report["clips"]}
    assert rows["swap"]["defects"][0]["hit"] and rows["subtle"]["defects"][0]["hit"] is False
    assert rows["gone"]["skipped"]
    assert report["recall"]["shape_substitution"] == "1/1" and report["recall"]["subject_collapse"] == "0/1"
    assert report["misses"] == ["subtle: subject_collapse [10, 20]"]
    assert report["window_recall"] == {"shape_substitution": "1/1", "subject_collapse": "0/1"}


# --- US3 --------------------------------------------------------------------------------------------

TASK = {"id": "bridge:a->b", "frames": 65, "seed": 7, "positive_prompt": "orchid becomes butterfly"}


def test_repair_proposal():
    flags = [{"type": "shape_substitution", "frames": [30, 34], "overlap": 0.2},
             {"type": "topology_change", "frames": [31, 33], "parts": 4}]
    prop = propose_repair({"flags": flags, "clip_sha256": "c" * 64}, TASK)
    assert prop["status"] == "proposed - owner review"
    assert any("replaced" in r for r in prop["refinements"]) and any("attached" in r for r in prop["refinements"])
    assert prop["intermediate_anchor"] == {"at_frame": 32, "first_frames": 33, "second_frames": 33}
    assert prop["controlled_comparison"]["seed"] == 7 and prop["controlled_comparison"]["frames"] == 65
    near = propose_repair({"flags": [{"type": "motion_jump", "frames": [3, 4]}]}, TASK)
    assert near["intermediate_anchor"] is None and near["refinements"]
    assert propose_repair({"flags": []}, TASK)["status"] == "no repair proposed"


# --- US4 --------------------------------------------------------------------------------------------

def test_repair_comparison():
    original = [frame([(0.5, 0.5, 0.4, 0.4)])] * 16 + [frame([(0.5, 0.5, 0.06, 0.9)])] * 17
    repaired = between((0.5, 0.5, 0.4, 0.4), (0.5, 0.5, 0.06, 0.9))
    assert detect_continuity(repaired)["flags"] == []
    result = compare_repair(original, repaired)
    assert result["verdict"] == COMPARE_VERDICT_OK and "shape_substitution" in result["removed"]
    assert result["endpoints"]["unchanged"]
    moved = list(repaired)
    moved[-1] = frame([(0.6, 0.5, 0.06, 0.9)])
    assert compare_repair(original, moved)["verdict"] == "endpoint regression"
    assert compare_repair(original, repaired[:-1])["verdict"] == "not comparable"
    worse = [frame([(0.5, 0.5, 0.4, 0.4)])] * 33
    worse[16] = frame([(0.5, 0.5, 0.4, 0.4)], colour=(240, 160, 160))
    bad = compare_repair(smooth(33), [smooth(33)[0]] + worse[1:-1] + [smooth(33)[-1]])
    assert bad["new"] and bad["verdict"] != COMPARE_VERDICT_OK


# --- CLI / real clips -------------------------------------------------------------------------------

def write_mp4(path: Path, frames) -> Path:
    raw = b"".join(bytes(c for px in f for c in px) for f in frames)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                    "-r", "16", "-i", "-", "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv444p", str(path)],
                   input=raw, check=True)
    return path


@needs_ffmpeg
def test_cli_continuity_propose_compare(tmp_path, capsys):
    swap = [frame([(0.5, 0.5, 0.4, 0.4)])] * 16 + [frame([(0.5, 0.5, 0.06, 0.9)])] * 17
    clip = write_mp4(tmp_path / "swap.mp4", swap)
    assert cli.main(["continuity", str(clip)]) == 13
    out = json.loads(capsys.readouterr().out)
    assert "shape_substitution" in kinds(out["flags"])
    capsys.readouterr()
    # run layout for repair-propose
    runs = tmp_path / "runs"
    job = runs / "j000000000000001"
    (job / "outputs").mkdir(parents=True)
    shutil.copy(clip, job / "outputs" / "bridge_00001_.mp4")
    (job / "job.json").write_text(json.dumps({"outputs": [{"kind": "video", "local_path": "outputs\\bridge_00001_.mp4"}]}),
                                  encoding="utf-8")
    run = runs / "run-aaaaaaaaaaaaaaaa"
    run.mkdir()
    (run / "manifest.json").write_text(json.dumps({"order": ["bridge:a->b"], "stages": {"bridge:a->b": {
        "state": "verified", "job_dir": "outputs\\runs\\j000000000000001"}}, "plan_sha256": "x"}), encoding="utf-8")
    (run / "plan.json").write_text(json.dumps({"tasks": {"bridge:a->b": {**TASK, "frames": 33}}}), encoding="utf-8")
    out_file = tmp_path / "repair.json"
    assert cli.main(["repair-propose", str(run), "bridge:a->b", "--out", str(out_file)]) == 0
    capsys.readouterr()
    assert json.loads(out_file.read_text(encoding="utf-8"))["refinements"]
    assert cli.main(["repair-propose", str(run), "bridge:a->b", "--out", str(out_file)]) == 2  # no overwrite
    capsys.readouterr()
    fixed = between((0.5, 0.5, 0.4, 0.4), (0.5, 0.5, 0.06, 0.9))
    repaired = write_mp4(tmp_path / "fixed.mp4", fixed)
    assert cli.main(["repair-compare", str(clip), str(repaired)]) == 0
    assert json.loads(capsys.readouterr().out)["verdict"] == COMPARE_VERDICT_OK


def test_module_has_no_comfy_client():
    source = (REPO / "src/morph_studio/continuity.py").read_text(encoding="utf-8")
    assert "comfy_client" not in source and "httpx" not in source
