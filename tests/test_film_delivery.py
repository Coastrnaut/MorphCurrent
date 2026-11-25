"""F40: assembly from approved versions, delivery, provenance report and the F31-F40 gate matrix."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from morph_studio import cli
from morph_studio import film_delivery as fd
from morph_studio.media import probe_video

from conftest import REPO

FILM = REPO / "configs/sequences/engineering-film.yaml"
LEDGER = REPO / "docs/SPECKIT_FEATURE_LEDGER.md"
needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="ffmpeg missing")
IDS = ["a", "b", "c", "d"]
BRIDGES = [f"bridge:{IDS[i]}->{IDS[i + 1]}" for i in range(3)]


def storyboard(tmp_path: Path) -> Path:
    anchors = [{"id": k, "prompt": f"subject {k}", "chapter": "one"} for k in IDS]
    for i in range(1, 4):
        anchors[i].update(generation="reference_edit", reference=IDS[i - 1])
    sb = {"schema_version": 1, "name": "mini-film",
          "render": {"anchor_profile": "anchor_t2i", "bridge_profile": "wan22_flf2v", "master_seed": 3},
          "style": {"description": "x"}, "anchors": anchors,
          "transitions": [{"from": IDS[i], "to": IDS[i + 1], "frames": 33, "prompt": "m"} for i in range(3)]}
    path = tmp_path / "mini-film.yaml"
    path.write_text(yaml.safe_dump(sb, sort_keys=False), encoding="utf-8")
    return path


def media(path: Path, color: str, still: bool = False) -> None:
    args = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c={color}:size=96x64:rate=16"]
    args += (["-frames:v", "1", str(path)] if still else ["-frames:v", "33", "-pix_fmt", "yuv420p", str(path)])
    subprocess.run(args, check=True)


def build_runs(tmp_path: Path, colors: dict | None = None, broken_stills: bool = False, tag: str = "v1",
               created: str = "2026-11-24T10:00:00+00:00", name: str = "run-00000000000000a1") -> Path:
    root = tmp_path / "runs"
    root.mkdir(exist_ok=True)
    colors = colors or {}
    stages = {}
    for tid in [f"anchor:{k}" for k in IDS] + BRIDGES:
        job = root / hashlib.sha256(f"{tid}:{tag}".encode()).hexdigest()[:16]
        job.mkdir()
        if tid.startswith("bridge"):
            media(job / "out.mp4", colors.get(tid, "gray"))
            rec = {"outputs": [{"kind": "video", "local_path": "out.mp4"}], "timings": {"execution_seconds": 300.0}}
            digest = {"video_sha256": hashlib.sha256((job / "out.mp4").read_bytes()).hexdigest() + tag[:0]}
            extra = {"qa": "no_flags", "qa_flags": []}
        else:
            if broken_stills:
                (job / "a.png").write_bytes(b"not an image")
            else:
                media(job / "a.png", "gray", still=True)
            rec = {"image": {"local_path": "a.png"}, "timings": {"execution_seconds": 20.0}}
            digest = {"image_sha256": hashlib.sha256((job / "a.png").read_bytes() + tag.encode()).hexdigest()}
            extra = {}
        (job / "job.json").write_text(json.dumps(rec), encoding="utf-8")
        stages[tid] = {"state": "verified", "job_dir": f"outputs\\runs\\{job.name}",
                       "job_id": hashlib.sha256(f"job:{tid}:{tag}".encode()).hexdigest(), **digest, **extra}
    run = root / name
    run.mkdir()
    (run / "manifest.json").write_text(json.dumps({"created_at": created, "stages": stages,
                                                   "order": list(stages)}), encoding="utf-8")
    return root


def approve(tmp_path, sb, root, stages=BRIDGES, decision="approved"):
    from morph_studio import batch_review as br
    st = br.film_state(sb, root, tmp_path / "log.jsonl", repo_root=REPO)
    for s in stages:
        br.record(st, s, decision)
    return st


# --- foundational ---------------------------------------------------------------------------------

def test_choose_reasons(tmp_path):
    from morph_studio import batch_review as br
    sb = storyboard(tmp_path)
    st = br.film_state(sb, tmp_path / "none", tmp_path / "log.jsonl", repo_root=REPO)
    pick = fd.choose(st)
    assert [b["reason"] for b in pick["blockers"]] == ["missing"] * 3
    for s, (dec, stale) in zip(st["stages"][1::2], [("approved", False), ("rejected", False), ("approved", True)]):
        s["versions"] = [{"sha256": "x", "job_id": "j", "run": "r", "media": None}]
        s["current"] = "x" if not stale else "y"
        s["decision"] = {"decision": dec, "version": "x"}
        s["stale"] = stale
    pick = fd.choose(st)
    assert [(b["stage"], b["reason"]) for b in pick["blockers"]] == [(BRIDGES[1], "rejected"), (BRIDGES[2], "stale")]
    prev = fd.choose(st, preview=True)
    assert not prev["blockers"] and [u["reason"] for u in prev["unapproved"]] == ["rejected", "stale"]
    st["stages"][1]["decision"] = None
    assert fd.choose(st)["blockers"][0]["reason"] == "unreviewed"


def test_real_film_blocked(tmp_path):
    with pytest.raises(fd.Blocked) as exc:
        fd.assemble(FILM, tmp_path / "none", tmp_path / "log.jsonl", tmp_path / "f.mp4", repo_root=REPO)
    assert len(exc.value.blockers) == 95 and {b["reason"] for b in exc.value.blockers} == {"missing"}


# --- US1 ------------------------------------------------------------------------------------------

@needs_ffmpeg
def test_assemble_approved(tmp_path):
    sb = storyboard(tmp_path)
    root = build_runs(tmp_path)
    with pytest.raises(fd.Blocked, match="unreviewed"):
        fd.assemble(sb, root, tmp_path / "log.jsonl", tmp_path / "m.mp4", repo_root=REPO)
    approve(tmp_path, sb, root)
    rec = fd.assemble(sb, root, tmp_path / "log.jsonl", tmp_path / "film" / "m.mp4", repo_root=REPO)
    assert rec["frames"] == rec["planned_frames"] == 97 and not rec["preview"]
    assert abs(rec["duration_s"] - 97 / 16) <= 1 / 16 and rec["seam_mode"] == "anchor+boundary"
    assert [c["stage"] for c in rec["chosen"]] == BRIDGES and all(c["decision"] == "approved" for c in rec["chosen"])
    assert probe_video(tmp_path / "film" / "m.mp4")["frame_count"] == 97
    assert Path(rec["record"]).is_file()
    with pytest.raises(FileExistsError):
        fd.assemble(sb, root, tmp_path / "log.jsonl", tmp_path / "film" / "m.mp4", repo_root=REPO)
    with pytest.raises(fd.ReviewError, match="licensed"):
        fd.assemble(sb, root, tmp_path / "log.jsonl", tmp_path / "x.mp4", audio=tmp_path / "a.wav", repo_root=REPO)
    tone = tmp_path / "tone.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=9", str(tone)],
                   check=True)
    rec2 = fd.assemble(sb, root, tmp_path / "log.jsonl", tmp_path / "film" / "audio.mp4", audio=tone,
                       audio_licensed=True, repo_root=REPO)
    assert rec2["audio_licensed"] and rec2["frames"] == 97


@needs_ffmpeg
def test_assemble_preview_and_stale(tmp_path):
    sb = storyboard(tmp_path)
    root = build_runs(tmp_path)
    approve(tmp_path, sb, root, BRIDGES[:2])
    rec = fd.assemble(sb, root, tmp_path / "log.jsonl", tmp_path / "p.mp4", preview=True, repo_root=REPO)
    assert rec["preview"] and Path(rec["master"]).name == "p_PREVIEW.mp4"
    assert rec["unapproved"] == [{"stage": BRIDGES[2], "reason": "unreviewed"}]
    approve(tmp_path, sb, root, BRIDGES[2:])
    build_runs(tmp_path, tag="v2", created="2026-11-24T11:00:00+00:00", name="run-00000000000000b2",
               colors={BRIDGES[1]: "white"})
    with pytest.raises(fd.Blocked, match="stale"):
        fd.assemble(sb, root, tmp_path / "log.jsonl", tmp_path / "s.mp4", repo_root=REPO)


@needs_ffmpeg
def test_assemble_seam_mismatch_and_boundary_mode(tmp_path):
    from morph_studio.stitcher import SeamError
    sb = storyboard(tmp_path)
    root = build_runs(tmp_path, colors={BRIDGES[1]: "white"})
    approve(tmp_path, sb, root)
    with pytest.raises(SeamError):
        fd.assemble(sb, root, tmp_path / "log.jsonl", tmp_path / "mm.mp4", repo_root=REPO)
    assert not (tmp_path / "mm.mp4").exists()
    t2 = tmp_path / "b"
    t2.mkdir()
    sb2 = storyboard(t2)
    root2 = build_runs(t2, broken_stills=True)
    approve(t2, sb2, root2)
    rec = fd.assemble(sb2, root2, t2 / "log.jsonl", t2 / "m.mp4", repo_root=REPO)
    assert rec["seam_mode"] == "boundary"


# --- US2 ------------------------------------------------------------------------------------------

@needs_ffmpeg
def test_deliver_master(tmp_path):
    sb = storyboard(tmp_path)
    root = build_runs(tmp_path)
    approve(tmp_path, sb, root)
    rec = fd.assemble(sb, root, tmp_path / "log.jsonl", tmp_path / "m.mp4", repo_root=REPO)
    out = fd.deliver_master(rec["master"], tmp_path / "d", ["video-only-1080p", "licensed-audio-1080p"])
    assert len(out["results"]) == 1 and out["errors"][0]["preset"] == "licensed-audio-1080p"
    assert Path(out["record"]).is_file() and not out["preview"]
    with pytest.raises(fd.ReviewError):
        fd.deliver_master(tmp_path / "none.mp4")


# --- US3 ------------------------------------------------------------------------------------------

@needs_ffmpeg
def test_provenance(tmp_path):
    sb = storyboard(tmp_path)
    root = build_runs(tmp_path)
    approve(tmp_path, sb, root)
    rec = fd.assemble(sb, root, tmp_path / "log.jsonl", tmp_path / "m.mp4", repo_root=REPO)
    rep = fd.provenance(rec["record"], repo_root=REPO)
    assert len(rep["stages"]) == 7 and all(s["seed"] is not None and s["run"] for s in rep["stages"])
    assert rep["gpu"]["measured_s"] == 3 * 300.0 + 4 * 20.0 and rep["gpu"]["jobs_timed"] == 7
    assert rep["gpu"]["estimated_s"] > 0 and rep["gpu"]["ratio"] is not None
    assert {w["profile"] for w in rep["workflows"]} == {"anchor_t2i", "anchor_edit", "wan22_flf2v"}
    assert all(w["matches"] for w in rep["workflows"]) and rep["models"]
    assert any(m.startswith("licence of") for m in rep["missing"])  # catalogue licences still NOT RECORDED
    assert rep["approvals"]["concept_bank"]["status"] == "approved"
    assert rep["approvals"]["review_decisions"]["approved_bridges"] == 3 and not rep["complete"]
    prev = fd.assemble(sb, root, tmp_path / "log.jsonl", tmp_path / "p.mp4", preview=True, repo_root=REPO)
    assert "preview master (not acceptance evidence)" in fd.provenance(prev["record"], repo_root=REPO)["missing"]


# --- US4 ------------------------------------------------------------------------------------------

def test_gates(tmp_path):
    g = fd.gates(LEDGER, REPO / "configs/film/accepted-blockers.yaml")
    assert [r["feature"] for r in g["rows"]] == [f"F{i}" for i in range(31, 41)] and g["total"] == 10
    open_ = [r for r in g["rows"] if not r["resolved"]]
    assert open_ and not g["ok"]
    acc = tmp_path / "acc.yaml"
    acc.write_text(yaml.safe_dump({"version": 1, "accepted": [
        {"feature": open_[0]["feature"], "blocker": "x", "owner": "owner", "date": "2026-11-24"}]}), encoding="utf-8")
    row = next(r for r in fd.gates(LEDGER, acc)["rows"] if r["feature"] == open_[0]["feature"])
    assert row["resolved"] and row["accepted"]["owner"] == "owner"
    for bad in [{"feature": "F12", "blocker": "x", "owner": "o", "date": "2026-11-24"},
                {"feature": "F33", "blocker": "x", "owner": " ", "date": "2026-11-24"},
                {"feature": "F33", "blocker": "x", "owner": "o", "date": "24/11/2026"}]:
        acc.write_text(yaml.safe_dump({"version": 1, "accepted": [bad]}), encoding="utf-8")
        with pytest.raises(fd.ReviewError):
            fd.gates(LEDGER, acc)


# --- CLI ------------------------------------------------------------------------------------------

def test_cli_gates_and_blocked(tmp_path, capsys):
    assert cli.main(["film-gates"]) == 1
    text = capsys.readouterr().out
    text.encode("ascii")
    assert text.count("\n") >= 11 and "F38" in text
    assert cli.main(["film-gates", "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["total"] == 10
    assert cli.main(["film-assemble", "--runs-root", str(tmp_path / "none"), "--log", str(tmp_path / "l.jsonl"),
                     "--out", str(tmp_path / "f.mp4")]) == 2
    err = capsys.readouterr().err
    assert "95 stage(s) block assembly" in err


@needs_ffmpeg
def test_cli_assemble_deliver_provenance(tmp_path, capsys):
    sb = storyboard(tmp_path)
    root = build_runs(tmp_path)
    approve(tmp_path, sb, root)
    common = ["--storyboard", str(sb), "--runs-root", str(root), "--log", str(tmp_path / "log.jsonl")]
    assert cli.main(["film-assemble", *common, "--out", str(tmp_path / "m.mp4")]) == 0
    rec = json.loads(capsys.readouterr().out)
    assert rec["frames"] == 97
    assert cli.main(["film-deliver", rec["master"], "--preset", "video-only-1080p", "--out-dir", str(tmp_path / "d")]) == 0
    capsys.readouterr()
    assert cli.main(["film-provenance", rec["record"], "--out", str(tmp_path / "prov.json")]) == 1  # licences missing
    assert json.loads((tmp_path / "prov.json").read_text(encoding="utf-8"))["gpu"]["jobs_timed"] == 7


@needs_ffmpeg
def test_preview_delivery_and_cli_failure(tmp_path, capsys):
    sb = storyboard(tmp_path)
    root = build_runs(tmp_path)
    rec = fd.assemble(sb, root, tmp_path / "log.jsonl", tmp_path / "p.mp4", preview=True, repo_root=REPO)
    out = fd.deliver_master(rec["master"], tmp_path / "d", ["video-only-1080p"])
    assert out["preview"] and json.loads(Path(out["record"]).read_text(encoding="utf-8"))["preview"]
    assert cli.main(["film-deliver", rec["master"], "--preset", "licensed-audio-1080p",
                     "--out-dir", str(tmp_path / "d2")]) == 1
