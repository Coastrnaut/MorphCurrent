"""Multi-stage pipeline glue: DAG tasks -> anchor jobs -> Wan bridge jobs (F06+).

Bridges are rendered by the unchanged, GPU-verified ``bridge.plan_bridge`` /
``run_bridge`` path (MC-FLF2V-003). Their endpoint images come only from verified
anchor jobs, so the shared anchor of two adjacent bridges is the same file/SHA.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .anchors import AnchorError, anchor_image_path, job_is_verified
from .bridge import BridgeJob, BridgeRequest, plan_bridge, run_bridge
from .comfy_client import ComfyClient
from .media import probe_video


class PipelineError(RuntimeError):
    pass


@dataclass
class BridgeStageResult:
    jobs: dict[str, BridgeJob] = field(default_factory=dict)
    blocked: dict[str, str] = field(default_factory=dict)
    stopped_at: str | None = None

    @property
    def complete(self) -> bool:
        return not self.blocked and self.stopped_at is None and \
            all(j.state == "verified" for j in self.jobs.values())


def bridge_request_for(task: dict, start: Path, end: Path, profile: str) -> BridgeRequest:
    return BridgeRequest(profile=profile, start_image=str(start), end_image=str(end),
                         seed=task["seed"], positive_prompt=task["positive_prompt"],
                         negative_prompt=task.get("negative_prompt"),
                         width=task["width"], height=task["height"], length=task["frames"],
                         fps=float(task["fps"]))


def run_bridge_stage(dag_plan: dict, anchor_jobs: dict[str, BridgeJob], *, client: ComfyClient,
                     runs_root: str | Path, submit: bool = False, retry: bool = False,
                     allow_busy_queue: bool = False, repo_root: str | Path | None = None,
                     timeout: float = 3600, poll_seconds: float = 2,
                     probe: Callable[[Path], dict] = probe_video, budget=None) -> BridgeStageResult:
    """Plan/run every DAG bridge from verified anchors, one GPU job at a time."""
    profile = dag_plan["requirements"]["wan_flf2v"]["profile"]
    result = BridgeStageResult()
    object_info = client.object_info()
    shared: dict[str, str] = {}
    for task_id in dag_plan["order"]:
        task = dag_plan["tasks"][task_id]
        if task["kind"] != "bridge":
            continue
        try:
            start = anchor_image_path(_anchor_job(anchor_jobs, task["from"]))
            end = anchor_image_path(_anchor_job(anchor_jobs, task["to"]))
        except AnchorError as exc:
            result.blocked[task_id] = f"BLOCKED: {exc}"
            continue
        plan = plan_bridge(bridge_request_for(task, start, end, profile), object_info, repo_root=repo_root)
        if (submit and budget is not None and not job_is_verified(runs_root, plan.job_id)
                and not budget.allow("bridge", task)):
            result.stopped_at = task_id  # F17: budget reached before a new GPU submission
            break
        for anchor_id, role in ((task["from"], "start_image"), (task["to"], "end_image")):
            digest = plan.image_sha256[role]
            if shared.setdefault(anchor_id, digest) != digest:
                raise PipelineError(f"anchor {anchor_id} has two different byte versions across bridges")
        job = run_bridge(plan, client, runs_root, submit=submit, retry=retry,
                         allow_busy_queue=allow_busy_queue, timeout=timeout,
                         poll_seconds=poll_seconds, probe=probe)
        job.record["pipeline"] = {
            "task": task_id, "candidates_requested": task.get("candidates", 1),
            "candidate_index": 0,
            "anchor_jobs": {"start": anchor_jobs[task["from"]].record["job_id"],
                            "end": anchor_jobs[task["to"]].record["job_id"]},
        }
        job.save()
        result.jobs[task_id] = job
        if job.state != "verified":
            result.stopped_at = task_id
            if submit:
                break
    return result


def _anchor_job(jobs: dict[str, BridgeJob], anchor_id: str) -> BridgeJob:
    job = jobs.get(anchor_id)
    if job is None:
        raise AnchorError(f"anchor {anchor_id!r} has not been generated")
    return job
