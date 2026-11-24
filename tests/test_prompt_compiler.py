"""F13 choreography → deterministic bridge prompts; plan hash preserved without it."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from morph_studio import cli
from morph_studio.dag import compile_plan
from morph_studio.prompt_compiler import PromptError, compile_bridge_prompts, variants
from morph_studio.schema import Storyboard, Transition, load_storyboard

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "configs/sequences/organic-machines.yaml"
CHOREO = {
    "correspondences": [{"source": "the glass wings", "target": "silver feathered wings"},
                        {"source": "the slender body", "target": "the phoenix's chest and tail"}],
    "phases": ["the wings widen", "feathers assemble from the wing lattice", "the head and tail form"],
    "camera": "static",
    "negative": ["side view", "Blurry", "walking"],
}


def transition(**extra) -> Transition:
    data = {"from": "butterfly", "to": "phoenix", "duration_beats": 8,
            "prompt": "  Continuous physical\nmetamorphosis\tof the butterfly into a phoenix  ", **extra}
    return Transition.model_validate(data)


def test_without_choreography_prompt_is_cleaned_prose_and_no_negative():
    assert compile_bridge_prompts(transition()) == (
        "Continuous physical metamorphosis of the butterfly into a phoenix", None)


def test_golden_compiled_prompts():
    positive, negative = compile_bridge_prompts(transition(choreography=CHOREO))
    assert positive == (
        "Continuous physical metamorphosis of the butterfly into a phoenix. "
        "Correspondences: the glass wings becomes silver feathered wings; "
        "the slender body becomes the phoenix's chest and tail. "
        "Sequence: first the wings widen, then feathers assemble from the wing lattice, "
        "finally the head and tail form. "
        "The camera is static and front-facing. "
        "The subject stays centered and keeps the same size. "
        "One continuous shot with no cuts, dissolves or crossfades.")
    assert negative.startswith("cut, scene change, dissolve, crossfade")
    assert negative.endswith("blurry, side view, walking")  # 'Blurry' deduplicated with the default
    assert compile_bridge_prompts(transition(choreography=CHOREO)) == (positive, negative)


def test_framing_switches_and_single_phase():
    positive, _ = compile_bridge_prompts(transition(choreography={
        "phases": ["everything melts"], "camera": "slow_push", "keep_centered": False, "keep_scale": False}))
    assert "Sequence: everything melts." in positive and "The camera pushes in slowly." in positive
    assert "The subject" not in positive


def test_length_cap_and_unknown_camera():
    with pytest.raises(PromptError, match="limit 1500"):
        compile_bridge_prompts(transition(choreography={"negative": [f"{i}" + "x" * 180 for i in range(9)]}))
    with pytest.raises(ValidationError):
        transition(choreography={"camera": "drone_dive"})


def test_sample_storyboard_plan_hash_unchanged():
    plan = compile_plan(load_storyboard(SAMPLE), repo_root=REPO)
    assert plan["plan_sha256"] == "ba2d9dbedb6189beaef6c39a8e5e2a06caef260a2729620c7e8ffa1071bb4bdf"
    assert all("negative_prompt" not in t for t in plan["tasks"].values() if t["kind"] == "bridge")


def test_choreographed_bridge_task_gets_both_prompts():
    data = yaml.safe_load(SAMPLE.read_text(encoding="utf-8"))
    data["transitions"][1]["choreography"] = CHOREO
    plan = compile_plan(Storyboard.model_validate(data), repo_root=REPO)
    task = plan["tasks"]["bridge:butterfly->phoenix"]
    assert "Correspondences:" in task["positive_prompt"] and "side view" in task["negative_prompt"]
    assert plan["plan_sha256"] != "ba2d9dbedb6189beaef6c39a8e5e2a06caef260a2729620c7e8ffa1071bb4bdf"


def test_negative_reaches_wan_graph(image_repo):
    from fake_comfy import FakeComfy
    from test_pipeline_bridges import EDIT, T2I, anchors, fake_probe
    from morph_studio.pipeline import run_bridge_stage
    data = yaml.safe_load(SAMPLE.read_text(encoding="utf-8"))
    data["transitions"][1]["choreography"] = CHOREO
    plan = compile_plan(Storyboard.model_validate(data), repo_root=image_repo,
                        profiles={"text_to_image": T2I, "reference_edit": EDIT})
    fake = FakeComfy()
    chain = anchors(image_repo, fake, plan)
    result = run_bridge_stage(plan, chain.jobs, client=fake.client(), runs_root=image_repo / "outputs/runs",
                              repo_root=image_repo, poll_seconds=0,
                              probe=fake_probe(plan["tasks"]["bridge:butterfly->phoenix"]), submit=True)
    graph = json.loads((result.jobs["bridge:butterfly->phoenix"].dir / "workflow.api.json").read_text(encoding="utf-8"))
    assert graph["78"]["inputs"]["text"] == plan["tasks"]["bridge:butterfly->phoenix"]["negative_prompt"]
    first = json.loads((result.jobs["bridge:orchid->butterfly"].dir / "workflow.api.json").read_text(encoding="utf-8"))
    orig = json.loads((REPO / "workflows/03_wan22_flf2v.json").read_text(encoding="utf-8"))
    assert first["78"]["inputs"]["text"] == orig["78"]["inputs"]["text"]  # un-choreographed: export default


def test_variants_and_cli_preview(tmp_path, capsys):
    ab = variants(transition(choreography=CHOREO), seed=202)
    assert [v["variant"] for v in ab] == ["A-prose", "B-choreography"] and {v["seed"] for v in ab} == {202}
    data = yaml.safe_load(SAMPLE.read_text(encoding="utf-8"))
    data["transitions"][1]["choreography"] = CHOREO
    sb = tmp_path / "sb.yaml"
    sb.write_text(yaml.safe_dump(data), encoding="utf-8")
    assert cli.main(["prompt-preview", str(sb), "--variants"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["bridges"][0]["negative"] == "(workflow default)" and out["bridges"][1]["choreography"]
    assert len(out["bridges"][1]["ab_plan"]) == 2
