"""Read-only inspection of a fresh ComfyUI API export before writing its binding profile (F02).

The report lists nodes, cloud API nodes, literal model filenames with their
installed status and schema problems, plus *candidate* semantic roles. Candidates
are hints for the human/engineer who writes ``configs/profiles/*.binding.json``
after reading the graph; nothing here writes a profile or guesses node IDs into
an executable artifact.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .gates import is_cloud_class
from .workflow_adapter import (
    WorkflowBindingError,
    _input_specs,
    graph_sha256,
    is_link,
    validate_graph,
)

MODEL_INPUT_KEYS = ("ckpt_name", "unet_name", "clip_name", "clip_name1", "clip_name2",
                    "vae_name", "lora_name", "model_name", "control_net_name")
TEXT_KEYS = ("text", "prompt")
SEED_KEYS = ("seed", "noise_seed")
SIZE_KEYS = ("width", "height")


def load_export(path: str | Path) -> dict:
    """Load a Save (API Format) export; UI-format workflows are rejected with guidance."""
    with Path(path).open("r", encoding="utf-8") as stream:
        payload = json.load(stream)
    if isinstance(payload, dict) and ("nodes" in payload and "links" in payload):
        raise WorkflowBindingError(
            f"{path} is a UI-format workflow; in ComfyUI use Workflow > Export (API) / "
            "'Save (API Format)' and inspect that file")
    if not isinstance(payload, dict) or not payload or not all(
            isinstance(node, dict) and isinstance(node.get("class_type"), str)
            and isinstance(node.get("inputs"), dict) for node in payload.values()):
        raise WorkflowBindingError(f"{path} is not an API-format ComfyUI graph")
    return payload


def _choices(spec: list | None) -> list | None:
    if not spec:
        return None
    if isinstance(spec[0], list):
        return spec[0]
    if len(spec) > 1 and isinstance(spec[1], dict) and isinstance(spec[1].get("options"), list):
        return spec[1]["options"]
    return None


def _candidates(graph: dict, object_info: dict | None) -> list[dict]:
    found: list[dict] = []

    def add(hint: str, node_id: str, key: str, node: dict) -> None:
        found.append({"role_hint": hint, "node_id": node_id, "input": key,
                      "class_type": node["class_type"], "current": node["inputs"].get(key),
                      "status": "candidate"})

    for node_id, node in sorted(graph.items()):
        inputs = node["inputs"]
        cls = node["class_type"]
        for key, value in inputs.items():
            if is_link(value):
                continue
            if key in TEXT_KEYS and isinstance(value, str):
                add("positive_prompt or negative_prompt", node_id, key, node)
            elif key in SEED_KEYS and isinstance(value, int):
                add("seed", node_id, key, node)
            elif key in SIZE_KEYS and isinstance(value, int):
                add(key, node_id, key, node)
            elif cls == "LoadImage" and key == "image":
                add("reference_image / start_image / end_image", node_id, key, node)
            elif key == "filename_prefix":
                add("filename_prefix", node_id, key, node)
        definition = (object_info or {}).get(cls)
        if isinstance(definition, dict) and definition.get("output_node") is True:
            kind = "image" if "IMAGE" in definition.get("output", []) or "images" in inputs else "other"
            found.append({"role_hint": f"output ({kind})", "node_id": node_id, "input": None,
                          "class_type": cls, "current": None, "status": "candidate"})
    return found


def inspect_export(graph: dict, object_info: dict | None = None) -> dict:
    """Structural + (optional) schema report for an API export. Pure; no I/O."""
    errors: list[str] = []
    warnings: list[str] = []
    models: list[dict] = []
    nodes: list[dict] = []
    for node_id, node in sorted(graph.items()):
        definition = (object_info or {}).get(node["class_type"])
        nodes.append({"id": node_id, "class_type": node["class_type"],
                      "cloud": is_cloud_class(definition) if object_info is not None else None,
                      "output_node": (definition.get("output_node") is True)
                      if isinstance(definition, dict) else None})
        for key, value in node["inputs"].items():
            if key not in MODEL_INPUT_KEYS or not isinstance(value, str):
                continue
            installed: bool | None = None
            if object_info is not None and isinstance(definition, dict):
                choices = _choices(_input_specs(definition).get(key))
                installed = value in choices if choices is not None else None
            models.append({"node_id": node_id, "class_type": node["class_type"], "input": key,
                           "value": value, "installed": installed})
            if installed is False:
                errors.append(f"model file {value!r} (node {node_id} {node['class_type']}.{key}) "
                              "is not installed in this ComfyUI")
    cloud = [f"{n['id']} ({n['class_type']})" for n in nodes if n["cloud"]]
    if object_info is not None:
        report = validate_graph(graph, object_info)
        # model-choice problems are already reported above in plainer words
        errors.extend(e for e in report.errors
                      if not any(m["value"] in e and m["installed"] is False for m in models))
        warnings.extend(report.warnings)
    else:
        warnings.append("offline: schema, model installation and cloud checks skipped")
    return {"ok": not errors, "format": "api", "graph_sha256": graph_sha256(graph),
            "node_count": len(graph), "nodes": nodes, "cloud_nodes": cloud, "models": models,
            "errors": errors, "warnings": list(dict.fromkeys(warnings)),
            "candidates": _candidates(graph, object_info),
            "note": "candidates are hints only; write the binding profile from the real node IDs "
                    "after reading the graph, then run workflow-check"}


def as_json(report: dict) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False, default=_default) + "\n"


def _default(value: Any) -> Any:
    return str(value)
