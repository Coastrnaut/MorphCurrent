"""Long-form sequencing helpers (F19). Pure: no ComfyUI, no network.

- ``stage_identities`` / ``plan_diff``: which stages an edit re-runs, and why. A stage's
  identity hashes only its inference-relevant fields plus its dependencies' identities, so a
  reference-edit lineage change invalidates every descendant edit and bridge touching them.
- ``chapter_index`` / ``ffmetadata``: anchor and chapter timestamps in the final movie.
- ``proxy_storyboard``: a cheap preview variant with its own plan identity.
- ``estimate_bytes`` / ``storage_report`` / ``disk_preflight``: storage accounting.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Callable

from .schema import Storyboard

IDENTITY_FIELDS = {
    "anchor": ("method", "positive_prompt", "negative_prompt", "seed", "width", "height"),
    "bridge": ("frames", "fps", "width", "height", "seed", "positive_prompt", "negative_prompt",
               "candidates"),
}
PROFILE_FOR = {"anchor": {"text_to_image": "text_to_image", "independent_t2i": "text_to_image",
                          "reference_edit": "reference_edit"}}
PROXY_SIZE = (640, 368)  # BENCH-001: fastest measured Wan size (≈240 s per 65-frame bridge)
# Measured on MC-RUN artifacts: anchor PNG 0.42–0.49 MB at 832x480 (≈1.2 B/px), 65-frame bridge
# MP4 0.73–1.38 MB (≈0.053 B per frame-pixel). Rounded up for safety, then doubled because
# ComfyUI keeps its own copy in its output folder.
ANCHOR_BYTES_PER_PX = 2.0
BRIDGE_BYTES_PER_FRAME_PX = 0.1
COPIES = 2
GIB = 1024 ** 3


def _canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _own_fields(task: dict, profiles: dict) -> dict:
    kind = task["kind"]
    if kind not in IDENTITY_FIELDS:
        return {"kind": kind}
    own = {f: task.get(f) for f in IDENTITY_FIELDS[kind]}
    capability = PROFILE_FOR["anchor"][task["method"]] if kind == "anchor" else "wan_flf2v"
    own["profile"] = profiles.get(capability)
    own["kind"] = kind
    return own


def stage_identities(plan: dict) -> dict[str, str]:
    """Merkle identity per task (plan order is topological)."""
    profiles = plan.get("profiles") or {k: v["profile"] for k, v in plan.get("requirements", {}).items()}
    ids: dict[str, str] = {}
    for task_id in plan["order"]:
        task = plan["tasks"][task_id]
        deps = [ids[d] for d in task.get("depends_on", [])]
        ids[task_id] = hashlib.sha256(_canonical([_own_fields(task, profiles), deps]).encode()).hexdigest()
    return ids


def plan_diff(old: dict, new: dict) -> dict:
    """Compare two compiled plans: what stays cached, what re-runs and why."""
    old_ids, new_ids = stage_identities(old), stage_identities(new)
    old_by_identity = {v: k for k, v in old_ids.items()}
    old_profiles = old.get("profiles") or {}
    new_profiles = new.get("profiles") or {}
    rows, rerun = [], set()
    for task_id in new["order"]:
        task = new["tasks"][task_id]
        identity = new_ids[task_id]
        if identity in old_by_identity:
            status, reason = "cached", None
            if old_by_identity[identity] != task_id:
                reason = f"same content as {old_by_identity[identity]}"
        elif task_id not in old["tasks"]:
            status, reason = "rerun", "added"
        else:
            own_changed = _own_fields(task, new_profiles) != _own_fields(old["tasks"][task_id], old_profiles)
            upstream = next((d for d in task.get("depends_on", []) if d in rerun), None)
            status = "rerun"
            reason = "direct" if own_changed else f"upstream:{upstream}" if upstream else "dependencies"
        if status == "rerun":
            rerun.add(task_id)
        rows.append({"task": task_id, "kind": task["kind"], "status": status, "reason": reason})
    removed = [t for t in old["order"] if t not in new["tasks"] and old_ids[t] not in set(new_ids.values())]
    gpu = [r for r in rows if r["kind"] in ("anchor", "bridge") and r["status"] == "rerun"]
    return {"old_plan": old["plan_sha256"], "new_plan": new["plan_sha256"], "stages": rows,
            "removed": removed, "gpu_rerun": len(gpu),
            "gpu_cached": sum(r["kind"] in ("anchor", "bridge") and r["status"] == "cached" for r in rows),
            "rerun_anchors": [r["task"] for r in gpu if r["kind"] == "anchor"],
            "rerun_bridges": [r["task"] for r in gpu if r["kind"] == "bridge"]}


def chapter_index(storyboard: Storyboard, plan: dict) -> dict:
    """Anchor and chapter timestamps (seconds) in the joined final movie."""
    fps = storyboard.render.generation_fps
    spans = {(t["from"], t["to"]): t["frames"] - 1 for t in plan["tasks"].values() if t["kind"] == "bridge"}
    anchors, frame = [], 0
    ids = [a.id for a in storyboard.anchors]
    for i, anchor in enumerate(storyboard.anchors):
        anchors.append({"anchor": anchor.id, "chapter": anchor.chapter, "frame": frame,
                        "time_s": round(frame / fps, 4)})
        if i + 1 < len(ids):
            frame += spans[(ids[i], ids[i + 1])]
    end_s = round((frame + 1) / fps, 4)  # nominal container duration (unique frames / fps)
    chapters: list[dict] = []
    for row in anchors:
        name = row["chapter"]
        if name is None:
            continue
        if not chapters or chapters[-1]["chapter"] != name:
            chapters.append({"chapter": name, "start_s": row["time_s"], "anchors": []})
        chapters[-1]["anchors"].append(row["anchor"])
    for i, chapter in enumerate(chapters):
        chapter["end_s"] = chapters[i + 1]["start_s"] if i + 1 < len(chapters) else end_s
    return {"fps": fps, "duration_s": end_s, "anchors": anchors, "chapters": chapters}


def ffmetadata(index: dict) -> str:
    """FFMETADATA1 chapter file (``ffmpeg -i movie -i chapters.txt -map_metadata 1 -codec copy``)."""
    lines = [";FFMETADATA1"]
    for chapter in index["chapters"]:
        title = chapter["chapter"].replace("=", "\\=").replace(";", "\\;").replace("#", "\\#")
        lines += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={round(chapter['start_s'] * 1000)}",
                  f"END={round(chapter['end_s'] * 1000)}", f"title={title}"]
    return "\n".join(lines) + "\n"


def proxy_storyboard(data: dict, size: tuple[int, int] = PROXY_SIZE) -> dict:
    """Preview variant of a raw storyboard mapping: smaller frames, ``-proxy`` name suffix."""
    out = json.loads(json.dumps(data))
    out["render"]["width"], out["render"]["height"] = size
    if not out["name"].endswith("-proxy"):
        out["name"] = f"{out['name']}-proxy"
    return out


def estimate_bytes(task: dict) -> int:
    pixels = int(task.get("width", 0)) * int(task.get("height", 0))
    if task["kind"] == "anchor":
        return int(pixels * ANCHOR_BYTES_PER_PX * COPIES)
    if task["kind"] == "bridge":
        return int(pixels * task["frames"] * BRIDGE_BYTES_PER_FRAME_PX * COPIES * task.get("candidates", 1))
    if task["kind"] == "final":
        return 0  # counted from bridges below
    return 0


def plan_bytes(plan: dict, done: set[str] | frozenset = frozenset()) -> dict:
    """Estimated new bytes for stages not yet done (final movie ≈ sum of its bridges, one copy)."""
    rows = {t: estimate_bytes(plan["tasks"][t]) for t in plan["order"] if t not in done}
    bridges = sum(estimate_bytes(plan["tasks"][t]) // (COPIES * plan["tasks"][t].get("candidates", 1))
                  for t in plan["order"] if plan["tasks"][t]["kind"] == "bridge")  # one chosen take each
    if "final:movie" in rows:
        rows["final:movie"] = bridges
    return {"stages": rows, "total_bytes": sum(rows.values())}


def verified_identities(runs_root: str | Path) -> set[str]:
    """Stage identities already verified in any earlier run (content-addressed jobs are reused)."""
    found: set[str] = set()
    root = Path(runs_root)
    if not root.is_dir():
        return found
    for run in root.glob("run-*"):
        try:
            plan = json.loads((run / "plan.json").read_text(encoding="utf-8"))
            stages = json.loads((run / "manifest.json").read_text(encoding="utf-8")).get("stages", {})
            ids = stage_identities(plan)
        except (OSError, ValueError, KeyError, TypeError):
            continue
        found.update(ids[t] for t, s in stages.items() if s.get("state") == "verified" and t in ids)
    return found


def cached_stages(plan: dict, runs_root: str | Path) -> set[str]:
    """Tasks of ``plan`` whose identical stage was already verified in some run."""
    known = verified_identities(runs_root)
    return {t for t, ident in stage_identities(plan).items() if ident in known}


def disk_preflight(plan: dict, runs_root: str | Path, *, done: set[str] | frozenset = frozenset(),
                   min_free_gb: float = 2.0,
                   disk_usage: Callable[[Path], tuple] | None = None) -> dict:
    root = Path(runs_root)
    probe_at = root
    while not probe_at.exists() and probe_at != probe_at.parent:
        probe_at = probe_at.parent
    free = (disk_usage or shutil.disk_usage)(probe_at)[2]  # resolved at call time
    need = plan_bytes(plan, done)["total_bytes"]
    reserve = int(min_free_gb * GIB)
    return {"free_bytes": free, "needed_bytes": need, "reserve_bytes": reserve,
            "ok": free - need >= reserve,
            "message": (f"need ~{need / GIB:.2f} GiB for uncached stages plus a {min_free_gb:g} GiB reserve; "
                        f"{free / GIB:.2f} GiB free at {probe_at}")}


def storage_report(runs_root: str | Path) -> dict:
    """Bytes in the runs root by job kind and state (read-only)."""
    root = Path(runs_root)
    kinds: dict[str, dict] = {}
    runs = {"count": 0, "bytes": 0}
    if not root.is_dir():
        return {"runs_root": str(root), "jobs": kinds, "runs": runs, "total_bytes": 0}
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        size = sum(f.stat().st_size for f in entry.rglob("*") if f.is_file())
        if entry.name.startswith("run-"):
            runs["count"] += 1
            runs["bytes"] += size
            continue
        record = entry / "job.json"
        kind, state = "unknown", "unknown"
        if record.is_file():
            try:
                data = json.loads(record.read_text(encoding="utf-8"))
                raw = str(data.get("kind", ""))
                kind = "anchor" if "anchor" in raw else "bridge" if "bridge" in raw else raw or "unknown"
                state = data.get("state", "unknown")
            except (OSError, ValueError):
                pass
        bucket = kinds.setdefault(kind, {"count": 0, "bytes": 0, "states": {}})
        bucket["count"] += 1
        bucket["bytes"] += size
        bucket["states"][state] = bucket["states"].get(state, 0) + 1
    total = runs["bytes"] + sum(b["bytes"] for b in kinds.values())
    return {"runs_root": str(root), "jobs": kinds, "runs": runs, "total_bytes": total}
