"""F23: labelled prompt-only camera moves, endpoint satisfiability, framing targets and crops."""
from __future__ import annotations

import json
import shutil
import struct
import zlib
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from morph_studio import cli
from morph_studio.camera import (LABEL, camera_check, camera_clause, crop_check, framing_check,
                                 graph_camera_nodes, satisfiability)
from morph_studio.dag import compile_plan
from morph_studio.schema import Storyboard

from conftest import REPO

SAMPLE = REPO / "configs/sequences/organic-machines.yaml"
needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


def rect_png(path: Path, cx: float, cy: float, w: float, h: float, size=(320, 184)) -> Path:
    """Bright rectangle (centre cx,cy; size w,h as frame fractions) on a dark background."""
    W, H = size
    x0, x1 = int((cx - w / 2) * W), int((cx + w / 2) * W)
    y0, y1 = int((cy - h / 2) * H), int((cy + h / 2) * H)
    rows = b"".join(b"\x00" + b"".join((b"\xdc\xdc\xdc" if x0 <= x < x1 and y0 <= y < y1 else b"\x08\x08\x10")
                                       for x in range(W)) for y in range(H))

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))
    return path


def geo(cx, cy, w, h, **extra):
    return {"centroid": [cx, cy], "extent": [w, h], "area": w * h, **extra}


def sample(**changes) -> dict:
    data = yaml.safe_load(SAMPLE.read_text(encoding="utf-8"))
    for key, value in changes.items():
        data["transitions"][0][key] = value
    return data


# --- US1 --------------------------------------------------------------------------------------------

def test_camera_clause_deterministic_and_worded():
    assert camera_clause("push_in", 0.15) == camera_clause("push_in", 0.15)
    assert "moderately" in camera_clause("push_in", 0.15) and "15%" in camera_clause("push_in", 0.15)
    assert "slightly" in camera_clause("pan_left", 0.05) and "left" in camera_clause("pan_left", 0.05)
    assert "strongly" in camera_clause("pull_out", 0.4)
    assert camera_clause("static", 0.3).startswith("The camera stays locked")
    for move in ("tilt_up", "tilt_down", "orbit_left", "orbit_right", "rise", "pan_right"):
        assert camera_clause(move, 0.1).startswith("The camera")


def test_plan_records_labelled_camera_and_hash_unchanged():
    base = compile_plan(Storyboard.model_validate(sample()), repo_root=REPO)
    assert base["plan_sha256"] == "ba2d9dbedb6189beaef6c39a8e5e2a06caef260a2729620c7e8ffa1071bb4bdf"
    assert "camera" not in base["tasks"]["bridge:orchid->butterfly"]
    plan = compile_plan(Storyboard.model_validate(sample(camera={"move": "push_in", "amount": 0.15})), repo_root=REPO)
    task = plan["tasks"]["bridge:orchid->butterfly"]
    assert task["camera"] == {"move": "push_in", "amount": 0.15, "clause": camera_clause("push_in", 0.15),
                              "label": LABEL}
    assert camera_clause("push_in", 0.15) in task["positive_prompt"]
    assert plan["plan_sha256"] != base["plan_sha256"]


def test_graph_control_refused_and_validation():
    graph = json.loads((REPO / "workflows/03_wan22_flf2v.json").read_text(encoding="utf-8"))
    assert graph_camera_nodes(graph) == []
    with pytest.raises(ValueError, match="no camera-control"):
        compile_plan(Storyboard.model_validate(sample(camera={"move": "pan_left", "control": "graph"})),
                     repo_root=REPO)
    for bad in ({"move": "push_in", "amount": -0.1}, {"move": "push_in", "amount": 0.6}, {"move": "zoom"}):
        with pytest.raises(ValidationError):
            Storyboard.model_validate(sample(camera=bad))
    chor = {"camera": "slow_push", "correspondences": [{"source": "petal", "target": "wing"}]}
    with pytest.raises(ValidationError, match="camera"):
        Storyboard.model_validate(sample(camera={"move": "pan_left"}, choreography=chor))
    ok = {"camera": "static", "correspondences": [{"source": "petal", "target": "wing"}]}
    Storyboard.model_validate(sample(camera={"move": "pan_left"}, choreography=ok))


# --- US2 --------------------------------------------------------------------------------------------

def test_satisfiability_rules():
    small, big = geo(0.5, 0.5, 0.3, 0.3), geo(0.5, 0.5, 0.39, 0.39)  # end 1.3x larger
    assert satisfiability("push_in", 0.15, small, big)["verdict"] == "satisfiable"
    out = satisfiability("pull_out", 0.15, small, big)
    assert out["verdict"] == "unsatisfiable" and out["extent_ratio"] == 1.3 and "smaller" in out["reason"]
    same = geo(0.5, 0.5, 0.3, 0.3)
    assert satisfiability("pan_left", 0.2, same, same)["verdict"] == "unsatisfiable"
    assert satisfiability("pan_left", 0.2, same, geo(0.62, 0.5, 0.3, 0.3))["verdict"] == "satisfiable"
    assert satisfiability("pan_right", 0.2, same, geo(0.38, 0.5, 0.3, 0.3))["verdict"] == "satisfiable"
    assert satisfiability("tilt_up", 0.2, same, geo(0.5, 0.62, 0.3, 0.3))["verdict"] == "satisfiable"
    assert satisfiability("tilt_down", 0.2, same, geo(0.5, 0.62, 0.3, 0.3))["verdict"] == "unsatisfiable"
    assert satisfiability("static", 0.1, same, geo(0.53, 0.5, 0.33, 0.33))["verdict"] == "satisfiable"
    assert satisfiability("static", 0.1, same, geo(0.7, 0.5, 0.3, 0.3))["verdict"] == "unsatisfiable"
    assert satisfiability("static", 0.1, same, geo(0.5, 0.5, 0.45, 0.45))["verdict"] == "unsatisfiable"
    assert satisfiability("orbit_left", 0.2, same, same)["verdict"] == "not_verifiable"
    assert satisfiability("rise", 0.2, same, same)["verdict"] == "not_verifiable"
    assert satisfiability("push_in", 0.2, {"area": 0.95, "mask_unreliable": True}, same)["verdict"] == "unknown"


# --- US3 --------------------------------------------------------------------------------------------

def test_framing_and_crops():
    target = {"center": [0.5, 0.5], "tolerance": 0.08, "size": [0.25, 0.6]}
    assert framing_check(geo(0.52, 0.49, 0.4, 0.4), target)["on_target"]
    off = framing_check(geo(0.7, 0.5, 0.4, 0.4), target)
    assert not off["on_target"] and "centre" in off["reason"]
    assert not framing_check(geo(0.5, 0.5, 0.1, 0.1), target)["on_target"]
    centred = crop_check(geo(0.5, 0.5, 0.2, 0.6), 832, 480, ["16:9", "9:16"])
    assert centred == {"16:9": "inside", "9:16": "inside"}
    right = crop_check(geo(0.8, 0.5, 0.2, 0.4), 832, 480, ["16:9", "9:16"])
    assert right == {"16:9": "inside", "9:16": "outside"}
    assert crop_check(geo(0.5, 0.5, 0.99, 0.5), 832, 480, ["16:9"])["16:9"] == "outside"  # beyond 5% margin


# --- US4 --------------------------------------------------------------------------------------------

def test_camera_check_without_anchors(tmp_path, capsys):
    report = camera_check(SAMPLE, repo_root=REPO)
    assert report["verdict"] == "pending_anchors"
    assert {t["verdict"] for t in report["transitions"]} == {"pending_anchors"}
    assert cli.main(["camera-check", str(SAMPLE), "--repo-root", str(REPO)]) == 0
    capsys.readouterr()


def make_run(root: Path, images: dict[str, Path]) -> Path:
    run = root / "run-aaaaaaaaaaaaaaaa"
    run.mkdir(parents=True)
    stages, order = {}, []
    for i, (anchor, img) in enumerate(images.items()):
        job = root / f"j{i:015d}"
        (job / "outputs").mkdir(parents=True)
        shutil.copy(img, job / "outputs" / "anchor_00001_.png")
        (job / "job.json").write_text(json.dumps({"image": {"local_path": "outputs\\anchor_00001_.png"}}),
                                      encoding="utf-8")
        stages[f"anchor:{anchor}"] = {"state": "verified", "job_dir": f"outputs\\runs\\{job.name}"}
        order.append(f"anchor:{anchor}")
    (run / "manifest.json").write_text(json.dumps({"order": order, "stages": stages, "plan_sha256": "x"}),
                                       encoding="utf-8")
    return run


@needs_ffmpeg
def test_camera_check_with_run_anchors(tmp_path, capsys):
    imgs = tmp_path / "imgs"
    imgs.mkdir()
    a = rect_png(imgs / "a.png", 0.5, 0.5, 0.25, 0.4)
    b = rect_png(imgs / "b.png", 0.5, 0.5, 0.25, 0.4)
    c = rect_png(imgs / "c.png", 0.85, 0.5, 0.18, 0.4)  # far right: outside 9:16, off target
    run = make_run(tmp_path / "runs", {"orchid": a, "butterfly": b, "phoenix": c})
    data = sample(camera={"move": "pull_out", "amount": 0.2})  # orchid->butterfly: same size → unsatisfiable
    data["render"]["delivery_crops"] = ["16:9", "9:16"]
    data["anchors"][2]["framing"] = {"center": [0.5, 0.5], "tolerance": 0.08, "size": [0.15, 0.6]}
    sb = tmp_path / "sb.yaml"
    sb.write_text(yaml.safe_dump(data), encoding="utf-8")
    report = camera_check(sb, run_dir=run, repo_root=REPO)
    first = report["transitions"][0]
    assert first["verdict"] == "unsatisfiable" and first["label"] == LABEL
    second = report["transitions"][1]  # no camera set: static check by default
    assert second["move"] == "static" and second["verdict"] == "unsatisfiable"  # subject jumped right
    phoenix = next(x for x in report["anchors"] if x["anchor"] == "phoenix")
    assert phoenix["crops"] == {"16:9": "inside", "9:16": "outside"} and not phoenix["framing"]["on_target"]
    assert report["verdict"] == "issues"
    assert cli.main(["camera-check", str(sb), "--run", str(run), "--repo-root", str(REPO)]) == 12
    capsys.readouterr()


def test_camera_module_has_no_comfy_client():
    source = (REPO / "src/morph_studio/camera.py").read_text(encoding="utf-8")
    assert "comfy_client" not in source and "httpx" not in source


def test_cli_output_is_ascii_safe(capsys):
    """Windows cp1252 consoles/redirects crashed on non-ASCII reason text (found in real use)."""
    assert cli.main(["camera-check", str(SAMPLE), "--repo-root", str(REPO)]) == 0
    capsys.readouterr().out.encode("ascii")
    source = (REPO / "src/morph_studio/camera.py").read_text(encoding="utf-8")
    body = source.split('"""', 2)[2]  # outside the module docstring
    assert all(ord(ch) < 128 for ch in body)


def test_graph_control_uses_active_profile_and_is_always_refused(image_repo):
    """Converge T015: check the workflow named by the active Wan profile; never accept graph control."""
    graph = json.loads((image_repo / "workflows/03_wan22_flf2v.json").read_text(encoding="utf-8"))
    graph["999"] = {"class_type": "WanCameraEmbedding", "inputs": {}}
    (image_repo / "workflows/cam_wan.json").write_text(json.dumps(graph), encoding="utf-8")
    prof = json.loads((image_repo / "configs/profiles/wan22_flf2v.binding.json").read_text(encoding="utf-8"))
    prof["workflow"] = "workflows/cam_wan.json"
    (image_repo / "configs/profiles/cam_wan.binding.json").write_text(json.dumps(prof), encoding="utf-8")
    sb = Storyboard.model_validate(sample(camera={"move": "pan_left", "control": "graph"}))
    with pytest.raises(ValueError, match="WanCameraEmbedding.*no binding"):
        compile_plan(sb, repo_root=image_repo, profiles={"wan_flf2v": "configs/profiles/cam_wan.binding.json"})
    with pytest.raises(ValueError, match="03_wan22_flf2v.json has no camera-control"):
        compile_plan(sb, repo_root=image_repo)
