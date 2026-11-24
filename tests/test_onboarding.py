"""F02 capability contracts and read-only export inspection (offline)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from image_graphs import (QWEN_UNET_T2I, edit_graph, edit_profile_dict, installed_object_info,
                          real_object_info, t2i_graph, t2i_profile_dict)
from morph_studio import cli
from morph_studio.onboarding import inspect_export, load_export
from morph_studio.workflow_adapter import (BindingProfile, WorkflowBindingError, graph_sha256,
                                           load_api_workflow, load_binding_profile,
                                           validate_profile)

REPO = Path(__file__).resolve().parents[1]


def _profile(data: dict) -> BindingProfile:
    return BindingProfile.model_validate(data)


def test_t2i_profile_satisfies_contract_with_simulated_install():
    graph = t2i_graph()
    report = validate_profile(_profile(t2i_profile_dict(graph_sha256(graph))), graph,
                              installed_object_info())
    assert report.ok, report.errors


def test_edit_profile_satisfies_contract_with_simulated_install():
    graph = edit_graph()
    report = validate_profile(_profile(edit_profile_dict(graph_sha256(graph))), graph,
                              installed_object_info())
    assert report.ok, report.errors


def test_reference_edit_without_reference_image_is_rejected():
    graph = edit_graph()
    data = edit_profile_dict(graph_sha256(graph))
    del data["bindings"]["reference_image"]
    report = validate_profile(_profile(data), graph)
    assert any("requires role 'reference_image'" in e for e in report.errors)


def test_t2i_with_video_output_is_rejected():
    graph = t2i_graph()
    data = t2i_profile_dict(graph_sha256(graph))
    data["outputs"][0]["kind"] = "video"
    report = validate_profile(_profile(data), graph)
    assert any("output of kind 'image'" in e for e in report.errors)


def test_real_object_info_reports_missing_image_models():
    graph = t2i_graph()
    report = validate_profile(_profile(t2i_profile_dict(graph_sha256(graph))), graph,
                              real_object_info())
    assert not report.ok and any(QWEN_UNET_T2I in e for e in report.errors)


def test_existing_wan_profile_still_satisfies_its_contract():
    path = REPO / "configs/profiles/wan22_flf2v.binding.json"
    profile = load_binding_profile(path)
    assert profile.capability == "wan_flf2v"
    graph = load_api_workflow(REPO / profile.workflow)
    info = json.loads((REPO / "tests/fixtures/object_info_wan22_flf2v.json").read_text(encoding="utf-8"))
    assert validate_profile(profile, graph, info).ok


def test_inspect_reports_missing_models_and_candidates():
    report = inspect_export(t2i_graph(), real_object_info())
    assert not report["ok"]
    missing = {m["value"] for m in report["models"] if m["installed"] is False}
    assert QWEN_UNET_T2I in missing and "qwen_image_vae.safetensors" in missing
    hints = {(c["role_hint"], c["node_id"]) for c in report["candidates"]}
    assert ("seed", "8") in hints and ("output (image)", "10") in hints
    assert all(c["status"] == "candidate" for c in report["candidates"])
    assert report["cloud_nodes"] == []


def test_inspect_ok_after_simulated_install():
    report = inspect_export(edit_graph(), installed_object_info())
    assert report["ok"], report["errors"]
    assert ("reference_image / start_image / end_image", "11") in {
        (c["role_hint"], c["node_id"]) for c in report["candidates"]}


def test_inspect_flags_cloud_node():
    graph = {**t2i_graph(), "20": {"class_type": "QwenImageEditApi", "inputs": {}}}
    report = inspect_export(graph, installed_object_info())
    assert report["cloud_nodes"] == ["20 (QwenImageEditApi)"] and not report["ok"]


def test_inspect_offline_is_structural():
    report = inspect_export(t2i_graph(), None)
    assert report["ok"] and all(m["installed"] is None for m in report["models"])


def test_load_export_rejects_ui_format(tmp_path):
    ui = tmp_path / "ui.json"
    ui.write_text(json.dumps({"nodes": [], "links": [], "version": 0.4}), encoding="utf-8")
    with pytest.raises(WorkflowBindingError, match="Save \\(API Format\\)"):
        load_export(ui)


def test_cli_inspect_writes_nothing(tmp_path, capsys):
    export = tmp_path / "export.json"
    export.write_text(json.dumps(t2i_graph()), encoding="utf-8")
    info = tmp_path / "oi.json"
    info.write_text(json.dumps(real_object_info()), encoding="utf-8")
    before = sorted(p.name for p in tmp_path.iterdir())
    assert cli.main(["workflow-inspect", str(export), "--object-info", str(info)]) == 4
    assert json.loads(capsys.readouterr().out)["ok"] is False
    assert cli.main(["workflow-inspect", str(export), "--offline"]) == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == before


def test_decision_record_keeps_gate_blocked():
    text = (REPO / "docs/ANCHOR_MODEL_DECISION.md").read_text(encoding="utf-8")
    assert "BLOCKED" in text and "owner to verify" in text
    assert "No model has been downloaded" in text
