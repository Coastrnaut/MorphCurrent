"""F40: full-song film delivery and acceptance.

Assembles the film from the owner-approved version of every bridge (F39 review state), joins them with the
seam-verified join (no frame dropping), checks that the picture covers the whole song, hands the master to
the F30 delivery presets, and writes a provenance report (hashes, chosen versions and seeds, workflows and
models, licences, owner approvals, measured vs estimated GPU time) plus the F31-F40 gate matrix.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .batch_review import ReviewError, film_state

DEFAULT_PRESETS = ["landscape-1080p", "vertical-1080x1920"]
ACCEPTED = Path("configs/film/accepted-blockers.yaml")
PROFILES = ["anchor_t2i", "anchor_edit", "wan22_flf2v"]


class Blocked(ReviewError):
    def __init__(self, blockers: list[dict]):
        self.blockers = blockers
        super().__init__(f"{len(blockers)} stage(s) block assembly: "
                         + ", ".join(f"{b['stage']} ({b['reason']})" for b in blockers[:6])
                         + (" ..." if len(blockers) > 6 else ""))


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------------------------------ choice

def choose(state: dict, preview: bool = False) -> dict:
    """Per bridge the approved current version (or, in preview, the current one); blockers with reasons."""
    chosen, blockers, unapproved, anchors = [], [], [], []
    for s in state["stages"]:
        if s["kind"] == "anchor":
            v = s["versions"][-1] if s["versions"] else None
            anchors.append({"stage": s["stage"], "version": v["sha256"] if v else None,
                            "media": v["media"] if v else None})
            continue
        d = s["decision"]
        if not s["versions"]:
            reason = "missing"
        elif d is None:
            reason = "unreviewed"
        elif s["stale"]:
            reason = "stale"
        elif d["decision"] != "approved":
            reason = d["decision"]
        else:
            reason = None
        if reason == "missing" or (reason and not preview):
            blockers.append({"stage": s["stage"], "reason": reason})
            continue
        if reason:
            unapproved.append({"stage": s["stage"], "reason": reason})
        v = s["versions"][-1]
        chosen.append({"stage": s["stage"], "version": v["sha256"], "job_id": v["job_id"], "run": v["run"],
                       "media": v["media"], "decision": d["decision"] if d and not s["stale"] else None})
    return {"chosen": chosen, "blockers": blockers, "unapproved": unapproved, "anchors": anchors}


def _readable_image(path: str | None) -> bool:
    if not path or not Path(path).is_file():
        return False
    head = Path(path).read_bytes()[:8]
    return head.startswith(b"\x89PNG") or head[:3] == b"\xff\xd8\xff"


# ------------------------------------------------------------------------------------------ assemble

def assemble(storyboard: str | Path, runs_root: str | Path = "outputs/runs", log: str | Path | None = None,
             out: str | Path | None = None, *, preview: bool = False, audio: str | Path | None = None,
             audio_licensed: bool = False, offset: float = 0.0, repo_root: str | Path = ".") -> dict:
    from .media import probe_video
    from .schema import load_storyboard
    from .soundtrack import anchor_frames
    from .stitcher import join_verified
    if audio is not None and not audio_licensed:
        raise ReviewError("audio must be marked licensed (--audio-licensed) before it is muxed")
    state = film_state(storyboard, runs_root, log, repo_root=repo_root)
    pick = choose(state, preview)
    if pick["blockers"]:
        raise Blocked(pick["blockers"])
    sb = load_storyboard(storyboard)
    fps = int(sb.render.generation_fps)
    planned = anchor_frames(sb)[-1] + 1
    if out is None:
        plan8 = (state["plan_sha256"] or "")[:8]
        out = Path("outputs/film") / f"{state['film']}_{_ts()}_{plan8}{'_PREVIEW' if preview else ''}.mp4"
    out = Path(out)
    if preview and "PREVIEW" not in out.stem.upper():
        out = out.with_name(out.stem + "_PREVIEW" + out.suffix)
    if out.exists():
        raise FileExistsError(f"{out} exists; refusing to overwrite")
    clips = [Path(c["media"]) for c in pick["chosen"]]
    for c, p in zip(pick["chosen"], clips):
        if not p.is_file():
            raise ReviewError(f"media of {c['stage']} ({c['version'][:12]}) is not available")
    stills = [a["media"] for a in pick["anchors"]]
    inner = stills[1:-1]  # the anchor shared by each seam
    seam_mode = "anchor+boundary" if inner and all(_readable_image(p) for p in inner) else "boundary"
    joined = join_verified(clips, out, fps=fps, anchors=[Path(p) for p in inner] if seam_mode != "boundary" else None,
                           audio=Path(audio) if audio else None, audio_offset=offset)
    if joined["frames"] != planned:
        out.unlink(missing_ok=True)
        raise ReviewError(f"joined film has {joined['frames']} frames but the storyboard plans {planned}; "
                          "the picture would not cover the song")
    measured = probe_video(out)
    duration = measured.get("duration_s") or joined["frames"] / fps
    if abs(duration - planned / fps) > 1.0 / fps + 1e-3:
        raise ReviewError(f"master lasts {duration:.3f} s, planned {planned / fps:.3f} s")
    record = {"film": state["film"], "storyboard": str(storyboard), "plan_sha256": state["plan_sha256"],
              "storyboard_sha256": _sha(Path(storyboard)), "preview": preview, "chosen": pick["chosen"],
              "anchors": pick["anchors"], "unapproved": pick["unapproved"], "master": str(out),
              "master_sha256": _sha(out), "frames": joined["frames"], "planned_frames": planned, "fps": fps,
              "duration_s": round(duration, 6), "planned_s": planned / fps, "seams": joined["seams"],
              "seam_mode": seam_mode, "audio": str(audio) if audio else None, "audio_licensed": bool(audio),
              "audio_offset_s": offset if audio else None, "runs_root": str(runs_root),
              "log": state["log"], "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "note": "PREVIEW - not acceptance evidence" if preview else "assembled from owner-approved versions"}
    rec_path = out.with_name(out.stem + ".assembly.json")
    rec_path.write_text(json.dumps(record, indent=2, ensure_ascii=True), encoding="utf-8")
    record["record"] = str(rec_path)
    return record


# ------------------------------------------------------------------------------------------ deliver

def deliver_master(master: str | Path, out_dir: str | Path | None = None, presets: list[str] | None = None, *,
                   audio: str | Path | None = None, audio_licensed: bool = False) -> dict:
    from .delivery import deliver
    master = Path(master)
    if not master.is_file():
        raise ReviewError(f"master not found: {master}")
    preview = "PREVIEW" in master.stem.upper()
    out_dir = Path(out_dir) if out_dir else master.with_name(master.stem + "_delivery")
    kwargs = {"audio": audio, "audio_licensed": audio_licensed} if audio else {}
    res = deliver(master, out_dir, presets or list(DEFAULT_PRESETS), **kwargs)
    record = {"master": str(master), "preview": preview, "presets": presets or list(DEFAULT_PRESETS),
              "results": res["results"], "errors": res["errors"], "out_dir": str(out_dir)}
    path = master.with_name(master.stem + ".delivery.json")
    if path.exists():
        path = master.with_name(f"{master.stem}.delivery-{_ts()}.json")
    path.write_text(json.dumps(record, indent=2, ensure_ascii=True, default=str), encoding="utf-8")
    record["record"] = str(path)
    return record


# ------------------------------------------------------------------------------------------ provenance

def _job_seconds(runs_root: Path, job_id: str | None, run: str | None, stage: str) -> float | None:
    if not run:
        return None
    try:
        manifest = json.loads((runs_root / run / "manifest.json").read_text(encoding="utf-8"))
        job_dir = manifest["stages"][stage]["job_dir"]
        rec = json.loads((runs_root / Path(job_dir.replace("\\", "/")).name / "job.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, KeyError):
        return None
    secs = (rec.get("timings") or {}).get("execution_seconds")
    return float(secs) if secs else None


def provenance(assembly: str | Path | dict, *, repo_root: str | Path = ".", history: str | Path | None = None) -> dict:
    from .accuracy import load_plan
    from .production import DEFAULT_HISTORY, _load_history, budget
    from .provenance import models_in_graph
    from .workflow_adapter import graph_sha256
    rec = json.loads(Path(assembly).read_text(encoding="utf-8")) if not isinstance(assembly, dict) else assembly
    root = Path(repo_root)
    plan = load_plan(rec["storyboard"], repo_root)
    tasks = plan["tasks"]
    runs_root = Path(rec.get("runs_root") or "outputs/runs")
    missing: list[str] = []
    stages = []
    measured, timed = 0.0, 0
    for item in rec["anchors"] + rec["chosen"]:
        st = item["stage"]
        run = item.get("run")
        if run is None:  # anchors: find the run of that version
            run = next((v["run"] for s in film_state(rec["storyboard"], runs_root, rec.get("log"),
                                                     repo_root=repo_root)["stages"]
                        if s["stage"] == st for v in s["versions"] if v["sha256"] == item["version"]), None) \
                if item.get("version") else None
        secs = _job_seconds(runs_root, item.get("job_id"), run, st)
        if secs is not None:
            measured += secs
            timed += 1
        stages.append({"stage": st, "version": item.get("version"), "job_id": item.get("job_id"),
                       "seed": tasks.get(st, {}).get("seed"), "run": run, "exec_s": secs})
        if not item.get("version"):
            missing.append(f"version of {st}")
    catalogue = json.loads((root / "configs/model_catalogue.json").read_text(encoding="utf-8"))
    cat = catalogue.get("models", catalogue)
    try:
        recorded = json.loads((root / "outputs/model_hashes.json").read_text(encoding="utf-8")).get("files", {})
    except (OSError, ValueError):
        recorded = {}
    workflows, models, seen = [], [], set()
    for prof in PROFILES:
        bpath = root / "configs/profiles" / f"{prof}.binding.json"
        if not bpath.is_file():
            missing.append(f"profile binding {prof}")
            continue
        b = json.loads(bpath.read_text(encoding="utf-8"))
        wf = root / b["workflow"]
        graph = json.loads(wf.read_text(encoding="utf-8")) if wf.is_file() else None
        refs = [f"{folder}/{name}" for folder, name in models_in_graph(graph)] if graph else []
        actual = graph_sha256(graph) if graph else None  # same canonical hash the binding pins
        if actual != b.get("workflow_sha256"):
            missing.append(f"workflow hash of {prof} does not match its binding")
        workflows.append({"profile": prof, "workflow": b["workflow"], "workflow_sha256": b.get("workflow_sha256"),
                          "matches": actual == b.get("workflow_sha256"), "models": refs})
        for ref in refs:
            if ref in seen:
                continue
            seen.add(ref)
            entry = cat.get(ref) or {}
            licence = entry.get("licence")
            if not licence or str(licence).upper().startswith("NOT RECORDED"):
                missing.append(f"licence of {ref}")
            models.append({"file": ref, "sha256": entry.get("sha256"), "licence": licence,
                           "recorded_sha256": (recorded.get(ref) or {}).get("sha256")})
    approvals = {}
    bank = yaml.safe_load((root / "configs/concepts/engineering-film.yaml").read_text(encoding="utf-8"))
    approvals["concept_bank"] = {"status": bank.get("status"), "approval": bank.get("approval")}
    lang = yaml.safe_load((root / "configs/film/visual-language.yaml").read_text(encoding="utf-8"))
    approvals["visual_language"] = {"selected": lang.get("selected"), "status": lang.get("status")}
    acts_log = root / "outputs/production" / f"{rec['film']}.approvals.jsonl"
    approvals["acts"] = ([json.loads(x) for x in acts_log.read_text(encoding="utf-8").splitlines() if x.strip()]
                         if acts_log.is_file() else [])
    approvals["review_decisions"] = {"log": rec.get("log"),
                                     "approved_bridges": sum(1 for c in rec["chosen"] if c.get("decision") == "approved"),
                                     "bridges": len(rec["chosen"])}
    for key in ("concept_bank", "visual_language"):
        if approvals[key].get("status") != "approved":
            missing.append(f"{key} approval")
    if not approvals["acts"]:
        missing.append("act approvals")
    if rec.get("preview"):
        missing.append("preview master (not acceptance evidence)")
    if rec.get("unapproved"):
        missing.append(f"{len(rec['unapproved'])} unapproved bridge(s)")
    hist = _load_history(Path(history) if history else DEFAULT_HISTORY)["entries"]
    estimate = budget(plan, hist)["totals"]["seconds"]
    if timed < len(stages):
        missing.append(f"execution time of {len(stages) - timed} job(s)")
    return {"film": rec["film"], "plan_sha256": rec["plan_sha256"], "storyboard_sha256": rec.get("storyboard_sha256"),
            "master": rec["master"], "master_sha256": rec.get("master_sha256"), "preview": bool(rec.get("preview")),
            "stages": stages, "workflows": workflows, "models": models, "approvals": approvals,
            "audio": {"file": rec.get("audio"), "licensed": rec.get("audio_licensed")},
            "gpu": {"measured_s": round(measured, 1), "estimated_s": estimate, "jobs_timed": timed,
                    "ratio": round(measured / estimate, 3) if estimate else None},
            "missing": missing, "complete": not missing}


# ------------------------------------------------------------------------------------------ gates

def _load_accepted(path: Path) -> dict:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out = {}
    for e in data.get("accepted") or []:
        if not re.fullmatch(r"F3\d|F40", str(e.get("feature", ""))):
            raise ReviewError(f"accepted blocker has a bad feature: {e!r}")
        if not str(e.get("owner") or "").strip() or not str(e.get("blocker") or "").strip():
            raise ReviewError(f"accepted blocker needs an owner and a blocker text: {e!r}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(e.get("date", ""))):
            raise ReviewError(f"accepted blocker needs a YYYY-MM-DD date: {e!r}")
        out[e["feature"]] = {"blocker": e["blocker"], "owner": e["owner"], "date": str(e["date"])}
    return out


def gates(ledger: str | Path = "docs/SPECKIT_FEATURE_LEDGER.md", accepted: str | Path = ACCEPTED) -> dict:
    from .release import acceptance_matrix
    rows = [r for r in acceptance_matrix(ledger, through=40)["rows"] if "F31" <= r["feature"] <= "F40"]
    acc = _load_accepted(Path(accepted))
    out = []
    for r in rows:
        a = acc.get(r["feature"])
        out.append({**r, "accepted": a, "resolved": bool(r["evidenced"] or a)})
    return {"rows": out, "resolved": sum(r["resolved"] for r in out), "total": len(out),
            "ok": len(out) == 10 and all(r["resolved"] for r in out)}
