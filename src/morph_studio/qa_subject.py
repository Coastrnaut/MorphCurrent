"""Subject-aware temporal QA and calibration against labelled defect windows (F16).

F08's frame-difference heuristics missed every real defect seen so far (petal
collapse, a subject shrinking to a small blur, sliding off-centre). These detectors
look at the *subject* in each frame instead: mask area, centroid (F12 geometry) and
sharpness. Thresholds were fixed before evaluating on the labelled clips. Flags are
heuristic and never replace human review.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .geometry import H, W, anchor_geometry
from .media import ProbeUnavailable

COLLAPSE_RATIO = 0.55
DRIFT_MAX = 0.12
BLUR_RATIO = 0.5
MIN_RUN = 3


def decode_rgb_frames(path: str | Path) -> list[list[tuple[int, int, int]]]:
    executable = shutil.which("ffmpeg")
    if not executable:
        raise ProbeUnavailable("ffmpeg not found on PATH")
    done = subprocess.run([executable, "-hide_banner", "-nostdin", "-v", "error", "-i", str(path),
                           "-vf", f"scale={W}:{H}:flags=area,format=rgb24", "-f", "rawvideo",
                           "-pix_fmt", "rgb24", "-"], capture_output=True, timeout=600, shell=False, check=False)
    if done.returncode != 0:
        raise RuntimeError(f"ffmpeg decode failed: {done.stderr.decode(errors='replace')[:200]}")
    size = W * H * 3
    data = done.stdout
    return [[tuple(data[o + i:o + i + 3]) for i in range(0, size, 3)]  # type: ignore[misc]
            for o in range(0, len(data) - size + 1, size)]


def _sharpness(pixels: list[tuple[int, int, int]], threshold: int) -> float:
    lum = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in pixels]
    total = count = 0.0
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            i = y * W + x
            if lum[i] <= threshold:
                continue
            total += abs(4 * lum[i] - lum[i - 1] - lum[i + 1] - lum[i - W] - lum[i + W])
            count += 1
    return total / count if count else 0.0


def frame_metrics(frames: list[list[tuple[int, int, int]]]) -> list[dict]:
    out = []
    for i, px in enumerate(frames):
        geo = anchor_geometry(px)
        row = {"frame": i, "area": geo["area"], "centroid": geo.get("centroid"),
               "unreliable": bool(geo.get("mask_unreliable"))}
        row["sharpness"] = round(_sharpness(px, geo["threshold"]), 3) if geo.get("centroid") else 0.0
        out.append(row)
    return out


def _runs(flags: list[bool]) -> list[list[int]]:
    runs, start = [], None
    for i, f in enumerate(flags + [False]):
        if f and start is None:
            start = i
        elif not f and start is not None:
            if i - start >= MIN_RUN:
                runs.append([start, i - 1])
            start = None
    return runs


def detect_subject_defects(metrics: list[dict]) -> list[dict]:
    if len(metrics) < 3:
        return []
    first, last = metrics[0], metrics[-1]
    flags: list[dict] = []
    ref_area = min(first["area"], last["area"])
    if ref_area > 0:
        for run in _runs([(not m["unreliable"]) and m["area"] < COLLAPSE_RATIO * ref_area for m in metrics]):
            low = min(metrics[k]["area"] for k in range(run[0], run[1] + 1))
            flags.append({"type": "subject_collapse", "frames": run,
                          "min_area_ratio": round(low / ref_area, 3)})
    if first["centroid"] and last["centroid"]:
        n = len(metrics) - 1
        def off(k: int) -> float:
            c = metrics[k]["centroid"]
            if not c:
                return 0.0
            t = k / n
            ex = first["centroid"][0] + t * (last["centroid"][0] - first["centroid"][0])
            ey = first["centroid"][1] + t * (last["centroid"][1] - first["centroid"][1])
            return ((c[0] - ex) ** 2 + (c[1] - ey) ** 2) ** 0.5
        for run in _runs([off(k) > DRIFT_MAX for k in range(len(metrics))]):
            flags.append({"type": "subject_drift", "frames": run,
                          "max_offset": round(max(off(k) for k in range(run[0], run[1] + 1)), 3)})
    ref_sharp = min(first["sharpness"], last["sharpness"])
    if ref_sharp > 0:
        for run in _runs([m["sharpness"] < BLUR_RATIO * ref_sharp for m in metrics]):
            low = min(metrics[k]["sharpness"] for k in range(run[0], run[1] + 1))
            flags.append({"type": "blur_dip", "frames": run, "min_sharpness_ratio": round(low / ref_sharp, 3)})
    return flags


def analyze_subject(path: str | Path) -> dict:
    metrics = frame_metrics(decode_rgb_frames(path))
    return {"frames": len(metrics), "flags": detect_subject_defects(metrics),
            "method": "heuristic (subject mask area / centroid / sharpness per frame)"}


def _overlap(a: list[int], b: list[int], tolerance: int = 4) -> bool:
    return a[0] <= b[1] + tolerance and b[0] <= a[1] + tolerance


def calibrate(labels_path: str | Path, repo_root: str | Path = ".") -> dict:
    """Precision/recall of the detectors against labelled defect windows (window overlap ± 4 frames)."""
    labels = json.loads(Path(labels_path).read_text(encoding="utf-8"))
    root = Path(repo_root)
    per_kind: dict[str, dict] = {}
    clips = []
    for clip in labels["clips"]:
        path = root / clip["clip"]
        if not path.is_file():
            clips.append({"clip": clip["clip"], "status": "skipped: file not found locally"})
            continue
        result = analyze_subject(path)
        found = result["flags"]
        entry = {"clip": clip["clip"], "labels": clip["defects"], "flags": found}
        for kind in {d["kind"] for d in clip["defects"]} | {f["type"] for f in found} | set(labels["kinds"]):
            stats = per_kind.setdefault(kind, {"tp": 0, "fn": 0, "fp": 0})
            truth = [d["frames"] for d in clip["defects"] if d["kind"] == kind]
            pred = [f["frames"] for f in found if f["type"] == kind]
            hit_truth = sum(1 for t in truth if any(_overlap(t, p) for p in pred))
            stats["tp"] += hit_truth
            stats["fn"] += len(truth) - hit_truth
            stats["fp"] += sum(1 for p in pred if not any(_overlap(t, p) for t in truth))
        clips.append(entry)
    summary = {}
    for kind, s in per_kind.items():
        precision = s["tp"] / (s["tp"] + s["fp"]) if s["tp"] + s["fp"] else None
        recall = s["tp"] / (s["tp"] + s["fn"]) if s["tp"] + s["fn"] else None
        summary[kind] = {**s, "precision": None if precision is None else round(precision, 3),
                         "recall": None if recall is None else round(recall, 3)}
    return {"labels": str(labels_path), "summary": summary, "clips": clips,
            "note": "Thresholds fixed before this evaluation; labels are coarse owner/assistant observations."}
