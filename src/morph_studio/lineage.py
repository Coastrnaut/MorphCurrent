"""Long-chain lineage and drift control (F35). Offline; re-anchoring is always an explicit owner decision.

``lineage`` gives every anchor its root (last separately generated anchor), reference-edit depth and chain.
``drift_curve`` measures rendered anchors against their act's reference image (subject colour, sharpness,
centring, scale). ``propose`` picks anchors to restart as explicit independent keyframes so no chain exceeds
the depth limit (plus the first drift-flagged anchor per act), with the exact invalidation from the F33 rule;
``apply_proposals`` writes them to a *new* storyboard. ``shared_check`` confirms each bridge used the exact
recorded anchor bytes.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import yaml

DEFAULT_CONFIG = Path("configs/film/lineage.yaml")


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if int(data.get("depth_limit", 0)) < 1:
        raise ValueError("lineage config needs depth_limit >= 1")
    return data


def _anchor_tasks(plan: dict) -> list[dict]:
    return [plan["tasks"][t] for t in plan["order"] if plan["tasks"][t]["kind"] == "anchor"]


def lineage(plan: dict, limit: int | None = None) -> dict:
    entries, by_id = [], {}
    for task in _anchor_tasks(plan):
        parent = by_id.get(task.get("reference")) if task.get("conditioned_on_parent") else None
        if parent:
            entry = {"anchor": task["anchor"], "chapter": task.get("chapter"), "root": parent["root"],
                     "depth": parent["depth"] + 1, "chain": parent["chain"] + [task["anchor"]]}
        else:
            entry = {"anchor": task["anchor"], "chapter": task.get("chapter"), "root": task["anchor"], "depth": 0,
                     "chain": [task["anchor"]]}
        by_id[task["anchor"]] = entry
        entries.append(entry)
    per_act: dict = {}
    for e in entries:
        per_act[e["chapter"]] = max(per_act.get(e["chapter"], 0), e["depth"])
    report = {"entries": entries, "per_act_max": per_act, "max_depth": max((e["depth"] for e in entries), default=0),
              "limit": limit}
    report["over_limit"] = [e["anchor"] for e in entries if limit is not None and e["depth"] > limit]
    return report


def _image_metrics(path: Path) -> dict:
    from .geometry import image_geometry
    from .qa_subject import decode_rgb_frames, frame_metrics
    geo = image_geometry(path)
    sharp = frame_metrics(decode_rgb_frames(path)[:1])[0]["sharpness"]
    return {"geo": geo, "sharpness": sharp}


def drift_curve(storyboard: str | Path, run_dir: str | Path, config: dict) -> dict:
    from .release import _stage_files
    from .schema import load_storyboard
    sb = load_storyboard(storyboard)
    files = _stage_files(Path(run_dir))
    metrics, missing = {}, []
    for a in sb.anchors:
        file = (files.get(f"anchor:{a.id}") or {}).get("file")
        if file and Path(file).is_file():
            metrics[a.id] = _image_metrics(Path(file))
        else:
            missing.append(a.id)
    depth = {}
    for a in sb.anchors:
        depth[a.id] = depth.get(a.reference, -1) + 1 if a.generation == "reference_edit" else 0
    d = config["drift"]
    reference: dict = {}
    points = []
    for i, a in enumerate(sb.anchors):
        act = a.chapter
        if i == 0 or act != sb.anchors[i - 1].chapter:
            reference[act] = a.id
        ref = reference[act]
        if a.id not in metrics or ref not in metrics:
            if a.id not in missing:
                missing.append(a.id)
            continue
        m, r = metrics[a.id], metrics[ref]
        flags, point = [], {"anchor": a.id, "act": act, "reference": ref, "depth": depth[a.id]}
        if m["geo"].get("mask_unreliable") or "centroid" not in m["geo"] or "centroid" not in r["geo"]:
            point["flags"] = ["unreliable"]
            points.append(point)
            continue
        colour = round(math.dist(m["geo"]["mean_colour"], r["geo"]["mean_colour"]), 1)
        sharp_ratio = round(m["sharpness"] / r["sharpness"], 3) if r["sharpness"] else None
        cx, cy = m["geo"]["centroid"]
        offset = round(math.hypot(cx - 0.5, cy - 0.5), 4)
        ext, rext = m["geo"]["extent"], r["geo"]["extent"]
        scale = round(math.sqrt((ext[0] * ext[1]) / (rext[0] * rext[1])), 3) if rext[0] and rext[1] else None
        if colour > d["colour_max"]:
            flags.append("colour")
        if sharp_ratio is not None and sharp_ratio < d["sharpness_min_ratio"]:
            flags.append("sharpness")
        if offset > d["centroid_max"]:
            flags.append("centroid")
        if scale is not None and not d["scale_ratio"][0] <= scale <= d["scale_ratio"][1]:
            flags.append("scale")
        point.update(colour_distance=colour, sharpness_ratio=sharp_ratio, centroid_offset=offset, scale_ratio=scale,
                     flags=flags)
        points.append(point)
    return {"storyboard": sb.name, "points": points, "missing": missing,
            "ok": not any(p["flags"] for p in points),
            "note": "Drift versus each act's reference anchor; thresholds are starting points for owner calibration."}


def propose(plan: dict, limit: int, curve: dict | None = None) -> dict:
    from .accuracy import impact
    entries = lineage(plan)["entries"]
    first_of_act, prev_chapter = set(), object()
    for e in entries:
        if e["chapter"] != prev_chapter:
            first_of_act.add(e["anchor"])
        prev_chapter = e["chapter"]
    reasons: dict[str, list[str]] = {}
    # depth cuts: walk anchors, tracking depth since the last (existing or proposed) separate keyframe
    since: dict[str, int] = {}
    tasks = {t["anchor"]: t for t in _anchor_tasks(plan)}
    for e in entries:
        task = tasks[e["anchor"]]
        if task.get("conditioned_on_parent") and task.get("reference") in since:
            d = since[task["reference"]] + 1
            if d > limit and e["anchor"] not in first_of_act:
                reasons.setdefault(e["anchor"], []).append("depth")
                d = 0
        else:
            d = 0
        since[e["anchor"]] = d
    if curve:
        seen_acts = set()
        for p in curve.get("points", []):
            flags = [f for f in p.get("flags", []) if f != "unreliable"]
            if flags and p.get("act") not in seen_acts and p["anchor"] not in first_of_act:
                seen_acts.add(p.get("act"))
                reasons.setdefault(p["anchor"], []).append("drift:" + ",".join(flags))
    order = [e["anchor"] for e in entries]
    proposals = []
    for anchor in [a for a in order if a in reasons]:
        imp = impact(plan, [anchor])
        stop = [a for a in imp["invalidated_anchors"] if a in reasons and a != anchor]
        kept = imp["invalidated_anchors"]
        if stop:  # a later proposal restarts the chain itself
            kept = kept[:kept.index(stop[0])]
        proposals.append({"anchor": anchor, "reasons": reasons[anchor], "invalidated_anchors": kept,
                          "invalidated_bridges": [b for b in imp["invalidated_bridges"]
                                                  if b.split(":", 1)[1].split("->")[0] in kept
                                                  or b.split(":", 1)[1].split("->")[1] in kept]})
    depth_after = max(since.values(), default=0)
    return {"limit": limit, "proposals": proposals, "max_depth_after": depth_after,
            "note": "Proposals only: adopt by reviewing the written storyboard; nothing is changed silently."}


def apply_proposals(storyboard: str | Path, anchors: list[str], out: str | Path) -> Path:
    from .schema import Storyboard
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"{out} exists; refusing to overwrite")
    data = yaml.safe_load(Path(storyboard).read_text(encoding="utf-8"))
    ids = [a["id"] for a in data["anchors"]]
    for anchor in data["anchors"]:
        if anchor["id"] in anchors:
            anchor["generation"] = "independent_t2i"
            anchor["reference"] = ids[ids.index(anchor["id"]) - 1]
    Storyboard.model_validate(data)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"# F35 re-anchor proposal for {Path(storyboard).name}: {len(anchors)} anchor(s) made explicit "
                   f"independent keyframes ({', '.join(anchors)}). Review before adopting.\n"
                   + yaml.safe_dump(data, sort_keys=False, width=120), encoding="utf-8")
    return out


def shared_check(run_dir: str | Path) -> dict:
    run = Path(run_dir)
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    stages = manifest.get("stages") or {}
    hashes = {k.split(":", 1)[1]: v.get("image_sha256") for k, v in stages.items() if k.startswith("anchor:")}
    results = []
    for key, stage in stages.items():
        if not key.startswith("bridge:"):
            continue
        a, b = key.split(":", 1)[1].split("->")
        job = run.parent / Path(str(stage.get("job_dir") or "").replace("\\", "/")).name
        record = None
        try:
            record = json.loads((job / "job.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        for endpoint, role, anchor in (("start", "start_image", a), ("end", "end_image", b)):
            used = ((record or {}).get("anchors") or {}).get(role, {}).get("sha256") if record else None
            expected = hashes.get(anchor)
            status = "unchecked" if not used or not expected else ("match" if used == expected else "mismatch")
            results.append({"bridge": key, "endpoint": endpoint, "anchor": anchor, "expected": expected,
                            "used": used, "status": status})
    return {"results": results, "ok": bool(results) and all(r["status"] == "match" for r in results)}
