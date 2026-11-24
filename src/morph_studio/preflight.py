"""Read-only environment baseline (F01).

Builds a factual report from git, the local ComfyUI's GET endpoints and an
optional single ``nvidia-smi`` query. Never uploads, submits, interrupts, frees
memory or hashes model weights. Memory readings are labelled snapshots; peak
VRAM and checkpoint SHA-256 stay ``NOT MEASURED`` until F07 measures them.
"""
from __future__ import annotations

import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from . import __version__
from .comfy_client import ComfyClient, ComfyError
from .gates import is_cloud_class, queue_counts
from .workflow_adapter import (
    WorkflowBindingError,
    load_api_workflow,
    load_binding_profile,
    resolve_workflow_path,
    validate_profile,
)

NOT_MEASURED = "NOT MEASURED"
SNAPSHOT = "snapshot (not peak)"
CAPABILITIES = ("text_to_image", "reference_edit", "wan_flf2v")
# Inventory role -> (loader class, input) whose choice list mirrors a ComfyUI model folder.
LOADERS = {
    "checkpoints": ("CheckpointLoaderSimple", "ckpt_name"),
    "diffusion_models": ("UNETLoader", "unet_name"),
    "text_encoders": ("CLIPLoader", "clip_name"),
    "vae": ("VAELoader", "vae_name"),
    "loras": ("LoraLoaderModelOnly", "lora_name"),
}

Runner = Callable[[list[str]], str | None]


def _run(args: list[str]) -> str | None:
    """Run a read-only tool with an argument list; ``None`` if unavailable or failing."""
    if not shutil.which(args[0]):
        return None
    try:
        done = subprocess.run(args, capture_output=True, text=True, errors="replace",
                              timeout=20, shell=False, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def loader_choices(object_info: dict, class_type: str, input_name: str) -> list[str] | None:
    """Installed choices of a combo input, or ``None`` if the loader class is absent."""
    definition = object_info.get(class_type)
    if not isinstance(definition, dict):
        return None
    registered = definition.get("input", {}) or {}
    spec = {**registered.get("required", {}), **registered.get("optional", {})}.get(input_name)
    if not spec:
        return None
    if isinstance(spec[0], list):
        return list(spec[0])
    if len(spec) > 1 and isinstance(spec[1], dict) and isinstance(spec[1].get("options"), list):
        return list(spec[1]["options"])
    return None


def model_inventory(object_info: dict) -> dict:
    inventory: dict = {role: loader_choices(object_info, *loader) for role, loader in LOADERS.items()}
    inventory["sha256"] = NOT_MEASURED
    inventory["note"] = "filenames from /object_info loader choices; weights not hashed"
    return inventory


def profile_reports(profiles_dir: Path, repo_root: Path, object_info: dict | None) -> list[dict]:
    reports = []
    for path in sorted(profiles_dir.glob("*.binding.json")):
        entry: dict = {"file": path.relative_to(repo_root).as_posix()}
        try:
            profile = load_binding_profile(path)
            graph = load_api_workflow(resolve_workflow_path(profile, path, repo_root))
            report = validate_profile(profile, graph, object_info)
            entry.update(profile=profile.profile, capability=profile.capability,
                         workflow=profile.workflow, validated_live=object_info is not None,
                         **report.as_dict())
        except (WorkflowBindingError, OSError, ValueError) as exc:
            entry.update(ok=False, errors=[str(exc)], warnings=[], capability=None)
        reports.append(entry)
    return reports


def classify_capabilities(profiles: list[dict], inventory: dict | None) -> dict:
    """``available`` only for a capability whose profile validated against live object_info."""
    result = {}
    for capability in CAPABILITIES:
        matching = [p for p in profiles if p.get("capability") == capability]
        good = [p for p in matching if p.get("ok") and p.get("validated_live")]
        if good:
            result[capability] = {"status": "available", "profiles": [p["profile"] for p in good]}
        elif matching:
            result[capability] = {"status": "blocked", "reason": "profile present but not validated "
                                  "against live /object_info: " + "; ".join(
                                      e for p in matching for e in p.get("errors", [])[:3]) or "offline"}
        else:
            reason = f"no verified {capability} workflow export + binding profile in configs/profiles"
            if capability != "wan_flf2v" and inventory is not None and not inventory.get("checkpoints"):
                reason += "; no image checkpoint installed (CheckpointLoaderSimple choices empty)"
            result[capability] = {"status": "blocked", "reason": reason}
    return result


def repository_facts(repo_root: Path, run: Runner = _run) -> dict:
    git = ["git", "-C", str(repo_root)]
    head = run([*git, "rev-parse", "HEAD"])
    branch = run([*git, "rev-parse", "--abbrev-ref", "HEAD"])
    status = run([*git, "status", "--porcelain"])
    return {"head": head or "unknown", "branch": branch or "unknown",
            "dirty_files": len([l for l in status.splitlines() if l.strip()])
            if status is not None else "unknown"}


def gpu_snapshot(run: Runner = _run) -> dict:
    out = run(["nvidia-smi", "--query-gpu=name,memory.used,memory.total",
               "--format=csv,noheader,nounits"])
    if not out:
        return {"status": "unavailable", "label": SNAPSHOT}
    gpus = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
            gpus.append({"name": parts[0], "memory_used_mib": int(parts[1]),
                         "memory_total_mib": int(parts[2])})
    return {"status": "ok" if gpus else "unparsed", "gpus": gpus, "label": SNAPSHOT,
            "t": _now()}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_baseline_report(*, repo_root: str | Path, client: ComfyClient | None,
                          object_info: dict | None = None, run: Runner = _run) -> dict:
    """Assemble the BaselineReport. ``client=None`` means ComfyUI was skipped."""
    root = Path(repo_root)
    report: dict = {"schema": 1, "generated_at": _now(), "morphcurrent_version": __version__,
                    "repository": repository_facts(root, run),
                    "peak_vram": NOT_MEASURED}
    comfy: dict = {"status": "skipped"}
    queue: dict = {"status": "skipped"}
    live_info: dict | None = None
    if client is not None:
        try:
            stats = client.health()
            system = stats.get("system", {})
            comfy = {"status": "ok", "version": system.get("comfyui_version"),
                     "pytorch_version": system.get("pytorch_version"),
                     "argv": system.get("argv"),
                     "devices": [{k: d.get(k) for k in ("name", "vram_total", "vram_free")}
                                 for d in stats.get("devices", [])],
                     "vram_label": SNAPSHOT}
            raw = client.queue()
            running, pending = queue_counts(raw)
            queue = {"status": "ok",
                     "running": [i[1] for i in raw.get("queue_running", []) if isinstance(i, list) and len(i) > 1],
                     "pending": [i[1] for i in raw.get("queue_pending", []) if isinstance(i, list) and len(i) > 1],
                     "gpu_busy": bool(running + pending)}
            live_info = object_info if object_info is not None else client.object_info()
        except ComfyError as exc:
            comfy = {"status": "unreachable", "error": str(exc)[:300]}
    info = live_info if live_info is not None else object_info
    report["comfyui"] = comfy
    report["queue"] = queue
    report["inventory"] = model_inventory(info) if info is not None else {"status": "unknown"}
    report["cloud_api_node_classes"] = (sum(1 for d in info.values() if is_cloud_class(d))
                                        if info is not None else None)
    profiles = profile_reports(root / "configs" / "profiles", root, live_info)
    report["profiles"] = profiles
    report["capabilities"] = classify_capabilities(
        profiles, report["inventory"] if info is not None else None)
    report["gpu_snapshot"] = gpu_snapshot(run)
    return report
