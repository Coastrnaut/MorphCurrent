"""Shared GPU submission gate (F01).

Every stage that would queue GPU work (Wan bridge, anchor images, full pipeline)
asks ``check_gpu_gate`` first. Submission requires explicit consent, an idle
ComfyUI queue (unless explicitly overridden) and a graph without ComfyUI cloud
API nodes, which would send prompts/media to a remote service.
"""
from __future__ import annotations

from dataclasses import dataclass, field

CLOUD_MODULE_PREFIX = "comfy_api_nodes"


def is_cloud_class(definition: object) -> bool:
    """A class is cloud when object_info marks ``api_node`` or it ships in comfy_api_nodes."""
    if not isinstance(definition, dict):
        return False
    module = definition.get("python_module")
    return definition.get("api_node") is True or (
        isinstance(module, str) and module.startswith(CLOUD_MODULE_PREFIX))


def cloud_nodes(graph: dict, object_info: dict) -> list[str]:
    """``"<node_id> (<class>)"`` for every node whose class is a cloud API node."""
    return [f"{node_id} ({node['class_type']})" for node_id, node in sorted(graph.items())
            if is_cloud_class(object_info.get(node.get("class_type")))]


def queue_counts(queue: dict) -> tuple[int, int]:
    return len(queue.get("queue_running", []) or []), len(queue.get("queue_pending", []) or [])


@dataclass
class GateDecision:
    reasons: list[str] = field(default_factory=list)
    queue_running: int = 0
    queue_pending: int = 0
    cloud_nodes: list[str] = field(default_factory=list)

    @property
    def allowed(self) -> bool:
        return not self.reasons

    @property
    def queue_busy(self) -> int:
        return self.queue_running + self.queue_pending

    def as_dict(self) -> dict:
        return {"allowed": self.allowed, "reasons": self.reasons,
                "queue_running": self.queue_running, "queue_pending": self.queue_pending,
                "cloud_nodes": self.cloud_nodes}


def check_gpu_gate(*, consent: bool, queue: dict, graph: dict | None = None,
                   object_info: dict | None = None,
                   allow_busy_queue: bool = False) -> GateDecision:
    """Decide whether one GPU job may be submitted now. Pure; performs no I/O."""
    running, pending = queue_counts(queue)
    decision = GateDecision(queue_running=running, queue_pending=pending)
    if consent is not True:
        decision.reasons.append("consent: explicit owner GPU approval (--confirm-gpu) is required")
    if running + pending and not allow_busy_queue:
        decision.reasons.append(f"queue_busy: ComfyUI queue has {running + pending} job(s)")
    if graph is not None and object_info is not None:
        decision.cloud_nodes = cloud_nodes(graph, object_info)
        if decision.cloud_nodes:
            decision.reasons.append("cloud_node: graph contains ComfyUI cloud API node(s) "
                                    f"{', '.join(decision.cloud_nodes)}; MorphCurrent is local-only")
    return decision
