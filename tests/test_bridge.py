"""Bridge dispatch against a stateful fake ComfyUI (httpx.MockTransport); no GPU."""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import httpx
import pytest

from fake_comfy import make_png
from morph_studio.bridge import (
    BridgeError,
    BridgeRequest,
    cancel_bridge,
    load_job,
    plan_bridge,
    run_bridge,
)
from morph_studio.comfy_client import ComfyClient
from morph_studio.media import ProbeUnavailable, probe_video

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "tests" / "fixtures" / "object_info_wan22_flf2v.json"
# Two distinct small image files; bridge planning hashes bytes, it does not decode them.
_ANCHOR_DIR = Path(tempfile.mkdtemp(prefix="mc_bridge_anchors_"))
START = str(_ANCHOR_DIR / "start.jpg")
END = str(_ANCHOR_DIR / "end.jpg")
Path(START).write_bytes(make_png(64, 32, (200, 40, 40)))
Path(END).write_bytes(make_png(64, 32, (40, 40, 200)))
VIDEO_BYTES = b"\x00\x00\x00\x18ftypmp42fake-video"


class FakeComfy:
    """Just enough ComfyUI 0.46 behaviour: uploads extend LoadImage choices,
    prompts honour client prompt_id, history appears after ``polls_to_finish``."""

    def __init__(self):
        self.object_info = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.uploads: dict[str, bytes] = {}
        self.prompts: dict[str, dict] = {}
        self.pending: list[str] = []
        self.running: list[str] = []
        self.history: dict[str, dict] = {}
        self.calls: list[str] = []
        self.polls_to_finish = 1
        self.fail_execution = False
        self.drop_next_prompt_response = False  # store prompt, then lose the connection
        self.refuse_next_prompt_connection = False  # connection fails before receipt
        self.upload_rename: str | None = None
        self.interrupted: list[str] = []
        self.deleted: list[str] = []
        self._polls: dict[str, int] = {}

    def _image_choices(self) -> list:
        return self.object_info["LoadImage"]["input"]["required"]["image"][0]

    def handler(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        self.calls.append(f"{request.method} {path}")
        if path == "/system_stats":
            return httpx.Response(200, json={
                "system": {"comfyui_version": "0.46.0", "pytorch_version": "test", "argv": []},
                "devices": [{"name": "cuda:0 fake", "vram_total": 1, "vram_free": 1}]})
        if path == "/object_info":
            return httpx.Response(200, json=self.object_info)
        if path == "/upload/image":
            body = request.read()
            name = body.split(b'filename="', 1)[1].split(b'"', 1)[0].decode()
            if self.upload_rename:
                name = self.upload_rename
            self.uploads[name] = body
            if name not in self._image_choices():
                self._image_choices().append(name)
            return httpx.Response(200, json={"name": name, "subfolder": "", "type": "input"})
        if path == "/queue" and request.method == "GET":
            return httpx.Response(200, json={
                "queue_running": [[0, pid, {}, {}, []] for pid in self.running],
                "queue_pending": [[1, pid, {}, {}, []] for pid in self.pending]})
        if path == "/queue" and request.method == "POST":
            for pid in json.loads(request.read())["delete"]:
                self.deleted.append(pid)
                self.pending.remove(pid)
            return httpx.Response(200)
        if path == "/interrupt":
            self.interrupted.append(json.loads(request.read())["prompt_id"])
            return httpx.Response(200)
        if path == "/prompt":
            if self.refuse_next_prompt_connection:
                self.refuse_next_prompt_connection = False
                raise httpx.ConnectError("refused", request=request)
            body = json.loads(request.read())
            pid = body.get("prompt_id")
            self.prompts[pid] = body["prompt"]
            self.pending.append(pid)
            if self.drop_next_prompt_response:
                self.drop_next_prompt_response = False
                raise httpx.ReadError("connection reset", request=request)
            return httpx.Response(200, json={"prompt_id": pid, "number": 1, "node_errors": {}})
        if path.startswith("/history/"):
            pid = path.rsplit("/", 1)[1]
            if pid in self.pending or pid in self.running:
                self._polls[pid] = self._polls.get(pid, 0) + 1
                if self._polls[pid] >= self.polls_to_finish:
                    self._finish(pid)
            return httpx.Response(200, json={pid: self.history[pid]} if pid in self.history else {})
        if path == "/view":
            return httpx.Response(200, content=VIDEO_BYTES)
        return httpx.Response(404)

    def _finish(self, pid: str) -> None:
        for queue in (self.pending, self.running):
            if pid in queue:
                queue.remove(pid)
        graph = self.prompts[pid]
        prefix = graph["83"]["inputs"]["filename_prefix"]
        subfolder, _, stem = prefix.rpartition("/")
        if self.fail_execution:
            self.history[pid] = {"status": {"status_str": "error", "completed": False,
                                            "messages": [["execution_error", {"node_id": "84"}]]},
                                 "outputs": {}}
            return
        self.history[pid] = {
            "status": {"status_str": "success", "completed": True, "messages": [
                ["execution_start", {"prompt_id": pid, "timestamp": 1_000_000}],
                ["execution_success", {"prompt_id": pid, "timestamp": 1_183_500}]]},
            "outputs": {"83": {"images": [{"filename": f"{stem}_00001_.mp4", "subfolder": subfolder,
                                           "type": "output"}], "animated": [True]}}}


@pytest.fixture()
def fake():
    return FakeComfy()


@pytest.fixture()
def client(fake):
    http = httpx.Client(base_url="http://127.0.0.1:8188", transport=httpx.MockTransport(fake.handler))
    with http, ComfyClient(http_client=http) as comfy:
        yield comfy


def request(**overrides) -> BridgeRequest:
    values = {"start_image": START, "end_image": END, "seed": 42, "length": 65,
              "width": 640, "height": 368, "fps": 16}
    values.update(overrides)
    return BridgeRequest(**values)


def good_probe(path: Path) -> dict:
    return {"width": 640, "height": 368, "frame_count": 65, "fps": 16.0, "codec": "h264"}


def run(plan, client, root, **kw):
    kw.setdefault("poll_seconds", 0)
    kw.setdefault("timeout", 5)
    kw.setdefault("probe", good_probe)
    return run_bridge(plan, client, root, **kw)


def test_plan_is_deterministic_and_content_addressed(fake):
    oi = fake.object_info
    a = plan_bridge(request(), oi, REPO)
    b = plan_bridge(request(), oi, REPO)
    assert a.job_id == b.job_id
    assert plan_bridge(request(seed=43), oi, REPO).job_id != a.job_id
    assert plan_bridge(request(start_image=END, end_image=START), oi, REPO).job_id != a.job_id
    assert a.graph["80"]["inputs"]["image"] == a.upload_names["start_image"]
    assert a.upload_names["start_image"].startswith("mc_") and a.upload_names["start_image"].endswith(".jpg")
    assert a.graph["83"]["inputs"]["filename_prefix"] == f"morphcurrent/{a.job_id[:16]}/bridge"
    assert a.graph["84"]["inputs"]["noise_seed"] == 42
    # unset roles keep the exported graph's values
    assert a.values["positive_prompt"].startswith("A translucent glass orchid")
    assert a.models["76.unet_name"] == "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"


def test_plan_rejects_invalid_values_before_contacting_comfy(fake):
    with pytest.raises(ValueError, match=r"1 \+ k\*4"):
        plan_bridge(request(length=64), fake.object_info, REPO)
    with pytest.raises(FileNotFoundError):
        plan_bridge(request(start_image=str(_ANCHOR_DIR / "missing.jpg")), fake.object_info, REPO)


def test_without_confirm_gpu_stops_after_validation(fake, client, tmp_path):
    job = run(plan_bridge(request(), fake.object_info, REPO), client, tmp_path)
    assert job.state == "validated"
    assert "POST /prompt" not in fake.calls
    assert len(fake.uploads) == 2
    assert (job.dir / "workflow.api.json").is_file()
    assert [e["event"] for e in job.record["events"]] == ["planned", "uploaded", "validated"]


def test_full_render_downloads_and_verifies(fake, client, tmp_path):
    plan = plan_bridge(request(), fake.object_info, REPO)
    job = run(plan, client, tmp_path, submit=True)
    assert job.state == "verified"
    pid = job.record["prompt_id"]
    assert list(fake.prompts) == [pid]  # client-chosen ID honoured, one submission
    assert fake.prompts[pid] == plan.graph
    [output] = job.record["outputs"]
    local = job.dir / output["local_path"]
    assert local.read_bytes() == VIDEO_BYTES and output["bytes"] == len(VIDEO_BYTES)
    assert job.record["timings"]["execution_seconds"] == 183.5
    assert job.record["verification"]["status"] == "pass"
    assert job.record["comfyui"]["validated"]["comfyui_version"] == "0.46.0"
    assert "NOT MEASURED" in job.record["comfyui"]["peak_vram"]
    on_disk = json.loads((job.dir / "job.json").read_text(encoding="utf-8"))
    assert on_disk["state"] == "verified"


def test_verified_job_is_reused_without_new_gpu_work(fake, client, tmp_path):
    plan = plan_bridge(request(), fake.object_info, REPO)
    run(plan, client, tmp_path, submit=True)
    fake.calls.clear()
    job = run(plan_bridge(request(), fake.object_info, REPO), client, tmp_path, submit=True)
    assert job.state == "verified"
    assert fake.calls == []


def test_lost_response_is_reconciled_without_duplicate(fake, client, tmp_path):
    plan = plan_bridge(request(), fake.object_info, REPO)
    fake.drop_next_prompt_response = True
    with pytest.raises(Exception):
        run(plan, client, tmp_path, submit=True)
    job = load_job(tmp_path / plan.job_id[:16])
    assert job.state == "submitting" and job.record["prompt_id"] in fake.prompts
    job = run(plan, client, tmp_path, submit=True)
    assert job.state == "verified"
    assert len(fake.prompts) == 1
    assert any(e["event"] == "submit_confirmed_on_resume" for e in job.record["events"])


def test_unreceived_submit_is_resent_with_same_prompt_id(fake, client, tmp_path):
    plan = plan_bridge(request(), fake.object_info, REPO)
    fake.refuse_next_prompt_connection = True
    with pytest.raises(Exception):
        run(plan, client, tmp_path, submit=True)
    saved = load_job(tmp_path / plan.job_id[:16]).record["prompt_id"]
    job = run(plan, client, tmp_path, submit=True)
    assert job.state == "verified" and list(fake.prompts) == [saved]


def test_execution_error_fails_then_retry_resubmits(fake, client, tmp_path):
    plan = plan_bridge(request(), fake.object_info, REPO)
    fake.fail_execution = True
    with pytest.raises(BridgeError, match="execution failed"):
        run(plan, client, tmp_path, submit=True)
    with pytest.raises(BridgeError, match="pass retry"):
        run(plan, client, tmp_path, submit=True)
    fake.fail_execution = False
    job = run(plan, client, tmp_path, submit=True, retry=True)
    assert job.state == "verified" and len(fake.prompts) == 2


def test_prompt_lost_after_restart_fails_closed(fake, client, tmp_path):
    plan = plan_bridge(request(), fake.object_info, REPO)
    fake.polls_to_finish = 10**6
    with pytest.raises(TimeoutError):
        run(plan, client, tmp_path, submit=True, timeout=0.01)
    fake.pending.clear()  # ComfyUI restarted: in-memory queue and history gone
    with pytest.raises(BridgeError, match="neither /history nor /queue"):
        run(plan, client, tmp_path, submit=True)


def test_busy_queue_is_refused(fake, client, tmp_path):
    fake.pending.append("someone-elses-job")
    plan = plan_bridge(request(), fake.object_info, REPO)
    with pytest.raises(BridgeError, match="queue has 1"):
        run(plan, client, tmp_path, submit=True)
    assert load_job(tmp_path / plan.job_id[:16]).state == "validated"


def test_upload_renamed_by_comfy_fails(fake, client, tmp_path):
    fake.upload_rename = "mc_other (1).jpg"
    with pytest.raises(BridgeError, match="already uses that name"):
        run(plan_bridge(request(), fake.object_info, REPO), client, tmp_path)


def test_verification_mismatch_and_missing_ffprobe(fake, client, tmp_path):
    plan = plan_bridge(request(), fake.object_info, REPO)
    with pytest.raises(BridgeError, match="differ from the request"):
        run(plan, client, tmp_path, submit=True,
            probe=lambda p: {**good_probe(p), "frame_count": 49})
    other = plan_bridge(request(seed=7), fake.object_info, REPO)

    def no_probe(path):
        raise ProbeUnavailable("ffprobe not found on PATH")
    job = run(other, client, tmp_path, submit=True, probe=no_probe)
    assert job.state == "downloaded" and job.record["verification"]["status"] == "skipped"


def test_cancel_pending_and_running(fake, client, tmp_path):
    fake.polls_to_finish = 10**6
    plan = plan_bridge(request(), fake.object_info, REPO)
    with pytest.raises(TimeoutError):
        run(plan, client, tmp_path, submit=True, timeout=0.01)
    job_dir = tmp_path / plan.job_id[:16]
    pid = load_job(job_dir).record["prompt_id"]
    assert cancel_bridge(job_dir, client).state == "cancelled"
    assert fake.deleted == [pid] and fake.interrupted == []

    plan2 = plan_bridge(request(seed=9), fake.object_info, REPO)
    with pytest.raises(TimeoutError):
        run(plan2, client, tmp_path, submit=True, timeout=0.01)
    job_dir2 = tmp_path / plan2.job_id[:16]
    pid2 = load_job(job_dir2).record["prompt_id"]
    fake.pending.remove(pid2)
    fake.running.append(pid2)
    cancel_bridge(job_dir2, client)
    assert fake.interrupted == [pid2]  # targeted, never a global interrupt


def test_tampered_job_workflow_is_rejected(fake, client, tmp_path):
    plan = plan_bridge(request(), fake.object_info, REPO)
    job = run(plan, client, tmp_path)
    graph = json.loads((job.dir / "workflow.api.json").read_text(encoding="utf-8"))
    graph["84"]["inputs"]["cfg"] = 7
    (job.dir / "workflow.api.json").write_text(json.dumps(graph), encoding="utf-8")
    with pytest.raises(BridgeError, match="no longer matches"):
        run(plan, client, tmp_path)


def test_cli_bridge_dry_run(fake, tmp_path, monkeypatch, capsys):
    import morph_studio.cli as cli
    http = httpx.Client(base_url="http://127.0.0.1:8188", transport=httpx.MockTransport(fake.handler))
    monkeypatch.setattr(cli, "ComfyClient", lambda url: ComfyClient(http_client=http))
    monkeypatch.chdir(REPO)
    code = cli.main(["bridge", "--start", START, "--end", END, "--seed", "5",
                     "--length", "65", "--runs-root", str(tmp_path)])
    assert code == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["state"] == "validated" and summary["values"]["seed"] == 5
    assert "POST /prompt" not in fake.calls
    assert cli.main(["bridge-status", summary["job_dir"]]) == 0


@pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("ffprobe")),
                    reason="native ffmpeg/ffprobe not on PATH")
def test_probe_video_on_synthetic_clip(tmp_path):
    clip = tmp_path / "synthetic.mp4"
    subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-n", "-f", "lavfi",
                    "-i", "testsrc=size=64x48:rate=16", "-frames:v", "17",
                    "-pix_fmt", "yuv420p", str(clip)], check=True, capture_output=True, shell=False)
    measured = probe_video(clip)
    assert (measured["width"], measured["height"], measured["frame_count"]) == (64, 48, 17)
    assert measured["fps"] == 16.0
