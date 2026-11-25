"""F35: lineage depth, drift curve, explicit re-anchor proposals and shared-anchor byte identity."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from morph_studio import cli
from morph_studio import lineage as ln
from morph_studio.dag import compile_plan
from morph_studio.schema import Storyboard, load_storyboard

from conftest import REPO

FILM = REPO / "configs/sequences/engineering-film.yaml"
CONFIG = REPO / "configs/film/lineage.yaml"
needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


def chain_storyboard() -> dict:
    """a(t2i) -> b -> c -> d (edits) | e independent(ref d) -> f (edit of e)."""
    ids = list("abcdef")
    anchors = [{"id": "a", "prompt": "a"}]
    for prev, k in zip("abc", "bcd"):
        anchors.append({"id": k, "prompt": k, "generation": "reference_edit", "reference": prev})
    anchors.append({"id": "e", "prompt": "e", "generation": "independent_t2i", "reference": "d"})
    anchors.append({"id": "f", "prompt": "f", "generation": "reference_edit", "reference": "e"})
    return {"schema_version": 1, "name": "chain", "render": {"anchor_profile": "anchor_t2i", "bridge_profile": "wan22_flf2v"},
            "style": {"description": "x"}, "anchors": anchors,
            "transitions": [{"from": ids[i], "to": ids[i + 1], "frames": 33, "prompt": "m"} for i in range(5)]}


def plan_of(data: dict) -> dict:
    return compile_plan(Storyboard.model_validate(data), repo_root=REPO)


# --- US1 ------------------------------------------------------------------------------------------

def test_lineage_synthetic():
    rep = ln.lineage(plan_of(chain_storyboard()), limit=2)
    e = {x["anchor"]: x for x in rep["entries"]}
    assert [e[k]["depth"] for k in "abcdef"] == [0, 1, 2, 3, 0, 1]
    assert e["d"]["root"] == "a" and e["d"]["chain"] == ["a", "b", "c", "d"]
    assert e["f"]["root"] == "e"
    assert rep["max_depth"] == 3 and rep["over_limit"] == ["d"]


def test_lineage_film():
    plan = compile_plan(load_storyboard(FILM), repo_root=REPO, storyboard_bytes=FILM.read_bytes())
    rep = ln.lineage(plan, limit=12)
    # depths change as anchor fixes restart edit chains (configs/film/anchor-fixes.yaml); check the structure
    assert list(rep["per_act_max"]) == ["spark", "power", "signal", "logic", "scale"]
    assert rep["max_depth"] == max(rep["per_act_max"].values())
    assert sorted(rep["over_limit"]) == sorted(e["anchor"] for e in rep["entries"] if e["depth"] > 12)
    data = yaml.safe_load(FILM.read_text(encoding="utf-8"))
    fresh = {a["id"] for a in data["anchors"] if a.get("generation") != "reference_edit"}
    assert all(e["depth"] == 0 for e in rep["entries"] if e["anchor"] in fresh)


# --- US2 ------------------------------------------------------------------------------------------

def img(path: Path, colour: str, blur: float = 0) -> Path:
    vf = f"drawbox=x=356:y=180:w=120:h=120:color={colour}:t=fill" + (f",gblur=sigma={blur}" if blur else "")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x080808:size=832x480",
                    "-vf", vf, "-frames:v", "1", str(path)], check=True)
    return path


def fake_run(tmp_path, images: dict[str, Path], bridges: list[tuple[str, str]] | None = None) -> Path:
    runs = tmp_path / "runs"
    run = runs / "run-x"
    run.mkdir(parents=True)
    stages = {}
    for i, (k, src) in enumerate(images.items()):
        job = runs / f"job{i}"
        (job / "outputs").mkdir(parents=True)
        shutil.copy(src, job / "outputs" / "anchor.png")
        (job / "job.json").write_text(json.dumps({"image": {"local_path": "outputs/anchor.png"}}), encoding="utf-8")
        stages[f"anchor:{k}"] = {"state": "verified", "job_dir": f"outputs/runs/{job.name}",
                                 "image_sha256": hashlib.sha256(src.read_bytes()).hexdigest()}
    for j, (x, y) in enumerate(bridges or []):
        job = runs / f"bjob{j}"
        job.mkdir()
        rec = {"anchors": {"start_image": {"sha256": stages[f"anchor:{x}"]["image_sha256"]},
                           "end_image": {"sha256": stages[f"anchor:{y}"]["image_sha256"]}}}
        (job / "job.json").write_text(json.dumps(rec), encoding="utf-8")
        stages[f"bridge:{x}->{y}"] = {"state": "verified", "job_dir": f"outputs/runs/{job.name}"}
    (run / "manifest.json").write_text(json.dumps({"order": list(stages), "stages": stages}), encoding="utf-8")
    return run


@needs_ffmpeg
def test_drift_curve_flags(tmp_path):
    data = chain_storyboard()
    path = tmp_path / "chain.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    colours = {"a": ("0xC87830", 0), "b": ("0xC07030", 0), "c": ("0x6090E0", 0), "d": ("0xC87830", 6)}
    images = {k: img(tmp_path / f"{k}.png", c, b) for k, (c, b) in colours.items()}
    run = fake_run(tmp_path, images)
    curve = ln.drift_curve(path, run, ln.load_config(CONFIG))
    p = {x["anchor"]: x for x in curve["points"]}
    assert p["a"]["colour_distance"] == 0 and p["a"]["sharpness_ratio"] == 1.0 and not p["a"]["flags"]
    assert not p["b"]["flags"]
    assert "colour" in p["c"]["flags"]
    assert "sharpness" in p["d"]["flags"]
    assert set(curve["missing"]) == {"e", "f"} and curve["ok"] is False


@needs_ffmpeg
def test_drift_unreliable_mask(tmp_path):
    data = chain_storyboard()
    path = tmp_path / "chain.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    full = tmp_path / "full.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0xE0E0E0:size=832x480",
                    "-frames:v", "1", str(full)], check=True)
    run = fake_run(tmp_path, {"a": img(tmp_path / "a.png", "0xC87830"), "b": full})
    p = {x["anchor"]: x for x in ln.drift_curve(path, run, ln.load_config(CONFIG))["points"]}
    assert p["b"]["flags"] == ["unreliable"] and "colour_distance" not in p["b"]


# --- US3 ------------------------------------------------------------------------------------------

def test_proposals_film(tmp_path):
    plan = compile_plan(load_storyboard(FILM), repo_root=REPO, storyboard_bytes=FILM.read_bytes())
    rep = ln.propose(plan, limit=12)
    sb = load_storyboard(FILM)
    first = {a.id for i, a in enumerate(sb.anchors) if i == 0 or a.chapter != sb.anchors[i - 1].chapter}
    chosen = [p["anchor"] for p in rep["proposals"]]
    assert chosen and not set(chosen) & first
    assert rep["max_depth_after"] <= 12
    assert all(p["reasons"] == ["depth"] and p["invalidated_anchors"][0] == p["anchor"] for p in rep["proposals"])
    before = FILM.read_bytes()
    out = tmp_path / "film.reanchored.yaml"
    ln.apply_proposals(FILM, chosen, out)
    assert FILM.read_bytes() == before
    new = load_storyboard(out)
    by_id = {a.id: a for a in new.anchors}
    ids = [a.id for a in new.anchors]
    for c in chosen:
        assert by_id[c].generation == "independent_t2i" and by_id[c].reference == ids[ids.index(c) - 1]
    newplan = compile_plan(new, repo_root=REPO)
    assert ln.lineage(newplan, limit=12)["max_depth"] <= 12
    with pytest.raises(FileExistsError):
        ln.apply_proposals(FILM, chosen, out)


def test_proposals_include_drift():
    plan = plan_of(chain_storyboard())
    curve = {"points": [{"anchor": "c", "act": None, "flags": ["colour"]}], "missing": []}
    rep = ln.propose(plan, limit=12, curve=curve)
    assert [p["anchor"] for p in rep["proposals"]] == ["c"]
    assert rep["proposals"][0]["reasons"] == ["drift:colour"]
    assert rep["proposals"][0]["invalidated_anchors"] == ["c", "d"]


# --- US4 ------------------------------------------------------------------------------------------

@needs_ffmpeg
def test_shared_check(tmp_path):
    images = {k: img(tmp_path / f"{k}.png", "0xC87830") for k in "ab"}
    images["b"] = img(tmp_path / "b2.png", "0x2850E0")
    run = fake_run(tmp_path, images, bridges=[("a", "b")])
    rep = ln.shared_check(run)
    assert rep["ok"] and rep["results"][0]["status"] == "match" and len(rep["results"]) == 2
    job = run.parent / "bjob0" / "job.json"
    rec = json.loads(job.read_text())
    rec["anchors"]["end_image"]["sha256"] = "0" * 64
    job.write_text(json.dumps(rec))
    bad = ln.shared_check(run)
    assert not bad["ok"] and any(r["status"] == "mismatch" and r["endpoint"] == "end" for r in bad["results"])
    job.unlink()
    assert all(r["status"] == "unchecked" for r in ln.shared_check(run)["results"])


# --- CLI ------------------------------------------------------------------------------------------

def test_cli(tmp_path, capsys):
    assert cli.main(["lineage", str(FILM)]) == 1
    assert json.loads(capsys.readouterr().out)["max_depth"] == 26
    out = tmp_path / "p.yaml"
    assert cli.main(["lineage-propose", str(FILM), "--out", str(out)]) == 0
    res = json.loads(capsys.readouterr().out)
    assert res["out"] == str(out) and res["max_depth_after"] <= 12
    assert cli.main(["lineage", str(out)]) == 0
    capsys.readouterr()
    assert cli.main(["lineage-propose", str(FILM), "--out", str(out)]) == 2
    capsys.readouterr().out.encode("ascii")
