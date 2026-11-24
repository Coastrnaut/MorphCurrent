"""F17 run lock, budgets with pause/resume (no duplicate prompts), schedule preview."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

from fake_comfy import FakeComfy
from morph_studio import cli
from morph_studio.dag import compile_plan
from morph_studio.perf import load_history
from morph_studio.render import run_render
from morph_studio.scheduler import Budget, LockBusy, RunLock, schedule_preview
from morph_studio.schema import load_storyboard

from conftest import REPO

PROFILES = {"text_to_image": "configs/profiles/test_t2i.binding.json",
            "reference_edit": "configs/profiles/test_edit.binding.json"}
needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                                  reason="ffmpeg/ffprobe not installed")


def test_lock_contention_and_release(tmp_path):
    first = RunLock(tmp_path).acquire()
    with pytest.raises(LockBusy, match="holds"):
        RunLock(tmp_path).acquire()
    first.release()
    with RunLock(tmp_path) as again:
        assert again.held
    assert not (tmp_path / ".morphcurrent-gpu.lock").exists()


def test_stale_lock_is_taken_over(tmp_path):
    now = [1000.0]
    old = RunLock(tmp_path, clock=lambda: now[0]).acquire()
    now[0] += 31 * 60  # heartbeat older than 30 min: holder presumed crashed
    taker = RunLock(tmp_path, clock=lambda: now[0]).acquire()
    assert taker.held and taker.took_over["pid"] == old._payload()["pid"]
    taker.release()


def test_heartbeat_keeps_lock_fresh(tmp_path):
    now = [0.0]
    lock = RunLock(tmp_path, clock=lambda: now[0]).acquire()
    now[0] += 25 * 60
    lock.heartbeat()
    now[0] += 25 * 60  # 50 min since start but only 25 since heartbeat
    with pytest.raises(LockBusy):
        RunLock(tmp_path, clock=lambda: now[0]).acquire()


def test_budget_rules():
    b = Budget(max_jobs=2)
    assert b.allow("anchor", {"id": "a"}) and b.allow("anchor", {"id": "b"})
    assert not b.allow("anchor", {"id": "c"}) and b.blocked["task"] == "c"
    g = Budget(max_gpu_s=100, cost_of=lambda k, t: 60.0)
    assert g.allow("bridge", {"id": "x"}) and not g.allow("bridge", {"id": "y"})
    n = Budget(max_gpu_s=100, cost_of=lambda k, t: None)
    assert not n.allow("bridge", {"id": "z"}) and "NO DATA" in n.blocked["reason"]


def small_storyboard(root: Path) -> Path:
    data = yaml.safe_load((REPO / "configs/sequences/organic-machines.yaml").read_text(encoding="utf-8"))
    data["render"].update(width=256, height=256)
    path = root / "sb.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


@needs_ffmpeg
def test_budget_pauses_and_resumes_without_duplicates(image_repo):
    fake = FakeComfy()
    fake.real_video = True
    sb = small_storyboard(image_repo)
    kw = dict(runs_root=image_repo / "runs", repo_root=image_repo, profiles=PROFILES, poll_seconds=0,
              confirm_gpu=True)
    first = run_render(sb, fake.client, max_jobs=2, **kw)
    assert first["status"] == "paused_budget" and fake.prompt_posts == 2
    assert first["budget"]["blocked"]["task"] == "anchor:phoenix"
    assert not (image_repo / "runs" / ".morphcurrent-gpu.lock").exists()  # released
    second = run_render(sb, fake.client, max_jobs=2, **kw)  # 1 anchor + 1 bridge more
    assert second["status"] == "paused_budget" and fake.prompt_posts == 4
    third = run_render(sb, fake.client, **kw)  # no cap: finish
    assert third["status"] == "awaiting_review" and fake.prompt_posts == 5  # 3 anchors + 2 bridges, no duplicates


def test_second_gpu_render_refused_while_locked(image_repo):
    fake = FakeComfy()
    lock = RunLock(image_repo / "runs").acquire()
    try:
        with pytest.raises(LockBusy):
            run_render(small_storyboard(image_repo), fake.client, runs_root=image_repo / "runs",
                       repo_root=image_repo, profiles=PROFILES, poll_seconds=0, confirm_gpu=True)
        # validation-only runs never take the lock
        assert run_render(small_storyboard(image_repo), fake.client, runs_root=image_repo / "runs",
                          repo_root=image_repo, profiles=PROFILES, poll_seconds=0)["status"] == "validated"
    finally:
        lock.release()
    assert fake.prompt_posts == 0


def test_schedule_preview_and_cli(capsys):
    plan = compile_plan(load_storyboard(REPO / "configs/sequences/organic-machines.yaml"), repo_root=REPO)
    history = load_history(REPO / "configs/perf_history.json")
    preview = schedule_preview(plan, history, max_gpu_s=600)
    tasks = [r["task"] for r in preview["stages"]]
    assert tasks[:3] == ["anchor:orchid", "anchor:butterfly", "anchor:phoenix"]  # dependency order
    assert [r["fits_budget"] for r in preview["stages"]] == [True, True, True, False, False]
    assert cli.main(["schedule", str(REPO / "configs/sequences/organic-machines.yaml"), "--max-jobs", "4"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["fitting_stages"] == 4
