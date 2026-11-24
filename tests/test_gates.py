"""F01 shared GPU gate and cloud-node rejection (offline)."""
from __future__ import annotations

import json
from pathlib import Path

from morph_studio.gates import check_gpu_gate, cloud_nodes, is_cloud_class
from morph_studio.workflow_adapter import validate_graph

FIXTURE = Path(__file__).parent / "fixtures" / "object_info_image_nodes.json"
OBJECT_INFO = json.loads(FIXTURE.read_text(encoding="utf-8"))
IDLE = {"queue_running": [], "queue_pending": []}
BUSY = {"queue_running": [[0, "p1", {}, {}, []]], "queue_pending": [[1, "p2", {}, {}, []]]}

LOCAL_GRAPH = {"1": {"class_type": "LoadImage", "inputs": {"image": "x.png"}},
               "2": {"class_type": "SaveImage", "inputs": {"images": ["1", 0], "filename_prefix": "a"}}}
CLOUD_GRAPH = {**LOCAL_GRAPH,
               "3": {"class_type": "QwenImageEditApi", "inputs": {}}}


def test_fixture_has_real_cloud_and_local_markers():
    assert is_cloud_class(OBJECT_INFO["QwenImageEditApi"])
    assert not is_cloud_class(OBJECT_INFO["TextEncodeQwenImageEdit"])
    assert not is_cloud_class(OBJECT_INFO["LoadImage"])


def test_module_prefix_alone_marks_cloud():
    assert is_cloud_class({"python_module": "comfy_api_nodes.nodes_x"})
    assert not is_cloud_class({"python_module": "comfy_extras.nodes_x"})


def test_cloud_nodes_lists_offenders():
    assert cloud_nodes(CLOUD_GRAPH, OBJECT_INFO) == ["3 (QwenImageEditApi)"]
    assert cloud_nodes(LOCAL_GRAPH, OBJECT_INFO) == []


def test_gate_denies_without_consent():
    decision = check_gpu_gate(consent=False, queue=IDLE)
    assert not decision.allowed and decision.reasons[0].startswith("consent")


def test_gate_denies_busy_queue_unless_overridden():
    decision = check_gpu_gate(consent=True, queue=BUSY)
    assert not decision.allowed and decision.queue_busy == 2
    assert any(r.startswith("queue_busy") for r in decision.reasons)
    assert check_gpu_gate(consent=True, queue=BUSY, allow_busy_queue=True).allowed


def test_gate_denies_cloud_graph_even_with_consent():
    decision = check_gpu_gate(consent=True, queue=IDLE, graph=CLOUD_GRAPH, object_info=OBJECT_INFO)
    assert not decision.allowed and decision.cloud_nodes == ["3 (QwenImageEditApi)"]


def test_gate_collects_all_reasons():
    decision = check_gpu_gate(consent=False, queue=BUSY, graph=CLOUD_GRAPH, object_info=OBJECT_INFO)
    assert [r.split(":")[0] for r in decision.reasons] == ["consent", "queue_busy", "cloud_node"]


def test_gate_allows_local_idle_consented():
    decision = check_gpu_gate(consent=True, queue=IDLE, graph=LOCAL_GRAPH, object_info=OBJECT_INFO)
    assert decision.allowed and decision.as_dict()["allowed"] is True


def test_validate_graph_rejects_cloud_node():
    report = validate_graph(CLOUD_GRAPH, OBJECT_INFO)
    assert any("cloud API node" in e for e in report.errors)
    assert not any("cloud" in e for e in validate_graph(LOCAL_GRAPH, OBJECT_INFO).errors)
