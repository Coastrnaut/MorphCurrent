"""F10 one-command render, offline E2E with a fake ComfyUI producing real FFmpeg clips."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

from fake_comfy import FakeComfy
from morph_studio import cli
from morph_studio.qa import record_review
from morph_studio.render import dry_run, render_status, run_render

from conftest import REPO

PROFILES = {"text_to_image": "configs/profiles/test_t2i.binding.json",
            "reference_edit": "configs/profiles/test_edit.binding.json"}
needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                                  reason="ffmpeg/ffprobe not installed")


def small_storyboard(image_repo: Path) -> Path:
    data = yaml.safe_load((REPO / "configs/sequences/organic-machines.yaml").read_text(encoding="utf-8"))
    data["render"].update(width=256, height=256)  # keep synthetic clips small
    path = image_repo / "sb.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def kw(image_repo: Path) -> dict:
    return dict(runs_root=image_repo / "runs", repo_root=image_repo, profiles=PROFILES, poll_seconds=0)


def test_dry_run_is_offline_and_reports_blocked(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "ComfyClient", lambda *a, **k: pytest.fail("network used"))
    missing = {"text_to_image": "configs/profiles/absent_t2i.binding.json", "reference_edit": "configs/profiles/absent_edit.binding.json"}
    report = dry_run(REPO / "configs/sequences/organic-machines.yaml", missing, repo_root=REPO)
    assert report["status"] == "blocked" and report["gpu_jobs"] == {"anchors": 3, "bridges": 2}
    monkeypatch.chdir(REPO)
    assert cli.main(["render", "configs/sequences/organic-machines.yaml", "--dry-run",
                     "--t2i-profile", missing["text_to_image"], "--runs-root", str(tmp_path)]) == 6
    assert cli.main(["render", "configs/sequences/organic-machines.yaml", "--dry-run",
                     "--runs-root", str(tmp_path)]) == 0  # real profiles present since F02
    assert list(tmp_path.iterdir()) == []


def test_missing_profiles_block_before_any_request(image_repo):
    fake = FakeComfy()
    result = run_render(small_storyboard(image_repo), fake.client, runs_root=image_repo / "runs",
                        repo_root=image_repo, confirm_gpu=True)
    assert result["status"] == "blocked" and fake.calls == []
    assert not (image_repo / "runs").exists()


def test_without_consent_validates_only(image_repo):
    fake = FakeComfy()
    result = run_render(small_storyboard(image_repo), fake.client, **kw(image_repo))
    assert result["status"] == "validated" and fake.prompt_posts == 0


@needs_ffmpeg
def test_full_offline_render_review_gate_join_and_resume(image_repo):
    fake = FakeComfy()
    fake.real_video = True
    sb = small_storyboard(image_repo)
    first = run_render(sb, fake.client, confirm_gpu=True, **kw(image_repo))
    assert first["status"] == "awaiting_review", first
    assert fake.prompt_posts == 5
    run_dir = Path(first["run_dir"])
    status = render_status(run_dir)
    assert status["stages"]["bridge:orchid->butterfly"]["state"] == "verified"
    b_sha = status["stages"]["anchor:butterfly"]["image_sha256"]
    for task in first["pending"]:
        record_review(run_dir / "review.json", task, "approved")
    done = run_render(sb, fake.client, confirm_gpu=True, **kw(image_repo))
    assert done["status"] == "complete", done
    assert fake.prompt_posts == 5  # resume: no repeat inference
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    final = manifest["final"]
    assert final["frames"] == 129 and final["crossfade"] is False and final["approval"] == "human"
    assert all(s["match"] for s in final["seams"]) and final["measured"]["frame_count"] == 129
    assert manifest["stages"]["anchor:butterfly"]["image_sha256"] == b_sha
    assert (run_dir / "anchors_contact_sheet.png").exists()
    again = run_render(sb, fake.client, confirm_gpu=True, **kw(image_repo))
    assert again["status"] == "complete" and fake.prompt_posts == 5


@needs_ffmpeg
def test_rejected_bridge_requests_rerender(image_repo):
    fake = FakeComfy()
    fake.real_video = True
    sb = small_storyboard(image_repo)
    first = run_render(sb, fake.client, confirm_gpu=True, **kw(image_repo))
    record_review(Path(first["run_dir"]) / "review.json", "bridge:butterfly->phoenix", "rejected", "flare")
    result = run_render(sb, fake.client, confirm_gpu=True, **kw(image_repo))
    assert result["status"] == "rerender_needed" and result["rejected"] == ["bridge:butterfly->phoenix"]


def test_cli_status_is_read_only(image_repo, capsys):
    fake = FakeComfy()
    result = run_render(small_storyboard(image_repo), fake.client, **kw(image_repo))
    assert cli.main(["render", "--status", result["run_dir"]]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "validated"
