"""F14 transition risk and intermediate-anchor ladder proposals (offline)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from morph_studio import cli
from morph_studio.dag import compile_plan
from morph_studio.ladder import LadderError, prompt_distance, propose_ladder, transition_risk
from morph_studio.perf import load_history
from morph_studio.schema import Storyboard

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "configs/sequences/organic-machines.yaml"
HISTORY = load_history(REPO / "configs/perf_history.json")


def sample() -> dict:
    return yaml.safe_load(SAMPLE.read_text(encoding="utf-8"))


def test_prompt_distance_and_risk_levels():
    assert prompt_distance("a glass orchid flower", "a glass orchid flower") == 0.0
    low = transition_risk("silver mechanical butterfly glass wings", "silver mechanical butterfly glass wings spread")
    high = transition_risk("lightning bolt over a stormy sea", "laboratory leyden jar with brass electrode")
    assert low["level"] == "low" and high["level"] == "high"
    assert any(r.startswith("prompt_distance") for r in high["reasons"])
    geo = transition_risk("glass orchid", "glass orchid bloom", {"flags": ["symmetry_drop", "scale_change"]})
    assert "geometry symmetry_drop" in geo["reasons"] and geo["risk"] >= 0.4


def test_split_one_step_halves_beats_into_valid_lengths():
    sb, report = propose_ladder(sample(), "butterfly", "phoenix", steps=1, history=HISTORY)
    ids = [a["id"] for a in sb["anchors"]]
    assert ids == ["orchid", "butterfly", "butterfly_to_phoenix_1", "phoenix"]
    mid = sb["anchors"][2]
    assert mid["generation"] == "reference_edit" and mid["reference"] == "butterfly"
    assert sb["anchors"][3]["reference"] == "butterfly_to_phoenix_1"
    assert [(s["from"], s["to"], s["frames"]) for s in report["segments"]] == [
        ("butterfly", "butterfly_to_phoenix_1", 33), ("butterfly_to_phoenix_1", "phoenix", 33)]
    assert [t["from"] for t in sb["transitions"]] == ["orchid", "butterfly", "butterfly_to_phoenix_1"]
    assert sb["transitions"][0]["duration_beats"] == 8  # untouched upstream transition
    plan = compile_plan(Storyboard.model_validate(sb), repo_root=REPO)
    assert plan["tasks"]["final:movie"]["unique_frames_if_endpoints_match"] == 1 + 64 + 32 + 32
    assert "50% of the way" in mid["prompt"] and report["status"].startswith("PROPOSAL")


def test_deterministic_and_input_untouched():
    data = sample()
    before = json.dumps(data, sort_keys=True)
    a, _ = propose_ladder(data, "orchid", "butterfly", steps=2)
    b, _ = propose_ladder(data, "orchid", "butterfly", steps=2)
    assert a == b and json.dumps(data, sort_keys=True) == before
    assert [x["id"] for x in a["anchors"][1:3]] == ["orchid_to_butterfly_1", "orchid_to_butterfly_2"]
    assert a["anchors"][2]["reference"] == "orchid_to_butterfly_1"


def test_choreography_copied_to_segments():
    data = sample()
    data["transitions"][1]["choreography"] = {"camera": "static", "phases": ["wings widen"]}
    sb, _ = propose_ladder(data, "butterfly", "phoenix")
    assert all(t.get("choreography", {}).get("camera") == "static" for t in sb["transitions"][1:])


def test_refusals():
    with pytest.raises(LadderError, match="adjacent"):
        propose_ladder(sample(), "orchid", "phoenix")
    with pytest.raises(LadderError, match="steps"):
        propose_ladder(sample(), "orchid", "butterfly", steps=4)
    tiny = sample()
    tiny["transitions"][0]["duration_beats"] = 0.25  # 0.0625 beats per segment: below Wan's minimum
    with pytest.raises(LadderError, match="cannot split"):
        propose_ladder(tiny, "orchid", "butterfly", steps=3)
    with_33 = HISTORY + [{"run": "TEST", "kind": "bridge", "width": 832, "height": 480, "frames": 33,
                          "exec_s": 250.0}]
    with pytest.raises(LadderError, match="budget"):
        propose_ladder(sample(), "butterfly", "phoenix", history=with_33, max_gpu_s=10)
    _, ok = propose_ladder(sample(), "butterfly", "phoenix", history=with_33, max_gpu_s=1000)
    assert abs(ok["added_gpu_s"] - (51.7 + 2 * 250.0 - 496.0)) < 1.0  # one edit + two short bridges - original


def test_added_cost_from_history_or_no_data():
    _, report = propose_ladder(sample(), "butterfly", "phoenix", history=HISTORY)
    assert report["added_gpu_s"] is None  # no measured 33-frame bridges yet -> NO DATA, not a guess
    with pytest.raises(LadderError, match="no measured history"):
        propose_ladder(sample(), "butterfly", "phoenix", history=HISTORY, max_gpu_s=5000)


def test_cli_risk_and_propose(tmp_path, capsys):
    assert cli.main(["ladder-risk", str(SAMPLE)]) == 0
    risks = json.loads(capsys.readouterr().out)
    assert [r["transition"] for r in risks] == ["orchid->butterfly", "butterfly->phoenix"]
    out = tmp_path / "proposal.yaml"
    assert cli.main(["ladder-propose", str(SAMPLE), "--split", "butterfly->phoenix", "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert text.startswith("# PROPOSAL") and "butterfly_to_phoenix_1" in text
    Storyboard.model_validate(yaml.safe_load(text))
    assert cli.main(["ladder-propose", str(SAMPLE), "--split", "butterfly->phoenix", "--out", str(out)]) == 2
