"""Semantic binding for user-verified API-format ComfyUI exports.

Bindings come from a versioned profile (``configs/profiles/*.binding.json``) that
names real node IDs taken from an exported graph. Nothing here searches a graph
for "the" seed or prompt node: an unbound role, changed class or missing input
fails closed with an actionable message.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .gates import is_cloud_class

DYNAMIC_COMBO = "COMFY_DYNAMICCOMBO_V3"


class WorkflowBindingError(ValueError):
    pass


# --------------------------------------------------------------------------- graph IO

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


def graph_sha256(graph: dict) -> str:
    """Hash of the executable graph content, independent of whitespace/line endings.

    ``_meta`` (UI titles, node-pack versions) is excluded because ComfyUI ignores it.
    """
    stripped = {node_id: {"class_type": node["class_type"], "inputs": node["inputs"]}
                for node_id, node in graph.items()}
    canonical = json.dumps(stripped, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def is_link(value: Any) -> bool:
    return (isinstance(value, list) and len(value) == 2 and isinstance(value[0], str)
            and isinstance(value[1], int) and not isinstance(value[1], bool))


# ------------------------------------------------------------------- object_info schema

def _input_specs(definition: dict) -> dict[str, list]:
    registered = definition.get("input", {}) or {}
    return {**registered.get("required", {}), **registered.get("optional", {})}


def _required_inputs(definition: dict) -> set[str]:
    return set((definition.get("input", {}) or {}).get("required", {}))


def _resolve_spec(specs: dict[str, list], inputs: dict, key: str) -> list | None:
    """Find the schema for ``key``, following dotted dynamic-combo sub-inputs.

    ``format.codec`` is valid when ``format`` is a dynamic combo whose selected
    option (the graph's ``format`` value) declares a ``codec`` input.
    """
    if key in specs:
        return specs[key]
    head, sep, rest = key.partition(".")
    if not sep or head not in specs:
        return None
    spec = specs[head]
    if spec[0] != DYNAMIC_COMBO or len(spec) < 2:
        return None
    selected = inputs.get(head)
    for option in spec[1].get("options", []):
        if option.get("key") == selected:
            sub_specs = _input_specs({"input": option.get("inputs", {})})
            sub_inputs = {k[len(head) + 1:]: v for k, v in inputs.items()
                          if k.startswith(head + ".")}
            return _resolve_spec(sub_specs, sub_inputs, rest)
    return None


def check_value(spec: list, value: Any) -> str | None:
    """Return a problem description if a literal violates an object_info spec."""
    kind = spec[0]
    options = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
    if isinstance(kind, list):
        return None if value in kind else f"{value!r} not among {len(kind)} installed choices"
    if kind == "COMBO":
        choices = options.get("options")
        if isinstance(choices, list) and value not in choices:
            return f"{value!r} not among {len(choices)} choices"
        return None
    if kind == DYNAMIC_COMBO:
        keys = [option.get("key") for option in options.get("options", [])]
        return None if value in keys else f"{value!r} not among {keys}"
    if kind == "INT":
        if isinstance(value, bool) or not isinstance(value, int):
            return f"expected INT, got {type(value).__name__}"
    elif kind == "FLOAT":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f"expected FLOAT, got {type(value).__name__}"
    elif kind == "STRING":
        return None if isinstance(value, str) else f"expected STRING, got {type(value).__name__}"
    elif kind == "BOOLEAN":
        return None if isinstance(value, bool) else f"expected BOOLEAN, got {type(value).__name__}"
    else:
        return f"{kind} is a link-only input type and cannot hold a literal"
    low, high = options.get("min"), options.get("max")
    if low is not None and value < low:
        return f"{value} below minimum {low}"
    if high is not None and value > high:
        return f"{value} above maximum {high}"
    # ComfyUI's backend enforces only min/max. INT steps are model-meaningful here
    # (Wan: width/height multiples of 16, length 4n+1) so enforce them; float steps
    # are UI rounding hints and are not enforced.
    step = options.get("step")
    if kind == "INT" and isinstance(step, int) and step > 1:
        base = low if isinstance(low, int) else 0
        if (value - base) % step:
            return f"{value} is not {base} + k*{step}"
    return None


def coerce_for_spec(spec: list, raw: str) -> Any:
    """Convert a CLI string to the type the object_info spec expects."""
    kind = spec[0]
    if kind == "INT":
        return int(raw)
    if kind == "FLOAT":
        return float(raw)
    if kind == "BOOLEAN":
        if raw.lower() not in {"true", "false"}:
            raise ValueError(f"expected true/false, got {raw!r}")
        return raw.lower() == "true"
    return raw


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def extend(self, other: "ValidationReport") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)

    def as_dict(self) -> dict:
        return {"ok": self.ok, "errors": self.errors, "warnings": self.warnings}


def validate_graph(graph: dict, object_info: dict) -> ValidationReport:
    """Check every node of an API graph against a live ``/object_info`` snapshot.

    Errors: unknown class, missing required input, broken link, literal outside the
    installed choices (e.g. a checkpoint filename not on disk) or numeric range.
    Warnings: extra keys ComfyUI ignores (e.g. ``video-preview`` UI widget state).
    """
    report = ValidationReport()
    for node_id, node in graph.items():
        class_type = node["class_type"]
        definition = object_info.get(class_type)
        where = f"node {node_id} ({class_type})"
        if not isinstance(definition, dict):
            report.errors.append(f"{where}: class not installed in this ComfyUI")
            continue
        if is_cloud_class(definition):
            report.errors.append(f"{where}: cloud API node (sends data to a remote service); "
                                 "MorphCurrent workflows must run locally")
        specs = _input_specs(definition)
        inputs = node["inputs"]
        for name in sorted(_required_inputs(definition) - set(inputs)):
            report.errors.append(f"{where}: required input {name!r} missing")
        for name, value in inputs.items():
            spec = _resolve_spec(specs, inputs, name)
            if spec is None:
                report.warnings.append(f"{where}: input {name!r} not in object_info (ignored by ComfyUI)")
                continue
            if is_link(value):
                source = graph.get(value[0])
                if source is None:
                    report.errors.append(f"{where}.{name}: links to missing node {value[0]}")
                    continue
                source_def = object_info.get(source["class_type"])
                if isinstance(source_def, dict):
                    outputs = source_def.get("output", [])
                    if value[1] >= len(outputs):
                        report.errors.append(f"{where}.{name}: output {value[1]} of node {value[0]} does not exist")
                    elif not isinstance(spec[0], list) and outputs[value[1]] != spec[0] \
                            and "*" not in (outputs[value[1]], spec[0]):
                        report.errors.append(
                            f"{where}.{name}: expects {spec[0]}, linked output is {outputs[value[1]]}")
                continue
            problem = check_value(spec, value)
            if problem:
                report.errors.append(f"{where}.{name}: {problem}")
    return report


# -------------------------------------------------------------------------- profiles

class InputBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    node_id: str
    input: str
    class_type: str
    note: str | None = None


class OutputBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    node_id: str
    class_type: str
    kind: str = "video"


class InputAssertion(BaseModel):
    """A literal the profile's correctness depends on (e.g. sampler 2 adds no noise)."""
    model_config = ConfigDict(extra="forbid")
    node_id: str
    class_type: str
    input: str
    equals: Any
    reason: str


class BindingProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile: str
    # What the graph produces; used by preflight capability reporting and anchor/bridge stages.
    capability: Literal["text_to_image", "reference_edit", "wan_flf2v"] | None = None
    workflow: str
    workflow_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    verified_against: dict[str, Any] = Field(default_factory=dict)
    bindings: dict[str, InputBinding]
    outputs: list[OutputBinding] = Field(min_length=1)
    assertions: list[InputAssertion] = Field(default_factory=list)


def load_binding_profile(path: str | Path) -> BindingProfile:
    try:
        with Path(path).open("r", encoding="utf-8") as stream:
            return BindingProfile.model_validate(json.load(stream))
    except ValidationError as exc:
        raise WorkflowBindingError(f"invalid binding profile {path}: {exc}") from exc


def resolve_workflow_path(profile: BindingProfile, profile_path: str | Path,
                          repo_root: str | Path | None = None) -> Path:
    """Workflow paths are repo-relative; resolve from ``repo_root`` or the profile's ancestors."""
    relative = Path(profile.workflow)
    if relative.is_absolute() or ".." in relative.parts:
        raise WorkflowBindingError("profile workflow must be a repository-relative path")
    candidates = [Path(repo_root)] if repo_root else list(Path(profile_path).resolve().parents)
    for base in candidates:
        if (base / relative).is_file():
            return base / relative
    raise WorkflowBindingError(f"workflow {profile.workflow} not found for profile {profile_path}")


def validate_profile(profile: BindingProfile, graph: dict,
                     object_info: dict | None = None) -> ValidationReport:
    """Structural profile <-> graph checks; schema checks when ``object_info`` given."""
    report = ValidationReport()
    actual_hash = graph_sha256(graph)
    if actual_hash != profile.workflow_sha256:
        report.errors.append(
            f"workflow hash {actual_hash} != profile {profile.workflow_sha256}; "
            "graph was re-exported or edited, re-verify every binding")

    def node_for(kind: str, node_id: str, class_type: str) -> dict | None:
        node = graph.get(node_id)
        if node is None:
            report.errors.append(f"{kind}: node {node_id} not in graph")
            return None
        if node["class_type"] != class_type:
            report.errors.append(f"{kind}: node {node_id} is {node['class_type']}, profile says {class_type}")
            return None
        return node

    for role, binding in profile.bindings.items():
        node = node_for(f"binding {role}", binding.node_id, binding.class_type)
        if node is None:
            continue
        if binding.input not in node["inputs"]:
            report.errors.append(f"binding {role}: input {binding.input!r} absent on node {binding.node_id}")
        elif is_link(node["inputs"][binding.input]):
            report.errors.append(f"binding {role}: {binding.input!r} is a link, not a patchable literal")
        if object_info is not None:
            definition = object_info.get(binding.class_type)
            if not isinstance(definition, dict):
                report.errors.append(f"binding {role}: {binding.class_type} not installed")
            elif _resolve_spec(_input_specs(definition), node["inputs"], binding.input) is None:
                report.errors.append(f"binding {role}: {binding.class_type}.{binding.input} not in object_info")

    for output in profile.outputs:
        node = node_for("output", output.node_id, output.class_type)
        if node is not None and object_info is not None:
            definition = object_info.get(output.class_type)
            if not isinstance(definition, dict) or definition.get("output_node") is not True:
                report.errors.append(f"output {output.node_id}: {output.class_type} is not an output node")

    for assertion in profile.assertions:
        node = node_for("assertion", assertion.node_id, assertion.class_type)
        if node is not None and node["inputs"].get(assertion.input) != assertion.equals:
            report.errors.append(
                f"assertion {assertion.node_id}.{assertion.input} == {assertion.equals!r} failed "
                f"(got {node['inputs'].get(assertion.input)!r}): {assertion.reason}")

    if object_info is not None:
        report.extend(validate_graph(graph, object_info))
    return report


def profile_bindings(profile: BindingProfile) -> dict[str, dict]:
    return {role: binding.model_dump(exclude={"note"}) for role, binding in profile.bindings.items()}


# --------------------------------------------------------------------------- patching

def patch_workflow(graph: dict, bindings: dict, values: dict,
                   object_info: dict | None = None) -> dict:
    """Patches semantic field -> {node_id, input, class_type}, never guessed IDs.

    With ``object_info`` each value is also checked against the installed schema
    (types, ranges, INT steps, installed choices). ``LoadImage.image`` choices list
    the ComfyUI input folder, so refresh ``object_info`` after uploading anchors.
    """
    patched = copy.deepcopy(graph)
    for role, value in values.items():
        binding = bindings.get(role)
        if not isinstance(binding, dict):
            raise WorkflowBindingError(f"no binding for {role}")
        node_id = binding.get("node_id")
        field_name = binding.get("input")
        expected_class = binding.get("class_type")
        node = patched.get(node_id)
        if node is None or not isinstance(field_name, str) or not expected_class:
            raise WorkflowBindingError(f"invalid node binding for {role}")
        if node.get("class_type") != expected_class:
            raise WorkflowBindingError(f"class_type mismatch for {role}")
        if field_name not in node.get("inputs", {}):
            raise WorkflowBindingError(f"input {field_name!r} missing for {role}")
        if is_link(node["inputs"][field_name]):
            raise WorkflowBindingError(f"{role}: {field_name!r} is a graph link, refusing to overwrite")
        if object_info is not None:
            definition = object_info.get(expected_class)
            if not isinstance(definition, dict):
                raise WorkflowBindingError(f"node {expected_class!r} unavailable in ComfyUI")
            spec = _resolve_spec(_input_specs(definition), node["inputs"], field_name)
            if spec is None:
                raise WorkflowBindingError(f"{expected_class}.{field_name} unavailable in ComfyUI")
            problem = check_value(spec, value)
            if problem:
                raise WorkflowBindingError(f"{role} ({expected_class}.{field_name}): {problem}")
        node["inputs"][field_name] = value
    return patched


def spec_for_role(profile: BindingProfile, graph: dict, object_info: dict, role: str) -> list:
    binding = profile.bindings.get(role)
    if binding is None:
        raise WorkflowBindingError(f"no binding for {role}; profile has {sorted(profile.bindings)}")
    definition = object_info.get(binding.class_type)
    node = graph.get(binding.node_id)
    spec = None
    if isinstance(definition, dict) and node is not None:
        spec = _resolve_spec(_input_specs(definition), node["inputs"], binding.input)
    if spec is None:
        raise WorkflowBindingError(f"{binding.class_type}.{binding.input} unavailable in ComfyUI")
    return spec


# --------------------------------------------------------------------------- outputs

def extract_outputs(history_item: dict, profile: BindingProfile) -> list[dict]:
    """Collect output file records for the profile's output nodes from ``/history``.

    Observed ComfyUI 0.46 ``SaveVideo`` shape:
    ``outputs[node_id] = {"images": [{filename, subfolder, type, metadata}], "animated": [true]}``.
    """
    outputs = history_item.get("outputs") or {}
    found: list[dict] = []
    for output in profile.outputs:
        entry = outputs.get(output.node_id)
        files = []
        if isinstance(entry, dict):
            for key in ("images", "videos", "gifs"):
                files.extend(item for item in entry.get(key, []) if isinstance(item, dict))
        if not files:
            raise WorkflowBindingError(f"history has no files for output node {output.node_id}")
        for item in files:
            if not item.get("filename"):
                raise WorkflowBindingError(f"output node {output.node_id} entry lacks filename")
            found.append({
                "node_id": output.node_id,
                "kind": output.kind,
                "filename": item["filename"],
                "subfolder": item.get("subfolder", ""),
                "type": item.get("type", "output"),
                "metadata": item.get("metadata", {}),
            })
    return found
