"""F27: local workflow/model capability registry, compatibility preview, approved selection and rollback."""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest

from morph_studio import cli
from morph_studio import registry as rg
from morph_studio.workflow_adapter import CAPABILITY_CONTRACTS, graph_sha256

from conftest import REPO

PROFILES = ("anchor_t2i", "anchor_edit", "wan22_flf2v")
WORKFLOWS = ("01_anchor_t2i", "02_anchor_edit", "03_wan22_flf2v")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture()
def repo(tmp_path) -> Path:
    """tmp repo with the three real production profiles, workflows and the model catalogue."""
    (tmp_path / "configs" / "profiles").mkdir(parents=True)
    (tmp_path / "workflows").mkdir()
    for name in PROFILES:
        rel = f"configs/profiles/{name}.binding.json"
        (tmp_path / rel).write_bytes((REPO / rel).read_bytes())
    for name in WORKFLOWS:
        (tmp_path / "workflows" / f"{name}.json").write_bytes((REPO / "workflows" / f"{name}.json").read_bytes())
    (tmp_path / "configs/model_catalogue.json").write_bytes((REPO / "configs/model_catalogue.json").read_bytes())
    return tmp_path


@pytest.fixture()
def wan_info() -> dict:
    return _load(REPO / "tests/fixtures/object_info_wan22_flf2v.json")


def wan(repo: Path) -> Path:
    return repo / "configs/profiles/wan22_flf2v.binding.json"


def variant(repo: Path, name: str, edit_graph=None, edit_profile=None) -> Path:
    """Copy of the Wan profile/workflow as a candidate, optionally edited (hash re-pinned)."""
    graph = _load(repo / "workflows/03_wan22_flf2v.json")
    if edit_graph:
        edit_graph(graph)
    (repo / "workflows" / f"{name}.json").write_text(json.dumps(graph), encoding="utf-8")
    prof = _load(wan(repo))
    prof.update(profile=name, workflow=f"workflows/{name}.json", workflow_sha256=graph_sha256(graph))
    if edit_profile:
        edit_profile(prof)
    path = repo / "configs/profiles" / f"{name}.binding.json"
    path.write_text(json.dumps(prof), encoding="utf-8")
    return path


def models_root(repo: Path, entry: dict, skip: str | None = None) -> Path:
    root = repo / "models"
    for m in entry["models"]:
        if m["file"] != skip:
            (root / m["folder"]).mkdir(parents=True, exist_ok=True)
            (root / m["folder"] / m["file"]).write_bytes(b"")
    return root


# --- setup / foundational ------------------------------------------------------------------------

def test_upscale_contract():
    assert CAPABILITY_CONTRACTS["upscale"] == (("input_video",), "video")


def test_catalogue_mirrors_models_md():
    hashes = set(re.findall(r"`([0-9a-f]{64})`", (REPO / "docs/MODELS.md").read_text(encoding="utf-8")))
    cat = rg.load_catalogue(REPO / "configs/model_catalogue.json")
    assert hashes and hashes <= {m["sha256"] for m in cat.values()}
    assert cat["upscale_models/RealESRGAN_x2plus.pth"]["licence"] == "BSD-3-Clause"


def test_severity_order():
    assert rg.SEVERITY[0] == "cloud-node" and rg.SEVERITY[-1] == "ready" and len(rg.SEVERITY) == 7


# --- US1 registry ---------------------------------------------------------------------------------

def test_offline_registry(repo):
    entries = rg.build_registry(repo / "configs/profiles", repo_root=repo)
    assert [e["capability"] for e in entries] == ["reference_edit", "text_to_image", "wan_flf2v"]
    assert {e["status"] for e in entries} == {"offline-unverified"}
    w = entries[2]
    assert w["length_rule"] == "4n+1" and w["actual_sha256"] == w["workflow_sha256"]
    assert {"start_image", "end_image", "length", "seed"} <= set(w["roles"])
    assert "WanFirstLastFrameToVideo" in w["node_classes"] and w["outputs"] == ["video"]
    roles = {m["file"]: m["role"] for m in w["models"]}
    assert roles["wan_2.1_vae.safetensors"] == "vae"
    assert roles["umt5_xxl_fp8_e4m3fn_scaled.safetensors"] == "text_encoder"
    assert roles["wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"] == "diffusion"
    assert all(m["sha256"] != rg.NOT_RECORDED and m["present"] is None for m in w["models"])
    assert entries[1]["length_rule"] is None


def test_ready_with_object_info(repo, wan_info):
    e = rg.build_entry(wan(repo), object_info=wan_info, repo_root=repo)
    assert e["status"] == "ready", e["problems"]
    assert e["constraints"]["length"]["step"] == 4 and e["constraints"]["width"]["step"] == 16
    root = models_root(repo, e)
    assert rg.build_entry(wan(repo), object_info=wan_info, models_root=root, repo_root=repo)["status"] == "ready"


def test_stale_hash(repo, wan_info):
    path = repo / "workflows/03_wan22_flf2v.json"
    graph = _load(path)
    graph["90"]["inputs"]["text"] = "edited after pinning"
    path.write_text(json.dumps(graph), encoding="utf-8")
    e = rg.build_entry(wan(repo), object_info=wan_info, repo_root=repo)
    assert e["status"] == "stale-hash"


def test_missing_node(repo, wan_info):
    info = {k: v for k, v in wan_info.items() if k != "CreateVideo"}
    e = rg.build_entry(wan(repo), object_info=info, repo_root=repo)
    assert e["status"] == "missing-node"
    assert any("CreateVideo" in a and "owner approval" in a for a in e["approval_needed"])


def test_missing_model(repo, wan_info):
    e = rg.build_entry(wan(repo), object_info=wan_info, repo_root=repo)
    root = models_root(repo, e, skip="wan_2.1_vae.safetensors")
    e = rg.build_entry(wan(repo), object_info=wan_info, models_root=root, repo_root=repo)
    assert e["status"] == "missing-model"
    assert any("wan_2.1_vae.safetensors" in a and "owner approval" in a for a in e["approval_needed"])
    assert [m["present"] for m in e["models"] if m["file"] == "wan_2.1_vae.safetensors"] == [False]


def test_cloud_node(repo, wan_info):
    info = copy.deepcopy(wan_info)
    info["CreateVideo"]["api_node"] = True
    e = rg.build_entry(wan(repo), object_info=info, repo_root=repo)
    assert e["status"] == "cloud-node" and not e["selectable"]


def test_contract_errors(repo):
    no_seed = variant(repo, "no_seed", edit_profile=lambda p: p["bindings"].pop("seed"))
    assert rg.build_entry(no_seed, repo_root=repo)["status"] == "contract-error"
    bad = repo / "configs/profiles/bad.binding.json"
    bad.write_text("{not json", encoding="utf-8")
    e = rg.build_entry(bad, repo_root=repo)
    assert e["status"] == "contract-error" and e["problems"]
    gone = variant(repo, "gone")
    (repo / "workflows/gone.json").unlink()
    assert "not found" in rg.build_entry(gone, repo_root=repo)["problems"][0]["message"]
    assert len(rg.build_registry(repo / "configs/profiles", repo_root=repo)) == 6  # never raises


def test_most_severe_and_all_problems(repo, wan_info):
    info = {k: v for k, v in wan_info.items() if k != "CreateVideo"}
    path = repo / "workflows/03_wan22_flf2v.json"
    graph = _load(path)
    graph["90"]["inputs"]["text"] = "edited"
    path.write_text(json.dumps(graph), encoding="utf-8")
    e = rg.build_entry(wan(repo), object_info=info, repo_root=repo)
    assert e["status"] == "stale-hash"
    assert {"stale-hash", "missing-node"} <= {p["status"] for p in e["problems"]}


def test_uncatalogued_model(repo):
    def swap_vae(graph):
        node = next(k for k, n in graph.items() if n["class_type"] == "VAELoader")
        graph[node]["inputs"]["vae_name"] = "new_vae.safetensors"
    e = rg.build_entry(variant(repo, "other_vae", edit_graph=swap_vae), repo_root=repo)
    assert e["status"] == "offline-unverified"
    m = next(m for m in e["models"] if m["file"] == "new_vae.safetensors")
    assert m["licence"] == rg.NOT_RECORDED and m["sha256"] == rg.NOT_RECORDED


# --- US2 preview ----------------------------------------------------------------------------------

def _entries(repo, cand_path, info=None):
    return (rg.build_entry(wan(repo), object_info=info, repo_root=repo),
            rg.build_entry(cand_path, object_info=info, repo_root=repo))


def test_preview_identical_and_compatible(repo, wan_info):
    same = rg.compare(*_entries(repo, wan(repo), wan_info))
    assert same["verdict"] == "compatible" and same["changes"] == []
    prompt = variant(repo, "prompt", edit_graph=lambda g: g["90"]["inputs"].update(text="new default"))
    p = rg.compare(*_entries(repo, prompt, wan_info))
    assert p["verdict"] == "compatible" and [c["type"] for c in p["changes"]] == ["hash_changed"]
    added = variant(repo, "added", edit_profile=lambda pr: pr["bindings"].update(
        steps={"node_id": "84", "input": "steps", "class_type": "KSamplerAdvanced"}))
    a = rg.compare(*_entries(repo, added))
    assert a["verdict"] == "compatible" and {"type": "role_added", "role": "steps"}.items() <= a["changes"][0].items()


def test_preview_needs_rebinding(repo, wan_info):
    def move(pr):
        pr["bindings"]["negative_prompt"]["node_id"] = "90"
    moved = rg.compare(*_entries(repo, variant(repo, "moved", edit_profile=move)))
    assert moved["verdict"] == "needs-rebinding" and moved["changes"][0]["type"] == "role_moved"
    removed = rg.compare(*_entries(repo, variant(repo, "removed",
                                                 edit_profile=lambda pr: pr["bindings"].pop("negative_prompt"))))
    assert removed["verdict"] == "needs-rebinding"
    cur, cand = _entries(repo, variant(repo, "step"), wan_info)
    cand["constraints"]["length"]["step"] = 8
    c = rg.compare(cur, cand)
    assert c["verdict"] == "needs-rebinding" and any(x["type"] == "constraint_changed" for x in c["changes"])


def test_preview_incompatible(repo):
    cap = variant(repo, "cap", edit_profile=lambda pr: pr.update(capability="text_to_image"))
    assert rg.compare(*_entries(repo, cap))["verdict"] == "incompatible"
    out = variant(repo, "out", edit_profile=lambda pr: pr["outputs"][0].update(kind="image"))
    assert any(c["type"] == "output_changed" for c in rg.compare(*_entries(repo, out))["changes"])
    seed = variant(repo, "seedless", edit_profile=lambda pr: pr["bindings"].pop("seed"))
    s = rg.compare(*_entries(repo, seed))
    assert s["verdict"] == "incompatible" and any(c["type"] == "required_role_missing" for c in s["changes"])


# --- US3 selection --------------------------------------------------------------------------------

def test_defaults(repo):
    sel = repo / "configs/registry/selection.json"
    assert rg.active_profile("wan_flf2v", sel) == "configs/profiles/wan22_flf2v.binding.json"
    assert rg.active_profile("upscale", sel) is None
    assert not sel.exists()


def test_select_refusals(repo, wan_info):
    sel = repo / "configs/registry/selection.json"
    cand = variant(repo, "prompt", edit_graph=lambda g: g["90"]["inputs"].update(text="new default"))
    with pytest.raises(rg.RegistryRefusal, match="approve"):
        rg.select(cand, approve=False, object_info=wan_info, selection_path=sel, repo_root=repo)
    with pytest.raises(rg.RegistryRefusal, match="offline-unverified"):
        rg.select(cand, approve=True, object_info=None, selection_path=sel, repo_root=repo)
    info = copy.deepcopy(wan_info)
    info["CreateVideo"]["api_node"] = True
    with pytest.raises(rg.RegistryRefusal, match="cloud-node"):
        rg.select(cand, approve=True, object_info=info, selection_path=sel, repo_root=repo)
    e = rg.build_entry(cand, object_info=wan_info, repo_root=repo)
    root = models_root(repo, e, skip="wan_2.1_vae.safetensors")
    with pytest.raises(rg.RegistryRefusal, match="missing-model"):
        rg.select(cand, approve=True, object_info=wan_info, models_root=root, selection_path=sel, repo_root=repo)
    assert not sel.exists()


def test_select_incompatible_refused(repo, wan_info, monkeypatch):
    sel = repo / "configs/registry/selection.json"
    cand = variant(repo, "prompt", edit_graph=lambda g: g["90"]["inputs"].update(text="x"))
    real = rg.compare
    monkeypatch.setattr(rg, "compare", lambda a, b: {**real(a, b), "verdict": "incompatible"})
    with pytest.raises(rg.RegistryRefusal, match="incompatible"):
        rg.select(cand, approve=True, object_info=wan_info, selection_path=sel, repo_root=repo)
    assert not sel.exists()


def test_select_and_rollback(repo, wan_info):
    sel = repo / "configs/registry/selection.json"
    a = variant(repo, "cand_a", edit_graph=lambda g: g["90"]["inputs"].update(text="a"))
    b = variant(repo, "cand_b", edit_graph=lambda g: g["90"]["inputs"].update(text="b"))
    r1 = rg.select(a, approve=True, note="owner ok a", object_info=wan_info, selection_path=sel, repo_root=repo)
    assert r1["active"]["profile"] == "configs/profiles/cand_a.binding.json"
    assert rg.active_profile("wan_flf2v", sel) == "configs/profiles/cand_a.binding.json"
    first = _load(sel)["history"][0]
    assert first["previous"]["profile"] == "configs/profiles/wan22_flf2v.binding.json"
    assert first["new"]["workflow_sha256"] == _load(a)["workflow_sha256"] and first["note"] == "owner ok a"
    with pytest.raises(rg.RegistryRefusal, match="already active"):
        rg.select(a, approve=True, object_info=wan_info, selection_path=sel, repo_root=repo)
    rg.select(b, approve=True, object_info=wan_info, selection_path=sel, repo_root=repo)
    before = json.dumps(_load(sel)["history"][:2])
    assert rg.rollback("wan_flf2v", sel)["active"] == "configs/profiles/cand_a.binding.json"
    assert rg.rollback("wan_flf2v", sel)["active"] == "configs/profiles/wan22_flf2v.binding.json"
    data = _load(sel)
    assert json.dumps(data["history"][:2]) == before  # append-only
    assert [h["action"] for h in data["history"]] == ["select", "select", "rollback", "rollback"]
    assert "wan_flf2v" not in data["active"]
    with pytest.raises(rg.RegistryRefusal, match="nothing to roll back"):
        rg.rollback("wan_flf2v", sel)
    assert not list(sel.parent.glob("*.part"))


# --- CLI / safety ---------------------------------------------------------------------------------

def test_cli(repo, wan_info, capsys, tmp_path):
    info_file = tmp_path / "info.json"
    info_file.write_text(json.dumps(wan_info), encoding="utf-8")
    profiles = str(repo / "configs/profiles")
    assert cli.main(["registry", "--profiles", profiles, "--repo-root", str(repo)]) == 0
    out = capsys.readouterr().out
    out.encode("ascii")
    assert json.loads(out)["offline"] is True
    assert cli.main(["registry", "--profiles", profiles, "--repo-root", str(repo), "--strict"]) == 1
    capsys.readouterr()
    assert cli.main(["registry-diff", str(wan(repo)), str(wan(repo)), "--repo-root", str(repo)]) == 0
    assert json.loads(capsys.readouterr().out)["verdict"] == "compatible"
    bad = repo / "configs/profiles/bad.binding.json"
    bad.write_text("{", encoding="utf-8")
    assert cli.main(["registry-diff", str(wan(repo)), str(bad), "--repo-root", str(repo)]) == 2
    bad.unlink()
    cand = variant(repo, "cand", edit_graph=lambda g: g["90"]["inputs"].update(text="c"))
    sel = str(repo / "sel.json")
    base = ["registry-select", "--profile", str(cand), "--object-info", str(info_file), "--selection", sel,
            "--repo-root", str(repo)]
    assert cli.main(base) == 2 and not Path(sel).exists()
    capsys.readouterr()
    assert cli.main(base + ["--approve", "--note", "ok"]) == 0
    assert json.loads(capsys.readouterr().out)["history_length"] == 1
    assert cli.main(["registry-rollback", "--capability", "wan_flf2v", "--selection", sel]) == 0
    capsys.readouterr()
    assert cli.main(["registry-rollback", "--capability", "wan_flf2v", "--selection", sel]) == 2


def test_no_download_or_install_code():
    source = (REPO / "src/morph_studio/registry.py").read_text(encoding="utf-8")
    for banned in ("urlretrieve", "urlopen", "pip install", "git clone", "requests.", ".post(", "queue_prompt",
                   "/prompt"):
        assert banned not in source


def test_render_defaults_unchanged():
    source = (REPO / "src/morph_studio/cli.py").read_text(encoding="utf-8")
    assert 'default="configs/profiles/wan22_flf2v.binding.json"' in source
    for module in ("render.py", "dag.py", "pipeline.py"):
        assert "registry" not in (REPO / "src/morph_studio" / module).read_text(encoding="utf-8")
