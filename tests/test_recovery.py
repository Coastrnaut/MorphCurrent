"""F07 crash-at-every-transition resume, run manifest, model hash cache, VRAM sampler."""
from __future__ import annotations

import json

import pytest

from fake_comfy import FakeComfy
from morph_studio import bridge as bridge_mod
from morph_studio.anchors import AnchorRequest, plan_anchor, run_anchor
from morph_studio.dag import compile_plan
from morph_studio.provenance import hash_models, models_in_graph, recorded_hashes
from morph_studio.run_manifest import RunManifest
from morph_studio.schema import load_storyboard
from morph_studio.vram import VramSampler, parse

from conftest import REPO

T2I = "configs/profiles/test_t2i.binding.json"
CRASH_STATES = ["uploaded", "validated", "submitting", "submitted", "completed", "downloaded", "verified"]


class Crash(BaseException):
    """Simulated hard stop (not caught by any except Exception)."""


@pytest.mark.parametrize("state", CRASH_STATES)
def test_crash_after_each_transition_resumes_with_one_prompt(image_repo, monkeypatch, state):
    fake = FakeComfy()
    original = bridge_mod.BridgeJob.transition
    armed = {"on": True}

    def crashing(self, new_state, event=None, **data):
        original(self, new_state, event, **data)  # persisted first, like a real crash after save
        if armed["on"] and new_state == state:
            armed["on"] = False
            raise Crash(new_state)

    monkeypatch.setattr(bridge_mod.BridgeJob, "transition", crashing)
    request = AnchorRequest(profile=T2I, positive_prompt="orchid", seed=5, width=832, height=480)

    def go():
        client = fake.client()
        plan = plan_anchor(request, client.object_info(), repo_root=image_repo)
        return run_anchor(plan, client, image_repo / "outputs/runs", submit=True, poll_seconds=0)

    with pytest.raises(Crash):
        go()
    job = go()
    assert job.state == "verified" and fake.prompt_posts == 1


def test_run_manifest_atomic_and_keyed_by_plan(image_repo):
    plan = compile_plan(load_storyboard(REPO / "configs/sequences/organic-machines.yaml"), repo_root=image_repo)
    m = RunManifest.open(image_repo / "outputs/runs", plan, storyboard="x.yaml", repo_head="abc")
    assert m.dir.name == f"run-{plan['plan_sha256'][:16]}"
    assert m.data["stages"]["anchor:orchid"] == {"state": "pending"}
    (m.dir / "manifest.json.tmp").write_text("garbage")  # leftover from a crash
    m.record_stage("anchor:orchid", state="blocked", reason="no profile")
    again = RunManifest.open(image_repo / "outputs/runs", plan)
    assert again.data["stages"]["anchor:orchid"]["state"] == "blocked"
    assert (m.dir / "plan.json").exists()
    other = dict(plan, plan_sha256="0" * 64)
    assert RunManifest.open(image_repo / "outputs/runs", other).dir != m.dir


def test_model_hash_cache_reuses_unchanged_files(tmp_path):
    root = tmp_path / "models"
    (root / "vae").mkdir(parents=True)
    (root / "vae" / "v.safetensors").write_bytes(b"weights")
    calls = []

    def hasher(path):
        calls.append(path)
        return "f" * 64

    cache = tmp_path / "hashes.json"
    pairs = [("vae", "v.safetensors"), ("diffusion_models", "missing.safetensors")]
    first = hash_models(pairs, root, cache, hasher)
    assert first["vae/v.safetensors"]["status"] == "hashed" and first["diffusion_models/missing.safetensors"]["status"] == "missing"
    second = hash_models(pairs, root, cache, hasher)
    assert second["vae/v.safetensors"]["status"] == "cached" and len(calls) == 1
    assert recorded_hashes({"3.vae_name": "v.safetensors", "1.unet_name": "x"}, cache, root) == {
        "3.vae_name": "f" * 64, "1.unet_name": "NOT RECORDED"}
    (root / "vae" / "v.safetensors").write_bytes(b"changed weights")
    assert recorded_hashes({"3.vae_name": "v.safetensors"}, cache, root)["3.vae_name"] == "NOT RECORDED"


def test_models_in_wan_graph():
    graph = json.loads((REPO / "workflows/03_wan22_flf2v.json").read_text(encoding="utf-8"))
    pairs = models_in_graph(graph)
    assert ("vae", "wan_2.1_vae.safetensors") in pairs and len(pairs) == 4


def test_models_hash_cli_refuses_busy_queue(monkeypatch, capsys):
    from morph_studio import cli
    fake = FakeComfy()
    fake.running.append("owner-job")
    monkeypatch.setattr(cli, "ComfyClient", lambda url: fake.client())
    assert cli.main(["models-hash", "--confirm-io"]) == 2
    assert "queue" in capsys.readouterr().err


def test_vram_sampler_summary():
    series = iter(["0, 1000, 49140", "0, 30000, 49140", "0, 42000, 49140"] + ["0, 2000, 49140"] * 100)
    sampler = VramSampler(interval=0.01, query=lambda: next(series))
    with sampler:
        pass
    s = sampler.summary()
    assert s["status"] == "sampled" and s["baseline_mib"] == 1000 and s["peak_mib"] >= 2000
    assert s["total_mib"] == 49140 and "all processes" in s["label"]
    assert parse("0, 5, 10\n1, 7, 10", gpu_index=1) == (7, 10)


def test_vram_sampler_without_nvidia_smi_is_not_measured():
    sampler = VramSampler(interval=0.01, query=lambda: None)
    with sampler:
        pass
    assert sampler.summary()["status"] == "NOT MEASURED"
