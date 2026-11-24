"""F05 storyboard -> task DAG (offline, deterministic)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from morph_studio import cli
from morph_studio.dag import compile_plan
from morph_studio.schema import Storyboard, load_storyboard

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "configs/sequences/organic-machines.yaml"


def sample_dict() -> dict:
    return load_storyboard(SAMPLE).model_dump(by_alias=True)


def test_sample_compiles_to_three_anchors_two_bridges_one_final():
    plan = compile_plan(load_storyboard(SAMPLE), repo_root=REPO)
    assert plan["order"] == ["anchor:orchid", "anchor:butterfly", "anchor:phoenix",
                             "bridge:orchid->butterfly", "bridge:butterfly->phoenix", "final:movie"]
    t = plan["tasks"]
    assert t["anchor:orchid"]["method"] == "text_to_image" and t["anchor:orchid"]["depends_on"] == []
    assert t["anchor:butterfly"]["depends_on"] == ["anchor:orchid"]
    assert t["anchor:phoenix"]["capability"] == "reference_edit"
    assert "anchor:butterfly" in t["bridge:orchid->butterfly"]["depends_on"]
    assert "anchor:butterfly" in t["bridge:butterfly->phoenix"]["depends_on"]
    assert [x for x in plan["order"] if x == "anchor:butterfly"] == ["anchor:butterfly"]
    assert t["bridge:orchid->butterfly"]["frames"] == 65 and t["bridge:orchid->butterfly"]["seed"] == 201
    final = t["final:movie"]
    assert final["unique_frames_if_endpoints_match"] == 129
    assert final["anchor_span_seconds"] == 8.0 and final["nominal_duration_seconds"] == 129 / 16
    assert final["audio"] == "none"
    assert "Surreal cinematic macro photography" in t["anchor:orchid"]["positive_prompt"]


def test_requirements_report_missing_anchor_profiles():
    plan = compile_plan(load_storyboard(SAMPLE), repo_root=REPO, profiles={"text_to_image": "configs/profiles/absent_t2i.binding.json", "reference_edit": "configs/profiles/absent_edit.binding.json"})
    assert plan["requirements"]["wan_flf2v"]["exists"] is True
    assert plan["requirements"]["text_to_image"]["exists"] is False
    assert any(b.startswith("reference_edit: missing") for b in plan["blocked"])


def test_real_anchor_profiles_exist_since_f02():
    plan = compile_plan(load_storyboard(SAMPLE), repo_root=REPO)
    assert plan["blocked"] == [] and plan["requirements"]["reference_edit"]["exists"] is True


def test_plan_hash_is_deterministic_and_sensitive():
    a = compile_plan(load_storyboard(SAMPLE), repo_root=REPO)
    b = compile_plan(load_storyboard(SAMPLE), repo_root=REPO)
    assert a["plan_sha256"] == b["plan_sha256"]
    data = sample_dict()
    data["anchors"][1]["prompt"] += " Extra."
    c = compile_plan(Storyboard.model_validate(data), repo_root=REPO)
    assert c["plan_sha256"] != a["plan_sha256"]


def test_null_seeds_are_derived_and_labelled():
    data = sample_dict()
    data["anchors"][0]["seed"] = None
    data["transitions"][0]["seed"] = None
    t = compile_plan(Storyboard.model_validate(data), repo_root=REPO)["tasks"]
    assert isinstance(t["anchor:orchid"]["seed"], int) and t["anchor:orchid"]["seed_source"].startswith("derived")
    assert isinstance(t["bridge:orchid->butterfly"]["seed"], int)
    again = compile_plan(Storyboard.model_validate(data), repo_root=REPO)["tasks"]
    assert again["anchor:orchid"]["seed"] == t["anchor:orchid"]["seed"]


def test_independent_t2i_dependency_is_ordering_only():
    data = sample_dict()
    data["anchors"][2]["generation"] = "independent_t2i"
    t = compile_plan(Storyboard.model_validate(data), repo_root=REPO)["tasks"]["anchor:phoenix"]
    assert t["capability"] == "text_to_image" and t["conditioned_on_parent"] is False
    assert t["depends_on"] == ["anchor:butterfly"]


@pytest.mark.parametrize("mutate", [
    lambda d: d["render"].update(width=840),               # not a multiple of 16
    lambda d: d["anchors"][1].update(reference="phoenix"),  # forward reference
    lambda d: d["transitions"][0].update(duration_beats=40),  # beyond max_bridge_frames
])
def test_invalid_storyboards_fail_at_compile(mutate):
    data = sample_dict()
    mutate(data)
    with pytest.raises((ValidationError, ValueError)):
        compile_plan(Storyboard.model_validate(data), repo_root=REPO)


def test_cli_dag_makes_no_network_calls(monkeypatch, capsys):
    monkeypatch.setattr(cli, "ComfyClient", lambda *a, **k: pytest.fail("network used"))
    assert cli.main(["dag", str(SAMPLE)]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["storyboard_sha256"] and len(plan["tasks"]) == 6
