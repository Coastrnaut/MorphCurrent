"""Programmatic Wan 2.2 FLF2V bridge dispatch against a local ComfyUI.

One bridge = one immutable job directory ``<runs_root>/<job_id[:16]>/`` holding a
``job.json`` state record, the exact patched API graph and the downloaded clip.
The job ID is a content hash of the patched graph (anchors referenced by their
SHA-256-derived upload names), the anchor bytes, the exported workflow hash and
the MorphCurrent version, so identical requests reuse a verified result and any
change produces a new directory. Nothing is overwritten.

State machine (persisted after every transition, so any crash is resumable)::

    planned -> uploaded -> validated -> submitting -> submitted -> completed
            -> downloaded -> verified            (terminal: failed, cancelled)

The ComfyUI ``prompt_id`` is a UUID chosen and saved *before* ``POST /prompt``;
on resume it is looked up in ``/history`` and ``/queue`` so a run is never
silently queued twice. Submission only happens when the caller passes
``submit=True`` (the CLI's ``--confirm-gpu``).
"""
from __future__ import annotations

import copy
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field

from . import __version__
from .cache import cache_key, sha256_file
from .comfy_client import ComfyClient, ComfyError, ComfyRejected
from .media import ProbeUnavailable, probe_video
from .workflow_adapter import (
    BindingProfile,
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

DEFAULT_PROFILE = "configs/profiles/wan22_flf2v.binding.json"
IMAGE_ROLES = ("start_image", "end_image")
NUMERIC_ROLES = ("width", "height", "length", "fps")
MODEL_INPUTS = ("unet_name", "clip_name", "vae_name", "ckpt_name", "lora_name")
STATES = ("planned", "uploaded", "validated", "submitting", "submitted",
          "completed", "downloaded", "verified")
TERMINAL = ("failed", "cancelled")
PREFIX_PLACEHOLDER = "morphcurrent/__job__/bridge"


class BridgeError(RuntimeError):
    pass


class BridgeRequest(BaseModel):
    """Semantic inputs. ``None`` keeps the value baked into the exported graph."""
    model_config = ConfigDict(extra="forbid")
    profile: str = DEFAULT_PROFILE
    start_image: str
    end_image: str
    seed: int = Field(ge=0)
    positive_prompt: str | None = None
    negative_prompt: str | None = None
    width: int | None = None
    height: int | None = None
    length: int | None = None
    fps: float | None = None


@dataclass
class BridgePlan:
    request: BridgeRequest
    profile: BindingProfile
    base_graph: dict
    graph: dict
    job_id: str
    image_sha256: dict[str, str]
    image_paths: dict[str, Path]
    upload_names: dict[str, str]
    values: dict[str, Any]
    models: dict[str, str]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def upload_name_for(path: Path, digest: str) -> str:
    """Content-addressed basename in ComfyUI's input root (LoadImage lists only the root)."""
    return f"mc_{digest[:16]}{path.suffix.lower()}"


def plan_bridge(request: BridgeRequest, object_info: dict | None = None,
                repo_root: str | Path | None = None) -> BridgePlan:
    """Resolve, patch and hash a bridge without touching ComfyUI.

    With ``object_info`` every non-image value is checked against the installed
    schema here; image choices are checked after upload, when they exist.
    """
    root = Path(repo_root) if repo_root else Path.cwd()
    profile_path = Path(request.profile)
    if not profile_path.is_absolute():
        profile_path = root / profile_path
    profile = load_binding_profile(profile_path)
    base_graph = load_api_workflow(resolve_workflow_path(profile, profile_path, repo_root))
    pre = validate_profile(profile, base_graph)
    if not pre.ok:
        raise WorkflowBindingError("; ".join(pre.errors))

    image_paths: dict[str, Path] = {}
    digests: dict[str, str] = {}
    names: dict[str, str] = {}
    for role in IMAGE_ROLES:
        path = Path(getattr(request, role))
        if not path.is_absolute():
            path = root / path
        if not path.is_file():
            raise FileNotFoundError(f"{role}: {path}")
        image_paths[role] = path
        digests[role] = sha256_file(path)
        names[role] = upload_name_for(path, digests[role])

    bindings = profile_bindings(profile)
    scalar: dict[str, Any] = {"seed": request.seed}
    for role in ("positive_prompt", "negative_prompt", *NUMERIC_ROLES):
        value = getattr(request, role)
        if value is not None:
            scalar[role] = value
    if "filename_prefix" in bindings:
        scalar["filename_prefix"] = PREFIX_PLACEHOLDER
    graph = patch_workflow(base_graph, bindings, scalar, object_info)
    graph = patch_workflow(graph, bindings, names)

    models = {f"{node_id}.{key}": value for node_id, node in sorted(graph.items())
              for key, value in node["inputs"].items()
              if key in MODEL_INPUTS and isinstance(value, str)}
    job_id = cache_key(
        task={"kind": "wan22_flf2v_bridge", "profile": profile.profile,
              "graph_sha256": graph_sha256(graph)},
        dependencies={role: digests[role] for role in IMAGE_ROLES},
        workflow_sha256=profile.workflow_sha256,
        model_sha256={},  # checkpoint hashes not yet inventoried; filenames are in the graph
        code_revision=__version__,
    )
    if "filename_prefix" in bindings:
        graph = patch_workflow(graph, bindings,
                               {"filename_prefix": f"morphcurrent/{job_id[:16]}/bridge"})
    values = {role: graph[b["node_id"]]["inputs"][b["input"]] for role, b in bindings.items()}
    return BridgePlan(request=request, profile=profile, base_graph=base_graph, graph=graph,
                      job_id=job_id, image_sha256=digests, image_paths=image_paths,
                      upload_names=names, values=values, models=models)


# ------------------------------------------------------------------------ job record

class BridgeJob:
    def __init__(self, job_dir: Path, record: dict):
        self.dir = job_dir
        self.record = record

    @property
    def state(self) -> str:
        return self.record["state"]

    @property
    def path(self) -> Path:
        return self.dir / "job.json"

    def save(self) -> None:
        tmp = self.path.with_name("job.json.tmp")
        tmp.write_text(json.dumps(self.record, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8", newline="\n")
        os.replace(tmp, self.path)

    def transition(self, state: str, event: str | None = None, **data: Any) -> None:
        self.record["state"] = state
        self.record["events"].append({"t": _now(), "event": event or state, **data})
        self.save()

    def fail(self, error: str, **data: Any) -> BridgeError:
        self.record["error"] = error
        self.transition("failed", "failed", error=error, **data)
        return BridgeError(f"bridge {self.record['job_id'][:16]} failed: {error}")


def load_job(job_dir: str | Path) -> BridgeJob:
    job_dir = Path(job_dir)
    try:
        record = json.loads((job_dir / "job.json").read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BridgeError(f"no job.json in {job_dir}") from exc
    return BridgeJob(job_dir, record)


def open_job(plan: BridgePlan, runs_root: str | Path) -> BridgeJob:
    """Create the immutable job directory, or reopen it for resume."""
    job_dir = Path(runs_root) / plan.job_id[:16]
    workflow_file = job_dir / "workflow.api.json"
    if (job_dir / "job.json").exists():
        job = load_job(job_dir)
        if job.record.get("job_id") != plan.job_id:
            raise BridgeError(f"{job_dir} belongs to job {job.record.get('job_id')}, not {plan.job_id}")
        on_disk = load_api_workflow(workflow_file)
        if graph_sha256(on_disk) != graph_sha256(plan.graph):
            raise BridgeError(f"{workflow_file} no longer matches the planned graph")
        return job
    job_dir.mkdir(parents=True, exist_ok=False)
    with workflow_file.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(plan.graph, indent=2, ensure_ascii=False) + "\n")
    record = {
        "schema": 1,
        "job_id": plan.job_id,
        "kind": "wan22_flf2v_bridge",
        "morphcurrent_version": __version__,
        "created_at": _now(),
        "state": "planned",
        "request": plan.request.model_dump(),
        "profile": plan.profile.profile,
        "workflow": plan.profile.workflow,
        "workflow_sha256": plan.profile.workflow_sha256,
        "patched_graph_sha256": graph_sha256(plan.graph),
        "anchors": {role: {"path": str(plan.image_paths[role]),
                           "sha256": plan.image_sha256[role],
                           "upload_name": plan.upload_names[role]} for role in IMAGE_ROLES},
        "values": plan.values,
        "models": plan.models,
        "model_sha256": "NOT RECORDED",
        "prompt_id": None,
        "comfyui": {},
        "outputs": [],
        "verification": None,
        "error": None,
        "events": [{"t": _now(), "event": "planned"}],
    }
    job = BridgeJob(job_dir, record)
    job.save()
    return job


# -------------------------------------------------------------------------- execution

def _system_snapshot(client: ComfyClient) -> dict:
    stats = client.health()
    system = stats.get("system", {})
    return {
        "t": _now(),
        "comfyui_version": system.get("comfyui_version"),
        "pytorch_version": system.get("pytorch_version"),
        "argv": system.get("argv"),
        "devices": [{k: d.get(k) for k in ("name", "vram_total", "vram_free")}
                    for d in stats.get("devices", [])],
    }


def _timings(history_item: dict) -> dict:
    marks = {}
    for message in (history_item.get("status") or {}).get("messages", []):
        if isinstance(message, list) and len(message) == 2 and isinstance(message[1], dict):
            stamp = message[1].get("timestamp")
            if isinstance(stamp, (int, float)):
                marks[message[0]] = stamp
    start, end = marks.get("execution_start"), marks.get("execution_success")
    return {"messages_ms": marks,
            "execution_seconds": round((end - start) / 1000, 3) if start and end else None}


def _upload(job: BridgeJob, plan: BridgePlan, client: ComfyClient) -> None:
    uploads = {}
    for role in IMAGE_ROLES:
        expected = plan.upload_names[role]
        response = client.upload_image(plan.image_paths[role], name=expected)
        if response.get("name") != expected or response.get("subfolder", "") != "":
            raise job.fail(f"{role} uploaded as {response.get('subfolder')!r}/{response.get('name')!r}, "
                           f"expected {expected!r}; a different file already uses that name")
        uploads[role] = response.get("name")
    job.transition("uploaded", uploads=uploads)


def _validate(job: BridgeJob, plan: BridgePlan, client: ComfyClient) -> None:
    object_info = client.object_info()  # refreshed: LoadImage choices now include uploads
    report = validate_profile(plan.profile, plan.base_graph, object_info)
    report.extend(validate_graph(plan.graph, object_info))
    if not report.ok:
        raise job.fail("object_info validation failed", errors=report.errors)
    job.record["comfyui"]["validated"] = _system_snapshot(client)
    job.transition("validated", warnings=list(dict.fromkeys(report.warnings)))


def _submit(job: BridgeJob, plan: BridgePlan, client: ComfyClient, *,
            allow_busy_queue: bool) -> None:
    queue = client.queue()
    busy = len(queue.get("queue_running", [])) + len(queue.get("queue_pending", []))
    if busy and not allow_busy_queue:
        raise BridgeError(f"ComfyUI queue has {busy} job(s); refusing to stack GPU work "
                          "(wait, or pass allow_busy_queue/--allow-busy-queue)")
    prompt_id = job.record.get("prompt_id") or str(uuid.uuid4())
    job.record["prompt_id"] = prompt_id
    job.transition("submitting", prompt_id=prompt_id)  # persisted before the POST
    try:
        returned = client.submit(copy.deepcopy(plan.graph), prompt_id=prompt_id)
    except ComfyRejected as exc:
        raise job.fail(f"ComfyUI rejected prompt: {exc}")
    # Any other ComfyError (connection lost mid-POST) is ambiguous: stay "submitting"
    # and let the next run reconcile against /history and /queue.
    if returned != prompt_id:
        job.record["prompt_id"] = returned
    job.record["comfyui"]["submitted"] = _system_snapshot(client)
    job.transition("submitted", prompt_id=job.record["prompt_id"])


def _reconcile_submitting(job: BridgeJob, plan: BridgePlan, client: ComfyClient, *,
                          allow_busy_queue: bool) -> None:
    """Crash between saving the ID and the POST: find out whether ComfyUI got it."""
    prompt_id = job.record["prompt_id"]
    if client.history(prompt_id) is not None or client.queue_position(prompt_id):
        job.transition("submitted", "submit_confirmed_on_resume", prompt_id=prompt_id)
    else:
        job.record["events"].append({"t": _now(), "event": "resubmit_unconfirmed", "prompt_id": prompt_id})
        _submit(job, plan, client, allow_busy_queue=allow_busy_queue)


def _await(job: BridgeJob, plan: BridgePlan, client: ComfyClient, *,
           timeout: float, poll_seconds: float) -> None:
    prompt_id = job.record["prompt_id"]
    if client.history(prompt_id) is None and client.queue_position(prompt_id) is None:
        raise job.fail("prompt is in neither /history nor /queue (ComfyUI restarted?); "
                       "retry to resubmit", prompt_id=prompt_id)
    try:
        item = client.await_result(prompt_id, timeout=timeout, poll_seconds=poll_seconds)
    except ComfyError as exc:
        history = client.history(prompt_id) or {}
        raise job.fail(f"execution failed: {exc}", status=history.get("status"))
    try:
        outputs = extract_outputs(item, plan.profile)
    except WorkflowBindingError as exc:
        raise job.fail(str(exc))
    job.record["outputs"] = outputs
    job.record["timings"] = _timings(item)
    job.record["comfyui"]["completed"] = _system_snapshot(client)
    # Observed on ComfyUI 0.46 + cudaMallocAsync: /system_stats vram_free stayed byte-identical
    # before, during and after a render while nvidia-smi showed ~35.7 GB used, so the
    # snapshots are environment context only, never memory evidence.
    job.record["comfyui"]["peak_vram"] = ("NOT MEASURED (ComfyUI API exposes no peak; /system_stats "
                                          "vram_free observed static, not usable as evidence)")
    job.transition("completed", outputs=[o["filename"] for o in outputs])


def _download(job: BridgeJob, client: ComfyClient) -> None:
    out_dir = job.dir / "outputs"
    out_dir.mkdir(exist_ok=True)
    for output in job.record["outputs"]:
        target = out_dir / output["filename"]
        if target.exists():
            if output.get("sha256") and sha256_file(target) != output["sha256"]:
                raise job.fail(f"{target} exists with different content; refusing to overwrite")
        else:
            part = target.with_name(target.name + ".part")
            if part.exists():
                part.unlink()  # our own incomplete download from an interrupted run
            client.download_output(output["filename"], part, subfolder=output["subfolder"],
                                   folder_type=output["type"])
            if part.stat().st_size == 0:
                raise job.fail(f"downloaded {output['filename']} is empty")
            os.rename(part, target)  # fails rather than replaces if target appeared
        output["local_path"] = str(target.relative_to(job.dir))
        output["sha256"] = sha256_file(target)
        output["bytes"] = target.stat().st_size
    job.transition("downloaded")


def _verify(job: BridgeJob, probe: Callable[[Path], dict]) -> None:
    values = job.record["values"]
    expected = {"width": values.get("width"), "height": values.get("height"),
                "frame_count": values.get("length"), "fps": values.get("fps")}
    results = []
    for output in job.record["outputs"]:
        if output.get("kind") != "video":
            continue
        try:
            measured = probe(job.dir / output["local_path"])
        except ProbeUnavailable as exc:
            job.record["verification"] = {"status": "skipped", "reason": str(exc)}
            job.save()
            return
        mismatches = {key: {"expected": want, "measured": measured.get(key)}
                      for key, want in expected.items()
                      if want is not None and measured.get(key) is not None
                      and abs(float(measured[key]) - float(want)) > 1e-3}
        results.append({"file": output["local_path"], "measured": measured,
                        "mismatches": mismatches})
    job.record["verification"] = {"status": "pass" if not any(r["mismatches"] for r in results)
                                  else "mismatch", "files": results}
    if job.record["verification"]["status"] != "pass":
        raise job.fail("clip properties differ from the request", verification=results)
    job.transition("verified")


def run_bridge(plan: BridgePlan, client: ComfyClient, runs_root: str | Path, *,
               submit: bool = False, retry: bool = False, allow_busy_queue: bool = False,
               timeout: float = 3600, poll_seconds: float = 2,
               probe: Callable[[Path], dict] = probe_video) -> BridgeJob:
    """Advance a bridge job as far as allowed. Safe to call again after any failure."""
    job = open_job(plan, runs_root)
    if job.state == "verified":
        return job
    if job.state in TERMINAL:
        if not retry:
            raise BridgeError(f"job is {job.state}: {job.record.get('error')}; pass retry to try again")
        # Re-upload (deduplicated by ComfyUI) and re-validate against current object_info.
        restart = "planned"
        job.record["prompt_id"] = None
        job.record["error"] = None
        job.record["outputs"] = []
        job.record["verification"] = None
        job.transition(restart, "retry")

    if job.state == "planned":
        _upload(job, plan, client)
    if job.state == "uploaded":
        _validate(job, plan, client)
    if job.state == "validated":
        if not submit:
            return job
        _submit(job, plan, client, allow_busy_queue=allow_busy_queue)
    if job.state == "submitting":
        _reconcile_submitting(job, plan, client, allow_busy_queue=allow_busy_queue)
    if job.state == "submitted":
        _await(job, plan, client, timeout=timeout, poll_seconds=poll_seconds)
    if job.state == "completed":
        _download(job, client)
    if job.state == "downloaded":
        _verify(job, probe)
    return job


def cancel_bridge(job_dir: str | Path, client: ComfyClient) -> BridgeJob:
    """Dequeue or interrupt only this job's prompt; never a global interrupt."""
    job = load_job(job_dir)
    if job.state not in ("submitting", "submitted"):
        raise BridgeError(f"job is {job.state}; only queued/running jobs can be cancelled")
    was = client.cancel(job.record["prompt_id"])
    job.transition("cancelled", "cancelled", queue_state=was)
    return job


def request_from_job(job_dir: str | Path) -> BridgeRequest:
    return BridgeRequest.model_validate(load_job(job_dir).record["request"])
