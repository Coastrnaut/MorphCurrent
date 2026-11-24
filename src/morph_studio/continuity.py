"""Temporal shape / material continuity diagnostics, repair proposals and controlled comparison (F24).

Works on the F16 128x74 RGB analysis frames. One mask threshold per clip (from the endpoint frames)
keeps masks comparable across frames, so a sudden shape replacement, parts vanishing or splitting,
a changing background, a jumping subject or a sudden colour/material switch show up as numbers in a
frame window. Thresholds were fixed in the spec Clarifications before any evaluation. Everything is a
heuristic proxy - not optical flow and not proof of physical identity; the owner decides.
"""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path
from typing import Callable

from .geometry import H, W, _otsu

MIN_PART = 0.005          # components smaller than 0.5% of the frame are glints
SUBST_IOU, SUBST_MEDIAN = 0.45, 0.70
TOPO_DELTA, TOPO_MIN_RUN = 2, 2
BG_FLOOR, MOTION_FLOOR, COLOUR_FLOOR, REL = 12.0, 0.06, 40.0, 4.0
UNRELIABLE_AREA = 0.90
ENDPOINT_MAD = 2.0
MIN_HALF = 17
COMPARE_VERDICT_OK = "candidate improvement - needs owner review"
LABEL_TOLERANCE = 4
REFINEMENTS = {
    "shape_substitution": "The subject transforms continuously part by part; no part is replaced or swapped.",
    "topology_change": "All parts stay attached and visible throughout; nothing disappears or splits off.",
    "background_change": "The background stays dark and unchanged throughout.",
    "motion_jump": "The subject moves smoothly with no jumps, staying centred.",
    "colour_jump": "Materials and colours change gradually; no sudden colour or material switch.",
    "subject_collapse": "The subject keeps its full size throughout the transformation.",
    "subject_drift": "The subject stays centred in the frame.",
    "blur_dip": "The subject stays sharp and in focus.",
}


def _lum(px) -> list[float]:
    return [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in px]


def _centred_threshold(lum: list[float]) -> float:
    """Otsu split, then the midpoint of the two class means (stable for two-tone frames)."""
    t = _otsu([round(v) for v in lum])
    lo = [v for v in lum if v <= t]
    hi = [v for v in lum if v > t]
    if not lo or not hi:
        return float(t)
    return (sum(lo) / len(lo) + sum(hi) / len(hi)) / 2


def clip_threshold(frames) -> int:
    ends = [frames[0], frames[-1]]
    return max(24, round(sum(_centred_threshold(_lum(f)) for f in ends) / 2))


def _parts(mask: list[bool]) -> int:
    seen = bytearray(len(mask))
    count, minimum = 0, MIN_PART * len(mask)
    for start, on in enumerate(mask):
        if not on or seen[start]:
            continue
        stack, size = [start], 0
        seen[start] = 1
        while stack:
            i = stack.pop()
            size += 1
            x, y = i % W, i // W
            for j in ((i - 1) if x > 0 else -1, (i + 1) if x < W - 1 else -1,
                      (i - W) if y > 0 else -1, (i + W) if y < H - 1 else -1):
                if j >= 0 and mask[j] and not seen[j]:
                    seen[j] = 1
                    stack.append(j)
        count += size >= minimum
    return count


def frame_metrics(frames, threshold: int | None = None) -> list[dict]:
    threshold = threshold if threshold is not None else clip_threshold(frames)
    rows, prev_mask, prev_lum = [], None, None
    for k, px in enumerate(frames):
        lum = _lum(px)
        mask = [v > threshold for v in lum]
        area = sum(mask) / len(mask)
        row: dict = {"frame": k, "occupancy": round(area, 4), "unreliable": area > UNRELIABLE_AREA or area == 0,
                     "overlap_prev": None, "background_change": None, "centre": None, "colour": None,
                     "parts": _parts(mask)}
        if sum(mask):
            xs = [i % W for i, m in enumerate(mask) if m]
            ys = [i // W for i, m in enumerate(mask) if m]
            row["centre"] = [round(sum(xs) / len(xs) / W, 4), round(sum(ys) / len(ys) / H, 4)]
            sub = [p for p, m in zip(px, mask) if m]
            row["colour"] = [round(sum(c[i] for c in sub) / len(sub), 1) for i in range(3)]
        if prev_mask is not None:
            inter = sum(a and b for a, b in zip(mask, prev_mask))
            union = sum(a or b for a, b in zip(mask, prev_mask))
            row["overlap_prev"] = round(inter / union, 4) if union else 1.0
            bg = [abs(a - b) for a, b, m1, m2 in zip(lum, prev_lum, mask, prev_mask) if not m1 and not m2]
            row["background_change"] = round(sum(bg) / len(bg), 3) if bg else 0.0
        rows.append(row)
        prev_mask, prev_lum = mask, lum
    return rows


def _windows(indices: list[int], min_run: int = 1) -> list[list[int]]:
    runs, start, last = [], None, None
    for i in sorted(indices) + [None]:
        if start is None:
            start = last = i
        elif i is not None and i == last + 1:
            last = i
        else:
            if start is not None and last - start + 1 >= min_run:
                runs.append([start, last])
            start = last = i
    return runs


def _dist(a, b) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def detect_continuity(frames) -> dict:
    threshold = clip_threshold(frames)
    m = frame_metrics(frames, threshold)
    ok = [r for r in m if not r["unreliable"]]
    excluded = [r["frame"] for r in m if r["unreliable"]]
    flags: list[dict] = []
    if len(ok) >= 3:
        pairs = [(m[k - 1], m[k]) for k in range(1, len(m)) if not m[k]["unreliable"] and not m[k - 1]["unreliable"]]
        overlaps = [b["overlap_prev"] for _, b in pairs]
        median_iou = statistics.median(overlaps) if overlaps else 1.0
        if median_iou >= SUBST_MEDIAN:
            low = [b["frame"] for _, b in pairs if b["overlap_prev"] < SUBST_IOU]
            for w in _windows(low):
                flags.append({"type": "shape_substitution", "frames": w,
                              "overlap": min(m[k]["overlap_prev"] for k in range(w[0], w[1] + 1)),
                              "median_overlap": round(median_iou, 3)})
        p0, p1 = m[0]["parts"], m[-1]["parts"]
        hi, lo = max(p0, p1) + TOPO_DELTA, min(p0, p1) - TOPO_DELTA
        odd = [r["frame"] for r in ok if r["parts"] >= hi or (min(p0, p1) >= 3 and r["parts"] <= lo)]
        for w in _windows(odd, TOPO_MIN_RUN):
            parts = [m[k]["parts"] for k in range(w[0], w[1] + 1)]
            flags.append({"type": "topology_change", "frames": w, "parts": max(parts, key=lambda v: abs(v - p0)),
                          "endpoint_parts": [p0, p1]})
        for key, kind, floor in (("background_change", "background_change", BG_FLOOR),):
            values = [b[key] for _, b in pairs]
            limit = max(floor, REL * (statistics.median(values) if values else 0))
            for w in _windows([b["frame"] for _, b in pairs if b[key] > limit]):
                flags.append({"type": kind, "frames": w, "threshold": round(limit, 3),
                              "change": max(m[k][key] for k in range(w[0], w[1] + 1))})
        for field, kind, floor in (("centre", "motion_jump", MOTION_FLOOR), ("colour", "colour_jump", COLOUR_FLOOR)):
            steps = [(b["frame"], _dist(a[field], b[field])) for a, b in pairs if a[field] and b[field]]
            if not steps:
                continue
            limit = max(floor, REL * statistics.median(s for _, s in steps))
            for w in _windows([f for f, s in steps if s > limit]):
                flags.append({"type": kind, "frames": w, "threshold": round(limit, 3),
                              "step": round(max(s for f, s in steps if w[0] <= f <= w[1]), 3)})
    return {"frames": len(frames), "threshold": threshold, "excluded_frames": excluded, "flags": flags,
            "method": "heuristic (clip-level mask: overlap, parts, background, centre and colour paths)"}


def analyze_clip(path: str | Path, with_metrics: bool = False) -> dict:
    from .qa_subject import decode_rgb_frames
    frames = decode_rgb_frames(path)
    report = detect_continuity(frames)
    report["clip"] = str(path)
    report["clip_sha256"] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if with_metrics:
        report["metrics"] = frame_metrics(frames, report["threshold"])
    return report


# --- evaluation -------------------------------------------------------------------------------------

def _overlaps(a: list[int], b: list[int], tol: int = LABEL_TOLERANCE) -> bool:
    return a[0] <= b[1] + tol and b[0] <= a[1] + tol


def evaluate(labels_path: str | Path, repo_root: str | Path = ".", decode: Callable | None = None) -> dict:
    """F24 + F16 detectors vs labelled defect windows (thresholds fixed beforehand)."""
    from .qa_subject import decode_rgb_frames, detect_subject_defects, frame_metrics as f16_metrics
    decode = decode or decode_rgb_frames
    labels = json.loads(Path(labels_path).read_text(encoding="utf-8"))
    rows, hits, totals, misses, false_flags, windows = [], {}, {}, [], 0, {}
    for clip in labels.get("clips", []):
        path = Path(repo_root) / clip["clip"]
        if decode is decode_rgb_frames and not path.is_file():
            rows.append({"id": clip["id"], "skipped": "clip not found locally"})
            continue
        try:
            frames = decode(path)
        except (KeyError, OSError, RuntimeError):
            rows.append({"id": clip["id"], "skipped": "clip not found locally"})
            continue
        flags = detect_continuity(frames)["flags"] + detect_subject_defects(f16_metrics(frames))
        row = {"id": clip["id"], "flags": [{"type": f["type"], "frames": f["frames"]} for f in flags], "defects": []}
        for d in clip.get("defects", []):
            match = [f["type"] for f in flags if _overlaps(f["frames"], d["frames"])]
            hit = d["kind"] in match
            totals[d["kind"]] = totals.get(d["kind"], 0) + 1
            hits[d["kind"]] = hits.get(d["kind"], 0) + hit
            if not hit:
                misses.append(f"{clip['id']}: {d['kind']} {d['frames']}")
            windows[d["kind"]] = windows.get(d["kind"], 0) + bool(match)
            row["defects"].append({"kind": d["kind"], "frames": d["frames"], "hit": hit, "window_hit": bool(match),
                                   "flags_overlapping": match})
        unlabelled = [f for f in flags if not any(_overlaps(f["frames"], d["frames"]) for d in clip.get("defects", []))]
        false_flags += len(unlabelled)
        row["unlabelled_flags"] = len(unlabelled)
        rows.append(row)
    return {"clips": rows, "recall": {k: f"{hits[k]}/{totals[k]}" for k in sorted(totals)},
            "window_recall": {k: f"{windows[k]}/{totals[k]}" for k in sorted(totals)}, "misses": misses,
            "unlabelled_flags": false_flags,
            "thresholds": {"subst_iou": SUBST_IOU, "subst_median": SUBST_MEDIAN, "topology_delta": TOPO_DELTA,
                           "background_floor": BG_FLOOR, "motion_floor": MOTION_FLOOR, "colour_floor": COLOUR_FLOOR,
                           "relative": REL},
            "note": "Heuristic; label windows are coarse (+/- 4 frames). recall = right kind in the window; window_recall = any "
                    "detector fired in the window. Unlabelled flags may be real defects or false alarms."}


# --- repair proposals and controlled comparison -----------------------------------------------------

def _split_frame(window: list[int], frames: int) -> int | None:
    centre = (window[0] + window[1]) / 2
    candidates = [k for k in range(4, frames - 1, 4) if k + 1 >= MIN_HALF and frames - k >= MIN_HALF]
    return min(candidates, key=lambda k: (abs(k - centre), k)) if candidates else None


def propose_repair(report: dict, bridge_task: dict) -> dict:
    flags = report.get("flags", [])
    base = {"bridge": bridge_task.get("id"), "clip_sha256": report.get("clip_sha256"), "flags": flags}
    if not flags:
        return {**base, "status": "no repair proposed", "refinements": [], "intermediate_anchor": None}
    refinements = []
    for f in flags:
        text = REFINEMENTS.get(f["type"])
        if text and text not in refinements:
            refinements.append(text)
    frames = int(bridge_task.get("frames", 0))
    worst = max(flags, key=lambda f: f["frames"][1] - f["frames"][0])
    at = _split_frame(worst["frames"], frames) if frames else None
    anchor = None
    if at is not None and worst["frames"][0] - 2 <= at <= worst["frames"][1] + 2:
        anchor = {"at_frame": at, "first_frames": at + 1, "second_frames": frames - at}
    return {**base, "status": "proposed - owner review", "refinements": refinements,
            "positive_prompt_after": " ".join([bridge_task.get("positive_prompt", ""), *refinements]).strip(),
            "intermediate_anchor": anchor,
            "controlled_comparison": {"seed": bridge_task.get("seed"), "frames": frames,
                                      "endpoints": "unchanged (same anchor images)",
                                      "changed": "prompt refinements" + (" and one intermediate anchor" if anchor else "")},
            "note": "Nothing is rendered. Run a bounded owner-approved render, then repair-compare."}


def _grey(px) -> list[float]:
    return _lum(px)


def _mad(a, b) -> float:
    ga, gb = _grey(a), _grey(b)
    return sum(abs(x - y) for x, y in zip(ga, gb)) / len(ga)


def compare_repair(original, repaired) -> dict:
    if len(original) != len(repaired):
        return {"verdict": "not comparable", "reason": f"frame counts differ ({len(original)} vs {len(repaired)})"}
    start, end = round(_mad(original[0], repaired[0]), 3), round(_mad(original[-1], repaired[-1]), 3)
    endpoints = {"start_mad": start, "end_mad": end, "unchanged": start <= ENDPOINT_MAD and end <= ENDPOINT_MAD}
    before = {f["type"] for f in detect_continuity(original)["flags"]}
    after = {f["type"] for f in detect_continuity(repaired)["flags"]}
    removed, persisting, new = sorted(before - after), sorted(before & after), sorted(after - before)
    if not endpoints["unchanged"]:
        verdict = "endpoint regression"
    elif removed and not new:
        verdict = COMPARE_VERDICT_OK
    else:
        verdict = "no improvement"
    return {"frames": len(original), "endpoints": endpoints, "removed": removed, "persisting": persisting,
            "new": new, "verdict": verdict,
            "note": "Heuristic comparison; never automatic acceptance - the owner reviews both clips."}
