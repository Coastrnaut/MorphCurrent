"""F19: edit invalidation (predicted == actual), chapters, storage preflight, scale and restarts."""
from __future__ import annotations

import json
import random
import shutil
import time
from pathlib import Path

import pytest
import yaml

from fake_comfy import FakeComfy
from morph_studio import cli
from morph_studio.dag import compile_plan
from morph_studio.longform import (chapter_index, disk_preflight, ffmetadata, plan_bytes, plan_diff,
                                   proxy_storyboard, stage_identities, storage_report)
from morph_studio.render import run_render
from morph_studio.schema import Storyboard, load_storyboard

from conftest import REPO

SAMPLE = REPO / "configs/sequences/organic-machines.yaml"
PROFILES = {"text_to_image": "configs/profiles/test_t2i.binding.json",
            "reference_edit": "configs/profiles/test_edit.binding.json"}
needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                                  reason="ffmpeg/ffprobe not installed")


def sample_data(**render) -> dict:
    data = yaml.safe_load(SAMPLE.read_text(encoding="utf-8"))
    data["render"].update(render)
    return data


def plan_of(data: dict) -> dict:
    return compile_plan(Storyboard.model_validate(data), repo_root=REPO)


def test_sample_plan_hash_unchanged():
    assert plan_of(sample_data())["plan_sha256"] == \
        "ba2d9dbedb6189beaef6c39a8e5e2a06caef260a2729620c7e8ffa1071bb4bdf"


def test_diff_last_anchor_prompt():
    old = sample_data()
    new = sample_data()
    new["anchors"][2]["prompt"] += " Brighter rim light."
    d = plan_diff(plan_of(old), plan_of(new))
    assert d["rerun_anchors"] == ["anchor:phoenix"]
    assert d["rerun_bridges"] == ["bridge:butterfly->phoenix"] and d["gpu_cached"] == 3
    reasons = {r["task"]: r["reason"] for r in d["stages"]}
    assert reasons["anchor:phoenix"] == "direct"
    assert reasons["bridge:butterfly->phoenix"] == "upstream:anchor:phoenix"


def test_diff_reference_parent_invalidates_lineage():
    new = sample_data()
    new["anchors"][1]["seed"] = 999  # butterfly: phoenix is a reference edit of it
    d = plan_diff(plan_of(sample_data()), plan_of(new))
    assert d["rerun_anchors"] == ["anchor:butterfly", "anchor:phoenix"] and len(d["rerun_bridges"]) == 2
    assert d["gpu_cached"] == 1


def test_diff_bridge_only_and_timing_only():
    new = sample_data()
    new["transitions"][0]["prompt"] += " Slower."
    d = plan_diff(plan_of(sample_data()), plan_of(new))
    assert d["rerun_anchors"] == [] and d["rerun_bridges"] == ["bridge:orchid->butterfly"]
    same = plan_diff(plan_of(sample_data()), plan_of(sample_data()))
    assert same["gpu_rerun"] == 0


def test_diff_insert_scene_and_rename():
    new = sample_data()
    extra = {"id": "lantern", "prompt": "A glass lantern, same framing.", "seed": 7,
             "generation": "independent_t2i"}
    new["anchors"].append(extra)
    new["transitions"].append({"from": "phoenix", "to": "lantern", "duration_beats": 8, "prompt": "morph"})
    d = plan_diff(plan_of(sample_data()), plan_of(new))
    assert d["rerun_anchors"] == ["anchor:lantern"] and d["rerun_bridges"] == ["bridge:phoenix->lantern"]
    assert {r["reason"] for r in d["stages"] if r["status"] == "rerun" and r["kind"] != "final"} == {"added"}
    renamed = sample_data()
    renamed["anchors"][0]["id"] = "glass-orchid"
    renamed["anchors"][1]["reference"] = "glass-orchid"
    renamed["transitions"][0]["from"] = "glass-orchid"
    r = plan_diff(plan_of(sample_data()), plan_of(renamed))
    assert r["gpu_rerun"] == 0 and r["removed"] == []  # identity follows content, not names


@needs_ffmpeg
@pytest.mark.parametrize("edit, expected", [
    (lambda d: d["anchors"][2].__setitem__("seed", 777), 2),
    (lambda d: d["anchors"][1].__setitem__("seed", 4242), 4),
    (lambda d: d["transitions"][1].__setitem__("prompt", "slow unfolding"), 1),
])
def test_predicted_rerun_matches_actual_submissions(image_repo, edit, expected):
    fake = FakeComfy()
    fake.real_video = True
    fake.seed_colour = True  # a changed anchor yields different bytes, as a real model would
    base = sample_data(width=256, height=256)
    edited = json.loads(json.dumps(base))
    edit(edited)
    paths = []
    for name, data in (("a.yaml", base), ("b.yaml", edited)):
        (image_repo / name).write_text(yaml.safe_dump(data), encoding="utf-8")
        paths.append(image_repo / name)
    kw = dict(runs_root=image_repo / "runs", repo_root=image_repo, profiles=PROFILES, poll_seconds=0,
              confirm_gpu=True)
    assert run_render(paths[0], fake.client, **kw)["status"] == "awaiting_review"
    before = fake.prompt_posts
    plans = [compile_plan(load_storyboard(p), profiles=PROFILES, repo_root=image_repo) for p in paths]
    predicted = plan_diff(*plans)["gpu_rerun"]
    assert run_render(paths[1], fake.client, **kw)["status"] == "awaiting_review"
    assert predicted == expected == fake.prompt_posts - before


@needs_ffmpeg
def test_prediction_is_upper_bound_when_bytes_repeat(image_repo):
    """The fake returns identical bytes for a prompt-only edit, so the content-addressed bridge is
    reused: actual re-runs can be fewer than predicted, never more."""
    fake = FakeComfy()
    fake.real_video = True
    base = sample_data(width=256, height=256)
    edited = json.loads(json.dumps(base))
    edited["anchors"][2]["prompt"] += " Rim light."
    paths = []
    for name, data in (("a.yaml", base), ("b.yaml", edited)):
        (image_repo / name).write_text(yaml.safe_dump(data), encoding="utf-8")
        paths.append(image_repo / name)
    kw = dict(runs_root=image_repo / "runs", repo_root=image_repo, profiles=PROFILES, poll_seconds=0,
              confirm_gpu=True)
    run_render(paths[0], fake.client, **kw)
    before = fake.prompt_posts
    run_render(paths[1], fake.client, **kw)
    plans = [compile_plan(load_storyboard(p), profiles=PROFILES, repo_root=image_repo) for p in paths]
    assert fake.prompt_posts - before == 1 <= plan_diff(*plans)["gpu_rerun"] == 2


def test_chapters_index_and_ffmetadata():
    data = sample_data()
    for anchor, chapter in zip(data["anchors"], ["Act I", "Act I", "Act II"]):
        anchor["chapter"] = chapter
    sb = Storyboard.model_validate(data)
    plan = compile_plan(sb, repo_root=REPO)
    assert plan["plan_sha256"] != plan_of(sample_data())["plan_sha256"]
    assert stage_identities(plan) == stage_identities(plan_of(sample_data()))  # chapters cost no GPU
    index = chapter_index(sb, plan)
    assert [a["time_s"] for a in index["anchors"]] == [0.0, 4.0, 8.0]
    assert index["duration_s"] == 8.0625
    assert index["chapters"] == [
        {"chapter": "Act I", "start_s": 0.0, "anchors": ["orchid", "butterfly"], "end_s": 8.0},
        {"chapter": "Act II", "start_s": 8.0, "anchors": ["phoenix"], "end_s": 8.0625}]
    meta = ffmetadata(index)
    assert meta.startswith(";FFMETADATA1\n") and "START=8000\nEND=8062\ntitle=Act II" in meta


def test_chapters_must_be_contiguous():
    data = sample_data()
    for anchor, chapter in zip(data["anchors"], ["A", "B", "A"]):
        anchor["chapter"] = chapter
    with pytest.raises(ValueError, match="contiguous"):
        Storyboard.model_validate(data)


def test_proxy_storyboard_has_own_identity():
    proxy = proxy_storyboard(sample_data())
    assert proxy["render"]["width"] == 640 and proxy["name"] == "organic-machines-proxy"
    d = plan_diff(plan_of(sample_data()), plan_of(proxy))
    assert d["gpu_cached"] == 0 and d["gpu_rerun"] == 5  # never reuses full-resolution artifacts
    assert proxy_storyboard(proxy)["name"] == "organic-machines-proxy"


def test_storage_estimates_and_preflight(tmp_path):
    plan = plan_of(sample_data())
    est = plan_bytes(plan)
    # 832x480: 3 anchors x 1.6 MB, 2 bridges x 3 candidates x 5.2 MB, final 5.2 MB (2x measured sizes)
    assert est["stages"]["final:movie"] == 2 * est["stages"]["bridge:orchid->butterfly"] // 6
    assert 3e7 < est["total_bytes"] < 6e7
    assert plan_bytes(plan, done=set(plan["order"]))["total_bytes"] == 0
    ok = disk_preflight(plan, tmp_path / "runs", disk_usage=lambda p: (0, 0, 10 * 1024 ** 3))
    assert ok["ok"]
    low = disk_preflight(plan, tmp_path / "runs", disk_usage=lambda p: (0, 0, 2 * 1024 ** 3))
    assert not low["ok"] and "reserve" in low["message"]


def test_render_refuses_when_disk_low(image_repo):
    fake = FakeComfy()
    (image_repo / "sb.yaml").write_text(yaml.safe_dump(sample_data(width=256, height=256)), encoding="utf-8")
    result = run_render(image_repo / "sb.yaml", fake.client, runs_root=image_repo / "runs",
                        repo_root=image_repo, profiles=PROFILES, poll_seconds=0, confirm_gpu=True,
                        disk_usage=lambda p: (0, 0, 1024 ** 3))
    assert result["status"] == "blocked_disk" and fake.prompt_posts == 0
    assert not (image_repo / "runs" / ".morphcurrent-gpu.lock").exists()


def chain_storyboard(n: int, size: int = 256) -> dict:
    anchors = [{"id": "a0", "prompt": "scene 0", "seed": 1, "generation": "text_to_image"}]
    anchors += [{"id": f"a{i}", "prompt": f"scene {i}", "seed": i + 1, "generation": "reference_edit",
                 "reference": f"a{i - 1}"} for i in range(1, n)]
    return {"schema_version": 1, "name": f"chain-{n}",
            "render": {"width": size, "height": size, "anchor_profile": "x", "bridge_profile": "y",
                       "master_seed": 5},
            "style": {"description": "test"}, "audio": {"bpm": 120},
            "anchors": anchors,
            "transitions": [{"from": f"a{i}", "to": f"a{i + 1}", "duration_beats": 2, "prompt": "morph"}
                            for i in range(n - 1)]}


@pytest.mark.parametrize("n", [2, 10, 50])
def test_scale_compile(n):
    start = time.perf_counter()
    plan = plan_of(chain_storyboard(n))
    assert time.perf_counter() - start < 2
    assert plan == plan_of(chain_storyboard(n))  # deterministic
    seen = set()
    for task_id in plan["order"]:  # topological
        assert all(dep in seen for dep in plan["tasks"][task_id]["depends_on"])
        seen.add(task_id)
    assert sum(t["kind"] == "bridge" for t in plan["tasks"].values()) == n - 1
    index = chapter_index(Storyboard.model_validate(chain_storyboard(n)), plan)
    assert index["anchors"][-1]["time_s"] == (n - 1) * 1.0  # 2 beats @120 BPM = 17 frames = 1 s span
    edited = chain_storyboard(n)
    edited["anchors"][n // 2]["seed"] = 10_000
    d = plan_diff(plan, plan_of(edited))
    assert len(d["rerun_anchors"]) == n - n // 2  # lineage: the edited anchor and all later edits


@needs_ffmpeg
def test_random_restarts_no_duplicates(image_repo):
    fake = FakeComfy()
    fake.real_video = True
    sb = image_repo / "chain.yaml"
    sb.write_text(yaml.safe_dump(chain_storyboard(10)), encoding="utf-8")
    kw = dict(runs_root=image_repo / "runs", repo_root=image_repo, profiles=PROFILES, poll_seconds=0,
              confirm_gpu=True)
    rng = random.Random(19)
    statuses = []
    for _ in range(40):
        result = run_render(sb, fake.client, max_jobs=rng.randint(1, 4), **kw)
        statuses.append(result["status"])
        if result["status"] != "paused_budget":
            break
    assert statuses[-1] == "awaiting_review" and len(statuses) > 3
    assert fake.prompt_posts == 10 + 9  # one submission per stage despite the interruptions
    report = storage_report(image_repo / "runs")
    assert report["jobs"]["anchor"]["count"] == 10 and report["jobs"]["bridge"]["count"] == 9


def test_cli_plan_diff_timeline_storage(tmp_path, capsys):
    new = sample_data()
    new["anchors"][2]["prompt"] += " x"
    (tmp_path / "new.yaml").write_text(yaml.safe_dump(new), encoding="utf-8")
    assert cli.main(["plan-diff", str(SAMPLE), str(tmp_path / "new.yaml"), "--repo-root", str(REPO)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["gpu_rerun"] == 2 and all(r["status"] == "rerun" for r in out["stages"])
    meta, proxy = tmp_path / "ch.txt", tmp_path / "proxy.yaml"
    assert cli.main(["timeline", str(SAMPLE), "--ffmetadata", str(meta), "--write-proxy", str(proxy),
                     "--repo-root", str(REPO)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["duration_s"] == 8.0625 and meta.read_text(encoding="utf-8").startswith(";FFMETADATA1")
    assert load_storyboard(proxy).render.width == 640
    assert cli.main(["storage", "--runs-root", str(tmp_path / "none")]) == 0
    assert json.loads(capsys.readouterr().out)["total_bytes"] == 0
