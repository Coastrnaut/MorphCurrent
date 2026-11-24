"""Real Wan 2.2 FLF2V export (workflows/03_wan22_flf2v.json) checked against a
trimmed /object_info snapshot captured from local ComfyUI 0.46.0 on 2026-11-23."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest

from morph_studio.workflow_adapter import (
    WorkflowBindingError,
    extract_outputs,
    graph_sha256,
    load_api_workflow,
    load_binding_profile,
    patch_workflow,
    profile_bindings,
    resolve_workflow_path,
    validate_graph,
    validate_profile,
)

REPO = Path(__file__).resolve().parents[1]
PROFILE_PATH = REPO / "configs" / "profiles" / "wan22_flf2v.binding.json"
FIXTURE = REPO / "tests" / "fixtures" / "object_info_wan22_flf2v.json"


@pytest.fixture(scope="module")
def object_info() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def profile():
    return load_binding_profile(PROFILE_PATH)


@pytest.fixture()
def graph(profile) -> dict:
    return load_api_workflow(resolve_workflow_path(profile, PROFILE_PATH))


def test_real_profile_binds_expected_nodes(profile):
    expected = {
        "start_image": ("80", "image", "LoadImage"),
        "end_image": ("89", "image", "LoadImage"),
        "positive_prompt": ("90", "text", "CLIPTextEncode"),
        "negative_prompt": ("78", "text", "CLIPTextEncode"),
        "width": ("81", "width", "WanFirstLastFrameToVideo"),
        "height": ("81", "height", "WanFirstLastFrameToVideo"),
        "length": ("81", "length", "WanFirstLastFrameToVideo"),
        "fps": ("86", "fps", "CreateVideo"),
        "seed": ("84", "noise_seed", "KSamplerAdvanced"),
        "filename_prefix": ("83", "filename_prefix", "SaveVideo"),
    }
    actual = {role: (b.node_id, b.input, b.class_type) for role, b in profile.bindings.items()}
    assert actual == expected
    assert [(o.node_id, o.class_type) for o in profile.outputs] == [("83", "SaveVideo")]


def test_bindings_trace_into_flf2v_node(graph):
    flf = graph["81"]["inputs"]
    assert flf["start_image"] == ["80", 0] and flf["end_image"] == ["89", 0]
    assert flf["positive"] == ["90", 0] and flf["negative"] == ["78", 0]


def test_real_graph_valid_against_object_info(graph, object_info, profile):
    report = validate_profile(profile, graph, object_info)
    assert report.errors == []
    # UI-only widget state is tolerated but surfaced; the dynamic combo sub-key resolves.
    assert report.warnings == [
        "node 83 (SaveVideo): input 'video-preview' not in object_info (ignored by ComfyUI)"]


def test_graph_hash_ignores_meta_and_detects_edits(graph, profile):
    assert graph_sha256(graph) == profile.workflow_sha256
    retitled = copy.deepcopy(graph)
    retitled["81"]["_meta"]["title"] = "renamed"
    assert graph_sha256(retitled) == profile.workflow_sha256
    edited = copy.deepcopy(graph)
    edited["84"]["inputs"]["cfg"] = 5
    report = validate_profile(profile, edited)
    assert any("re-exported or edited" in e for e in report.errors)


def test_patch_all_semantic_roles(graph, object_info, profile):
    values = {
        "start_image": "02_metallic_butterfly.jpg",
        "end_image": "01_glass_orchid.jpg",
        "positive_prompt": "pos", "negative_prompt": "neg",
        "width": 832, "height": 480, "length": 81, "fps": 24.0,
        "seed": 18446744073709551615, "filename_prefix": "video/mc_test",
    }
    patched = patch_workflow(graph, profile_bindings(profile), values, object_info)
    assert patched["80"]["inputs"]["image"] == "02_metallic_butterfly.jpg"
    assert patched["89"]["inputs"]["image"] == "01_glass_orchid.jpg"
    assert patched["90"]["inputs"]["text"] == "pos"
    assert patched["78"]["inputs"]["text"] == "neg"
    flf = patched["81"]["inputs"]
    assert (flf["width"], flf["height"], flf["length"]) == (832, 480, 81)
    assert patched["86"]["inputs"]["fps"] == 24.0
    assert patched["84"]["inputs"]["noise_seed"] == 18446744073709551615
    assert patched["87"]["inputs"]["noise_seed"] == 0  # inert low-noise seed is left alone
    assert patched["83"]["inputs"]["filename_prefix"] == "video/mc_test"
    assert validate_graph(patched, object_info).ok
    assert graph["81"]["inputs"]["length"] == 65  # source graph is not mutated


@pytest.mark.parametrize("role,value,message", [
    ("length", 64, r"1 \+ k\*4"),
    ("length", 0, "below minimum"),
    ("width", 650, r"16 \+ k\*16"),
    ("seed", -1, "below minimum"),
    ("seed", "42", "expected INT"),
    ("fps", 0.5, "below minimum"),
    ("start_image", "not_uploaded.png", "installed choices"),
])
def test_patch_rejects_values_outside_schema(graph, object_info, profile, role, value, message):
    with pytest.raises(WorkflowBindingError, match=message):
        patch_workflow(graph, profile_bindings(profile), {role: value}, object_info)


def test_unbound_role_and_link_overwrite_fail(graph, object_info, profile):
    with pytest.raises(WorkflowBindingError, match="no binding for steps"):
        patch_workflow(graph, profile_bindings(profile), {"steps": 30}, object_info)
    link_binding = {"x": {"node_id": "81", "input": "start_image",
                          "class_type": "WanFirstLastFrameToVideo"}}
    with pytest.raises(WorkflowBindingError, match="graph link"):
        patch_workflow(graph, link_binding, {"x": "a.png"}, object_info)


def test_profile_assertions_fail_closed(graph, profile):
    graph["87"]["inputs"]["add_noise"] = "enable"
    report = validate_profile(profile, graph)
    assert any("87.add_noise" in e for e in report.errors)


def test_missing_node_class_or_model_is_error(graph, object_info, profile):
    without_wan = {k: v for k, v in object_info.items() if k != "WanFirstLastFrameToVideo"}
    report = validate_profile(profile, graph, without_wan)
    assert any("node 81 (WanFirstLastFrameToVideo): class not installed" in e
               for e in report.errors)
    graph["76"]["inputs"]["unet_name"] = "wan2.2_i2v_high_noise_14B_fp16.safetensors"
    report = validate_graph(graph, object_info)
    assert any("node 76 (UNETLoader).unet_name" in e for e in report.errors)


def test_broken_link_is_error(graph, object_info):
    graph["85"]["inputs"]["samples"] = ["999", 0]
    graph["86"]["inputs"]["images"] = ["79", 0]  # VAE output wired into an IMAGE input
    errors = validate_graph(graph, object_info).errors
    assert any("missing node 999" in e for e in errors)
    assert any("expects IMAGE, linked output is VAE" in e for e in errors)


def test_extract_outputs_observed_history_shape(profile):
    history_item = {"status": {"status_str": "success", "completed": True}, "outputs": {"83": {
        "images": [{"filename": "ComfyUI_00003_.mp4", "subfolder": "video", "type": "output",
                    "metadata": {"kind": "video", "width": 640, "height": 368,
                                 "fps": 16.0, "frame_count": 65}}],
        "animated": [True]}}}
    [item] = extract_outputs(history_item, profile)
    assert item["filename"] == "ComfyUI_00003_.mp4" and item["subfolder"] == "video"
    assert item["metadata"]["frame_count"] == 65
    with pytest.raises(WorkflowBindingError, match="no files for output node 83"):
        extract_outputs({"outputs": {}}, profile)


@pytest.mark.integration
@pytest.mark.skipif(not os.environ.get("MORPHCURRENT_COMFY_URL"),
                    reason="set MORPHCURRENT_COMFY_URL=http://127.0.0.1:8188 to check live object_info")
def test_live_object_info_accepts_real_profile(graph, profile):
    """Reads /object_info only; never queues a prompt or touches the GPU."""
    from morph_studio.comfy_client import ComfyClient
    with ComfyClient(os.environ["MORPHCURRENT_COMFY_URL"]) as client:
        live = client.object_info()
    assert validate_profile(profile, graph, live).errors == []
