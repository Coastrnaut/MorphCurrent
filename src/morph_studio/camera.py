"""Camera moves and framing consistency (F23). Offline; no ComfyUI contact.

The installed Wan 2.2 FLF2V workflow is conditioned only on its first and last frames and has no
camera-control input, so a camera move is a deterministic **prompt-only approximation** and is
labelled as such. Because both end frames are fixed images, a requested move must agree with them;
``satisfiability`` checks that from the measured anchor geometry (F12) before bridge GPU time is
spent. ``framing_check`` and ``crop_check`` test per-anchor targets and 16:9 / 9:16 safe areas.
"""
from __future__ import annotations

from pathlib import Path

from .geometry import CENTROID_MAX, EXTENT_RANGE

LABEL = "prompt-only approximation"
SAFE_MARGIN = 0.05
UNVERIFIABLE = {"orbit_left", "orbit_right", "rise"}
# F13 choreography cameras expressed as F23 moves (used when a transition has no explicit camera)
FROM_CHOREOGRAPHY = {"static": ("static", 0.0), "slow_push": ("push_in", 0.1), "slow_pull": ("pull_out", 0.1),
                     "orbit_left": ("orbit_left", 0.1), "orbit_right": ("orbit_right", 0.1),
                     "rising": ("rise", 0.1)}


def _degree(amount: float) -> str:
    return "slightly" if amount < 0.10 else "moderately" if amount < 0.25 else "strongly"


def camera_clause(move: str, amount: float) -> str:
    """Deterministic prompt wording for a camera move."""
    pct = f"about {round(amount * 100)}% of the frame"
    d = _degree(amount)
    return {
        "static": "The camera stays locked off, front-facing, with no movement.",
        "push_in": f"The camera pushes in {d}, moving {pct} closer to the subject.",
        "pull_out": f"The camera pulls out {d}, moving {pct} farther from the subject.",
        "pan_left": f"The camera pans left {d}, sweeping {pct}.",
        "pan_right": f"The camera pans right {d}, sweeping {pct}.",
        "tilt_up": f"The camera tilts up {d}, sweeping {pct}.",
        "tilt_down": f"The camera tilts down {d}, sweeping {pct}.",
        "orbit_left": f"The camera orbits {d} to the left around the subject, {pct}.",
        "orbit_right": f"The camera orbits {d} to the right around the subject, {pct}.",
        "rise": f"The camera rises {d}, {pct}, keeping the subject in view.",
    }[move]


def graph_camera_nodes(graph: dict) -> list[str]:
    """Camera-control nodes present in an API graph (none in the installed Wan FLF2V export)."""
    return sorted({n.get("class_type", "") for n in graph.values()
                   if isinstance(n, dict) and "camera" in str(n.get("class_type", "")).lower()})


def require_graph_control(graph: dict, workflow_name: str) -> None:
    """Graph-level camera control is never accepted yet: either the workflow has no camera input,
    or a camera node exists but no binding drives it (capability registry, F27)."""
    nodes = graph_camera_nodes(graph)
    if not nodes:
        raise ValueError(f"camera control 'graph' requested but {workflow_name} has no camera-control "
                         "input; use control: prompt (a labelled prompt-only approximation)")
    raise ValueError(f"camera control 'graph' requested: {workflow_name} contains {', '.join(nodes)} but no "
                     "binding drives it yet (F27 capability registry); use control: prompt")


def _ratio(start: dict, end: dict) -> float | None:
    try:
        return round(sum(end["extent"][i] / start["extent"][i] for i in (0, 1)) / 2, 3)
    except (KeyError, ZeroDivisionError, TypeError):
        return None


def satisfiability(move: str, amount: float, start: dict, end: dict) -> dict:
    """Can a camera move connect two fixed endpoint frames? Thresholds: spec Clarifications."""
    out: dict = {"move": move, "amount": amount}
    if move in UNVERIFIABLE:
        return {**out, "verdict": "not_verifiable", "reason": "orbit/rise cannot be verified from 2D framing - review"}
    if any(g.get("mask_unreliable") or g.get("subject_too_small") or "centroid" not in g for g in (start, end)):
        return {**out, "verdict": "unknown", "reason": "subject not measurable reliably - review"}
    r = _ratio(start, end)
    dx = round(end["centroid"][0] - start["centroid"][0], 4)
    dy = round(end["centroid"][1] - start["centroid"][1], 4)
    shift = round((dx ** 2 + dy ** 2) ** 0.5, 4)
    out.update(extent_ratio=r, dx=dx, dy=dy)
    half = amount / 2
    rules = {
        "push_in": (r >= 1 + half, f"push in needs the end subject >= {1 + half:.3f}x larger (measured {r})"),
        "pull_out": (r <= 1 / (1 + half), f"pull out needs the end subject <= {1 / (1 + half):.3f}x (smaller; measured {r})"),
        "pan_left": (dx >= half, f"pan left needs the subject to move right by >= {half:.3f} (measured dx {dx})"),
        "pan_right": (dx <= -half, f"pan right needs the subject to move left by >= {half:.3f} (measured dx {dx})"),
        "tilt_up": (dy >= half, f"tilt up needs the subject to move down by >= {half:.3f} (measured dy {dy})"),
        "tilt_down": (dy <= -half, f"tilt down needs the subject to move up by >= {half:.3f} (measured dy {dy})"),
        "static": (shift <= CENTROID_MAX and EXTENT_RANGE[0] <= r <= EXTENT_RANGE[1],
                   f"static needs centre shift <= {CENTROID_MAX} and size ratio {EXTENT_RANGE[0]}-{EXTENT_RANGE[1]} "
                   f"(measured shift {shift}, ratio {r})"),
    }
    ok, reason = rules[move]
    return {**out, "verdict": "satisfiable" if ok else "unsatisfiable", "reason": reason}


def framing_check(geo: dict, target: dict) -> dict:
    if "centroid" not in geo:
        return {"on_target": None, "reason": "subject not measurable - review"}
    cx, cy = geo["centroid"]
    size = round(sum(geo["extent"]) / 2, 4)
    tol = target.get("tolerance", 0.08)
    centre = target.get("center", (0.5, 0.5))
    lo, hi = target.get("size", (0.2, 0.8))
    problems = []
    if abs(cx - centre[0]) > tol or abs(cy - centre[1]) > tol:
        problems.append(f"centre ({cx}, {cy}) outside ({centre[0]}, {centre[1]}) +/- {tol}")
    if not lo <= size <= hi:
        problems.append(f"size {size} outside {lo}-{hi}")
    return {"on_target": not problems, "center": [cx, cy], "size": size, "reason": "; ".join(problems) or None}


def crop_check(geo: dict, width: int, height: int, crops: list[str], margin: float = SAFE_MARGIN) -> dict:
    """inside/outside per delivery crop: subject box (centroid +/- extent/2) within the crop's safe area."""
    if "centroid" not in geo:
        return {c: "unknown" for c in crops}
    cx, cy = geo["centroid"]
    ex, ey = geo["extent"]
    box = (cx - ex / 2, cx + ex / 2, cy - ey / 2, cy + ey / 2)
    out = {}
    for crop in crops:
        crop_w = 1.0 if crop == "16:9" else min(1.0, height * 9 / 16 / width)
        x0, x1 = 0.5 - crop_w / 2, 0.5 + crop_w / 2
        sx0, sx1 = x0 + margin * crop_w, x1 - margin * crop_w
        sy0, sy1 = margin, 1 - margin
        inside = box[0] >= sx0 - 1e-9 and box[1] <= sx1 + 1e-9 and box[2] >= sy0 - 1e-9 and box[3] <= sy1 + 1e-9
        out[crop] = "inside" if inside else "outside"
    return out


def _move_of(transition) -> tuple[str, float, bool]:
    """(move, amount, explicit) for a transition."""
    if transition.camera:
        return transition.camera.move, transition.camera.amount, True
    chor = transition.choreography.camera if transition.choreography else "static"
    move, amount = FROM_CHOREOGRAPHY[chor]
    return move, amount, False


def camera_check(storyboard_path: str | Path, run_dir: str | Path | None = None, repo_root: str | Path = ".") -> dict:
    from .geometry import image_geometry
    from .release import _stage_files
    from .schema import load_storyboard
    sb = load_storyboard(storyboard_path)
    geos: dict[str, dict] = {}
    if run_dir:
        for task, entry in _stage_files(Path(run_dir)).items():
            if task.startswith("anchor:") and entry.get("file") and Path(entry["file"]).is_file():
                geos[task.split(":", 1)[1]] = image_geometry(entry["file"])
    transitions = []
    for tr in sb.transitions:
        move, amount, explicit = _move_of(tr)
        row = {"transition": f"{tr.from_anchor}->{tr.to_anchor}", "move": move, "amount": amount,
               "source": "camera" if explicit else "choreography/default",
               "clause": camera_clause(move, amount), "label": LABEL}
        if tr.from_anchor in geos and tr.to_anchor in geos:
            row.update({k: v for k, v in satisfiability(move, amount, geos[tr.from_anchor], geos[tr.to_anchor]).items()
                        if k not in ("move", "amount")})
        else:
            row["verdict"] = "pending_anchors"
        transitions.append(row)
    anchors = []
    crops = list(sb.render.delivery_crops)
    for anchor in sb.anchors:
        if anchor.id not in geos:
            continue
        g = geos[anchor.id]
        row = {"anchor": anchor.id, "center": g.get("centroid"), "extent": g.get("extent")}
        if anchor.framing:
            row["framing"] = framing_check(g, anchor.framing.model_dump())
        if crops:
            row["crops"] = crop_check(g, sb.render.width, sb.render.height, crops)
        anchors.append(row)
    bad = any(t["verdict"] == "unsatisfiable" for t in transitions) or any(
        a.get("framing", {}).get("on_target") is False or "outside" in (a.get("crops") or {}).values()
        for a in anchors)
    verdict = "issues" if bad else ("pending_anchors" if not geos else "ok")
    return {"storyboard": str(storyboard_path), "run": str(run_dir) if run_dir else None,
            "transitions": transitions, "anchors": anchors, "verdict": verdict,
            "note": f"Camera moves are a {LABEL}: the installed Wan FLF2V workflow has no camera input."}
