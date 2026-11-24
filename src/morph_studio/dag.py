"""Storyboard -> deterministic task DAG (F05). Pure: no ComfyUI, no network.

Tasks: ``anchor:<id>`` (T2I / reference edit / explicit independent T2I),
``bridge:<from>-><to>`` (Wan FLF2V, depends on both endpoint anchors, so a shared
anchor is generated once and used by two bridges) and ``final:movie``.
Timing follows ``timeline.py``: Wan length L = 4n+1, anchor separation (L-1)/F.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .prompt_compiler import compile_bridge_prompts
from .schema import Storyboard
from .timeline import compile_timeline, derived_seed

DEFAULT_PROFILES = {
    "text_to_image": "configs/profiles/anchor_t2i.binding.json",
    "reference_edit": "configs/profiles/anchor_edit.binding.json",
    "wan_flf2v": "configs/profiles/wan22_flf2v.binding.json",
}
CAPABILITY_FOR_GENERATION = {"text_to_image": "text_to_image", "independent_t2i": "text_to_image",
                             "reference_edit": "reference_edit"}


def _canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def anchor_prompt(anchor_prompt_text: str, style: str) -> str:
    """Composition rule (documented): anchor prompt, then the storyboard style description."""
    return " ".join(anchor_prompt_text.split()) + " " + " ".join(style.split())


def compile_plan(storyboard: Storyboard, *, profiles: dict[str, str] | None = None,
                 repo_root: str | Path = ".", storyboard_bytes: bytes | None = None) -> dict:
    root = Path(repo_root)
    chosen = {**DEFAULT_PROFILES, **(profiles or {})}
    render = storyboard.render
    tasks: dict[str, dict] = {}
    order: list[str] = []

    for anchor in storyboard.anchors:  # schema guarantees references point to earlier anchors
        task_id = f"anchor:{anchor.id}"
        explicit = anchor.seed is not None
        depends = [f"anchor:{anchor.reference}"] if anchor.reference else []
        tasks[task_id] = {
            "id": task_id, "kind": "anchor", "anchor": anchor.id,
            "method": anchor.generation,
            "capability": CAPABILITY_FOR_GENERATION[anchor.generation],
            "reference": anchor.reference,
            "conditioned_on_parent": anchor.generation == "reference_edit",
            "positive_prompt": anchor_prompt(anchor.prompt, storyboard.style.description),
            "negative_prompt": anchor.negative_prompt,
            "seed": anchor.seed if explicit else derived_seed(render.master_seed, task_id),
            "seed_source": "storyboard" if explicit else "derived(master_seed, task id)",
            "width": render.width, "height": render.height,
            "depends_on": depends,
        }
        order.append(task_id)

    bridges = compile_timeline(storyboard)
    for transition, bridge in zip(storyboard.transitions, bridges):
        task_id = f"bridge:{bridge.from_anchor}->{bridge.to_anchor}"
        positive, negative = compile_bridge_prompts(transition)
        tasks[task_id] = {
            "id": task_id, "kind": "bridge",
            "from": bridge.from_anchor, "to": bridge.to_anchor,
            "frames": bridge.frames, "fps": bridge.fps,
            "width": render.width, "height": render.height,
            "seed": bridge.seed,
            "seed_source": "storyboard" if transition.seed is not None else "derived(master_seed, index:from:to)",
            "positive_prompt": positive,
            "candidates": bridge.candidates, "motion": transition.motion, "mode": transition.mode,
            "requested_seconds": bridge.requested_seconds,
            "anchor_span_seconds": bridge.actual_span_seconds,
            "timing_error_seconds": bridge.timing_error_seconds,
            "depends_on": [f"anchor:{bridge.from_anchor}", f"anchor:{bridge.to_anchor}"],
        }
        if negative is not None:  # only choreographed bridges; keeps older plan hashes unchanged
            tasks[task_id]["negative_prompt"] = negative
        order.append(task_id)

    fps = render.generation_fps
    unique = 1 + sum(b.frames - 1 for b in bridges)
    tasks["final:movie"] = {
        "id": "final:movie", "kind": "final",
        "unique_frames_if_endpoints_match": unique,
        "anchor_span_seconds": sum(b.frames - 1 for b in bridges) / fps,
        "nominal_duration_seconds": unique / fps,
        "generation_fps": fps, "delivery_fps": render.delivery_fps,
        "audio": storyboard.audio.file or "none",
        "audio_sync": storyboard.audio.synchronization if storyboard.audio.file else "none",
        "join_rule": "drop a later clip's first frame only after its decoded first frame is verified "
                     "against the previous clip's last frame (shared anchor); no crossfades",
        "depends_on": [t for t in order if t.startswith("bridge:")],
    }
    order.append("final:movie")

    requirements = {}
    for capability, rel in chosen.items():
        needed = capability == "wan_flf2v" or any(
            t["kind"] == "anchor" and t["capability"] == capability for t in tasks.values())
        if needed:
            requirements[capability] = {"profile": rel, "exists": (root / rel).is_file()}
    plan_core = {"order": order, "tasks": tasks,
                 "profiles": {k: v["profile"] for k, v in requirements.items()}}
    return {
        "schema": 1,
        "storyboard": storyboard.name,
        "storyboard_sha256": hashlib.sha256(storyboard_bytes).hexdigest() if storyboard_bytes else None,
        "plan_sha256": hashlib.sha256(_canonical(plan_core).encode("utf-8")).hexdigest(),
        "order": order,
        "tasks": tasks,
        "requirements": requirements,
        "blocked": sorted(f"{cap}: missing {req['profile']}" for cap, req in requirements.items()
                          if not req["exists"]),
        "note": "Plan only. No ComfyUI request was made; GPU stages need --confirm-gpu.",
    }
