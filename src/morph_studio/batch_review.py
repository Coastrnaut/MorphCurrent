"""F39: batch review and iteration for the full-song film.

The film renders in many batch runs (F36). This module folds every run manifest in a runs folder into one
review state for the film's stages (versions = distinct media hashes, QA, latest decision), keeps decisions in
an append-only per-film log pinned to the version reviewed, bulk-approves clean bridges of an act, orders
review worst-first, builds the rerender queue (rejections plus their reference-edit dependants only) with a
production-model estimate, and makes review aids (act contact sheet, side-by-side comparison).
"""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .qa import SEVERITY

DECISIONS = ("approved", "rejected", "pending")
NOTE_MAX = 500
SHEET_W, SHEET_H = 288, 160


class ReviewError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_log(film: str) -> Path:
    return Path("outputs/reviews") / f"{film}.batch-review.jsonl"


def _media(runs_root: Path, job_dir: str | None) -> Path | None:
    from .review_ui import _job_dir, _job_media
    return _job_media(_job_dir(runs_root, job_dir))


def _load_log(log: Path | None) -> list[dict]:
    if log is None or not Path(log).is_file():
        return []
    return [json.loads(line) for line in Path(log).read_text(encoding="utf-8").splitlines() if line.strip()]


# ------------------------------------------------------------------------------------------ state

def film_state(storyboard: str | Path, runs_root: str | Path = "outputs/runs", log: str | Path | None = None,
               *, repo_root: str | Path = ".") -> dict:
    """Review state of every film stage across all run manifests (``_plan`` holds the compiled plan)."""
    from .accuracy import load_plan
    from .schema import load_storyboard
    sb = load_storyboard(storyboard)
    plan = load_plan(storyboard, repo_root)
    plan["_master_seed"] = sb.render.master_seed
    root = Path(runs_root)
    log = Path(log) if log else default_log(sb.name)
    tasks = plan["tasks"]
    act_of = {}
    for tid in plan["order"]:
        t = tasks[tid]
        if t["kind"] == "anchor":
            act_of[tid] = t.get("chapter") or "(film)"
    for tid in plan["order"]:
        t = tasks[tid]
        if t["kind"] == "bridge":
            act_of[tid] = act_of[f"anchor:{t['from']}"]
    pos = {sb.anchors[k].id: k for k in range(len(sb.anchors))}
    film_pos = {tid: 2 * pos[tasks[tid]["anchor"]] if tasks[tid]["kind"] == "anchor" else 2 * pos[tasks[tid]["from"]] + 1
                for tid in act_of}  # film order: anchor k, bridge k->k+1, anchor k+1, ...
    stages = {tid: {"stage": tid, "kind": tasks[tid]["kind"], "act": act_of[tid], "index": film_pos[tid],
                    "state": "missing", "qa": None, "qa_flags": [], "score": 0, "versions": [], "current": None,
                    "decision": None, "stale": False}
              for tid in sorted(act_of, key=lambda t: film_pos[t])}
    manifests = []
    for mpath in root.glob("run-*/manifest.json") if root.is_dir() else []:
        try:
            data = json.loads(mpath.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        manifests.append((data.get("created_at") or "", mpath.parent, data))
    manifests.sort(key=lambda m: (m[0], m[1].name))
    imported: list[dict] = []
    runs_used = []
    for created, run_dir, data in manifests:
        used = False
        run_hash: dict[str, str] = {}
        for tid, st in (data.get("stages") or {}).items():
            if tid not in stages:
                continue
            used = True
            s = stages[tid]
            digest = st.get("video_sha256") if s["kind"] == "bridge" else st.get("image_sha256")
            if st.get("state") == "verified" and digest:
                run_hash[tid] = digest
                if digest not in [v["sha256"] for v in s["versions"]]:
                    media = _media(root, st.get("job_dir"))
                    s["versions"].append({"sha256": digest, "job_id": st.get("job_id"), "run": run_dir.name,
                                          "t": created, "media": str(media) if media else None})
                if s["kind"] == "bridge" and "qa" in st:
                    s["qa_by_version"] = s.get("qa_by_version", {})
                    s["qa_by_version"][digest] = (st.get("qa"), st.get("qa_flags") or [])
            elif s["state"] == "missing" and st.get("job_dir") and _media(root, st.get("job_dir")):
                s["state"] = "rendered"
        if used:
            runs_used.append(run_dir.name)
            try:
                reviews = json.loads((run_dir / "review.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                reviews = {}
            for tid, rv in reviews.items():
                if tid in run_hash and rv.get("decision") in DECISIONS:
                    imported.append({"t": rv.get("t") or created, "stage": tid, "decision": rv["decision"],
                                     "note": rv.get("note", ""), "reviewer": "owner", "version": run_hash[tid],
                                     "source": "run-review"})
    for s in stages.values():
        if s["versions"]:
            s["state"] = "verified"
            s["current"] = s["versions"][-1]["sha256"]
            qa, flags = s.pop("qa_by_version", {}).get(s["current"], (None, []))
            s["qa"], s["qa_flags"] = qa, flags
            s["score"] = sum(SEVERITY.get(f.get("type"), 1) for f in flags)
        s.pop("qa_by_version", None)
    entries = sorted(imported + [dict(e, source=e.get("source", "film-log")) for e in _load_log(log)],
                     key=lambda e: e["t"])
    for e in entries:
        if e["stage"] in stages:
            stages[e["stage"]]["decision"] = e
    for s in stages.values():
        d = s["decision"]
        s["stale"] = bool(d and s["current"] and d.get("version") != s["current"])
    acts: dict[str, dict] = {}
    for s in stages.values():
        a = acts.setdefault(s["act"], {"anchors": 0, "bridges": 0, "verified": 0, "approved": 0, "rejected": 0,
                                       "stale": 0, "flagged": 0, "missing": 0})
        a["anchors" if s["kind"] == "anchor" else "bridges"] += 1
        a["verified"] += s["state"] == "verified"
        a["missing"] += s["state"] == "missing"
        a["flagged"] += bool(s["qa_flags"])
        a["stale"] += s["stale"]
        if s["decision"] and not s["stale"]:
            a["approved"] += s["decision"]["decision"] == "approved"
            a["rejected"] += s["decision"]["decision"] == "rejected"
    return {"film": sb.name, "storyboard": str(storyboard), "plan_sha256": plan.get("plan_sha256"),
            "log": str(log), "runs": runs_used, "stages": list(stages.values()), "acts": acts,
            "total": len(stages), "_plan": plan, "_runs_root": str(root)}


def public(state: dict) -> dict:
    return {k: v for k, v in state.items() if not k.startswith("_")}


def _stage(state: dict, stage: str) -> dict:
    for s in state["stages"]:
        if s["stage"] == stage:
            return s
    raise ReviewError(f"{stage!r} is not a stage of {state['film']}")


def _needs_review(s: dict) -> bool:
    d = s["decision"]
    return bool(s["current"]) and (d is None or s["stale"] or d["decision"] == "pending")


# ------------------------------------------------------------------------------------------ decisions

def record(state: dict, stage: str, decision: str, note: str = "", reviewer: str = "owner") -> dict:
    s = _stage(state, stage)
    if decision not in DECISIONS:
        raise ReviewError(f"decision must be one of {', '.join(DECISIONS)}")
    if not s["current"]:
        raise ReviewError(f"{stage} has no rendered version to review")
    if not str(reviewer).strip():
        raise ReviewError("reviewer must not be empty")
    entry = {"t": _now(), "stage": stage, "decision": decision, "note": str(note)[:NOTE_MAX],
             "reviewer": str(reviewer).strip(), "version": s["current"], "source": "film-log"}
    log = Path(state["log"])
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(entry, ensure_ascii=True) + "\n")
    s["decision"], s["stale"] = entry, False
    return entry


def approve_act(state: dict, act: str, reviewer: str = "owner") -> dict:
    if act not in state["acts"]:
        raise ReviewError(f"no act {act!r} in {state['film']}")
    done = []
    for s in state["stages"]:
        if s["act"] == act and s["kind"] == "bridge" and not s["qa_flags"] and _needs_review(s):
            record(state, s["stage"], "approved", "bulk approval of unflagged bridges", reviewer)
            done.append(s["stage"])
    return {"act": act, "approved": len(done), "stages": done}


def review_order(state: dict, act: str | None = None) -> list[dict]:
    todo = [s for s in state["stages"] if _needs_review(s) and (act is None or s["act"] == act)]
    return sorted(todo, key=lambda s: (0 if s["qa_flags"] else 1, -s["score"], s["index"]))


# ------------------------------------------------------------------------------------------ rerender

def rerender_queue(state: dict, history: str | Path | None = None) -> dict:
    from .production import DEFAULT_HISTORY, _load_history, stage_cost
    plan = state["_plan"]
    tasks = plan["tasks"]
    rejected = [s["stage"] for s in state["stages"]
                if s["decision"] and not s["stale"] and s["decision"]["decision"] == "rejected"]
    reasons: dict[str, str] = {r: "rejected" for r in rejected}
    bad = {tasks[r]["anchor"] for r in rejected if tasks[r]["kind"] == "anchor"}
    root_of: dict[str, str] = {a: a for a in bad}
    for tid in plan["order"]:  # topological: references precede their edits
        t = tasks[tid]
        if t["kind"] == "anchor" and t.get("conditioned_on_parent") and t.get("reference") in bad \
                and t["anchor"] not in bad:
            bad.add(t["anchor"])
            root_of[t["anchor"]] = root_of[t["reference"]]
            reasons.setdefault(tid, f"depends on {root_of[t['anchor']]}")
    for tid in plan["order"]:
        t = tasks[tid]
        if t["kind"] == "bridge" and tid not in reasons:
            hit = t["from"] if t["from"] in bad else t["to"] if t["to"] in bad else None
            if hit:
                reasons[tid] = f"touches {hit}"
    hist = _load_history(Path(history) if history else DEFAULT_HISTORY)["entries"]
    rows, total, labels = [], 0.0, {}
    for tid in plan["order"]:
        if tid in reasons:
            est, label = stage_cost(tasks[tid], hist)
            rows.append({"stage": tid, "reason": reasons[tid], "est_s": est, "label": label})
            total += est or 0.0
            labels[label] = labels.get(label, 0) + 1
    return {"stages": rows, "total_s": round(total, 1), "labels": labels, "rejected": rejected}


def write_rerender(state: dict, queue: dict, out: str | Path) -> Path:
    """Contiguous storyboard segment: queued stages get new derived seeds, others keep pinned film seeds."""
    from .timeline import derived_seed
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"{out} exists; refusing to overwrite")
    if not queue["stages"]:
        raise ReviewError("the rerender queue is empty")
    plan = state["_plan"]
    tasks = plan["tasks"]
    master = plan["_master_seed"]
    data = yaml.safe_load(Path(state["storyboard"]).read_text(encoding="utf-8"))
    order = [a["id"] for a in data["anchors"]]
    idx = {a: i for i, a in enumerate(order)}
    by_id = {a["id"]: a for a in data["anchors"]}
    trans = {(t["from"], t["to"]): t for t in data["transitions"]}
    queued = {r["stage"] for r in queue["stages"]}
    versions = {s["stage"]: len(s["versions"]) for s in state["stages"]}
    span = [idx[tasks[q]["anchor"]] if tasks[q]["kind"] == "anchor" else idx[tasks[q]["from"]] for q in queued]
    span += [idx[tasks[q]["to"]] for q in queued if tasks[q]["kind"] == "bridge"]
    lo, hi = min(span), max(span)
    act = by_id[order[lo]].get("chapter")
    while lo > 0 and by_id[order[lo - 1]].get("chapter") == act:
        lo -= 1  # start at the act's first anchor so reference edits have their parents
    ids = order[lo:hi + 1]

    def seed(tid: str) -> int:
        if tid in queued:
            return derived_seed(master, f"{tid}:rerender:{versions.get(tid, 0)}")
        return tasks[tid]["seed"]

    sub = copy.deepcopy(data)
    sub["name"] = f"{data['name']}-rerender"
    sub["anchors"] = [dict(copy.deepcopy(by_id[i]), seed=seed(f"anchor:{i}")) for i in ids]
    sub["transitions"] = [dict(copy.deepcopy(trans[(x, y)]), seed=seed(f"bridge:{x}->{y}"))
                          for x, y in zip(ids, ids[1:])]
    header = (f"# F39 rerender of {len(queued)} stage(s) of {data['name']} (est. {queue['total_s']} GPU s, "
              f"{', '.join(f'{k} {v}' for k, v in sorted(queue['labels'].items()))}); new seeds only for queued "
              f"stages, others pinned (cache hits).\n# render with `render {out.as_posix()} --confirm-gpu`\n")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(header + yaml.safe_dump(sub, sort_keys=False, width=120), encoding="utf-8")
    return out


# ------------------------------------------------------------------------------------------ media aids

def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise ReviewError("ffmpeg not found on PATH")
    return exe


def _run(args: list[str], cwd: Path | None = None) -> None:
    done = subprocess.run(args, capture_output=True, text=True, errors="replace", shell=False, check=False, cwd=cwd)
    if done.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {done.stderr[-400:]}")


def act_sheet(state: dict, act: str, out: str | Path) -> dict:
    """One row per rendered bridge of an act: first, middle and last frame."""
    from .media import probe_video
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"{out} exists; refusing to overwrite")
    if act not in state["acts"]:
        raise ReviewError(f"no act {act!r} in {state['film']}")
    bridges = [s for s in state["stages"] if s["act"] == act and s["kind"] == "bridge"]
    exe = _ffmpeg()
    rows, missing, counts = [], [], []
    for s in bridges:
        media = s["versions"][-1]["media"] if s["versions"] else None
        frames = None
        if media and Path(media).is_file():
            try:  # unreadable or truncated clips are listed as missing, not fatal
                frames = probe_video(media)["frame_count"]
            except (RuntimeError, ValueError, OSError):
                frames = None
        if frames:
            rows.append((s, media))
            counts.append(frames)
        else:
            missing.append((s, media))
    if not rows:
        raise ReviewError(f"no rendered bridge in act {act}")
    record_rows = []
    with tempfile.TemporaryDirectory(prefix="mc-sheet-") as tmp:
        tmpdir = Path(tmp)
        for n, ((s, media), frames) in enumerate(zip(rows, counts)):
            picks = [0, (frames - 1) // 2, frames - 1]
            sel = "+".join(f"eq(n\\,{p})" for p in picks)
            _run([exe, "-v", "error", "-y", "-i", str(media), "-vf",
                  f"select='{sel}',scale={SHEET_W}:{SHEET_H},setsar=1,tile=3x1", "-frames:v", "1",
                  "-fps_mode", "passthrough", str(tmpdir / f"r{n:03d}.png")])
            record_rows.append({"stage": s["stage"], "version": s["current"], "frames": picks})
        inputs = [a for n in range(len(rows)) for a in ("-i", f"r{n:03d}.png")]
        flt = f"vstack=inputs={len(rows)}" if len(rows) > 1 else "null"
        out.parent.mkdir(parents=True, exist_ok=True)
        _run([exe, "-v", "error", "-y", *inputs, "-filter_complex", flt, "-frames:v", "1",
              str(out.resolve())], cwd=tmpdir)
    rec = {"act": act, "rows": record_rows, "missing": [s["stage"] for s, _ in missing], "out": str(out),
           "row_px": [SHEET_W * 3, SHEET_H]}
    out.with_name(out.stem + ".sheet.json").write_text(json.dumps(rec, indent=2, ensure_ascii=True), encoding="utf-8")
    return rec


def _version(s: dict, ref: str | None, default: int) -> dict:
    if ref is None:
        return s["versions"][default]
    hits = [v for v in s["versions"] if v["sha256"].startswith(ref)]
    if len(hits) != 1:
        raise ReviewError(f"version {ref!r} is not exactly one version of {s['stage']}")
    return hits[0]


def compare(state: dict, stage: str, out: str | Path, a: str | None = None, b: str | None = None) -> dict:
    """Side-by-side clip of two versions of one bridge (default: the last two)."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"{out} exists; refusing to overwrite")
    s = _stage(state, stage)
    if len(s["versions"]) < 2:
        raise ReviewError(f"{stage} has {len(s['versions'])} version(s); two are needed to compare")
    va, vb = _version(s, a, -2), _version(s, b, -1)
    if va["sha256"] == vb["sha256"]:
        raise ReviewError("pick two different versions")
    for v in (va, vb):
        if not v["media"] or not Path(v["media"]).is_file():
            raise ReviewError(f"media of version {v['sha256'][:12]} is not available")
    out.parent.mkdir(parents=True, exist_ok=True)
    _run([_ffmpeg(), "-v", "error", "-y", "-i", va["media"], "-i", vb["media"], "-filter_complex",
          "[0:v]scale=-2:240,setsar=1[a];[1:v]scale=-2:240,setsar=1[b];[a][b]hstack=inputs=2",
          "-an", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(out)])
    return {"stage": stage, "a": va["sha256"], "b": vb["sha256"], "out": str(out)}
