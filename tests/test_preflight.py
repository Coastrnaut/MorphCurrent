"""F01 read-only baseline report (offline, fake ComfyUI that rejects writes)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import httpx
import pytest

from morph_studio import cli
from morph_studio.comfy_client import ComfyClient
from morph_studio.preflight import build_baseline_report, gpu_snapshot, model_inventory

REPO = Path(__file__).resolve().parents[1]
WAN_INFO = json.loads((REPO / "tests/fixtures/object_info_wan22_flf2v.json").read_text(encoding="utf-8"))
IMAGE_INFO = json.loads((REPO / "tests/fixtures/object_info_image_nodes.json").read_text(encoding="utf-8"))
OBJECT_INFO = {**IMAGE_INFO, **WAN_INFO}


def fake_run(args: list[str]) -> str | None:
    if args[0] == "git":
        return {"HEAD": "abc123", "--abbrev-ref": "main", "--porcelain": " M x.py"}.get(
            args[-1] if args[-1] != "HEAD" or args[-2] != "--abbrev-ref" else "--abbrev-ref")
    if args[0] == "nvidia-smi":
        return "NVIDIA RTX A6000, 36000, 49140"
    return None


class ReadOnlyComfy:
    def __init__(self, queue=None, down=False):
        self.methods: list[str] = []
        self.queue = queue or {"queue_running": [], "queue_pending": []}
        self.down = down

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.methods.append(f"{request.method} {request.url.path}")
        if request.method != "GET":
            raise AssertionError(f"write request {request.method} {request.url.path}")
        if self.down:
            raise httpx.ConnectError("down", request=request)
        if request.url.path == "/system_stats":
            return httpx.Response(200, json={"system": {"comfyui_version": "0.46.0", "argv": []},
                                             "devices": [{"name": "cuda:0", "vram_total": 5, "vram_free": 1}]})
        if request.url.path == "/queue":
            return httpx.Response(200, json=self.queue)
        if request.url.path == "/object_info":
            return httpx.Response(200, json=OBJECT_INFO)
        return httpx.Response(404)

    def client(self) -> ComfyClient:
        return ComfyClient(http_client=httpx.Client(transport=httpx.MockTransport(self.handler),
                                                    base_url="http://127.0.0.1:8188"))


def wan_only_repo(tmp_path):
    for rel in ("workflows/03_wan22_flf2v.json", "configs/profiles/wan22_flf2v.binding.json"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_bytes((REPO / rel).read_bytes())
    return tmp_path


def test_real_image_profiles_blocked_when_models_absent_from_object_info():
    report = build_baseline_report(repo_root=REPO, client=ReadOnlyComfy().client(), run=fake_run)
    t2i = report["capabilities"]["text_to_image"]
    assert t2i["status"] == "blocked" and "qwen_image_fp8_e4m3fn.safetensors" in t2i["reason"]


def test_idle_report_is_get_only_and_flags_missing_image_capability(tmp_path):
    fake = ReadOnlyComfy()
    report = build_baseline_report(repo_root=wan_only_repo(tmp_path), client=fake.client(), run=fake_run)
    assert all(m.startswith("GET ") for m in fake.methods)
    assert report["queue"] == {"status": "ok", "running": [], "pending": [], "gpu_busy": False}
    assert report["comfyui"]["vram_label"] == "snapshot (not peak)"
    assert report["peak_vram"] == "NOT MEASURED"
    assert report["inventory"]["sha256"] == "NOT MEASURED"
    assert report["inventory"]["checkpoints"] == []
    caps = report["capabilities"]
    assert caps["wan_flf2v"]["status"] == "available"
    assert caps["text_to_image"]["status"] == "blocked"
    assert "no image checkpoint installed" in caps["text_to_image"]["reason"]
    assert caps["reference_edit"]["status"] == "blocked"
    assert report["cloud_api_node_classes"] == 2  # QwenImageEditApi, QwenImageTextToImageApi
    assert report["gpu_snapshot"]["gpus"][0]["memory_used_mib"] == 36000
    assert report["gpu_snapshot"]["label"] == "snapshot (not peak)"


def test_busy_queue_is_reported_not_touched():
    fake = ReadOnlyComfy(queue={"queue_running": [[0, "owner-job", {}, {}, []]], "queue_pending": []})
    report = build_baseline_report(repo_root=REPO, client=fake.client(), run=fake_run)
    assert report["queue"]["running"] == ["owner-job"] and report["queue"]["gpu_busy"] is True
    assert all(m.startswith("GET ") for m in fake.methods)


def test_unreachable_comfy_still_reports_repository():
    report = build_baseline_report(repo_root=REPO, client=ReadOnlyComfy(down=True).client(), run=fake_run)
    assert report["comfyui"]["status"] == "unreachable"
    assert report["repository"]["head"] == "abc123"
    assert report["capabilities"]["wan_flf2v"]["status"] == "blocked"


def test_skip_comfy_makes_no_http_and_tools_may_be_missing():
    report = build_baseline_report(repo_root=REPO, client=None, run=lambda args: None)
    assert report["comfyui"] == {"status": "skipped"}
    assert report["repository"] == {"head": "unknown", "branch": "unknown", "dirty_files": "unknown"}
    assert report["gpu_snapshot"]["status"] == "unavailable"


def test_inventory_reads_loader_choices():
    inventory = model_inventory(OBJECT_INFO)
    assert "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors" in inventory["diffusion_models"]


def test_gpu_snapshot_unparsed_output():
    assert gpu_snapshot(lambda args: "garbage")["status"] == "unparsed"


def test_cli_baseline_skip_comfy_and_out_refuses_overwrite(tmp_path, capsys):
    out = tmp_path / "baseline.json"
    assert cli.main(["baseline", "--skip-comfy", "--out", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["comfyui"]["status"] == "skipped"
    capsys.readouterr()
    assert cli.main(["baseline", "--skip-comfy", "--out", str(out)]) == 2
    assert cli.main(["baseline", "--skip-comfy", "--strict"]) == 3


def test_environment_doc_labels_unmeasured_values():
    text = (REPO / "docs" / "ENVIRONMENT.md").read_text(encoding="utf-8")
    assert "NOT MEASURED" in text
    assert re.search(r"[Pp]eak VRAM.*per-process peak \*\*NOT MEASURED\*\*", text)
    assert re.search(r"SHA-256.*Wan files measured", text)
    assert not re.search(r"C:\\Users\\", text)
