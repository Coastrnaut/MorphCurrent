"""F20: run comparison, source/licence audit, run backup/restore, acceptance matrix (offline)."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

import pytest

from fake_comfy import FakeComfy, make_png
from morph_studio import cli
from morph_studio.release import (ReleaseError, acceptance_matrix, audit_repo, backup_run, compare_runs,
                                  restore_run)
from morph_studio.workflow_adapter import graph_sha256

from conftest import REPO

needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
needs_git = pytest.mark.skipif(not shutil.which("git"), reason="git not installed")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_job(root: Path, name: str, kind: str, payload: bytes) -> str:
    d = root / name
    (d / "outputs").mkdir(parents=True)
    fname = "anchor_00001_.png" if kind == "anchor" else "bridge_00001_.mp4"
    (d / "outputs" / fname).write_bytes(payload)
    record = {"job_id": name * 4, "kind": f"{kind}_job", "state": "verified"}
    if kind == "anchor":
        record["image"] = {"local_path": f"outputs\\{fname}", "sha256": sha(payload)}
    else:
        record["outputs"] = [{"kind": "video", "local_path": f"outputs\\{fname}", "sha256": sha(payload)}]
    (d / "job.json").write_text(json.dumps(record), encoding="utf-8")
    return f"outputs\\runs\\{name}"


def make_run(root: Path, run: str, payloads: dict, plan_sha: str = "ba2d9dbe" + "0" * 56) -> Path:
    """payloads: task -> bytes (None = stage pending)."""
    stages, order = {}, []
    for i, (task, data) in enumerate(payloads.items()):
        order.append(task)
        kind = task.split(":")[0]
        if data is None:
            stages[task] = {"state": "pending"}
            continue
        job = f"{run[-4:]}{i:012d}"
        entry = {"state": "verified", "job_dir": make_job(root, job, kind, data)}
        entry["image_sha256" if kind == "anchor" else "video_sha256"] = sha(data)
        stages[task] = entry
    run_dir = root / run
    (run_dir / "final").mkdir(parents=True)
    movie = b"movie" + b"".join(d for d in payloads.values() if d)
    (run_dir / "final" / "sb_20261124-120000Z_ba2d9dbe.mp4").write_bytes(movie)
    order.append("final:movie")
    stages["final:movie"] = {"state": "verified", "frames": 129}
    manifest = {"schema": 1, "plan_sha256": plan_sha, "order": order, "stages": stages,
                "status": "complete", "storyboard": "sb.yaml",
                "final": {"output": f"outputs\\runs\\{run}\\final\\sb_20261124-120000Z_ba2d9dbe.mp4"}}
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (run_dir / "plan.json").write_text(json.dumps({"plan_sha256": plan_sha}), encoding="utf-8")
    (run_dir / "review.json").write_text(json.dumps({"bridge:a->b": {"decision": "approved"}}), encoding="utf-8")
    return run_dir


PAYLOADS = {"anchor:a": make_png(8, 8, (1, 2, 3)), "anchor:b": make_png(8, 8, (4, 5, 6)),
            "bridge:a->b": b"\x00video-ab" * 50}


# --- US1 compare ---------------------------------------------------------------------------------

def test_identical_runs_reproduce(tmp_path):
    a = make_run(tmp_path / "r1", "run-aaaaaaaaaaaaaaaa", PAYLOADS)
    b = make_run(tmp_path / "r2", "run-bbbbbbbbbbbbbbbb", PAYLOADS)
    report = compare_runs(a, b)
    assert report["verdict"] == "reproduced" and report["same_plan"]
    assert {s["status"] for s in report["stages"]} == {"identical"}
    assert [s["task"] for s in report["stages"]][-1] == "final:movie"


def test_different_missing_and_pending(tmp_path):
    a = make_run(tmp_path / "r1", "run-aaaaaaaaaaaaaaaa", PAYLOADS)
    changed = {**PAYLOADS, "bridge:a->b": b"\x01other" * 50}
    b = make_run(tmp_path / "r2", "run-bbbbbbbbbbbbbbbb", changed)
    report = compare_runs(a, b)
    status = {s["task"]: s["status"] for s in report["stages"]}
    assert status["bridge:a->b"] == "different" and status["anchor:a"] == "identical"
    assert report["verdict"] == "differs"
    # corrupt a file after the fact: re-hash detects it even though the manifest still matches
    job = next((tmp_path / "r2").glob("bbbb*000000"))
    (job / "outputs" / "anchor_00001_.png").write_bytes(b"corrupt")
    assert {s["task"]: s["status"] for s in compare_runs(a, b)["stages"]}["anchor:a"] == "different"
    pending = make_run(tmp_path / "r3", "run-cccccccccccccccc", {**PAYLOADS, "anchor:b": None})
    status = {s["task"]: s["status"] for s in compare_runs(a, pending)["stages"]}
    assert status["anchor:b"] == "not_verified"
    shutil.rmtree(next((tmp_path / "r1").glob("aaaa*000002")))  # bridge job of run A gone
    assert {s["task"]: s["status"] for s in compare_runs(a, pending)["stages"]}["bridge:a->b"] == "missing_a"


def test_different_plans_compare_common_stages(tmp_path):
    a = make_run(tmp_path / "r1", "run-aaaaaaaaaaaaaaaa", PAYLOADS)
    b = make_run(tmp_path / "r2", "run-bbbbbbbbbbbbbbbb", {"anchor:a": PAYLOADS["anchor:a"]}, plan_sha="1" * 64)
    report = compare_runs(a, b)
    assert not report["same_plan"] and report["verdict"] == "differs"
    assert {s["task"]: s["status"] for s in report["stages"]}["anchor:b"] == "missing_b"


@needs_ffmpeg
def test_frame_comparison_visually_equivalent(tmp_path):
    def clip(path: Path, level: int):
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"color=c=0x{level:02x}{level:02x}{level:02x}:s=64x64:d=1:r=16",
                        "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv444p", str(path)], check=True)
    tmp = tmp_path / "clips"
    tmp.mkdir()
    clip(tmp / "a.mp4", 100)
    clip(tmp / "b.mp4", 100)
    clip(tmp / "c.mp4", 160)
    base = {k: v for k, v in PAYLOADS.items() if k.startswith("anchor")}
    a = make_run(tmp_path / "r1", "run-aaaaaaaaaaaaaaaa", {**base, "bridge:a->b": (tmp / "a.mp4").read_bytes() + b""})
    b = make_run(tmp_path / "r2", "run-bbbbbbbbbbbbbbbb", {**base, "bridge:a->b": (tmp / "b.mp4").read_bytes() + b"\0"})
    c = make_run(tmp_path / "r3", "run-cccccccccccccccc", {**base, "bridge:a->b": (tmp / "c.mp4").read_bytes()})
    near = next(s for s in compare_runs(a, b, frames=True)["stages"] if s["task"] == "bridge:a->b")
    assert near["status"] == "different" and near["frames"]["visually_equivalent"]
    far = next(s for s in compare_runs(a, c, frames=True)["stages"] if s["task"] == "bridge:a->b")
    assert not far["frames"]["visually_equivalent"] and far["frames"]["max_mean_abs_diff"] > 30


def test_cli_run_compare_and_replay_refusals(tmp_path, capsys):
    a = make_run(tmp_path / "r1", "run-aaaaaaaaaaaaaaaa", PAYLOADS)
    b = make_run(tmp_path / "r2", "run-bbbbbbbbbbbbbbbb", PAYLOADS)
    assert cli.main(["run-compare", str(a), str(b)]) == 0
    assert json.loads(capsys.readouterr().out)["verdict"] == "reproduced"
    c = make_run(tmp_path / "r3", "run-cccccccccccccccc", {**PAYLOADS, "anchor:a": b"x"})
    assert cli.main(["run-compare", str(a), str(c)]) == 10
    capsys.readouterr()
    nonempty = tmp_path / "r1"
    assert cli.main(["replay", str(REPO / "configs/sequences/organic-machines.yaml"), "--reference", str(a),
                     "--runs-root", str(nonempty)]) == 2
    assert "empty" in capsys.readouterr().err


def test_replay_without_consent_only_validates(image_repo, tmp_path):
    from morph_studio.release import replay
    import yaml
    data = yaml.safe_load((REPO / "configs/sequences/organic-machines.yaml").read_text(encoding="utf-8"))
    data["render"].update(width=256, height=256)
    sb = image_repo / "sb.yaml"
    sb.write_text(yaml.safe_dump(data), encoding="utf-8")
    fake = FakeComfy()
    ref = make_run(tmp_path / "ref", "run-aaaaaaaaaaaaaaaa", PAYLOADS)
    result = replay(sb, ref, image_repo / "fresh", fake.client, repo_root=image_repo,
                    profiles={"text_to_image": "configs/profiles/test_t2i.binding.json",
                              "reference_edit": "configs/profiles/test_edit.binding.json"})
    assert result["render"]["status"] == "validated" and "comparison" not in result
    assert fake.prompt_posts == 0


# --- US2 audit -----------------------------------------------------------------------------------

def test_current_repo_audits_clean():
    start = time.perf_counter()
    report = audit_repo(REPO)
    assert time.perf_counter() - start < 5
    assert report["errors"] == [], report["errors"]
    assert len(report["models"]) >= 10
    assert any(m["file"].startswith("wan2.2_i2v_high_noise") for m in report["models"])
    assert any(c["check"].startswith("profile") and c["status"] == "ok" for c in report["checks"])


@needs_git
def test_audit_detects_seeded_defects(tmp_path):
    root = tmp_path / "repo"
    (root / "workflows").mkdir(parents=True)
    (root / "configs" / "profiles").mkdir(parents=True)
    graph = {"1": {"class_type": "SaveImage", "inputs": {"filename_prefix": "x"}}}
    (root / "workflows" / "w.json").write_text(json.dumps(graph), encoding="utf-8")
    (root / "configs" / "profiles" / "p.binding.json").write_text(
        json.dumps({"workflow": "workflows/w.json", "workflow_sha256": graph_sha256(graph)}), encoding="utf-8")
    graph["1"]["inputs"]["filename_prefix"] = "tampered"
    (root / "workflows" / "w.json").write_text(json.dumps(graph), encoding="utf-8")
    files = {"assets/pic.png": b"png", "assets/song.opus": b"opus", "model.safetensors": b"w", ".env": b"K=V",
             "outputs/a.mp4": b"v", "runs/run-1234567890abcdef/manifest.json": b"{}"}
    for rel, data in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(data)
    (root / "assets" / "song.json").write_text(json.dumps({"license": "CC0", "source": {"url": "local"}}), encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "-A", "-f"], check=True)
    errors = " | ".join(audit_repo(root)["errors"])
    for needle in ("p.binding.json", "assets/pic.png", "model.safetensors", ".env", "outputs/a.mp4",
                   "run-1234567890abcdef/manifest.json"):
        assert needle in errors, (needle, errors)
    assert "assets/song.opus" not in errors  # has licence provenance


def test_cli_audit_exit_code(capsys):
    assert cli.main(["audit", "--repo-root", str(REPO)]) == 0
    assert json.loads(capsys.readouterr().out)["errors"] == []


# --- US3 backup/restore --------------------------------------------------------------------------

def test_backup_restore_round_trip(tmp_path):
    run = make_run(tmp_path / "runs", "run-aaaaaaaaaaaaaaaa", PAYLOADS)
    archive = tmp_path / "run.zip"
    info = backup_run(run, archive)
    assert info["files"] >= 7 and archive.is_file() and info["missing_jobs"] == []
    with pytest.raises(ReleaseError, match="exists"):
        backup_run(run, archive)
    restored = restore_run(archive, tmp_path / "restored")
    assert compare_runs(run, restored)["verdict"] == "reproduced"
    assert (restored / "review.json").read_text(encoding="utf-8") == (run / "review.json").read_text(encoding="utf-8")
    with pytest.raises(ReleaseError, match="exists"):
        restore_run(archive, tmp_path / "restored")


def test_restore_rejects_tampering_and_unsafe_paths(tmp_path):
    run = make_run(tmp_path / "runs", "run-aaaaaaaaaaaaaaaa", PAYLOADS)
    archive = tmp_path / "run.zip"
    backup_run(run, archive)
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(archive) as src, zipfile.ZipFile(tampered, "w") as dst:
        for item in src.infolist():
            data = src.read(item)
            if item.filename.endswith("bridge_00001_.mp4"):
                data = b"tampered"
            dst.writestr(item, data)
    with pytest.raises(ReleaseError, match="bridge_00001_.mp4"):
        restore_run(tampered, tmp_path / "dest")
    assert not (tmp_path / "dest").exists() or not any((tmp_path / "dest").iterdir())
    evil = tmp_path / "evil.zip"
    with zipfile.ZipFile(evil, "w") as z:
        z.writestr("../escape.txt", b"x")
        z.writestr("SHA256SUMS.json", json.dumps({"../escape.txt": sha(b"x")}))
    with pytest.raises(ReleaseError, match="unsafe"):
        restore_run(evil, tmp_path / "dest2")
    assert not (tmp_path / "escape.txt").exists()


def test_backup_missing_job(tmp_path, capsys):
    run = make_run(tmp_path / "runs", "run-aaaaaaaaaaaaaaaa", PAYLOADS)
    shutil.rmtree(next((tmp_path / "runs").glob("aaaa*000001")))
    with pytest.raises(ReleaseError, match="missing"):
        backup_run(run, tmp_path / "a.zip")
    info = backup_run(run, tmp_path / "b.zip", allow_missing_jobs=True)
    assert len(info["missing_jobs"]) == 1
    assert cli.main(["run-backup", str(run), "--out", str(tmp_path / "c.zip")]) == 2
    assert cli.main(["run-backup", str(run), "--out", str(tmp_path / "d.zip"), "--allow-missing-jobs"]) == 0
    assert cli.main(["run-restore", str(tmp_path / "d.zip"), "--runs-root", str(tmp_path / "e")]) == 0


# --- US4 acceptance matrix -----------------------------------------------------------------------

def test_acceptance_matrix(capsys):
    ledger = REPO / "docs" / "SPECKIT_FEATURE_LEDGER.md"
    m = acceptance_matrix(ledger)
    ids = [r["feature"] for r in m["rows"]]
    assert ids == [f"F{i:02d}" for i in range(1, 21)]
    assert m["release_ready"] is False and m["unresolved"] >= 1
    assert len(acceptance_matrix(ledger, all_features=True)["rows"]) == 40
    assert cli.main(["acceptance"]) == 0
    assert len(json.loads(capsys.readouterr().out)["rows"]) == 20


# --- Polish --------------------------------------------------------------------------------------

def test_release_module_has_no_tagging_or_comfy_client():
    source = (REPO / "src" / "morph_studio" / "release.py").read_text(encoding="utf-8")
    for forbidden in ("comfy_client", "\"tag\"", "'tag'", "\"push\"", "httpx"):
        assert forbidden not in source


def test_restore_rolls_back_on_midway_failure(tmp_path, monkeypatch):
    import morph_studio.release as rel
    run = make_run(tmp_path / "runs", "run-aaaaaaaaaaaaaaaa", PAYLOADS)
    archive = tmp_path / "run.zip"
    backup_run(run, archive)
    real = rel.os.replace
    calls = []

    def flaky(src, dst):
        calls.append(dst)
        if len(calls) == 2:
            raise OSError("disk full")
        return real(src, dst)
    monkeypatch.setattr(rel.os, "replace", flaky)
    with pytest.raises(OSError):
        restore_run(archive, tmp_path / "dest")
    assert not any((tmp_path / "dest").iterdir())  # first moved folder rolled back
    assert not list(tmp_path.glob(".dest.restore-*"))  # staging removed


@needs_ffmpeg
def test_replay_with_consent_reproduces(image_repo):
    import yaml
    from morph_studio.release import replay
    from morph_studio.render import run_render
    data = yaml.safe_load((REPO / "configs/sequences/organic-machines.yaml").read_text(encoding="utf-8"))
    data["render"].update(width=256, height=256)
    sb = image_repo / "sb.yaml"
    sb.write_text(yaml.safe_dump(data), encoding="utf-8")
    profiles = {"text_to_image": "configs/profiles/test_t2i.binding.json",
                "reference_edit": "configs/profiles/test_edit.binding.json"}
    fake = FakeComfy()
    fake.real_video = True
    kw = dict(repo_root=image_repo, profiles=profiles, poll_seconds=0)
    first = run_render(sb, fake.client, runs_root=image_repo / "runs", confirm_gpu=True, **kw)
    before = fake.prompt_posts
    out = replay(sb, first["run_dir"], image_repo / "fresh", fake.client, confirm_gpu=True, **kw)
    assert fake.prompt_posts - before == 5  # fresh root: every stage recomputed
    statuses = {s["task"]: s["status"] for s in out["comparison"]["stages"]}
    assert all(v == "identical" for k, v in statuses.items() if k != "final:movie")
    assert statuses["final:movie"] == "not_verified"  # awaiting review: not joined yet
    assert out["comparison"]["verdict"] == "incomplete"


def test_validation_replay_leaves_fresh_root_empty(image_repo, tmp_path):
    import yaml
    from morph_studio.release import replay
    data = yaml.safe_load((REPO / "configs/sequences/organic-machines.yaml").read_text(encoding="utf-8"))
    sb = image_repo / "sb.yaml"
    sb.write_text(yaml.safe_dump(data), encoding="utf-8")
    fresh = image_repo / "fresh"
    out = replay(sb, tmp_path, fresh, FakeComfy().client, repo_root=image_repo,
                 profiles={"text_to_image": "configs/profiles/test_t2i.binding.json",
                           "reference_edit": "configs/profiles/test_edit.binding.json"})
    assert out["render"]["status"] == "validated" and out["render"]["gpu_jobs"] == {"anchors": 3, "bridges": 2}
    assert not fresh.exists() or not any(fresh.iterdir())
