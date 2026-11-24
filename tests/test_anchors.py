"""F03 anchor generation against a fake ComfyUI (offline, no GPU)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from fake_comfy import FakeComfy, make_png
from image_graphs import real_object_info
from morph_studio import cli
from morph_studio.anchors import AnchorError, AnchorRequest, anchor_image_path, plan_anchor, run_anchor
from morph_studio.bridge import BridgeError, load_job
from morph_studio.cache import sha256_file
from morph_studio.comfy_client import ComfyError
from morph_studio.workflow_adapter import WorkflowBindingError

T2I = "configs/profiles/test_t2i.binding.json"


def req(**kw) -> AnchorRequest:
    base = dict(profile=T2I, positive_prompt="A luminous glass orchid", negative_prompt="blurry",
                seed=101, width=832, height=480, label="orchid")
    base.update(kw)
    return AnchorRequest(**base)


def run(image_repo, fake, request=None, **kw):
    client = fake.client()
    plan = plan_anchor(request or req(), client.object_info(), repo_root=image_repo)
    return run_anchor(plan, client, image_repo / "outputs/runs", poll_seconds=0, **kw)


def test_without_consent_stops_validated(image_repo):
    fake = FakeComfy()
    job = run(image_repo, fake)
    assert job.state == "validated" and fake.prompt_posts == 0


def test_generates_verified_anchor_with_manifest(image_repo):
    fake = FakeComfy()
    job = run(image_repo, fake, submit=True)
    assert job.state == "verified", job.record.get("error")
    rec = job.record
    assert rec["kind"] == "anchor_image" and rec["method"] == "text_to_image" and rec["parent"] is None
    assert rec["image"]["width"] == 832 and rec["image"]["height"] == 480 and rec["image"]["format"] == "png"
    assert rec["values"]["seed"] == 101 and rec["values"]["positive_prompt"].startswith("A luminous")
    assert rec["values"]["filename_prefix"] == f"morphcurrent/{rec['job_id'][:16]}/anchor"
    assert rec["model_sha256"] == "NOT RECORDED" and "1.unet_name" in rec["models"]
    path = anchor_image_path(job)
    assert sha256_file(path) == rec["image"]["sha256"]
    assert fake.prompt_posts == 1


def test_identical_request_is_a_cache_hit(image_repo):
    fake = FakeComfy()
    first = run(image_repo, fake, submit=True)
    calls = len(fake.calls)
    # Planning needs object_info; the executor itself must make no further calls.
    client = fake.client()
    plan = plan_anchor(req(), fake.object_info, repo_root=image_repo)
    again = run_anchor(plan, client, image_repo / "outputs/runs", submit=True, poll_seconds=0)
    assert again.dir == first.dir and again.state == "verified" and len(fake.calls) == calls


def test_seed_change_is_a_new_job(image_repo):
    fake = FakeComfy()
    a = run(image_repo, fake, submit=True)
    b = run(image_repo, fake, req(seed=102), submit=True)
    assert a.dir != b.dir and a.record["image"]["sha256"] != b.record["image"]["sha256"]


def test_missing_model_fails_before_submission(image_repo):
    fake = FakeComfy(object_info=real_object_info())  # real machine: Qwen weights absent
    with pytest.raises(BridgeError, match="object_info validation failed"):
        run(image_repo, fake, submit=True)
    job = load_job(next((image_repo / "outputs/runs").iterdir()))
    assert job.state == "failed" and fake.prompt_posts == 0
    assert any("qwen_image_fp8_e4m3fn.safetensors" in e for e in job.record["events"][-1]["errors"])


def test_workflow_hash_drift_refuses_plan(image_repo):
    wf = image_repo / "workflows/test_t2i.json"
    graph = json.loads(wf.read_text(encoding="utf-8"))
    graph["8"]["inputs"]["steps"] = 30
    wf.write_text(json.dumps(graph), encoding="utf-8")
    with pytest.raises(WorkflowBindingError, match="hash"):
        plan_anchor(req(), None, repo_root=image_repo)


def test_wrong_profile_capability_refused(image_repo):
    with pytest.raises(WorkflowBindingError, match="needs a text_to_image profile"):
        plan_anchor(req(profile="configs/profiles/test_edit.binding.json"), None, repo_root=image_repo)


def test_seed_is_required():
    with pytest.raises(ValueError):
        AnchorRequest(profile=T2I, positive_prompt="x")


@pytest.mark.parametrize("override,images,match", [
    (b"\x00\x00\x00\x18ftypmp42", 1, "not a PNG"),
    (make_png(832, 480)[:-30], 1, "invalid"),
    (make_png(640, 368), 1, "dimensions"),
    (None, 0, "exactly one"),
    (None, 2, "exactly one"),
])
def test_bad_outputs_fail_closed(image_repo, override, images, match):
    fake = FakeComfy()
    fake.image_override = override
    fake.images_per_save = images
    if images == 0:
        with pytest.raises(BridgeError, match="history has no files|exactly one"):
            run(image_repo, fake, submit=True)
        return
    with pytest.raises(BridgeError, match=match):
        run(image_repo, fake, submit=True)


def test_lost_prompt_response_does_not_double_submit(image_repo):
    fake = FakeComfy()
    fake.drop_next_prompt_response = True
    with pytest.raises(ComfyError):
        run(image_repo, fake, submit=True)
    assert load_job(next((image_repo / "outputs/runs").iterdir())).state == "submitting"
    job = run(image_repo, fake, submit=True)
    assert job.state == "verified" and fake.prompt_posts == 1


def test_execution_error_then_retry(image_repo):
    fake = FakeComfy()
    fake.fail_execution = True
    with pytest.raises(BridgeError, match="execution failed"):
        run(image_repo, fake, submit=True)
    with pytest.raises(BridgeError, match="pass retry"):
        run(image_repo, fake, submit=True)
    fake.fail_execution = False
    assert run(image_repo, fake, submit=True, retry=True).state == "verified"


def test_tampered_anchor_is_rejected(image_repo):
    job = run(image_repo, FakeComfy(), submit=True)
    (job.dir / job.record["image"]["local_path"]).write_bytes(make_png(832, 480, (1, 2, 3)))
    with pytest.raises(AnchorError, match="SHA-256"):
        anchor_image_path(load_job(job.dir))


def test_busy_queue_refused(image_repo):
    fake = FakeComfy()
    fake.running.append("owner-render")
    with pytest.raises(BridgeError, match="refusing to stack"):
        run(image_repo, fake, submit=True)
    assert fake.prompt_posts == 0


def test_cli_anchor_validates_without_consent(image_repo, monkeypatch, capsys):
    fake = FakeComfy()
    monkeypatch.chdir(image_repo)
    monkeypatch.setattr(cli, "ComfyClient", lambda url: fake.client())
    code = cli.main(["anchor", "--profile", T2I, "--prompt", "orchid", "--seed", "7",
                     "--width", "832", "--height", "480"])
    out = json.loads(capsys.readouterr().out)
    assert code == 0 and out["state"] == "validated" and fake.prompt_posts == 0
    assert cli.main(["anchor-status", out["job_dir"]]) == 0
