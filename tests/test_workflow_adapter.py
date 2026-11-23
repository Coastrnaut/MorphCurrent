from pathlib import Path

import pytest

from morph_studio.workflow_adapter import (
    WorkflowBindingError,
    load_api_workflow,
    patch_workflow,
)


def test_binding_patch_is_safe_copy():
    graph = {"12": {"class_type": "CLIPTextEncode", "inputs": {
        "text": "old text", "clip": ["1", 0]
    }}}
    bindings = {"positive_prompt": {
        "node_id": "12", "input": "text", "class_type": "CLIPTextEncode"
    }}
    object_info = {"CLIPTextEncode": {
        "input": {"required": {"text": ["STRING", {}]}, "optional": {}}
    }}
    patched = patch_workflow(graph, bindings, {"positive_prompt": "new"}, object_info)
    assert patched["12"]["inputs"]["text"] == "new"
    assert graph["12"]["inputs"]["text"] == "old text"


def test_missing_or_changed_node_binding_fails():
    graph = {"12": {"class_type": "Other", "inputs": {"text": "old"}}}
    bindings = {"prompt": {
        "node_id": "12", "input": "text", "class_type": "CLIPTextEncode"
    }}
    with pytest.raises(WorkflowBindingError):
        patch_workflow(graph, bindings, {"prompt": "new"})


def test_api_format_rejected(tmp_path: Path):
    filename = tmp_path / "workflow.json"
    filename.write_text('{"nodes": []}', encoding="utf-8")
    with pytest.raises(WorkflowBindingError):
        load_api_workflow(filename)
