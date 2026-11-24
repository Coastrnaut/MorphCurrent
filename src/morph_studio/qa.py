"""Local temporal QA heuristics, candidate seeds and selective rerender (F08).

Heuristics flag likely defects (hard cut, freeze, flare, endpoint mismatch) on
small grayscale frames decoded locally by FFmpeg. They do NOT certify artistic
quality: a human review (approve/reject) is recorded separately and gates joining.
"""
from __future__ import annotations

import json
import os
import shutil
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .media import ProbeUnavailable
from .timeline import derived_seed

W, H = 64, 36
CUT_RATIO, CUT_MIN = 6.0, 20.0
FREEZE_DIFF, FREEZE_RUN = 0.5, 6
FLARE_JUMP = 40.0
ENDPOINT_MAX = 25.0


def decode_gray_frames(path: str | Path, *, ffmpeg: str | None = None, timeout: float = 300) -> list[bytes]:
    executable = ffmpeg or shutil.which("ffmpeg")
    if not executable:
        raise ProbeUnavailable("ffmpeg not found on PATH")
    args = [executable, "-hide_banner", "-nostdin", "-v", "error", "-i", str(path),
            "-vf", f"scale={W}:{H}:flags=area,format=gray", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    done = subprocess.run(args, capture_output=True, timeout=timeout, shell=False, check=False)
    if done.returncode != 0:
        raise RuntimeError(f"ffmpeg decode failed: {done.stderr.decode(errors='replace')[:300]}")
    size = W * H
    data = done.stdout
    return [data[i:i + size] for i in range(0, len(data) - size + 1, size)]


def _mad(a: bytes, b: bytes) -> float:
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def _mean(a: bytes) -> float:
    return sum(a) / len(a)


def analyze_frames(frames: list[bytes], start_ref: bytes | None = None,
                   end_ref: bytes | None = None) -> dict:
    if len(frames) < 3:
        raise ValueError("need at least 3 frames for temporal QA")
    diffs = [_mad(frames[i], frames[i + 1]) for i in range(len(frames) - 1)]
    lum = [_mean(f) for f in frames]
    median = statistics.median(diffs)
    flags: list[dict] = []
    for i, d in enumerate(diffs):
        if d > CUT_MIN and d > CUT_RATIO * max(median, 0.5):
            flags.append({"type": "hard_cut", "frame": i + 1, "diff": round(d, 2), "median": round(median, 2)})
        jump = lum[i + 1] - lum[i]
        if abs(jump) > FLARE_JUMP:
            flags.append({"type": "flare", "frame": i + 1, "luminance_jump": round(jump, 2)})
    run = 0
    for i, d in enumerate(diffs + [float("inf")]):
        if d < FREEZE_DIFF:
            run += 1
            continue
        if run + 1 >= FREEZE_RUN:
            flags.append({"type": "freeze", "first_frame": i - run, "frames": run + 1})
        run = 0
    endpoints = {}
    for name, ref, frame in (("start", start_ref, frames[0]), ("end", end_ref, frames[-1])):
        if ref is not None:
            diff = _mad(ref, frame)
            endpoints[name] = round(diff, 2)
            if diff > ENDPOINT_MAX:
                flags.append({"type": "endpoint_mismatch", "end": name, "diff": round(diff, 2)})
    severity = {"hard_cut": 3, "endpoint_mismatch": 3, "flare": 2, "freeze": 1}
    return {"method": "heuristic", "frames": len(frames), "median_diff": round(median, 3),
            "max_diff": round(max(diffs), 3), "endpoint_diff": endpoints, "flags": flags,
            "score": sum(severity[f["type"]] for f in flags),
            "status": "flagged" if flags else "no_flags",
            "note": "heuristic screen only; human review decides creative acceptance"}


def analyze_clip(path: Path, start_image: Path | None = None, end_image: Path | None = None) -> dict:
    frames = decode_gray_frames(path)
    refs = [decode_gray_frames(p)[0] if p else None for p in (start_image, end_image)]
    report = {"clip": str(path), **analyze_frames(frames, *refs)}
    from .qa_subject import analyze_subject  # F16 subject-aware detectors
    subject = analyze_subject(path)["flags"]
    if subject:
        report["flags"] = report["flags"] + subject
        report["score"] += 2 * len(subject)
        report["status"] = "flagged"
    return report


def candidate_seeds(task: dict, master_seed: int) -> list[int]:
    count = max(1, int(task.get("candidates", 1)))
    return [task["seed"]] + [derived_seed(master_seed, f"{task['id']}:candidate:{i}") for i in range(1, count)]


def rank_candidates(reports: dict[int, dict]) -> list[int]:
    """Seeds ordered by heuristic score (lower first), ties by seed order given."""
    order = list(reports)
    return sorted(order, key=lambda s: (reports[s]["score"], order.index(s)))


def rerender_plan(dag_plan: dict, qa: dict[str, dict], reviews: dict[str, dict]) -> list[str]:
    """Bridge task ids that need new candidates: flagged by QA or rejected by the human."""
    todo = []
    for task_id in dag_plan["order"]:
        if dag_plan["tasks"][task_id]["kind"] != "bridge":
            continue
        review = reviews.get(task_id, {}).get("decision", "pending")
        if review == "rejected" or (review != "approved" and qa.get(task_id, {}).get("status") == "flagged"):
            todo.append(task_id)
    return todo


def load_reviews(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def record_review(path: Path, task_id: str, decision: str, note: str = "") -> dict:
    if decision not in {"approved", "rejected", "pending"}:
        raise ValueError("decision must be approved, rejected or pending")
    reviews = load_reviews(path)
    reviews[task_id] = {"decision": decision, "note": note,
                        "t": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(reviews, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)
    return reviews
