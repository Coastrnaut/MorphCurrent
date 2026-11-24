"""One-command storyboard render (F10): DAG → anchors → bridges → QA → review → join.

Every stage is a content-addressed job reused on rerun, so running the same command
again resumes without repeating inference. GPU work only with ``confirm_gpu``.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

from .anchors import AnchorSpec, anchor_image_path, run_anchor_chain
from .comfy_client import ComfyClient
from .dag import compile_plan
from .media import ProbeUnavailable, contact_sheet, probe_video
from .pipeline import run_bridge_stage
from .qa import analyze_clip, load_reviews
from .run_manifest import RunManifest
from .schema import load_storyboard
from .stitcher import join_verified
from .vram import VramSampler

DECISION_DOC = "docs/ANCHOR_MODEL_DECISION.md"


def _repo_head(root: Path) -> str | None:
    try:
        done = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True,
                              text=True, timeout=10, shell=False, check=False)
        return done.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def build_plan(storyboard_path: str | Path, profiles: dict | None, repo_root: Path) -> dict:
    path = Path(storyboard_path)
    return compile_plan(load_storyboard(path), profiles=profiles, repo_root=repo_root,
                        storyboard_bytes=path.read_bytes())


def dry_run(storyboard_path: str | Path, profiles: dict | None = None, repo_root: str | Path = ".") -> dict:
    """No network, no writes: what would run and what is missing."""
    plan = build_plan(storyboard_path, profiles, Path(repo_root))
    tasks = plan["tasks"].values()
    return {"status": "blocked" if plan["blocked"] else "ready", "plan": plan,
            "gpu_jobs": {"anchors": sum(t["kind"] == "anchor" for t in tasks),
                         "bridges": sum(t["kind"] == "bridge" for t in tasks)},
            "blocked": plan["blocked"],
            "hint": f"see {DECISION_DOC}" if plan["blocked"] else "re-run with --confirm-gpu"}


def run_render(storyboard_path: str | Path, client_factory: Callable[[], ComfyClient], *,
               runs_root: str | Path = "outputs/runs", repo_root: str | Path = ".",
               profiles: dict | None = None, confirm_gpu: bool = False,
               accept_heuristics: bool = False, allow_busy_queue: bool = False,
               sample_vram: bool = False, poll_seconds: float = 2,
               probe: Callable[[Path], dict] = probe_video) -> dict:
    root = Path(repo_root)
    plan = build_plan(storyboard_path, profiles, root)
    if plan["blocked"]:  # preflight: nothing contacted, nothing written
        return {"status": "blocked", "blocked": plan["blocked"], "hint": f"see {DECISION_DOC}",
                "plan_sha256": plan["plan_sha256"]}
    storyboard = load_storyboard(storyboard_path)
    manifest = RunManifest.open(runs_root, plan, storyboard=str(storyboard_path), repo_head=_repo_head(root))
    if confirm_gpu:
        manifest.record("consent", {"flag": "--confirm-gpu", "scope": "this run's anchor and bridge jobs"})
    req = plan["requirements"]
    specs = [AnchorSpec(t["anchor"], t["method"], t["positive_prompt"], t["seed"],
                        negative_prompt=t["negative_prompt"], reference=t["reference"])
             for t in plan["tasks"].values() if t["kind"] == "anchor"]
    with client_factory() as client:
        sampler = VramSampler() if sample_vram and confirm_gpu else None
        if sampler:
            sampler.__enter__()
        try:
            chain = run_anchor_chain(
                specs, client=client, runs_root=runs_root, repo_root=root,
                t2i_profile=req.get("text_to_image", {}).get("profile"),
                edit_profile=req.get("reference_edit", {}).get("profile"),
                width=storyboard.render.width, height=storyboard.render.height,
                submit=confirm_gpu, allow_busy_queue=allow_busy_queue, poll_seconds=poll_seconds)
            for anchor_id, job in chain.jobs.items():
                manifest.record_stage(f"anchor:{anchor_id}", job)
            for anchor_id, reason in chain.blocked.items():
                manifest.record_stage(f"anchor:{anchor_id}", state="blocked", reason=reason)
            if not chain.complete:
                state = "validated" if not confirm_gpu else "blocked"
                return _finish(manifest, state, blocked=chain.blocked)
            bridges = run_bridge_stage(plan, chain.jobs, client=client, runs_root=runs_root,
                                       repo_root=root, submit=confirm_gpu,
                                       allow_busy_queue=allow_busy_queue, poll_seconds=poll_seconds,
                                       probe=probe)
        finally:
            if sampler:
                sampler.__exit__(None, None, None)
                manifest.record("vram", {"stage": "anchors+bridges", **sampler.summary()})
    for task_id, job in bridges.jobs.items():
        manifest.record_stage(task_id, job)
    if not bridges.complete:
        return _finish(manifest, "validated" if not confirm_gpu else "blocked", blocked=bridges.blocked)

    anchor_paths = {a: anchor_image_path(j) for a, j in chain.jobs.items()}
    try:
        sheet = manifest.dir / "anchors_contact_sheet.png"
        if not sheet.exists():
            contact_sheet([anchor_paths[s.id] for s in specs], sheet)
        manifest.record("contact_sheet", str(sheet))
    except ProbeUnavailable as exc:
        manifest.record("contact_sheet", f"skipped: {exc}")
    clips, qa = [], {}
    for task_id in plan["order"]:
        task = plan["tasks"][task_id]
        if task["kind"] != "bridge":
            continue
        job = bridges.jobs[task_id]
        clip = job.dir / next(o["local_path"] for o in job.record["outputs"] if o.get("kind") == "video")
        clips.append(clip)
        qa[task_id] = analyze_clip(clip, anchor_paths[task["from"]], anchor_paths[task["to"]])
        manifest.record_stage(task_id, job, qa=qa[task_id]["status"], qa_flags=qa[task_id]["flags"])
    reviews = load_reviews(manifest.dir / "review.json")
    pending = [t for t in qa if reviews.get(t, {}).get("decision") != "approved"]
    rejected = [t for t in qa if reviews.get(t, {}).get("decision") == "rejected"]
    if rejected:
        return _finish(manifest, "rerender_needed", rejected=rejected)
    if pending and not (accept_heuristics and all(qa[t]["status"] == "no_flags" for t in pending)):
        return _finish(manifest, "awaiting_review", pending=pending)
    movie = manifest.dir / "final" / "movie.mp4"
    if movie.exists():
        return _finish(manifest, "complete", movie=str(movie))
    shared = [anchor_paths[plan["tasks"][t]["to"]] for t in qa][:-1]
    audio = storyboard.audio.file
    report = join_verified(clips, movie, fps=storyboard.render.generation_fps, anchors=shared,
                           audio=Path(audio) if audio else None,
                           audio_offset=storyboard.audio.beat_offset_seconds, probe=probe)
    manifest.record("final", {**report, "approval": "human" if not pending else "heuristics (--accept-heuristics)"})
    manifest.record_stage("final:movie", state="verified", frames=report["frames"])
    return _finish(manifest, "complete", movie=str(movie))


def _finish(manifest: RunManifest, status: str, **info) -> dict:
    manifest.record("status", status)
    return {"status": status, "run_dir": str(manifest.dir), **info}


def render_status(run_dir: str | Path) -> dict:
    """Read-only summary of a run (no network)."""
    m = RunManifest.load(run_dir)
    return {"run_dir": str(m.dir), "status": m.data.get("status"), "plan_sha256": m.data["plan_sha256"],
            "stages": {k: {f: v.get(f) for f in ("state", "job_dir", "image_sha256", "video_sha256", "qa", "reason")
                           if v.get(f) is not None} for k, v in m.data["stages"].items()},
            "reviews": load_reviews(m.dir / "review.json"), "final": m.data.get("final", {}).get("output"),
            "vram": m.data.get("vram")}
