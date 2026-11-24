"""F08 temporal heuristics on synthetic frames/clips; candidate seeds; selective rerender."""
from __future__ import annotations

import shutil
import subprocess

import pytest

from morph_studio.dag import compile_plan
from morph_studio.qa import (H, W, analyze_clip, analyze_frames, candidate_seeds, load_reviews,
                             rank_candidates, record_review, rerender_plan)
from morph_studio.schema import load_storyboard

from conftest import REPO

N = W * H


def flat(v: int) -> bytes:
    return bytes([max(0, min(255, int(v)))]) * N


def smooth(n=33):
    return [flat(40 + i * 3) for i in range(n)]  # gentle ramp 40 -> 136


def test_smooth_clip_has_no_flags():
    frames = smooth()
    report = analyze_frames(frames, frames[0], frames[-1])
    assert report["status"] == "no_flags" and report["method"] == "heuristic"


def test_hard_cut_detected():
    frames = smooth()
    frames[16:] = [flat(220 - i) for i in range(len(frames) - 16)]
    assert any(f["type"] == "hard_cut" and f["frame"] == 16 for f in analyze_frames(frames)["flags"])


def test_freeze_detected():
    frames = smooth()
    frames[10:20] = [frames[10]] * 10
    assert any(f["type"] == "freeze" for f in analyze_frames(frames)["flags"])


def test_flare_detected():
    frames = smooth()
    frames[20] = flat(250)
    types = {f["type"] for f in analyze_frames(frames)["flags"]}
    assert "flare" in types


def test_endpoint_mismatch_detected():
    frames = smooth()
    report = analyze_frames(frames, start_ref=flat(200), end_ref=frames[-1])
    assert [f["end"] for f in report["flags"] if f["type"] == "endpoint_mismatch"] == ["start"]


def test_too_short_clip():
    with pytest.raises(ValueError):
        analyze_frames(smooth(2))


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_real_ffmpeg_clip_cut_detected(tmp_path):
    clip = tmp_path / "cut.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=0x202020:s=128x72:r=16:d=1",
                    "-f", "lavfi", "-i", "color=c=0xe0e0e0:s=128x72:r=16:d=1",
                    "-filter_complex", "[0:v][1:v]concat=n=2:v=1[v]", "-map", "[v]",
                    "-pix_fmt", "yuv420p", str(clip)], check=True, shell=False)
    report = analyze_clip(clip)
    assert report["frames"] == 32 and any(f["type"] == "hard_cut" for f in report["flags"])


def test_candidates_ranking_and_selective_rerender(tmp_path):
    plan = compile_plan(load_storyboard(REPO / "configs/sequences/organic-machines.yaml"), repo_root=REPO)
    task = plan["tasks"]["bridge:butterfly->phoenix"]
    seeds = candidate_seeds(task, 123456)
    assert seeds[0] == 202 and len(seeds) == 3 and len(set(seeds)) == 3
    assert seeds == candidate_seeds(task, 123456)
    ranked = rank_candidates({seeds[0]: {"score": 3}, seeds[1]: {"score": 0}, seeds[2]: {"score": 0}})
    assert ranked == [seeds[1], seeds[2], seeds[0]]
    reviews_file = tmp_path / "review.json"
    record_review(reviews_file, "bridge:orchid->butterfly", "approved")
    record_review(reviews_file, "bridge:butterfly->phoenix", "rejected", "wing flare")
    reviews = load_reviews(reviews_file)
    qa = {"bridge:orchid->butterfly": {"status": "flagged"}, "bridge:butterfly->phoenix": {"status": "no_flags"}}
    assert rerender_plan(plan, qa, reviews) == ["bridge:butterfly->phoenix"]
    assert rerender_plan(plan, {"bridge:orchid->butterfly": {"status": "flagged"}}, {}) == ["bridge:orchid->butterfly"]
    with pytest.raises(ValueError):
        record_review(reviews_file, "x", "maybe")
