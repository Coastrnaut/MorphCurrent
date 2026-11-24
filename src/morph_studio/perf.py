"""Run performance reports, whole-GPU sample analysis and time estimates (F11).

Everything here reads local files only: run manifests, stage ``job.json`` records,
``vram_samples.json`` and the history fixture. Nothing contacts ComfyUI, starts GPU
work or hashes models. Every number carries a label:

- ``MEASURED``: taken from a recorded measurement (ComfyUI ``/history`` timestamps,
  job events, nvidia-smi samples).
- ``ESTIMATED``: derived from measured history for a matching configuration.
- ``NOT MEASURED``: no measurement exists; nothing is guessed.

VRAM figures are **whole-GPU** (nvidia-smi ``memory.used``, all processes). Windows
WDDM exposes no per-process memory, so a stage's rise above the pre-run baseline is
an upper bound for MorphCurrent only if other applications stayed steady.
"""
from __future__ import annotations

import json
import statistics
from datetime import datetime
from pathlib import Path

from .provenance import load_cache

MEASURED, ESTIMATED, NOT_MEASURED = "MEASURED", "ESTIMATED", "NOT MEASURED"
EXTRAPOLATED = "ESTIMATED-EXTRAPOLATED"
WHOLE_GPU = "MEASURED (whole GPU, all processes)"
GAP_FACTOR = 3.0
WINDOW_PAD_S = 1.0  # job events have 1 s resolution
CAVEATS = [
    "VRAM is whole-GPU memory.used from nvidia-smi and includes other applications; "
    "Windows (WDDM) reports no per-process memory.",
    "Peaks between samples are not observed.",
    "Stage windows come from job events with 1 s resolution and are widened by 1 s.",
]


def _epoch(iso: str) -> float:
    return datetime.fromisoformat(iso).timestamp()


def analyze_samples(samples: list[list[float] | tuple[float, int]], interval: float,
                    before: float | None = None) -> dict:
    """Coverage, gaps, external baseline and peak of a whole-GPU sample series.

    ``before``: epoch of the first GPU submission; samples before it form the
    external (other-process) baseline. Without it the first sample is used.
    """
    if not samples:
        return {"status": NOT_MEASURED, "reason": "no samples"}
    times = [float(s[0]) for s in samples]
    used = [int(s[1]) for s in samples]
    gaps = [[times[i], times[i + 1]] for i in range(len(times) - 1)
            if times[i + 1] - times[i] > GAP_FACTOR * interval]
    span = times[-1] - times[0]
    missing = sum(b - a - interval for a, b in gaps)
    pre = [u for t, u in zip(times, used) if before is not None and t <= before]
    baseline = statistics.median(pre) if pre else used[0]
    return {"status": WHOLE_GPU, "samples": len(used), "interval_s": interval,
            "span_s": round(span, 3),
            "max_gap_s": round(max((b - a for a, b in zip(times, times[1:])), default=0.0), 3),
            "gaps": [[round(a, 3), round(b, 3)] for a, b in gaps],
            "coverage_pct": round(100.0 * (1 - missing / span), 1) if span > 0 else 100.0,
            "external_baseline_mib": int(baseline),
            "baseline_source": "median of samples before first submission" if pre else "first sample",
            "peak_mib": max(used), "peak_rise_mib": max(used) - int(baseline)}


def _job_size(job: dict) -> dict:
    if job.get("kind") == "anchor_image":
        image = job.get("image") or {}
        values = job.get("values") or {}
        return {"kind": "anchor", "method": job.get("method"),
                "width": image.get("width") or values.get("width"),
                "height": image.get("height") or values.get("height")}
    values = job.get("values") or {}
    return {"kind": "bridge", "width": values.get("width"), "height": values.get("height"),
            "frames": values.get("length")}


_EVENT_ALIASES = {"submitted": ("submitted", "submit_confirmed_on_resume")}


def _event_time(job: dict, name: str) -> float | None:
    """UTC epoch of the last occurrence of an event (a retry restarts the stage)."""
    names = _EVENT_ALIASES.get(name, (name,))
    times = [_epoch(e["t"]) for e in job.get("events", []) if e.get("event") in names]
    return times[-1] if times else None


def collect_stages(run_dir: str | Path) -> list[dict]:
    """One row per manifest stage with times taken from its ``job.json``."""
    run = Path(run_dir)
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    created = _epoch(manifest["created_at"])
    rows = []
    for task in manifest["order"]:
        stage = manifest["stages"].get(task, {})
        row: dict = {"task": task, "state": stage.get("state", "pending")}
        job_dir = stage.get("job_dir")
        if not job_dir:
            row["labels"] = {"time": NOT_MEASURED, "vram": NOT_MEASURED}
            rows.append(row)
            continue
        path = Path(job_dir)
        if not path.is_absolute() and not path.exists():
            path = run.parent.parent / job_dir  # recorded relative to the repo root
        job = json.loads((path / "job.json").read_text(encoding="utf-8"))
        row.update(_job_size(job))
        row["job"] = job["job_id"][:16]
        row["reused"] = _epoch(job["created_at"]) < created
        submitted, completed = _event_time(job, "submitted"), _event_time(job, "completed")
        verified = _event_time(job, "verified")
        exec_s = (job.get("timings") or {}).get("execution_seconds")
        row["exec_s"] = exec_s
        row["wall_s"] = round(verified - submitted, 1) if submitted and verified else None
        row["overhead_s"] = round(row["wall_s"] - exec_s, 1) if row["wall_s"] is not None and exec_s else None
        row["window"] = [submitted, completed] if submitted and completed else None
        row["labels"] = {"time": MEASURED if exec_s is not None else NOT_MEASURED, "vram": NOT_MEASURED}
        rows.append(row)
    return rows


def stage_window_peaks(rows: list[dict], samples: list, baseline: int) -> None:
    """Annotate rows with the whole-GPU peak inside each stage's execution window."""
    for row in rows:
        window = row.get("window")
        if not window or row.get("reused"):
            continue
        start, end = window[0] - WINDOW_PAD_S, window[1] + WINDOW_PAD_S
        inside = [int(s[1]) for s in samples if start <= float(s[0]) <= end]
        if inside:
            row["vram_window_peak_mib"] = max(inside)
            row["vram_window_rise_mib"] = max(inside) - baseline
            row["vram_window_samples"] = len(inside)
            row["labels"]["vram"] = WHOLE_GPU


def _provenance(manifest: dict, rows: list[dict], run: Path, cache_file: Path | None) -> dict:
    snapshot: dict = {}
    models: dict[str, str] = {}
    cache = load_cache(cache_file) if cache_file else {"files": {}}
    for row in rows:
        if not row.get("job"):
            continue
        job_dir = Path(manifest["stages"][row["task"]]["job_dir"])
        if not job_dir.exists():
            job_dir = run.parent.parent / job_dir
        job = json.loads((job_dir / "job.json").read_text(encoding="utf-8"))
        for value in (job.get("models") or {}).values():
            entry = next((v for k, v in cache["files"].items() if k.endswith("/" + value)), None)
            models[value] = entry["sha256"] if entry else NOT_MEASURED
        for snap in (job.get("comfyui") or {}).values():
            if isinstance(snap, dict) and snap.get("comfyui_version"):
                snapshot = snap
    devices = snapshot.get("devices") or [{}]
    return {"comfyui": snapshot.get("comfyui_version") or NOT_MEASURED,
            "pytorch": snapshot.get("pytorch_version") or NOT_MEASURED,
            "gpu": devices[0].get("name") or NOT_MEASURED,
            "models_sha256": dict(sorted(models.items()))}


def build_report(run_dir: str | Path, model_cache: str | Path | None = None) -> dict:
    run = Path(run_dir)
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    rows = collect_stages(run)
    fresh = [r for r in rows if r.get("job") and not r.get("reused")]
    first_submit = min((r["window"][0] for r in fresh if r.get("window")), default=None)
    vram: dict = {"status": NOT_MEASURED, "reason": "run was not sampled (--sample-vram)"}
    samples_file = run / "vram_samples.json"
    if samples_file.exists():
        data = json.loads(samples_file.read_text(encoding="utf-8"))
        vram = analyze_samples(data["samples"], data["interval_s"], before=first_submit)
        if vram.get("samples"):
            stage_window_peaks(rows, data["samples"], vram["external_baseline_mib"])
    elif manifest.get("vram"):
        summary = manifest["vram"][-1]
        vram = {"status": WHOLE_GPU + ", summary only (no timestamped samples; pre-F11 run)",
                "peak_mib": summary.get("peak_mib"), "first_sample_mib": summary.get("baseline_mib"),
                "samples": summary.get("samples")}
    cache = Path(model_cache) if model_cache else None
    return {
        "schema": 1, "run_dir": str(run), "plan_sha256": manifest["plan_sha256"],
        "stages": rows,
        "totals": {"gpu_exec_s": round(sum(r["exec_s"] for r in fresh if r.get("exec_s")), 1),
                   "fresh_stages": len(fresh),
                   "reused_stages": sum(1 for r in rows if r.get("reused")),
                   "label": MEASURED},
        "vram": vram,
        "provenance": _provenance(manifest, rows, run, cache),
        "caveats": CAVEATS,
    }


def load_history(path: str | Path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))["entries"]


def _matches(entry: dict, task: dict) -> bool:
    if entry["kind"] != task["kind"] or entry["width"] != task["width"] or entry["height"] != task["height"]:
        return False
    if task["kind"] == "anchor":
        method = "text_to_image" if task["method"] == "independent_t2i" else task["method"]
        return entry.get("method") == method
    return entry.get("frames") == task["frames"]


def estimate(dag_plan: dict, history: list[dict], *, extrapolate: bool = False) -> dict:
    """Per-stage GPU time from measured history; NO DATA instead of guesses."""
    rows, total, complete = [], 0.0, True
    for task_id in dag_plan["order"]:
        task = dag_plan["tasks"][task_id]
        if task["kind"] not in ("anchor", "bridge"):
            continue
        hits = [h["exec_s"] for h in history if _matches(h, task)]
        row = {"task": task_id, "kind": task["kind"], "width": task["width"], "height": task["height"]}
        if task["kind"] == "bridge":
            row["frames"] = task["frames"]
        if hits:
            row.update(exec_s=round(statistics.median(hits), 1), label=ESTIMATED, samples=len(hits),
                       runs=sorted({h["run"] for h in history if _matches(h, task)}))
        elif extrapolate:
            same_kind = [h for h in history if h["kind"] == task["kind"]
                         and (task["kind"] == "bridge" or h.get("method") == task.get("method"))]
            if same_kind:
                ref = max(same_kind, key=lambda h: h["width"] * h["height"])
                scale = (task["width"] * task["height"] * task.get("frames", 1)) / \
                        (ref["width"] * ref["height"] * ref.get("frames", 1))
                row.update(exec_s=round(ref["exec_s"] * scale, 1), label=EXTRAPOLATED,
                           basis=f"{ref['run']} {ref['width']}x{ref['height']} scaled by pixel x frame count")
        if "exec_s" not in row:
            row.update(exec_s=None, label="NO DATA")
            complete = False
        else:
            total += row["exec_s"]
        rows.append(row)
    return {"stages": rows, "total_gpu_s": round(total, 1) if complete else None,
            "partial_total_gpu_s": round(total, 1),
            "label": ESTIMATED if complete else "INCOMPLETE (some stages have NO DATA)",
            "note": "Estimates exclude model loading variance, queue wait and other GPU load."}
