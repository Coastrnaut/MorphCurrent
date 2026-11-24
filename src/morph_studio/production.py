"""Production GPU budget and batch scheduling for the full-song film (F36). Offline; renders stay owner-run.

``ingest`` folds measured, verified job timings into ``configs/perf_history.json``. ``stage_cost`` estimates
a stage from that history (exact medians; bridges interpolated/extrapolated linearly in frame count between
measured lengths of the same size; labelled). ``budget`` gives per-act GPU time, act-contained batches under
caps with ETA and a storage estimate. ``write_batches`` writes, for an owner-approved act, self-contained
batch storyboards whose stages are identical to the full film's (all seeds pinned), so rendering a batch
fills the same content-addressed cache. ``status`` reports progress, estimate-vs-actual ratios and duplicate
ComfyUI submissions.
"""
from __future__ import annotations

import copy
import json
import os
import statistics
from datetime import datetime, timezone
from pathlib import Path

import yaml

DEFAULT_HISTORY = Path("configs/perf_history.json")
COLD_S, MAX_BATCH_S, MAX_JOBS = 60.0, 7200.0, 20
RATIO_BAND = (0.8, 1.2)


class ProductionError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ------------------------------------------------------------------------------------------- ingest

def _load_history(path: Path) -> dict:
    if not path.exists():
        return {"schema": 1, "source": "measured job records (history-ingest)", "entries": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ProductionError(f"cost history {path} is not valid JSON; refusing to overwrite it") from exc
    if not isinstance(data.get("entries"), list):
        raise ProductionError(f"cost history {path} has no entries list")
    return data


def ingest(runs_root: str | Path, history_path: str | Path = DEFAULT_HISTORY) -> dict:
    path = Path(history_path)
    data = _load_history(path)
    known = {e.get("job") for e in data["entries"]}
    added = skipped = 0
    for record_path in sorted(Path(runs_root).glob("*/job.json")):
        try:
            rec = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            skipped += 1
            continue
        job_id = record_path.parent.name[:16]
        exec_s = (rec.get("timings") or {}).get("execution_seconds")
        if job_id in known:
            continue
        if rec.get("state") != "verified" or not exec_s:
            skipped += 1
            continue
        values, request = rec.get("values") or {}, rec.get("request") or {}
        entry = {"run": f"ingest:{record_path.parent.name}", "width": values.get("width") or request.get("width"),
                 "height": values.get("height") or request.get("height"), "exec_s": float(exec_s), "job": job_id}
        if "bridge" in str(rec.get("kind")):
            entry.update(kind="bridge", frames=values.get("length"))
        else:
            entry.update(kind="anchor", method=(rec.get("request") or {}).get("method") or rec.get("method"))
        if not entry["width"] or not entry["height"] or (entry["kind"] == "bridge" and not entry["frames"]):
            skipped += 1
            continue
        data["entries"].append(entry)
        known.add(job_id)
        added += 1
    if added:
        part = path.with_name(path.name + ".part")
        part.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        os.replace(part, path)
    return {"added": added, "skipped": skipped, "total": len(data["entries"]), "history": str(path)}


# --------------------------------------------------------------------------------------------- cost

def _size(e: dict) -> tuple:
    return (e.get("width"), e.get("height"))


def stage_cost(task: dict, history: list[dict]) -> tuple[float | None, str]:
    kind = task["kind"]
    if kind == "bridge":
        same = [h for h in history if h.get("kind") == "bridge" and _size(h) == _size(task)]
        exact = [h["exec_s"] for h in same if h.get("frames") == task["frames"]]
        if exact:
            return round(statistics.median(exact), 1), "ESTIMATED"
        by_len: dict[int, list[float]] = {}
        for h in same:
            by_len.setdefault(h["frames"], []).append(h["exec_s"])
        points = sorted((f, statistics.median(v)) for f, v in by_len.items())
        f = task["frames"]
        if len(points) >= 2:
            lower = [p for p in points if p[0] < f]
            upper = [p for p in points if p[0] > f]
            if lower and upper:
                (f0, s0), (f1, s1), label = lower[-1], upper[0], "INTERPOLATED"
            elif lower:
                (f0, s0), (f1, s1), label = lower[-2], lower[-1], "EXTRAPOLATED"
            else:
                (f0, s0), (f1, s1), label = upper[0], upper[1], "EXTRAPOLATED"
            return round(max(0.0, s0 + (s1 - s0) * (f - f0) / (f1 - f0)), 1), label
        if len(points) == 1:
            f0, s0 = points[0]
            return round(s0 * f / f0, 1), "EXTRAPOLATED"
        bridges = [h for h in history if h.get("kind") == "bridge" and h.get("width") and h.get("frames")]
        if bridges:
            ref = max(bridges, key=lambda h: h["width"] * h["height"])
            scale = (task["width"] * task["height"] * f) / (ref["width"] * ref["height"] * ref["frames"])
            return round(ref["exec_s"] * scale, 1), "EXTRAPOLATED"
        return None, "NO DATA"
    if kind == "anchor":
        method = "text_to_image" if task.get("method") in ("text_to_image", "independent_t2i") else task.get("method")
        same = [h for h in history if h.get("kind") == "anchor" and h.get("method") == method]
        exact = [h["exec_s"] for h in same if _size(h) == _size(task)]
        if exact:
            return round(statistics.median(exact), 1), "ESTIMATED"
        if same:
            ref = max(same, key=lambda h: h["width"] * h["height"])
            return round(ref["exec_s"] * task["width"] * task["height"] / (ref["width"] * ref["height"]), 1), \
                "EXTRAPOLATED"
        return None, "NO DATA"
    return 0.0, "n/a"


def _units(plan: dict) -> list[tuple[str, list[list[str]]]]:
    """Per act (contiguous chapter), units in film order: [anchor k, bridge k->k+1 (if any)]."""
    anchors = [plan["tasks"][t] for t in plan["order"] if plan["tasks"][t]["kind"] == "anchor"]
    out: list[tuple[str, list[list[str]]]] = []
    for i, a in enumerate(anchors):
        act = a.get("chapter") or "(film)"
        if not out or out[-1][0] != act:
            out.append((act, []))
        unit = [f"anchor:{a['anchor']}"]
        if i + 1 < len(anchors):
            key = f"bridge:{a['anchor']}->{anchors[i + 1]['anchor']}"
            if key in plan["tasks"]:
                unit.append(key)
        out[-1][1].append(unit)
    return out


def budget(plan: dict, history: list[dict], *, cold_s: float = COLD_S, max_batch_s: float = MAX_BATCH_S,
           max_jobs: int = MAX_JOBS) -> dict:
    from .longform import plan_bytes
    acts_out, total_s, total_batches = [], 0.0, 0
    for act, units in _units(plan):
        stages = [t for u in units for t in u]
        labels: dict[str, int] = {}
        costs = {}
        for t in stages:
            sec, label = stage_cost(plan["tasks"][t], history)
            costs[t] = sec or 0.0
            labels[label] = labels.get(label, 0) + 1
        batches, current = [], {"stages": [], "seconds": 0.0}
        for unit in units:  # batches split on unit boundaries, in film order
            unit_s = sum(costs[t] for t in unit)
            if current["stages"] and (len(current["stages"]) + len(unit) > max_jobs
                                      or current["seconds"] + unit_s > max_batch_s):
                batches.append(current)
                current = {"stages": [], "seconds": 0.0}
            current["stages"].extend(unit)
            current["seconds"] += unit_s
        if current["stages"]:
            batches.append(current)
        for i, b in enumerate(batches, 1):
            # a bridge needs both endpoints: an endpoint outside this batch's own stages (the next act's first
            # anchor, or a later anchor of this act) is rendered early here and counted in the ETA
            own = set(b["stages"])
            early = []
            for t in b["stages"]:
                task = plan["tasks"][t]
                if task["kind"] == "bridge" and f"anchor:{task['to']}" not in own:
                    early.append(f"anchor:{task['to']}")
            early_s = sum(stage_cost(plan["tasks"][t], history)[0] or 0.0 for t in early)
            b.update(index=i, seconds=round(b["seconds"], 1), early_stages=early,
                     eta_s=round(b["seconds"] + early_s + cold_s, 1), oversized=b["seconds"] > max_batch_s)
        seconds = round(sum(costs.values()), 1)
        total_s += seconds + cold_s * len(batches)
        total_batches += len(batches)
        acts_out.append({"id": act, "anchors": sum(plan["tasks"][t]["kind"] == "anchor" for t in stages),
                         "bridges": sum(plan["tasks"][t]["kind"] == "bridge" for t in stages),
                         "seconds": seconds, "hours": round(seconds / 3600, 2), "labels": labels, "batches": batches})
    return {"acts": acts_out,
            "totals": {"stages": sum(a["anchors"] + a["bridges"] for a in acts_out),
                       "seconds": round(sum(a["seconds"] for a in acts_out), 1),
                       "seconds_with_cold_start": round(total_s, 1), "hours": round(total_s / 3600, 2),
                       "batches": total_batches, "cold_s": cold_s},
            "storage_bytes": plan_bytes(plan).get("total_bytes"),
            "caps": {"max_batch_s": max_batch_s, "max_jobs": max_jobs},
            "note": "Estimates from measured history; INTERPOLATED/EXTRAPOLATED stages are not measurements."}


# ---------------------------------------------------------------------------------------- approvals

def default_approvals(storyboard_name: str) -> Path:
    return Path("outputs/production") / f"{storyboard_name}.approvals.jsonl"


def approve(log: str | Path, storyboard: str | Path, act: str, note: str = "", *, owner: str = "owner",
            revoke: bool = False) -> dict:
    from .schema import load_storyboard
    sb = load_storyboard(storyboard)
    acts = {a.chapter for a in sb.anchors}
    if act not in acts:
        raise ProductionError(f"act {act!r} not in {sb.name} (acts: {sorted(a for a in acts if a)})")
    rec = {"t": _now(), "storyboard": sb.name, "act": act, "note": note, "owner": owner,
           "decision": "revoked" if revoke else "approved"}
    path = Path(log)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(rec, ensure_ascii=True) + "\n")
    return rec


def approved_acts(log: str | Path) -> set[str]:
    state: dict[str, str] = {}
    path = Path(log)
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                state[rec["act"]] = rec["decision"]
    return {a for a, d in state.items() if d == "approved"}


# ------------------------------------------------------------------------------------------ batches

def write_batches(storyboard: str | Path, act: str, out_dir: str | Path, *, approvals_log: str | Path,
                  history: str | Path = DEFAULT_HISTORY, max_batch_s: float = MAX_BATCH_S,
                  max_jobs: int = MAX_JOBS, cold_s: float = COLD_S, repo_root: str | Path = ".") -> list[str]:
    from .dag import compile_plan
    from .schema import Storyboard, load_storyboard
    path = Path(storyboard)
    sb = load_storyboard(path)
    if act not in approved_acts(approvals_log):
        raise ProductionError(f"act {act!r} is not approved; record an owner approval with prod-approve first")
    plan = compile_plan(sb, repo_root=repo_root, storyboard_bytes=path.read_bytes())
    hist = _load_history(Path(history))["entries"]
    plan_budget = budget(plan, hist, cold_s=cold_s, max_batch_s=max_batch_s, max_jobs=max_jobs)
    batches = next(a["batches"] for a in plan_budget["acts"] if a["id"] == act)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    by_id = {a["id"]: a for a in data["anchors"]}
    trans = {(t["from"], t["to"]): t for t in data["transitions"]}
    out = Path(out_dir)
    targets = [out / f"{act}-b{b['index']:02d}.yaml" for b in batches]
    for t in targets:
        if t.exists():
            raise FileExistsError(f"{t} exists; refusing to overwrite")
    out.mkdir(parents=True, exist_ok=True)
    written = []
    order = [a["id"] for a in data["anchors"]]
    for batch, target in zip(batches, targets):
        # a batch is a contiguous film segment from the act's first anchor to its last needed anchor: earlier
        # stages are identical to the full plan's and are cache hits when batches run in order
        idx = {a: i for i, a in enumerate(order)}
        last = 0
        for stage in batch["stages"]:
            task = plan["tasks"][stage]
            last = max(last, idx[task["anchor"]] if task["kind"] == "anchor" else idx[task["to"]])
        first = next(i for i, a in enumerate(order) if by_id[a].get("chapter") == act)
        ids = order[first:last + 1]
        sub = copy.deepcopy(data)
        sub["name"] = f"{data['name']}-{act}-b{batch['index']:02d}"
        sub["anchors"] = []
        for i in ids:
            a = copy.deepcopy(by_id[i])
            a["seed"] = plan["tasks"][f"anchor:{i}"]["seed"]
            sub["anchors"].append(a)
        sub["transitions"] = []
        for x, y in zip(ids, ids[1:]):
            t = copy.deepcopy(trans[(x, y)])
            t["seed"] = plan["tasks"][f"bridge:{x}->{y}"]["seed"]
            sub["transitions"].append(t)
        Storyboard.model_validate(sub)
        target.write_text(f"# F36 batch {batch['index']} of act {act!r} ({len(batch['stages'])} stages, est. "
                          f"{batch['eta_s']} GPU s incl. cold start). Seeds pinned to the full film; render with "
                          f"`render {target.as_posix()} --confirm-gpu`.\n"
                          + yaml.safe_dump(sub, sort_keys=False, width=120), encoding="utf-8")
        written.append(str(target))
    return written


# ------------------------------------------------------------------------------------------- status

def status(plan: dict, runs_root: str | Path, history: list[dict]) -> dict:
    from .longform import cached_stages
    done = cached_stages(plan, runs_root)
    gpu = [t for t in plan["order"] if plan["tasks"][t]["kind"] in ("anchor", "bridge")]
    remaining = [t for t in gpu if t not in done]
    remaining_s = sum(stage_cost(plan["tasks"][t], history)[0] or 0.0 for t in remaining)
    prompts: dict[str, list[str]] = {}
    ratios = []
    for record_path in sorted(Path(runs_root).glob("*/job.json")):
        try:
            rec = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        job_id = record_path.parent.name[:16]
        if rec.get("prompt_id"):
            prompts.setdefault(rec["prompt_id"], []).append(job_id)
        exec_s = (rec.get("timings") or {}).get("execution_seconds")
        if rec.get("state") != "verified" or not exec_s:
            continue
        values, request = rec.get("values") or {}, rec.get("request") or {}
        width, height = values.get("width") or request.get("width"), values.get("height") or request.get("height")
        if not width or not height:
            continue  # size not recorded: no comparable estimate
        if "bridge" in str(rec.get("kind")):
            task = {"kind": "bridge", "frames": values.get("length"), "width": width, "height": height}
        else:
            task = {"kind": "anchor", "method": request.get("method"), "width": width, "height": height}
        others = [h for h in history if h.get("job") != job_id]  # leave-one-out
        estimate, label = stage_cost(task, others)
        if estimate:
            ratio = round(exec_s / estimate, 3)
            ratios.append({"job": job_id, "kind": task["kind"], "actual": exec_s, "estimate": estimate,
                           "label": label, "ratio": ratio, "flag": not RATIO_BAND[0] <= ratio <= RATIO_BAND[1]})
    duplicates = [{"prompt_id": p, "jobs": jobs} for p, jobs in prompts.items() if len(jobs) > 1]
    return {"finished": len(gpu) - len(remaining), "remaining": len(remaining),
            "remaining_seconds": round(remaining_s, 1), "eta_hours": round(remaining_s / 3600, 2),
            "ratios": ratios, "duplicates": duplicates,
            "ok": not duplicates and not any(r["flag"] for r in ratios)}
