"""Structured local A/B experiments on one bridge: design, budget, sequential runner, ratings, Pareto (F29).

A YAML definition names a subject bridge, fixed controls, varied factors (only inputs the Wan profile really
binds), a seed block and a budget. ``design`` lists the baseline then the full factorial x seeds in a fixed
order, each candidate content-hashed, with measured-history GPU estimates (NO DATA otherwise) and over-budget
candidates marked deferred. ``run`` executes one candidate at a time through the normal bridge jobs (idle
queue, ``--confirm-gpu``) and appends outcomes to ``results.jsonl``; ``rate`` and ``report`` turn owner ratings
into per-level summaries and a Pareto set, stated as observational evidence, not proof.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import os
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .timeline import derived_seed

DEFAULT_PROFILE = "configs/profiles/wan22_flf2v.binding.json"
ALLOWED = ("seed", "length", "width", "height", "positive_prompt", "negative_prompt", "fps", "profile")
NO_DATA = "NO DATA"
CAVEAT = ("Observational comparison of a handful of renders: each level has few samples and differences may be "
          "seed noise. Use it to choose what to look at next, not as proof.")


class ExperimentError(ValueError):
    pass


class Subject(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_image: str
    end_image: str
    positive_prompt: str | None = None
    negative_prompt: str | None = None
    profile: str = DEFAULT_PROFILE


class Budget(BaseModel):
    model_config = ConfigDict(extra="forbid")
    max_runs: int | None = Field(default=None, ge=1)
    max_gpu_s: float | None = Field(default=None, gt=0)
    max_frames: int | None = Field(default=None, ge=1)


class EarlyStop(BaseModel):
    model_config = ConfigDict(extra="forbid")
    consecutive_flagged: int = Field(ge=1)


class Definition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,62}$")
    subject: Subject
    controls: dict[str, Any] = Field(default_factory=dict)
    factors: dict[str, list[Any]] = Field(default_factory=dict)
    seeds: list[int] | None = None
    seed_count: int | None = Field(default=None, ge=1, le=64)
    master_seed: int = 0
    budget: Budget = Field(default_factory=Budget)
    early_stop: EarlyStop | None = None
    # filled by load_definition
    seed_block: list[int] = Field(default_factory=list)
    definition_sha256: str = ""
    warnings: list[str] = Field(default_factory=list)


def _check_value(key: str, value: Any, root: Path) -> None:
    if key == "length":
        if not isinstance(value, int) or value < 5 or (value - 1) % 4:
            raise ExperimentError(f"length {value!r} must be an integer 4n+1 >= 5 (Wan frame rule)")
    elif key in ("width", "height"):
        if not isinstance(value, int) or value <= 0 or value % 16:
            raise ExperimentError(f"{key} {value!r} must be a positive multiple of 16 (workflow step)")
    elif key == "fps":
        if not isinstance(value, (int, float)) or value <= 0:
            raise ExperimentError(f"fps {value!r} must be positive")
    elif key == "profile":
        from .workflow_adapter import load_binding_profile
        try:
            prof = load_binding_profile(root / value)
        except Exception as exc:  # noqa: BLE001
            raise ExperimentError(f"profile {value!r} cannot be loaded: {exc}") from exc
        if prof.capability != "wan_flf2v":
            raise ExperimentError(f"profile {value!r} is {prof.capability}, not a first/last-frame video profile")
    elif key in ("positive_prompt", "negative_prompt"):
        if not isinstance(value, str) or not value.strip():
            raise ExperimentError(f"{key} values must be non-empty text")


def load_definition(path: str | Path, *, repo_root: str | Path = ".") -> Definition:
    root, raw = Path(repo_root), Path(path).read_bytes()  # noqa: F841 (raw parsed below)
    try:
        data = yaml.safe_load(raw)
        defn = Definition.model_validate({k: v for k, v in (data or {}).items() if v is not None})
    except (ValidationError, yaml.YAMLError) as exc:
        raise ExperimentError(f"invalid experiment definition {path}: {exc}") from exc
    for key in list(defn.controls) + list(defn.factors):
        if key not in ALLOWED:
            raise ExperimentError(f"{key!r} is not a bindable bridge input; allowed: {', '.join(ALLOWED)}")
    leak = sorted(set(defn.controls) & set(defn.factors))
    if leak:
        raise ExperimentError(f"control leakage: {', '.join(leak)} appear in both controls and factors")
    if "seed" in defn.controls or "seed" in defn.factors:
        raise ExperimentError("seed varies only through the seed block (seeds / seed_count)")
    for key, value in defn.controls.items():
        _check_value(key, value, root)
    for key, values in defn.factors.items():
        if not values:
            raise ExperimentError(f"factor {key!r} has no values")
        for value in values:
            _check_value(key, value, root)
        if len(values) == 1:
            defn.warnings.append(f"factor {key!r} has a single value; it behaves like a control")
    for role in ("start_image", "end_image"):
        if not (root / getattr(defn.subject, role)).is_file():
            raise ExperimentError(f"subject {role} not found: {getattr(defn.subject, role)}")
    _check_value("profile", defn.subject.profile, root)
    if defn.seeds:
        defn.seed_block = list(dict.fromkeys(defn.seeds))
    elif defn.seed_count:
        defn.seed_block = [derived_seed(defn.master_seed, f"experiment:{defn.name}:{i}") for i in range(defn.seed_count)]
    else:
        raise ExperimentError("give a seed block: seeds: [..] or seed_count: N")
    # identity of the comparison itself; budget / early-stop changes keep the same folder so runs resume
    core = {"name": defn.name, "subject": defn.subject.model_dump(), "controls": defn.controls,
            "factors": defn.factors, "seeds": defn.seed_block}
    defn.definition_sha256 = hashlib.sha256(json.dumps(core, sort_keys=True).encode("utf-8")).hexdigest()
    return defn


def effective_defaults(profile: str, *, repo_root: str | Path = ".") -> dict:
    """Literal values baked into the exported workflow at the profile's bound inputs."""
    from .workflow_adapter import load_api_workflow, load_binding_profile, resolve_workflow_path
    root = Path(repo_root)
    prof = load_binding_profile(root / profile)
    graph = load_api_workflow(resolve_workflow_path(prof, root / profile, root))
    out = {}
    for role in ("length", "width", "height", "fps", "positive_prompt", "negative_prompt"):
        b = prof.bindings.get(role)
        if b and b.node_id in graph:
            out[role] = graph[b.node_id]["inputs"].get(b.input)
    return out


def load_history_file(path: str | Path | None) -> list[dict]:
    if not path or not Path(path).is_file():
        return []
    return json.loads(Path(path).read_text(encoding="utf-8")).get("entries", [])


def _estimate(history: list[dict], width: int, height: int, frames: int) -> tuple[float | None, str]:
    hits = [h["exec_s"] for h in history if h.get("kind") == "bridge" and h.get("width") == width
            and h.get("height") == height and h.get("frames") == frames]
    if not hits:
        return None, NO_DATA
    return round(statistics.median(hits), 1), f"ESTIMATED ({len(hits)} samples)"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def design(defn: Definition, history: list[dict], *, repo_root: str | Path = ".") -> list[dict]:
    """Baseline, then factorial x seeds (factors by name, values as written, seeds fastest), budget-marked."""
    root = Path(repo_root)
    images = {r: _sha(root / getattr(defn.subject, r)) for r in ("start_image", "end_image")}
    names = sorted(defn.factors)
    combos = [{}] + [dict(zip(names, values)) for values in itertools.product(*(defn.factors[n] for n in names))]
    candidates, seen = [], set()
    for combo_index, combo in enumerate(combos):
        for seed in (defn.seed_block[:1] if combo_index == 0 else defn.seed_block):
            settings = {"profile": defn.subject.profile, "positive_prompt": defn.subject.positive_prompt,
                        "negative_prompt": defn.subject.negative_prompt, **defn.controls, **combo, "seed": seed}
            defaults = effective_defaults(settings["profile"], repo_root=root)
            frames = settings.get("length") or defaults.get("length")
            width = settings.get("width") or defaults.get("width")
            height = settings.get("height") or defaults.get("height")
            effective = {k: (settings.get(k) if settings.get(k) is not None else defaults.get(k))
                         for k in ("length", "width", "height", "fps", "positive_prompt", "negative_prompt")}
            identity = json.dumps({"profile": settings["profile"], "seed": seed, "images": images,
                                   "effective": effective}, sort_keys=True)
            cid = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
            if cid in seen:
                continue
            seen.add(cid)
            est, label = _estimate(history, width, height, frames)
            candidates.append({"id": cid, "index": len(candidates), "baseline": combo_index == 0,
                               "start_image": str(root / defn.subject.start_image),
                               "end_image": str(root / defn.subject.end_image),
                               "settings": settings, "levels": combo, "seed": seed, "frames": frames,
                               "width": width, "height": height, "estimate_s": est, "estimate_label": label,
                               "status": "planned", "limit": None})
    b, runs, gpu, frames_total = defn.budget, 0, 0.0, 0
    for c in candidates:
        if b.max_runs is not None and runs + 1 > b.max_runs:
            c.update(status="deferred", limit="max_runs")
        elif b.max_gpu_s is not None and c["estimate_s"] is not None and gpu + c["estimate_s"] > b.max_gpu_s:
            c.update(status="deferred", limit="max_gpu_s")
        elif b.max_frames is not None and frames_total + c["frames"] > b.max_frames:
            c.update(status="deferred", limit="max_frames")
        else:
            runs += 1
            gpu += c["estimate_s"] or 0.0
            frames_total += c["frames"]
    return candidates


def out_dir_for(defn: Definition, out_root: str | Path) -> Path:
    return Path(out_root) / f"{defn.name}-{defn.definition_sha256[:8]}"


def plan_summary(defn: Definition, candidates: list[dict], out_root: str | Path) -> dict:
    known = [c["estimate_s"] for c in candidates if c["status"] == "planned" and c["estimate_s"] is not None]
    unknown = sum(1 for c in candidates if c["status"] == "planned" and c["estimate_s"] is None)
    return {"experiment": defn.name, "out_dir": str(out_dir_for(defn, out_root)), "warnings": defn.warnings,
            "seeds": defn.seed_block, "candidates": [{k: c[k] for k in ("id", "baseline", "levels", "seed", "frames",
                                                                         "width", "height", "estimate_s",
                                                                         "estimate_label", "status", "limit")}
                                                     for c in candidates],
            "planned": sum(c["status"] == "planned" for c in candidates),
            "deferred": sum(c["status"] == "deferred" for c in candidates),
            "estimated_known_s": round(sum(known), 1), "planned_without_estimate": unknown}


# ------------------------------------------------------------------------------------------ runner

def _read_results(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _append(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


FINISHED = ("done", "failed")


def run(defn: Definition, executor: Callable[..., dict], *, confirm_gpu: bool, history: list[dict],
        out_root: str | Path, repo_root: str | Path = ".") -> dict:
    """Execute planned candidates one at a time in design order; resumable; stops at the budget."""
    candidates = design(defn, history, repo_root=repo_root)
    log = out_dir_for(defn, out_root) / "results.jsonl"
    finished = {r["id"]: r for r in _read_results(log) if r.get("status") in FINISHED}
    summary = {"ran": 0, "validated": 0, "invalid": 0, "errors": [], "reused": 0, "skipped": 0, "skip_reasons": [], "stopped": None,
               "deferred": sum(c["status"] == "deferred" for c in candidates), "results": str(log)}
    runs = len(finished)
    gpu = sum(r.get("exec_s") or 0.0 for r in finished.values())
    streak: dict[str, int] = {}
    stopped_levels: set[str] = set()

    def level_keys(c: dict) -> list[str]:
        return [f"{k}={v}" for k, v in c["levels"].items()]

    def note_flags(c: dict, outcome: dict) -> None:
        flagged = outcome.get("status") == "failed" or bool(outcome.get("flags"))
        for key in level_keys(c):
            streak[key] = streak.get(key, 0) + 1 if flagged else 0
            if defn.early_stop and streak[key] >= defn.early_stop.consecutive_flagged:
                stopped_levels.add(key)

    b = defn.budget
    for c in candidates:
        if c["status"] == "deferred":
            continue
        if c["id"] in finished:
            summary["reused"] += 1
            note_flags(c, finished[c["id"]])
            continue
        blocked = [k for k in level_keys(c) if k in stopped_levels]
        if blocked:
            summary["skipped"] += 1
            summary["skip_reasons"].append(f"{c['id']}: early stop after flagged {', '.join(blocked)}")
            continue
        if confirm_gpu:
            if b.max_runs is not None and runs >= b.max_runs:
                summary["stopped"] = "budget exhausted (max_runs)"
                break
            if b.max_gpu_s is not None and gpu >= b.max_gpu_s:
                summary["stopped"] = "budget exhausted (max_gpu_s)"
                break
        outcome = dict(executor(c, submit=confirm_gpu))
        outcome.update(id=c["id"], frames_requested=c["frames"],
                       t=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        _append(log, outcome)
        if outcome.get("status") in FINISHED:
            summary["ran"] += 1
            runs += 1
            gpu += outcome.get("exec_s") or 0.0
            note_flags(c, outcome)
        elif outcome.get("status") == "invalid":
            summary["invalid"] += 1
            summary["errors"].append(f"{c['id']}: {outcome.get('error')}")
        else:
            summary["validated"] += 1
    if confirm_gpu and summary["stopped"] is None and b.max_gpu_s is not None and gpu >= b.max_gpu_s:
        summary["stopped"] = "budget exhausted (max_gpu_s)"
    summary["measured_exec_s"] = round(gpu, 1)
    return summary


def bridge_executor(*, url: str = "http://127.0.0.1:8188", runs_root: str | Path = "outputs/runs",
                    repo_root: str | Path = ".") -> Callable[..., dict]:
    """Real executor: one bridge job per candidate via the normal machinery (idle queue, --confirm-gpu)."""
    from .bridge import BridgeRequest, plan_bridge, run_bridge
    from .comfy_client import ComfyClient
    root = Path(repo_root)

    def execute(c: dict, *, submit: bool) -> dict:
        s = c["settings"]
        defn_subject = {k: s.get(k) for k in ("profile", "positive_prompt", "negative_prompt", "width", "height",
                                               "length", "fps")}
        request = BridgeRequest(start_image=c["start_image"], end_image=c["end_image"], seed=s["seed"],
                                **{k: v for k, v in defn_subject.items() if v is not None})
        try:
            with ComfyClient(url) as client:
                plan = plan_bridge(request, client.object_info(), repo_root=root)
                job = run_bridge(plan, client, runs_root, submit=submit)
        except Exception as exc:  # noqa: BLE001 - recorded, the experiment continues
            return {"status": "failed" if submit else "invalid", "error": str(exc), "exec_s": None}
        if not submit:
            return {"status": "validated", "job_dir": str(job.dir)}
        record = job.record
        video = next((o for o in record.get("outputs", []) if o.get("kind") == "video"), None)
        flags: list[str] = []
        if video and job.state == "verified":
            try:
                from .qa import analyze_clip
                flags = analyze_clip(job.dir / Path(video["local_path"].replace("\\", "/")))["flags"]
            except Exception as exc:  # noqa: BLE001
                flags = [f"qa unavailable: {exc}"]
        return {"status": "done" if job.state == "verified" else "failed", "job_dir": str(job.dir),
                "exec_s": (record.get("timings") or {}).get("execution_seconds"),
                "peak_vram": None, "frames_produced": ((video or {}).get("metadata") or {}).get("frame_count"),
                "bytes": (video or {}).get("bytes"), "flags": flags, "error": record.get("error")}

    return execute


# --------------------------------------------------------------------------------- ratings / report

def _ratings_path(defn: Definition, out_root: str | Path) -> Path:
    return out_dir_for(defn, out_root) / "ratings.json"


def rate(defn: Definition, candidate_id: str, score: int, note: str = "", *, out_root: str | Path,
         repo_root: str | Path = ".") -> dict:
    if not isinstance(score, int) or not 1 <= score <= 5:
        raise ExperimentError("rating must be an integer from 1 to 5")
    ids = {c["id"] for c in design(defn, [], repo_root=repo_root)}
    if candidate_id not in ids:
        raise ExperimentError(f"unknown candidate {candidate_id}")
    path = _ratings_path(defn, out_root)
    data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    data[candidate_id] = {"score": score, "note": note, "t": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    part.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    os.replace(part, path)
    return {"id": candidate_id, **data[candidate_id]}


def pareto(rows: list[dict], minimize: list[str], maximize: str = "rating") -> list[str]:
    """Ids not dominated: no other row is >= on rating and <= on every cost, and strictly better on one."""
    def dominates(a: dict, b: dict) -> bool:
        no_worse = a[maximize] >= b[maximize] and all(a[k] <= b[k] for k in minimize)
        better = a[maximize] > b[maximize] or any(a[k] < b[k] for k in minimize)
        return no_worse and better
    return [r["id"] for r in rows if not any(dominates(o, r) for o in rows if o is not r)]


def _mean(values: list) -> float | None:
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals), 3) if vals else None


def report(defn: Definition, *, out_root: str | Path, repo_root: str | Path = ".") -> dict:
    candidates = {c["id"]: c for c in design(defn, [], repo_root=repo_root)}
    out = out_dir_for(defn, out_root)
    results = {r["id"]: r for r in _read_results(out / "results.jsonl") if r.get("status") in FINISHED}
    ratings = json.loads(_ratings_path(defn, out_root).read_text(encoding="utf-8")) \
        if _ratings_path(defn, out_root).is_file() else {}
    done = [results[i] for i in candidates if i in results and results[i]["status"] == "done"]
    mismatches = [r["id"] for r in done if r.get("frames_produced") is not None
                  and r["frames_produced"] != candidates[r["id"]]["frames"]]
    rated_rows = [{"id": r["id"], "rating": ratings[r["id"]]["score"], "exec_s": r.get("exec_s"),
                   "peak_vram": r.get("peak_vram"), "bytes": r.get("bytes")} for r in done if r["id"] in ratings]
    dims = [k for k in ("exec_s", "peak_vram", "bytes") if rated_rows and all(x[k] is not None for x in rated_rows)]
    not_measured = [k for k in ("exec_s", "peak_vram", "bytes") if k not in dims]
    levels: dict[str, dict] = {}
    for factor, values in defn.factors.items():
        levels[factor] = {}
        for value in values:
            ids = [i for i, c in candidates.items() if c["levels"].get(factor) == value and i in results]
            rows = [results[i] for i in ids if results[i]["status"] == "done"]
            levels[factor][str(value)] = {
                "n": len(ids), "rated": sum(1 for i in ids if i in ratings),
                "mean_rating": _mean([ratings[i]["score"] for i in ids if i in ratings]),
                "mean_exec_s": _mean([r.get("exec_s") for r in rows]),
                "mean_bytes": _mean([r.get("bytes") for r in rows]),
                "mean_vram": _mean([r.get("peak_vram") for r in rows])}
    rep = {"experiment": defn.name, "definition_sha256": defn.definition_sha256, "subject": defn.subject.model_dump(),
           "controls": defn.controls, "factors": defn.factors, "seeds": defn.seed_block,
           "budget": defn.budget.model_dump(),
           "totals": {"candidates": len(candidates), "done": len(done),
                      "failed": sum(1 for r in results.values() if r["status"] == "failed"),
                      "exec_s": round(sum(r.get("exec_s") or 0 for r in done), 1)},
           "levels": levels, "mismatches": mismatches,
           "unrated": [i for i in candidates if i not in ratings],
           "pareto": pareto(rated_rows, dims) if rated_rows else [],
           "pareto_dimensions": ["rating (max)"] + [f"{d} (min)" for d in dims], "not_measured": not_measured,
           "notes": {i: ratings[i]["note"] for i in ratings if ratings[i].get("note")}, "caveat": CAVEAT}
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(rep, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    (out / "report.md").write_text(_markdown(rep, candidates), encoding="utf-8")
    return rep


def _markdown(rep: dict, candidates: dict) -> str:
    def text(v) -> str:
        return json.dumps(v, ensure_ascii=True)
    lines = [f"# Experiment report: {rep['experiment']}", "",
             f"*{rep['caveat']}*", "",
             "## Variables", "",
             f"- Controls: {text(rep['controls'])}", f"- Factors: {text(rep['factors'])}",
             f"- Seeds: {text(rep['seeds'])}", f"- Budget: {text(rep['budget'])}",
             f"- Totals: {text(rep['totals'])}", "",
             "## Levels", "", "| factor | value | n | rated | mean rating | mean GPU s | mean bytes |",
             "|---|---|---|---|---|---|---|"]
    for factor, values in rep["levels"].items():
        for value, s in values.items():
            lines.append(f"| {factor} | {text(value)} | {s['n']} | {s['rated']} | {s['mean_rating']} | "
                         f"{s['mean_exec_s']} | {s['mean_bytes']} |")
    lines += ["", "## Pareto choices", "", f"Dimensions: {', '.join(rep['pareto_dimensions'])}; "
              f"not measured: {', '.join(rep['not_measured']) or 'none'}.", ""]
    for cid in rep["pareto"]:
        c = candidates[cid]
        lines.append(f"- `{cid}` levels {text(c['levels'])} seed {c['seed']}: {text(rep['notes'].get(cid, ''))}")
    lines += ["", "## Flags", "", f"- Length mismatches: {text(rep['mismatches'])}",
              f"- Unrated: {len(rep['unrated'])}", ""]
    return "\n".join(lines)
