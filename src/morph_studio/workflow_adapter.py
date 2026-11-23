"""Semantic binding for user-verified API-format ComfyUI exports."""
from __future__ import annotations

import copy
import json
from pathlib import Path


class WorkflowBindingError(ValueError):
    pass


def load_api_workflow(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as stream:
        graph = json.load(stream)
    if not isinstance(graph, dict) or not graph:
        raise WorkflowBindingError("not an API-format ComfyUI graph")
    for node_id, node in graph.items():
        if (not isinstance(node_id, str) or not isinstance(node, dict)
                or not isinstance(node.get("class_type"), str)
                or not isinstance(node.get("inputs"), dict)):
            raise WorkflowBindingError("expected node-id -> {class_type,inputs} API graph")
    return graph


def patch_workflow(graph: dict, bindings: dict, values: dict,
                   object_info: dict | None = None) -> dict:
    """Patches semantic field -> {node_id, input, class_type}, never guessed IDs."""
    patched = copy.deepcopy(graph)
    for role, value in values.items():
        binding = bindings.get(role)
        if not isinstance(binding, dict):
            raise WorkflowBindingError(f"no binding for {role}")
        node_id = binding.get("node_id")
        field = binding.get("input")
        expected_class = binding.get("class_type")
        node = patched.get(node_id)
        if node is None or not isinstance(field, str) or not expected_class:
            raise WorkflowBindingError(f"invalid node binding for {role}")
        if node.get("class_type") != expected_class:
            raise WorkflowBindingError(f"class_type mismatch for {role}")
        if field not in node.get("inputs", {}):
            raise WorkflowBindingError(f"input {field!r} missing for {role}")
        if object_info is not None:
            definition = object_info.get(expected_class)
            if not isinstance(definition, dict):
                raise WorkflowBindingError(f"node {expected_class!r} unavailable in ComfyUI")
            registered = definition.get("input", {})
            known_inputs = {**registered.get("required", {}), **registered.get("optional", {})}
            if field not in known_inputs:
                raise WorkflowBindingError(f"{expected_class}.{field} unavailable in ComfyUI")
        node["inputs"][field] = value
    return patched
