"""F06 generated anchors -> unchanged Wan bridge path (offline, fake ComfyUI)."""
from __future__ import annotations

import copy

import pytest

from fake_comfy import FakeComfy
from morph_studio.anchors import AnchorSpec, run_anchor_chain
from morph_studio.bridge import BridgeError
from morph_studio.dag import compile_plan
from morph_studio.pipeline import run_bridge_stage
from morph_studio.schema import load_storyboard

from conftest import REPO

T2I = "configs/profiles/test_t2i.binding.json"
EDIT = "configs/profiles/test_edit.binding.json"


def fake_probe(expected):
    def probe(path):
        return {"width": expected["width"], "height": expected["height"],
                "frame_count": expected["frames"], "fps": expected["fps"], "codec": "h264"}
    return probe


def dag(image_repo):
    sb = load_storyboard(REPO / "configs/sequences/organic-machines.yaml")
    return compile_plan(sb, repo_root=image_repo, profiles={"text_to_image": T2I, "reference_edit": EDIT})


def anchors(image_repo, fake, plan, submit=True):
    specs = [AnchorSpec(t["anchor"], t["method"], t["positive_prompt"], t["seed"],
                        reference=t["reference"]) for t in plan["tasks"].values() if t["kind"] == "anchor"]
    return run_anchor_chain(specs, client=fake.client(), runs_root=image_repo / "outputs/runs",
                            t2i_profile=T2I, edit_profile=EDIT, width=832, height=480,
                            repo_root=image_repo, poll_seconds=0, submit=submit)


def bridges(image_repo, fake, plan, jobs, **kw):
    task = plan["tasks"]["bridge:orchid->butterfly"]
    return run_bridge_stage(plan, jobs, client=fake.client(), runs_root=image_repo / "outputs/runs",
                            repo_root=image_repo, poll_seconds=0, probe=fake_probe(task), **kw)


def test_bridges_consume_generated_anchor_bytes(image_repo):
    fake = FakeComfy()
    plan = dag(image_repo)
    chain = anchors(image_repo, fake, plan)
    assert chain.complete
    result = bridges(image_repo, fake, plan, chain.jobs, submit=True)
    assert result.complete, {k: j.record.get("error") for k, j in result.jobs.items()}
    ab, bc = result.jobs["bridge:orchid->butterfly"], result.jobs["bridge:butterfly->phoenix"]
    sha = {k: j.record["image"]["sha256"] for k, j in chain.jobs.items()}
    assert ab.record["anchors"]["start_image"]["sha256"] == sha["orchid"]
    assert ab.record["anchors"]["end_image"]["sha256"] == sha["butterfly"]
    assert bc.record["anchors"]["start_image"]["sha256"] == sha["butterfly"]
    assert bc.record["anchors"]["end_image"]["sha256"] == sha["phoenix"]
    assert ab.record["values"]["length"] == 65 and ab.record["values"]["seed"] == 201
    assert ab.record["values"]["width"] == 832 and ab.record["pipeline"]["candidates_requested"] == 3
    assert "assets" not in ab.record["anchors"]["start_image"]["path"]
    posts = fake.prompt_posts
    assert posts == 5
    again = bridges(image_repo, fake, plan, chain.jobs, submit=True)
    assert again.complete and fake.prompt_posts == posts


def test_without_consent_bridges_stop_validated(image_repo):
    fake = FakeComfy()
    plan = dag(image_repo)
    chain = anchors(image_repo, fake, plan)
    posts = fake.prompt_posts
    result = bridges(image_repo, fake, plan, chain.jobs)
    assert {j.state for j in result.jobs.values()} == {"validated"} and fake.prompt_posts == posts


def test_unverified_anchor_blocks_bridge(image_repo):
    fake = FakeComfy()
    plan = dag(image_repo)
    chain = anchors(image_repo, fake, plan, submit=False)  # only orchid validated
    result = bridges(image_repo, fake, plan, chain.jobs, submit=True)
    assert set(result.blocked) == {"bridge:orchid->butterfly", "bridge:butterfly->phoenix"}
    assert not result.jobs


def test_missing_wan_model_fails_validation_without_substitution(image_repo):
    fake = FakeComfy()
    plan = dag(image_repo)
    chain = anchors(image_repo, fake, plan)
    fake.object_info = copy.deepcopy(fake.object_info)
    fake.object_info["UNETLoader"]["input"]["required"]["unet_name"][0] = ["qwen_image_fp8_e4m3fn.safetensors"]
    posts = fake.prompt_posts
    with pytest.raises(BridgeError, match="object_info validation failed"):
        bridges(image_repo, fake, plan, chain.jobs, submit=True)
    assert fake.prompt_posts == posts


def test_busy_queue_refuses_bridge(image_repo):
    fake = FakeComfy()
    plan = dag(image_repo)
    chain = anchors(image_repo, fake, plan)
    fake.running.append("owner-job")
    with pytest.raises(BridgeError, match="refusing to stack"):
        bridges(image_repo, fake, plan, chain.jobs, submit=True)
