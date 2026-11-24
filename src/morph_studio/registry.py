"""Local workflow/model capability registry, compatibility preview and owner-approved selection (F27).

``build_registry`` reads every binding profile and reports, per profile, what it produces, the roles it
binds, the node classes and model files it needs (with licence/hash from ``configs/model_catalogue.json``),
its numeric input constraints and one status. Without a ComfyUI ``/object_info`` snapshot nothing is ever
``ready`` (``offline-unverified``). ``compare`` previews a candidate against the current profile.
``select``/``rollback`` keep an append-only selection record; render commands do not read it, so the
production Qwen/Wan profiles stay the defaults. This module never downloads, installs or dispatches.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .gates import is_cloud_class
from .workflow_adapter import (CAPABILITY_CONTRACTS, WorkflowBindingError, _input_specs, _resolve_spec,
                               graph_sha256, load_api_workflow, load_binding_profile, resolve_workflow_path,
                               validate_graph, validate_profile)

REPO = Path(__file__).resolve().parents[2]
CATALOGUE = Path("configs/model_catalogue.json")
SELECTION = Path("configs/registry/selection.json")
NOT_RECORDED = "NOT RECORDED"
SEVERITY = ("cloud-node", "contract-error", "stale-hash", "missing-node", "missing-model",
            "offline-unverified", "ready")
PRODUCTION_DEFAULTS = {
    "text_to_image": "configs/profiles/anchor_t2i.binding.json",
    "reference_edit": "configs/profiles/anchor_edit.binding.json",
    "wan_flf2v": "configs/profiles/wan22_flf2v.binding.json",
}
# loader input -> (models folder, role)
LOADER_ROLES = {
    "unet_name": ("diffusion_models", "diffusion"), "ckpt_name": ("checkpoints", "checkpoint"),
    "clip_name": ("text_encoders", "text_encoder"), "clip_name1": ("text_encoders", "text_encoder"),
    "clip_name2": ("text_encoders", "text_encoder"), "clip_name3": ("text_encoders", "text_encoder"),
    "vae_name": ("vae", "vae"), "lora_name": ("loras", "lora"),
}
CLASS_ROLES = {("UpscaleModelLoader", "model_name"): ("upscale_models", "upscaler"),
               ("CLIPVisionLoader", "clip_name"): ("clip_vision", "clip_vision")}
LENGTH_RULES = {"wan_flf2v": "4n+1"}
APPROVAL = "owner approval required; this tool never downloads or installs"


class RegistryRefusal(RuntimeError):
    pass


def load_catalogue(path: str | Path | None = None) -> dict:
    path = Path(path) if path else REPO / CATALOGUE
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("models", {})
    except FileNotFoundError:
        return {}


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _model_refs(graph: dict) -> list[tuple[str, str, str, str]]:
    """(folder, file, role, "node_id.input") for each loader input naming a model file."""
    found = {}
    for node_id, node in graph.items():
        for key, value in node.get("inputs", {}).items():
            hit = CLASS_ROLES.get((node.get("class_type"), key)) or LOADER_ROLES.get(key)
            if hit and isinstance(value, str):
                found.setdefault((hit[0], value), (hit[1], f"{node_id}.{key}"))
    return sorted((folder, name, role, where) for (folder, name), (role, where) in found.items())


def _status(problems: list[dict]) -> str:
    present = {p["status"] for p in problems}
    return next((s for s in SEVERITY if s in present), "ready")


def build_entry(profile_path: str | Path, *, object_info: dict | None = None, models_root: str | Path | None = None,
                catalogue: dict | None = None, repo_root: str | Path | None = None) -> dict:
    """Registry record for one profile. Never raises for a bad profile or workflow."""
    root = Path(repo_root) if repo_root else REPO
    profile_path = Path(profile_path)
    catalogue = load_catalogue(root / CATALOGUE) if catalogue is None else catalogue
    entry = {"profile": None, "path": _rel(profile_path, root), "capability": None, "workflow": None,
             "workflow_sha256": None, "actual_sha256": None, "roles": {}, "outputs": [], "node_classes": [],
             "models": [], "constraints": {}, "length_rule": None, "problems": [], "approval_needed": []}
    problems = entry["problems"]

    def problem(status: str, message: str) -> None:
        problems.append({"status": status, "message": message})

    def done() -> dict:
        entry["status"] = _status(problems)
        entry["selectable"] = entry["status"] == "ready"
        return entry

    try:
        profile = load_binding_profile(profile_path)
    except (WorkflowBindingError, OSError, ValueError) as exc:
        problem("contract-error", f"profile unreadable: {exc}")
        return done()
    entry.update(profile=profile.profile, capability=profile.capability, workflow=profile.workflow,
                 workflow_sha256=profile.workflow_sha256, length_rule=LENGTH_RULES.get(profile.capability or ""),
                 roles={r: {"node_id": b.node_id, "input": b.input, "class_type": b.class_type}
                        for r, b in sorted(profile.bindings.items())},
                 outputs=sorted({o.kind for o in profile.outputs}))
    try:
        graph = load_api_workflow(resolve_workflow_path(profile, profile_path, root))
    except (WorkflowBindingError, OSError, ValueError) as exc:
        problem("contract-error", f"workflow not found or unreadable: {exc}")
        return done()
    entry["actual_sha256"] = graph_sha256(graph)
    entry["node_classes"] = sorted({n["class_type"] for n in graph.values()})

    # structural checks (hash, nodes/inputs, assertions, capability contract) without object_info
    for message in validate_profile(profile, graph, None).errors:
        problem("stale-hash" if message.startswith("workflow hash") else "contract-error", message)

    models_dir = Path(models_root) if models_root else None
    model_keys = set()
    for folder, name, role, where in _model_refs(graph):
        model_keys.add(where)
        info = catalogue.get(f"{folder}/{name}", {})
        present = (models_dir / folder / name).is_file() if models_dir else None
        entry["models"].append({"folder": folder, "file": name, "role": role,
                                "licence": info.get("licence", NOT_RECORDED), "source": info.get("source", NOT_RECORDED),
                                "sha256": info.get("sha256", NOT_RECORDED), "present": present})
        if present is False:
            problem("missing-model", f"model file {folder}/{name} not found under {models_dir}")
            entry["approval_needed"].append(f"download {folder}/{name} ({APPROVAL})")

    if object_info is None:
        problem("offline-unverified", "no ComfyUI object_info supplied; node classes and constraints not verified")
        return done()

    for cls in entry["node_classes"]:
        definition = object_info.get(cls)
        if not isinstance(definition, dict):
            problem("missing-node", f"node class {cls} not installed in this ComfyUI")
            entry["approval_needed"].append(f"install node class {cls} ({APPROVAL})")
        elif is_cloud_class(definition):
            problem("cloud-node", f"node class {cls} is a cloud API node; MorphCurrent workflows must run locally")
    for output in profile.outputs:
        definition = object_info.get(output.class_type)
        if isinstance(definition, dict) and definition.get("output_node") is not True:
            problem("contract-error", f"output {output.node_id}: {output.class_type} is not an output node")
    for role, binding in sorted(profile.bindings.items()):
        definition = object_info.get(binding.class_type)
        node = graph.get(binding.node_id)
        if not isinstance(definition, dict) or node is None:
            continue
        spec = _resolve_spec(_input_specs(definition), node["inputs"], binding.input)
        if spec is None:
            problem("contract-error", f"binding {role}: {binding.class_type}.{binding.input} not in object_info")
        elif spec[0] in ("INT", "FLOAT") and len(spec) > 1 and isinstance(spec[1], dict):
            entry["constraints"][role] = {k: spec[1].get(k) for k in ("min", "max", "step")}

    # full graph validation; classify what the targeted checks above have not already covered
    for message in validate_graph(graph, object_info).errors:
        if "class not installed" in message or "cloud API node" in message:
            continue
        head = message.split(":", 1)[0]  # "node 39 (VAELoader).vae_name"
        node_id = head.split(" ", 2)[1] if head.startswith("node ") else ""
        key = head.rsplit(".", 1)[-1] if "." in head else ""
        if f"{node_id}.{key}" in model_keys:
            problem("missing-model", f"{message} (model not installed in this ComfyUI)")
            entry["approval_needed"].append(f"download for {head} ({APPROVAL})")
        else:
            problem("contract-error", message)
    return done()


def build_registry(profiles_dir: str | Path | None = None, **kwargs) -> list[dict]:
    root = Path(kwargs.get("repo_root") or REPO)
    folder = Path(profiles_dir) if profiles_dir else root / "configs" / "profiles"
    if "catalogue" not in kwargs:
        kwargs["catalogue"] = load_catalogue(root / CATALOGUE)
    return [build_entry(p, **kwargs) for p in sorted(folder.glob("*.binding.json"))]


# ------------------------------------------------------------------------------------------ preview

VERDICT = {"compatible": 0, "needs-rebinding": 1, "incompatible": 2}
CHANGE_VERDICT = {"hash_changed": "compatible", "model_added": "compatible", "model_removed": "compatible",
                  "role_added": "compatible", "role_removed": "needs-rebinding", "role_moved": "needs-rebinding",
                  "constraint_changed": "needs-rebinding", "capability_changed": "incompatible",
                  "output_changed": "incompatible", "required_role_missing": "incompatible"}


def _ident(e: dict) -> dict:
    return {"profile": e.get("profile"), "path": e.get("path"), "capability": e.get("capability"),
            "workflow_sha256": e.get("workflow_sha256")}


def compare(current: dict, candidate: dict) -> dict:
    """Changes from ``current`` to ``candidate`` (registry entries) and the resulting verdict."""
    changes = []

    def add(kind: str, **fields) -> None:
        changes.append({"type": kind, **fields})

    if current.get("capability") != candidate.get("capability"):
        add("capability_changed", before=current.get("capability"), after=candidate.get("capability"))
    if current.get("outputs") != candidate.get("outputs"):
        add("output_changed", before=current.get("outputs"), after=candidate.get("outputs"))
    required = CAPABILITY_CONTRACTS.get(candidate.get("capability") or "", ((), ""))[0]
    for role in required:
        if role not in candidate.get("roles", {}):
            add("required_role_missing", role=role)
    cur_roles, cand_roles = current.get("roles", {}), candidate.get("roles", {})
    for role in sorted(set(cand_roles) - set(cur_roles)):
        add("role_added", role=role, after=cand_roles[role])
    for role in sorted(set(cur_roles) - set(cand_roles)):
        if role not in required:
            add("role_removed", role=role, before=cur_roles[role])
    for role in sorted(set(cur_roles) & set(cand_roles)):
        if cur_roles[role] != cand_roles[role]:
            add("role_moved", role=role, before=cur_roles[role], after=cand_roles[role])
    cur_c, cand_c = current.get("constraints", {}), candidate.get("constraints", {})
    for role in sorted(set(cur_c) & set(cand_c)):
        if cur_c[role] != cand_c[role]:
            add("constraint_changed", role=role, before=cur_c[role], after=cand_c[role])
    key = lambda m: f"{m['folder']}/{m['file']}"  # noqa: E731
    cur_m = {key(m) for m in current.get("models", [])}
    cand_m = {key(m) for m in candidate.get("models", [])}
    for name in sorted(cand_m - cur_m):
        add("model_added", after=name)
    for name in sorted(cur_m - cand_m):
        add("model_removed", before=name)
    if current.get("workflow_sha256") != candidate.get("workflow_sha256"):
        add("hash_changed", before=current.get("workflow_sha256"), after=candidate.get("workflow_sha256"))
    verdict = max((CHANGE_VERDICT[c["type"]] for c in changes), key=VERDICT.get, default="compatible")
    return {"current": _ident(current), "candidate": _ident(candidate), "changes": changes, "verdict": verdict}


# ---------------------------------------------------------------------------------------- selection

def _read_selection(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"schema": 1, "active": {}, "history": []}


def _write_selection(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    part.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    os.replace(part, path)


def active_profile(capability: str, selection_path: str | Path | None = None) -> str | None:
    """Active profile path for a capability: the owner's selection, else the production default."""
    data = _read_selection(Path(selection_path) if selection_path else REPO / SELECTION)
    chosen = data.get("active", {}).get(capability)
    return chosen["profile"] if chosen else PRODUCTION_DEFAULTS.get(capability)


def _recorded(profile_rel: str | None, root: Path) -> dict | None:
    if not profile_rel:
        return None
    try:
        sha = load_binding_profile(root / profile_rel).workflow_sha256
    except (WorkflowBindingError, OSError, ValueError):
        sha = None
    return {"profile": profile_rel, "workflow_sha256": sha}


def select(candidate_path: str | Path, *, approve: bool, note: str = "", object_info: dict | None = None,
           models_root: str | Path | None = None, selection_path: str | Path | None = None,
           repo_root: str | Path | None = None) -> dict:
    """Make a ready candidate the active profile for its capability (explicit owner approval required)."""
    root = Path(repo_root) if repo_root else REPO
    sel = Path(selection_path) if selection_path else root / SELECTION
    if not approve:
        raise RegistryRefusal("selection needs explicit owner approval (--approve); nothing changed")
    kwargs = {"object_info": object_info, "models_root": models_root, "repo_root": root}
    entry = build_entry(candidate_path, **kwargs)
    if entry["status"] != "ready":
        reasons = "; ".join(p["message"] for p in entry["problems"])
        raise RegistryRefusal(f"candidate status is {entry['status']}, not ready: {reasons}")
    capability = entry["capability"]
    if not capability:
        raise RegistryRefusal("candidate declares no capability")
    data = _read_selection(sel)
    current_rel = active_profile(capability, sel)
    if current_rel == entry["path"] and (_recorded(current_rel, root) or {}).get("workflow_sha256") \
            == entry["workflow_sha256"]:
        raise RegistryRefusal(f"{entry['path']} is already active for {capability}")
    preview = None
    if current_rel:
        preview = compare(build_entry(root / current_rel, **kwargs), entry)
        if preview["verdict"] == "incompatible":
            raise RegistryRefusal(f"candidate is incompatible with the active {current_rel}: "
                                  + ", ".join(c["type"] for c in preview["changes"]))
    previous = data["active"].get(capability) or _recorded(current_rel, root)
    new = {"profile": entry["path"], "workflow_sha256": entry["workflow_sha256"]}
    data["history"].append({"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "action": "select",
                            "capability": capability, "previous": previous, "new": new, "note": note,
                            "verdict": preview["verdict"] if preview else None})
    data["active"][capability] = new
    _write_selection(sel, data)
    return {"selected": entry["path"], "capability": capability, "active": new, "preview": preview,
            "history_length": len(data["history"])}


def rollback(capability: str, selection_path: str | Path | None = None) -> dict:
    """Restore the profile that was active before the latest selection still in effect."""
    sel = Path(selection_path) if selection_path else REPO / SELECTION
    data = _read_selection(sel)
    stack = []
    for h in data["history"]:
        if h["capability"] != capability:
            continue
        if h["action"] == "select":
            stack.append(h["previous"])
        elif stack:
            stack.pop()
    if not stack:
        raise RegistryRefusal(f"nothing to roll back for {capability}")
    restore = stack.pop()
    current = data["active"].get(capability)
    if restore is None or restore.get("profile") == PRODUCTION_DEFAULTS.get(capability):
        data["active"].pop(capability, None)
    else:
        data["active"][capability] = restore
    data["history"].append({"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "action": "rollback",
                            "capability": capability, "previous": current, "new": restore, "note": "rollback"})
    _write_selection(sel, data)
    return {"capability": capability, "active": active_profile(capability, sel)}
