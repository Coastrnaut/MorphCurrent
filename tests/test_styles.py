"""F21 style packs: inheritance, overrides, plan identity, private asset checks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from morph_studio import cli
from morph_studio.dag import compile_plan
from morph_studio.schema import Storyboard, load_storyboard
from morph_studio.styles import StyleError, apply_override, check_assets, resolve_pack, style_text

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "configs/sequences/organic-machines.yaml"


def write_pack(d: Path, data: dict) -> None:
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{data['id']}.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")


def test_inheritance_merge_and_hash():
    child = resolve_pack("engineering-noir-power", REPO / "configs/styles")
    base = resolve_pack("engineering-noir", REPO / "configs/styles")
    assert child["lineage"] == ["engineering-noir@v1", "engineering-noir-power@v1"]
    assert child["lens"] == base["lens"] and child["lighting"] != base["lighting"]
    assert child["palette"] == ["polished copper", "hot amber", "deep blue"]  # replaced
    assert child["negative"][:len(base["negative"])] == base["negative"]  # merged in order
    assert child["negative"][-1] == "sparks covering the subject"
    assert child["sha256"] != base["sha256"] and len(child["sha256"]) == 64
    assert resolve_pack("engineering-noir-power", REPO / "configs/styles")["sha256"] == child["sha256"]


def test_cycle_unknown_parent_and_unsafe_id(tmp_path):
    write_pack(tmp_path, {"id": "a", "version": 1, "extends": "b"})
    write_pack(tmp_path, {"id": "b", "version": 1, "extends": "a"})
    with pytest.raises(StyleError, match="cycle"):
        resolve_pack("a", tmp_path)
    write_pack(tmp_path, {"id": "c", "version": 1, "extends": "missing"})
    with pytest.raises(StyleError, match="not found"):
        resolve_pack("c", tmp_path)
    with pytest.raises(StyleError, match="invalid style pack id"):
        resolve_pack("../secrets", tmp_path)


def test_override_changes_only_named_field():
    base = resolve_pack("engineering-noir", REPO / "configs/styles")
    over = apply_override(base, {"lighting": "cold blue moonlight"})
    assert over["lighting"] == "cold blue moonlight" and over["lens"] == base["lens"]
    assert over["sha256"] != base["sha256"]
    assert "cold blue moonlight" in style_text(over)


def three_scene_storyboard(override: dict | None = None) -> dict:
    data = yaml.safe_load(SAMPLE.read_text(encoding="utf-8"))
    data["style"]["pack"] = "engineering-noir"
    data["anchors"][0]["prompt"] = "A glass Leyden jar with a brass electrode."
    data["anchors"][1]["prompt"] = "Transform the jar into a stacked voltaic pile of copper and zinc discs."
    data["anchors"][2]["prompt"] = "Transform the pile into a spinning copper dynamo coil."
    if override:
        data["anchors"][1]["style_override"] = override
    return data


def test_three_linked_scenes_share_pack_with_one_override():
    plan = compile_plan(Storyboard.model_validate(three_scene_storyboard({"lighting": "warm amber glow"})),
                        repo_root=REPO)
    tasks = [plan["tasks"][f"anchor:{a}"] for a in ("orchid", "butterfly", "phoenix")]
    clause = style_text(resolve_pack("engineering-noir", REPO / "configs/styles"))
    assert tasks[0]["positive_prompt"] == "A glass Leyden jar with a brass electrode. " + clause
    assert tasks[0]["positive_prompt"].startswith("A glass Leyden jar")  # artist text first, unchanged
    assert tasks[0]["style_sha256"] == tasks[2]["style_sha256"] != tasks[1]["style_sha256"]
    assert "warm amber glow" in tasks[1]["positive_prompt"] and "warm amber glow" not in tasks[0]["positive_prompt"]
    assert "logo" in tasks[0]["negative_prompt"]
    assert all(t["style_pack"] == "engineering-noir@v1" for t in tasks)


def test_pack_change_invalidates_plan_but_sample_hash_is_stable(tmp_path):
    a = compile_plan(Storyboard.model_validate(three_scene_storyboard()), repo_root=REPO)
    # copy repo styles into a temp root and edit the pack
    root = tmp_path
    (root / "configs/styles").mkdir(parents=True)
    pack = yaml.safe_load((REPO / "configs/styles/engineering-noir.yaml").read_text(encoding="utf-8"))
    pack["lighting"] = "hard overhead light"
    (root / "configs/styles/engineering-noir.yaml").write_text(yaml.safe_dump(pack), encoding="utf-8")
    b = compile_plan(Storyboard.model_validate(three_scene_storyboard()), repo_root=root)
    assert a["plan_sha256"] != b["plan_sha256"]
    sample = compile_plan(load_storyboard(SAMPLE), repo_root=REPO)
    assert sample["plan_sha256"] == "ba2d9dbedb6189beaef6c39a8e5e2a06caef260a2729620c7e8ffa1071bb4bdf"
    assert "style_sha256" not in sample["tasks"]["anchor:orchid"]


def test_override_without_pack_is_rejected():
    data = yaml.safe_load(SAMPLE.read_text(encoding="utf-8"))
    data["anchors"][0]["style_override"] = {"lighting": "x"}
    with pytest.raises(ValueError, match="requires style.pack"):
        compile_plan(Storyboard.model_validate(data), repo_root=REPO)


def test_asset_checks(tmp_path):
    lib = tmp_path / "library"
    (lib / "refs").mkdir(parents=True)
    good = lib / "refs" / "copper.png"
    good.write_bytes(b"copper reference")
    sha = hashlib.sha256(b"copper reference").hexdigest()
    resolved = {"reference_assets": [
        {"path": "refs/copper.png", "sha256": sha, "license": "owner photo"},
        {"path": "refs/missing.png", "sha256": sha, "license": "owner photo"},
        {"path": "../outside.png", "sha256": sha, "license": "x"},
        {"path": "C:/abs.png", "sha256": sha, "license": "x"}]}
    status = [a["status"] for a in check_assets(resolved, lib)]
    assert status[0] == "ok" and status[1] == "missing" and status[2].startswith("unsafe") and status[3].startswith("unsafe")
    good.write_bytes(b"edited")
    assert check_assets(resolved, lib)[0]["status"].startswith("changed")


def test_cli_style_commands(capsys):
    assert cli.main(["style-list"]) == 0
    ids = [p.get("id") for p in json.loads(capsys.readouterr().out)]
    assert {"engineering-noir", "engineering-noir-power"} <= set(ids)
    assert cli.main(["style-show", "engineering-noir-power"]) == 0
    assert "prompt_clause" in json.loads(capsys.readouterr().out)
    assert cli.main(["style-check", "engineering-noir"]) == 0  # no reference assets -> nothing to fail
    assert cli.main(["style-show", "nope"]) == 2


def test_pack_size_is_advisory_only(tmp_path):
    from morph_studio.render import dry_run
    pilot = REPO / "configs/sequences/engineering-pilot.yaml"  # uses engineering-noir-power (size 832x480)
    data = yaml.safe_load(pilot.read_text(encoding="utf-8"))
    assert dry_run(pilot, repo_root=REPO)["advisories"] == []  # sizes agree
    data["render"].update(width=640, height=368)
    path = tmp_path / "proxy.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    report = dry_run(path, repo_root=REPO)
    assert report["advisories"] and "832x480" in report["advisories"][0]
    anchors = [t for t in report["plan"]["tasks"].values() if t["kind"] == "anchor"]
    assert all((t["width"], t["height"]) == (640, 368) for t in anchors)  # never applied
    assert dry_run(SAMPLE, repo_root=REPO)["advisories"] == []  # no pack, no advisory
