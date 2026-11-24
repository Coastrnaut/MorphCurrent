"""Small, operational offline CLI; no pretend GPU integration."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from pydantic import ValidationError

from .schema import load_storyboard
from .timeline import timeline_as_dict
from .comfy_client import ComfyClient, ComfyError
from .bridge import (
    BridgeError,
    BridgeRequest,
    cancel_bridge,
    load_job,
    plan_bridge,
    request_from_job,
    run_bridge,
)
from .dag import compile_plan
from .qa_subject import calibrate as calibrate_qa
from .audio import AudioError, analyze_audio, sync_report
from .audio_bands import analyze_bands, band_hits, render_timeline_png
from .prompt_compiler import NOTE as PROMPT_NOTE, variants as prompt_variants
from .geometry import compare_images
from .perf import build_report as build_perf_report, estimate as estimate_plan, load_history
from .gates import check_gpu_gate
from .qa import analyze_clip, record_review
from .render import dry_run, render_status, run_render
from .provenance import DEFAULT_MODELS_ROOT, hash_models, models_in_graph
from .anchors import AnchorRequest, plan_anchor, request_from_anchor_job, run_anchor
from .onboarding import as_json as inspect_json, inspect_export, load_export
from .preflight import build_baseline_report
from .windows import windows_diagnostics
from .workflow_adapter import (
    WorkflowBindingError,
    coerce_for_spec,
    load_api_workflow,
    load_binding_profile,
    patch_workflow,
    profile_bindings,
    resolve_workflow_path,
    spec_for_role,
    validate_profile,
)


def _load_object_info(args: argparse.Namespace) -> dict:
    """object_info from a saved snapshot (offline) or the local ComfyUI; never guessed."""
    if args.object_info:
        with open(args.object_info, "r", encoding="utf-8") as stream:
            payload = json.load(stream)
        if not isinstance(payload, dict):
            raise ValueError("object_info snapshot must be a JSON object")
        return payload
    with ComfyClient(args.url) as client:
        return client.object_info()


def _workflow_check(args: argparse.Namespace) -> int:
    profile = load_binding_profile(args.profile)
    graph = load_api_workflow(resolve_workflow_path(profile, args.profile))
    report = validate_profile(profile, graph, _load_object_info(args))
    print(json.dumps({"profile": profile.profile, "workflow": profile.workflow,
                      "roles": sorted(profile.bindings),
                      "outputs": [o.node_id for o in profile.outputs],
                      **report.as_dict()}, indent=2))
    return 0 if report.ok else 4


def _workflow_patch(args: argparse.Namespace) -> int:
    profile = load_binding_profile(args.profile)
    graph = load_api_workflow(resolve_workflow_path(profile, args.profile))
    object_info = _load_object_info(args)
    report = validate_profile(profile, graph, object_info)
    if not report.ok:
        print(json.dumps(report.as_dict(), indent=2), file=sys.stderr)
        return 4
    values = {}
    for item in args.set or []:
        role, sep, raw = item.partition("=")
        if not sep:
            raise ValueError(f"--set expects role=value, got {item!r}")
        values[role] = coerce_for_spec(spec_for_role(profile, graph, object_info, role), raw)
    patched = patch_workflow(graph, profile_bindings(profile), values, object_info)
    text = json.dumps(patched, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        with open(args.out, "x", encoding="utf-8", newline="\n") as stream:  # never overwrite
            stream.write(text)
        print(f"WROTE {args.out} (not submitted to ComfyUI)")
    else:
        sys.stdout.write(text)
    return 0


def _models_hash(args: argparse.Namespace) -> int:
    """Opt-in SHA-256 of model files referenced by profiles; refuses a busy ComfyUI queue."""
    if not args.confirm_io:
        raise ValueError("hashing reads multi-GB model files; pass --confirm-io to proceed")
    with ComfyClient(args.url) as client:
        gate = check_gpu_gate(consent=True, queue=client.queue())
    if not gate.allowed:
        raise ValueError(f"ComfyUI queue has {gate.queue_busy} job(s); not hashing during a render")
    pairs = set()
    for profile_path in args.profile or sorted(Path("configs/profiles").glob("*.binding.json")):
        profile = load_binding_profile(profile_path)
        pairs.update(models_in_graph(load_api_workflow(resolve_workflow_path(profile, profile_path))))
    results = hash_models(sorted(pairs), Path(args.models_root), Path(args.cache))
    print(json.dumps(results, indent=2))
    return 0 if all(r["status"] != "missing" for r in results.values()) else 4


def _qa(args: argparse.Namespace) -> int:
    """Local heuristic temporal QA of one clip (FFmpeg decode; no GPU, no network)."""
    report = analyze_clip(Path(args.clip), Path(args.start) if args.start else None,
                          Path(args.end) if args.end else None)
    print(json.dumps(report, indent=2))
    return 0


def _review(args: argparse.Namespace) -> int:
    """Record the human approve/reject decision for one bridge task of a run."""
    reviews = record_review(Path(args.run_dir) / "review.json", args.task, args.decision, args.note or "")
    print(json.dumps(reviews, indent=2))
    return 0


def _render(args: argparse.Namespace) -> int:
    """One command: storyboard -> anchors -> bridges -> QA -> review gate -> verified join."""
    if args.status:
        print(json.dumps(render_status(args.status), indent=2))
        return 0
    if not args.storyboard:
        raise ValueError("render needs STORYBOARD (or --status RUN_DIR)")
    profiles = {k: v for k, v in (("text_to_image", args.t2i_profile), ("reference_edit", args.edit_profile),
                                  ("wan_flf2v", args.bridge_profile)) if v}
    if args.dry_run:
        report = dry_run(args.storyboard, profiles)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 6 if report["status"] == "blocked" else 0
    result = run_render(args.storyboard, lambda: ComfyClient(args.url), runs_root=args.runs_root,
                        profiles=profiles, confirm_gpu=args.confirm_gpu,
                        accept_heuristics=args.accept_heuristics,
                        allow_busy_queue=args.allow_busy_queue, sample_vram=args.sample_vram)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] == "awaiting_review":
        print("REVIEW: inspect the clips/contact sheet, then `morphcurrent review RUN_DIR TASK approved` "
              "and re-run the same render command.", file=sys.stderr)
    return {"complete": 0, "validated": 0, "blocked": 6, "awaiting_review": 7,
            "rerender_needed": 7}.get(result["status"], 5)


def _perf_report(args: argparse.Namespace) -> int:
    """Local-file performance report for a run (no ComfyUI, no GPU)."""
    print(json.dumps(build_perf_report(args.run_dir, args.models_cache), indent=2, default=str))
    return 0


def _estimate(args: argparse.Namespace) -> int:
    """Offline GPU-time estimate for a storyboard from measured history."""
    plan = compile_plan(load_storyboard(args.storyboard))
    print(json.dumps(estimate_plan(plan, load_history(args.history), extrapolate=args.extrapolate), indent=2))
    return 0


def _anchor_check(args: argparse.Namespace) -> int:
    """Heuristic framing/scale/viewpoint comparison of two anchor images (local only)."""
    print(json.dumps(compare_images(args.parent, args.child), indent=2))
    return 0


def _prompt_preview(args: argparse.Namespace) -> int:
    """Show compiled bridge prompts (and optional prompt-only A/B plan); offline."""
    sequence = load_storyboard(args.storyboard)
    plan = compile_plan(sequence)
    out = []
    for transition in sequence.transitions:
        task = plan["tasks"][f"bridge:{transition.from_anchor}->{transition.to_anchor}"]
        entry = {"bridge": task["id"], "choreography": transition.choreography is not None,
                 "positive": task["positive_prompt"], "negative": task.get("negative_prompt", "(workflow default)")}
        if args.variants:
            entry["ab_plan"] = prompt_variants(transition, task["seed"])
        out.append(entry)
    print(json.dumps({"bridges": out, "note": PROMPT_NOTE}, indent=2, ensure_ascii=False))
    return 0


def _audio_analyze(args: argparse.Namespace) -> int:
    """Local beat/tempo analysis of an audio file (offline)."""
    result = analyze_audio(args.file)
    if not args.full:
        result["beats"] = result.get("beats", [])[:64]
        result.pop("onsets", None)
    print(json.dumps(result, indent=2))
    return 0


def _audio_sync(args: argparse.Namespace) -> int:
    """Bridge-boundary timing vs beats, with cumulative drift (offline)."""
    sequence = load_storyboard(args.storyboard)
    analysis = analyze_audio(args.audio) if args.audio else None
    print(json.dumps(sync_report(sequence, analysis), indent=2))
    return 0


def _audio_visualize(args: argparse.Namespace) -> int:
    """visualizer-style bass/mid/treble timeline PNG with beats and bridge boundaries (local)."""
    levels = analyze_bands(args.file, fps=args.fps)
    analysis = analyze_audio(args.file)
    boundaries = []
    if args.storyboard:
        report = sync_report(load_storyboard(args.storyboard), analysis)
        boundaries = [b["time_s"] for b in report["boundaries"]]
    out = render_timeline_png(levels, Path(args.out), beats=analysis.get("beats"), boundaries=boundaries)
    print(json.dumps({"png": str(out), "frames": len(levels), "fps": args.fps, "bpm": analysis.get("bpm"),
                      "bass_hits_s": band_hits(levels)[:64], "boundaries_s": boundaries}, indent=2))
    return 0


def _qa_calibrate(args: argparse.Namespace) -> int:
    """Precision/recall of subject-aware QA against labelled defect windows (local clips)."""
    print(json.dumps(calibrate_qa(args.labels, args.repo_root), indent=2))
    return 0


def _dag(args: argparse.Namespace) -> int:
    """Offline storyboard -> task DAG (no ComfyUI contact)."""
    sequence = load_storyboard(args.storyboard)
    profiles = {k: v for k, v in (("text_to_image", args.t2i_profile), ("reference_edit", args.edit_profile),
                                  ("wan_flf2v", args.bridge_profile)) if v}
    with open(args.storyboard, "rb") as stream:
        raw = stream.read()
    print(json.dumps(compile_plan(sequence, profiles=profiles, storyboard_bytes=raw), indent=2,
                     ensure_ascii=False))
    return 0


def _anchor(args: argparse.Namespace) -> int:
    """Plan, validate and (with --confirm-gpu) generate one anchor image."""
    if args.resume:
        request = request_from_anchor_job(args.resume)
    else:
        missing = [flag for flag, value in (("--profile", args.profile), ("--seed", args.seed))
                   if value is None]
        prompt = args.prompt
        if args.prompt_file:
            with open(args.prompt_file, "r", encoding="utf-8") as stream:
                prompt = stream.read().strip()
        if not prompt:
            missing.append("--prompt/--prompt-file")
        if missing:
            raise ValueError(f"missing {', '.join(missing)} (or use --resume JOB_DIR)")
        method = args.method or ("reference_edit" if args.reference else "text_to_image")
        request = AnchorRequest(profile=args.profile, method=method, positive_prompt=prompt,
                                negative_prompt=args.negative, seed=args.seed, width=args.width,
                                height=args.height, reference_image=args.reference, label=args.label)
    with ComfyClient(args.url) as client:
        plan = plan_anchor(request, client.object_info())
        try:
            job = run_anchor(plan, client, args.runs_root, submit=args.confirm_gpu, retry=args.retry,
                             allow_busy_queue=args.allow_busy_queue, timeout=args.timeout)
        except KeyboardInterrupt:
            print("INTERRUPTED: ComfyUI keeps rendering. Resume with `anchor --resume <job_dir> "
                  "--confirm-gpu`.", file=sys.stderr)
            return 130
    print(json.dumps(_job_summary(job), indent=2))
    if job.state == "validated" and not args.confirm_gpu:
        print("READY: validated against live /object_info; nothing queued. "
              "Re-run with --confirm-gpu to generate the image on the GPU.", file=sys.stderr)
    return 0 if job.state in {"verified", "validated", "downloaded"} else 5


def _workflow_inspect(args: argparse.Namespace) -> int:
    """Read-only report on a fresh API export (at most GET /object_info; writes nothing)."""
    graph = load_export(args.export)
    object_info = None if args.offline else _load_object_info(args)
    report = inspect_export(graph, object_info)
    sys.stdout.write(inspect_json(report))
    return 0 if report["ok"] else 4


def _baseline(args: argparse.Namespace) -> int:
    """Read-only environment report (GET requests only; nothing queued or loaded)."""
    object_info = None
    if args.object_info:
        object_info = _load_object_info(args)
    if args.skip_comfy:
        report = build_baseline_report(repo_root=args.repo_root, client=None, object_info=object_info)
    else:
        with ComfyClient(args.url) as client:
            report = build_baseline_report(repo_root=args.repo_root, client=client,
                                           object_info=object_info)
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        with open(args.out, "x", encoding="utf-8", newline="\n") as stream:  # never overwrite
            stream.write(text)
    sys.stdout.write(text)
    if args.strict:
        wan_ok = report["capabilities"]["wan_flf2v"]["status"] == "available"
        if report["comfyui"]["status"] != "ok" or not wan_ok:
            return 3
    return 0


def _job_summary(job) -> dict:
    record = job.record
    return {
        "job_dir": str(job.dir),
        "job_id": record["job_id"],
        "state": record["state"],
        "prompt_id": record.get("prompt_id"),
        "values": {k: v for k, v in record["values"].items() if not k.endswith("_prompt")},
        "outputs": [o.get("local_path") or o["filename"] for o in record.get("outputs", [])],
        "timings": record.get("timings"),
        "verification": record.get("verification"),
        **({"method": record.get("method"), "image": record.get("image"),
            "parent": record.get("parent")} if record.get("kind") == "anchor_image" else {}),
        "error": record.get("error"),
    }


def _bridge(args: argparse.Namespace) -> int:
    if args.resume:
        request = request_from_job(args.resume)
    else:
        missing = [flag for flag, value in (("--start", args.start), ("--end", args.end),
                                            ("--seed", args.seed)) if value is None]
        if missing:
            raise ValueError(f"missing {', '.join(missing)} (or use --resume JOB_DIR)")
        prompt = args.prompt
        if args.prompt_file:
            with open(args.prompt_file, "r", encoding="utf-8") as stream:
                prompt = stream.read()
        request = BridgeRequest(profile=args.profile, start_image=args.start, end_image=args.end,
                                seed=args.seed, positive_prompt=prompt,
                                negative_prompt=args.negative, width=args.width,
                                height=args.height, length=args.length, fps=args.fps)
    with ComfyClient(args.url) as client:
        plan = plan_bridge(request, client.object_info())
        try:
            job = run_bridge(plan, client, args.runs_root, submit=args.confirm_gpu,
                             retry=args.retry, allow_busy_queue=args.allow_busy_queue,
                             timeout=args.timeout)
        except KeyboardInterrupt:
            print("INTERRUPTED: ComfyUI keeps rendering. Resume with "
                  f"`bridge --resume <job_dir> --confirm-gpu` or stop it with `bridge-cancel <job_dir>`.",
                  file=sys.stderr)
            return 130
    print(json.dumps(_job_summary(job), indent=2))
    if job.state == "validated" and not args.confirm_gpu:
        print("READY: validated against live /object_info; nothing queued. "
              "Re-run with --confirm-gpu to render on the GPU.", file=sys.stderr)
    return 0 if job.state in {"verified", "validated", "downloaded"} else 5


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MorphCurrent local video orchestrator")
    subs = parser.add_subparsers(dest="command", required=True)
    for cmd in ("validate", "plan"):
        subs.add_parser(cmd).add_argument("storyboard")
    health = subs.add_parser("health")
    health.add_argument("--url", default="http://127.0.0.1:8188")
    doctor = subs.add_parser("doctor", help="Inspect native Windows 11 tools, GPU and optional local ComfyUI")
    doctor.add_argument("--url", default="http://127.0.0.1:8188")
    doctor.add_argument("--skip-comfy", action="store_true", help="Avoid contacting ComfyUI")
    doctor.add_argument("--strict", action="store_true", help="Nonzero if host/tools/GPU/ComfyUI not ready")
    for name, help_text in (("workflow-check", "Validate a binding profile + API graph against /object_info"),
                            ("workflow-patch", "Write a patched API graph (validated, never submitted)")):
        sub = subs.add_parser(name, help=help_text)
        sub.add_argument("--profile", default="configs/profiles/wan22_flf2v.binding.json")
        sub.add_argument("--url", default="http://127.0.0.1:8188")
        sub.add_argument("--object-info", help="Saved /object_info JSON instead of contacting ComfyUI")
        if name == "workflow-patch":
            sub.add_argument("--set", action="append", metavar="ROLE=VALUE",
                             help="Semantic role from the profile, e.g. seed=42 length=65")
            sub.add_argument("--out", help="Output file; refused if it already exists")
    bridge = subs.add_parser("bridge", help="Plan, upload, validate and (with --confirm-gpu) render one FLF2V bridge")
    bridge.add_argument("--profile", default="configs/profiles/wan22_flf2v.binding.json")
    bridge.add_argument("--url", default="http://127.0.0.1:8188")
    bridge.add_argument("--start", help="First-frame anchor image")
    bridge.add_argument("--end", help="Last-frame anchor image")
    bridge.add_argument("--seed", type=int)
    group = bridge.add_mutually_exclusive_group()
    group.add_argument("--prompt", help="Positive prompt (default: the exported graph's)")
    group.add_argument("--prompt-file", help="UTF-8 file holding the positive prompt")
    bridge.add_argument("--negative", help="Negative prompt (default: the exported graph's)")
    bridge.add_argument("--width", type=int)
    bridge.add_argument("--height", type=int)
    bridge.add_argument("--length", type=int, help="Frame count, 4n+1")
    bridge.add_argument("--fps", type=float)
    bridge.add_argument("--runs-root", default="outputs/runs")
    bridge.add_argument("--resume", metavar="JOB_DIR", help="Continue a job from its job.json request")
    bridge.add_argument("--confirm-gpu", action="store_true",
                        help="Actually queue the render on the local GPU (otherwise stop after validation)")
    bridge.add_argument("--retry", action="store_true", help="Retry a failed or cancelled job")
    bridge.add_argument("--allow-busy-queue", action="store_true",
                        help="Submit even when ComfyUI already has queued work")
    bridge.add_argument("--timeout", type=float, default=3600, help="Seconds to wait for the render")
    mh = subs.add_parser("models-hash", help="Opt-in SHA-256 of profile-referenced model files (idle queue only)")
    mh.add_argument("--profile", action="append", help="Binding profile(s); default all in configs/profiles")
    mh.add_argument("--models-root", default=str(DEFAULT_MODELS_ROOT))
    mh.add_argument("--cache", default="outputs/model_hashes.json")
    mh.add_argument("--url", default="http://127.0.0.1:8188")
    mh.add_argument("--confirm-io", action="store_true", help="Acknowledge multi-GB disk reads")
    render = subs.add_parser("render", help="One command: dry-run / approved render / resume / status")
    render.add_argument("storyboard", nargs="?")
    render.add_argument("--dry-run", action="store_true", help="Plan only: no network, no writes")
    render.add_argument("--status", metavar="RUN_DIR", help="Read-only run summary")
    render.add_argument("--confirm-gpu", action="store_true", help="Allow this run's GPU jobs")
    render.add_argument("--accept-heuristics", action="store_true",
                        help="Join without human review when QA heuristics raise no flags")
    render.add_argument("--allow-busy-queue", action="store_true")
    render.add_argument("--sample-vram", action="store_true", help="Opt-in nvidia-smi memory sampling")
    render.add_argument("--t2i-profile")
    render.add_argument("--edit-profile")
    render.add_argument("--bridge-profile")
    render.add_argument("--runs-root", default="outputs/runs")
    render.add_argument("--url", default="http://127.0.0.1:8188")
    qa = subs.add_parser("qa", help="Heuristic temporal QA of a clip (cut/freeze/flare/endpoints)")
    qa.add_argument("clip")
    qa.add_argument("--start", help="Start anchor image for endpoint comparison")
    qa.add_argument("--end", help="End anchor image for endpoint comparison")
    review = subs.add_parser("review", help="Record a human approve/reject decision for a bridge")
    review.add_argument("run_dir")
    review.add_argument("task", help="e.g. bridge:orchid->butterfly")
    review.add_argument("decision", choices=["approved", "rejected", "pending"])
    review.add_argument("--note")
    perf = subs.add_parser("perf-report", help="Measured stage times and whole-GPU VRAM for a run (local files only)")
    perf.add_argument("run_dir")
    perf.add_argument("--models-cache", default="outputs/model_hashes.json")
    est = subs.add_parser("estimate", help="Estimated GPU time for a storyboard from measured history (offline)")
    est.add_argument("storyboard")
    est.add_argument("--history", default="configs/perf_history.json")
    est.add_argument("--extrapolate", action="store_true",
                     help="Scale from the nearest measured size when no exact match exists (labelled)")
    ac = subs.add_parser("anchor-check", help="Compare framing/scale/viewpoint of a parent and child anchor")
    ac.add_argument("parent")
    ac.add_argument("child")
    pp = subs.add_parser("prompt-preview", help="Show compiled bridge prompts for a storyboard (offline)")
    pp.add_argument("storyboard")
    pp.add_argument("--variants", action="store_true", help="Also list a fixed-seed prompt-only A/B plan")
    aa = subs.add_parser("audio-analyze", help="Local tempo/beat/downbeat analysis of an audio file")
    aa.add_argument("file")
    aa.add_argument("--full", action="store_true", help="Print all beats and onsets")
    asy = subs.add_parser("audio-sync", help="Bridge boundary timing vs beats and drift (offline)")
    asy.add_argument("storyboard")
    asy.add_argument("--audio", help="Analyse this local file instead of using the storyboard BPM grid")
    av = subs.add_parser("audio-visualize", help="visualizer-style band timeline PNG with beats and boundaries")
    av.add_argument("file")
    av.add_argument("--out", required=True, help="PNG path (refused if it exists)")
    av.add_argument("--storyboard", help="Overlay this storyboard's bridge boundaries")
    av.add_argument("--fps", type=float, default=30.0)
    qc = subs.add_parser("qa-calibrate", help="Score QA detectors against labelled defect windows")
    qc.add_argument("labels", nargs="?", default="configs/qa_labels.json")
    qc.add_argument("--repo-root", default=".")
    dag = subs.add_parser("dag", help="Compile a storyboard into the anchor/bridge/final task DAG (offline)")
    dag.add_argument("storyboard")
    dag.add_argument("--t2i-profile")
    dag.add_argument("--edit-profile")
    dag.add_argument("--bridge-profile")
    anchor = subs.add_parser("anchor", help="Plan, validate and (with --confirm-gpu) generate one anchor image")
    anchor.add_argument("--profile", help="text_to_image or reference_edit binding profile")
    anchor.add_argument("--url", default="http://127.0.0.1:8188")
    anchor_prompt = anchor.add_mutually_exclusive_group()
    anchor_prompt.add_argument("--prompt")
    anchor_prompt.add_argument("--prompt-file")
    anchor.add_argument("--negative")
    anchor.add_argument("--seed", type=int)
    anchor.add_argument("--width", type=int)
    anchor.add_argument("--height", type=int)
    anchor.add_argument("--reference", help="Parent anchor image for reference_edit")
    anchor.add_argument("--method", choices=["text_to_image", "reference_edit", "independent_t2i"])
    anchor.add_argument("--label")
    anchor.add_argument("--runs-root", default="outputs/runs")
    anchor.add_argument("--resume", metavar="JOB_DIR")
    anchor.add_argument("--confirm-gpu", action="store_true",
                        help="Actually queue the image generation on the local GPU")
    anchor.add_argument("--retry", action="store_true")
    anchor.add_argument("--allow-busy-queue", action="store_true")
    anchor.add_argument("--timeout", type=float, default=1800)
    anchor_status = subs.add_parser("anchor-status", help="Show an anchor job record")
    anchor_status.add_argument("job_dir")
    inspect = subs.add_parser("workflow-inspect",
                              help="Read-only report on a new API export: nodes, models, cloud nodes, role candidates")
    inspect.add_argument("export", help="ComfyUI Save (API Format) JSON")
    inspect.add_argument("--url", default="http://127.0.0.1:8188")
    inspect.add_argument("--object-info", help="Saved /object_info JSON instead of contacting ComfyUI")
    inspect.add_argument("--offline", action="store_true", help="Structural report only, no schema checks")
    baseline = subs.add_parser("baseline", help="Read-only environment/queue/model report (never queues work)")
    baseline.add_argument("--url", default="http://127.0.0.1:8188")
    baseline.add_argument("--skip-comfy", action="store_true", help="Do not contact ComfyUI")
    baseline.add_argument("--object-info", help="Saved /object_info JSON instead of GET /object_info")
    baseline.add_argument("--repo-root", default=".", help=argparse.SUPPRESS)
    baseline.add_argument("--out", help="Also write the report here; refused if it exists")
    baseline.add_argument("--strict", action="store_true",
                          help="Exit 3 unless ComfyUI is reachable and the Wan profile validates")
    status = subs.add_parser("bridge-status", help="Show a bridge job record")
    status.add_argument("job_dir")
    cancel = subs.add_parser("bridge-cancel", help="Dequeue or interrupt only this job's prompt")
    cancel.add_argument("job_dir")
    cancel.add_argument("--url", default="http://127.0.0.1:8188")
    args = parser.parse_args(argv)
    try:
        if args.command in {"validate", "plan"}:
            sequence = load_storyboard(args.storyboard)
            if args.command == "validate":
                print(f"VALID: {sequence.name} ({len(sequence.anchors)} anchors)")
            else:
                print(json.dumps(timeline_as_dict(sequence), indent=2))
        elif args.command == "doctor":
            report = windows_diagnostics(args.url, check_comfy=not args.skip_comfy)
            print(json.dumps(report, indent=2))
            if args.strict:
                needed = ("ready_for_offline_development" if args.skip_comfy
                          else "ready_for_local_gpu_workflows")
                return 0 if report[needed] else 3
        elif args.command == "workflow-check":
            return _workflow_check(args)
        elif args.command == "workflow-patch":
            return _workflow_patch(args)
        elif args.command == "bridge":
            return _bridge(args)
        elif args.command == "baseline":
            return _baseline(args)
        elif args.command == "workflow-inspect":
            return _workflow_inspect(args)
        elif args.command == "models-hash":
            return _models_hash(args)
        elif args.command == "render":
            return _render(args)
        elif args.command == "qa":
            return _qa(args)
        elif args.command == "review":
            return _review(args)
        elif args.command == "perf-report":
            return _perf_report(args)
        elif args.command == "estimate":
            return _estimate(args)
        elif args.command == "anchor-check":
            return _anchor_check(args)
        elif args.command == "prompt-preview":
            return _prompt_preview(args)
        elif args.command == "audio-analyze":
            return _audio_analyze(args)
        elif args.command == "audio-sync":
            return _audio_sync(args)
        elif args.command == "audio-visualize":
            return _audio_visualize(args)
        elif args.command == "qa-calibrate":
            return _qa_calibrate(args)
        elif args.command == "dag":
            return _dag(args)
        elif args.command == "anchor":
            return _anchor(args)
        elif args.command == "anchor-status":
            print(json.dumps(_job_summary(load_job(args.job_dir)), indent=2))
        elif args.command == "bridge-status":
            print(json.dumps(_job_summary(load_job(args.job_dir)), indent=2))
        elif args.command == "bridge-cancel":
            with ComfyClient(args.url) as client:
                print(json.dumps(_job_summary(cancel_bridge(args.job_dir, client)), indent=2))
        elif args.command == "health":
            with ComfyClient(args.url) as client:
                print(json.dumps(client.health(), indent=2))
        return 0
    except (ValidationError, ValueError, OSError, AudioError, ComfyError, WorkflowBindingError, BridgeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
