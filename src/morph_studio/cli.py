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
from .scheduler import LockBusy, schedule_preview
from .brief import Brief, BriefError, plan_storyboard
from .schema import Storyboard
from .styles import StyleError, check_assets, list_packs, resolve_pack, style_text
from .ladder import (LadderError, propose_ladder, risk_report, sha256_text as ladder_sha256,
                     write_proposal)
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
                        allow_busy_queue=args.allow_busy_queue, sample_vram=args.sample_vram,
                        max_jobs=args.max_jobs, max_gpu_s=args.max_gpu_s, min_free_gb=args.min_free_gb)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] == "awaiting_review":
        print("REVIEW: inspect the clips/contact sheet, then `morphcurrent review RUN_DIR TASK approved` "
              "and re-run the same render command.", file=sys.stderr)
    if result["status"] == "paused_budget":
        print("PAUSED: budget reached before the next GPU job; re-run the same command (optionally with a "
              "new --max-jobs/--max-gpu-s) to continue without repeating finished stages.", file=sys.stderr)
    return RENDER_EXIT.get(result["status"], 5)


RENDER_EXIT = {"complete": 0, "validated": 0, "blocked": 6, "awaiting_review": 7,
               "rerender_needed": 7, "paused_budget": 8, "blocked_disk": 9}


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
    section_times = [s["t"] for s in analysis.get("sections", [])]
    out = render_timeline_png(levels, Path(args.out), beats=analysis.get("beats"), boundaries=boundaries,
                              sections=section_times)
    print(json.dumps({"png": str(out), "frames": len(levels), "fps": args.fps, "bpm": analysis.get("bpm"),
                      "confidence": analysis.get("confidence"), "sections_s": section_times,
                      "bass_hits_s": band_hits(levels)[:64], "boundaries_s": boundaries}, indent=2))
    return 0


def _qa_calibrate(args: argparse.Namespace) -> int:
    """Precision/recall of subject-aware QA against labelled defect windows (local clips)."""
    print(json.dumps(calibrate_qa(args.labels, args.repo_root), indent=2))
    return 0


def _ladder_risk(args: argparse.Namespace) -> int:
    """Interpretable per-transition morph risk (prompt distance; optional anchor geometry)."""
    sequence = load_storyboard(args.storyboard)
    geometry = {}
    if args.run:
        manifest = json.loads((Path(args.run) / "manifest.json").read_text(encoding="utf-8"))
        images = {}
        for task, stage in manifest["stages"].items():
            if task.startswith("anchor:") and stage.get("job_dir"):
                job = json.loads((Path(stage["job_dir"]) / "job.json").read_text(encoding="utf-8"))
                if job.get("image"):
                    images[task[7:]] = Path(stage["job_dir"]) / job["image"]["local_path"]
        for t in sequence.transitions:
            if t.from_anchor in images and t.to_anchor in images:
                geometry[f"{t.from_anchor}->{t.to_anchor}"] = compare_images(
                    images[t.from_anchor], images[t.to_anchor])["comparison"]
    print(json.dumps(risk_report(sequence, geometry), indent=2))
    return 0


def _ladder_propose(args: argparse.Namespace) -> int:
    """Write a proposal storyboard splitting one transition with intermediate anchors."""
    import yaml as _yaml
    src = Path(args.storyboard)
    data = _yaml.safe_load(src.read_text(encoding="utf-8"))
    from_id, _, to_id = args.split.partition("->")
    history = load_history(args.history) if Path(args.history).is_file() else None
    sb, report = propose_ladder(data, from_id, to_id, steps=args.steps, history=history,
                                max_new=args.max_new, max_gpu_s=args.max_gpu_s,
                                source_sha256=ladder_sha256(src))
    write_proposal(sb, report, Path(args.out))
    print(json.dumps({"out": args.out, **report}, indent=2))
    return 0


def _style(args: argparse.Namespace) -> int:
    """List, show (resolved + hash) or check style packs; read-only."""
    if args.command == "style-list":
        print(json.dumps(list_packs(args.styles_dir), indent=2))
        return 0
    resolved = resolve_pack(args.pack, args.styles_dir)
    if args.command == "style-show":
        print(json.dumps({**resolved, "prompt_clause": style_text(resolved)}, indent=2, ensure_ascii=False))
        return 0
    report = check_assets(resolved, args.library)
    print(json.dumps({"pack": args.pack, "assets": report}, indent=2))
    return 0 if all(a["status"] == "ok" for a in report) else 4


def _brief_plan(args: argparse.Namespace) -> int:
    """Brief -> editable storyboard YAML + preview (offline; nothing rendered)."""
    import yaml as _yaml
    out = Path(args.out)
    if out.exists():
        raise FileExistsError(f"{out} exists; choose another --out")
    brief = Brief.model_validate(_yaml.safe_load(Path(args.brief).read_text(encoding="utf-8")))
    data, preview = plan_storyboard(brief)
    sequence = Storyboard.model_validate(data)
    plan = compile_plan(sequence)
    history = load_history(args.history) if Path(args.history).is_file() else []
    est = estimate_plan(plan, history) if history else {"label": "NO DATA"}
    out.parent.mkdir(parents=True, exist_ok=True)
    header = (f"# Generated by `morphcurrent brief-plan` from {Path(args.brief).as_posix()} - edit freely, then\n"
              f"# `render {out.as_posix()} --dry-run` before any GPU work.\n")
    if brief.drafted_by:  # F22 US3 provenance (header only; never part of the plan hash)
        header += f"# Drafted by: {' '.join(brief.drafted_by.split())}\n"
    out.write_text(header + _yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100),
                   encoding="utf-8", newline="\n")
    print(json.dumps({"out": str(out), **preview, "bridges": len(sequence.transitions),
                      "estimated_gpu_s": est.get("total_gpu_s"), "estimate_label": est.get("label"),
                      "blocked": plan["blocked"]}, indent=2))
    return 0


def _accuracy(args: argparse.Namespace) -> int:
    """F33 technical-accuracy review: checklist, owner verdicts, text-free check, rejection impact, status."""
    from . import accuracy as ac
    from .schema import load_storyboard
    root = Path(args.repo_root)
    name = load_storyboard(args.storyboard).name
    log = Path(args.log) if getattr(args, "log", None) else ac.default_log(name, root)
    try:
        if args.command == "accuracy-checklist":
            out = {"storyboard": name, "anchors": ac.checklist(args.storyboard, args.bank, repo_root=root)}
        elif args.command == "accuracy-negatives":
            out = ac.text_free_check(ac.load_plan(args.storyboard, root))
            print(json.dumps(out, indent=2, ensure_ascii=True))
            return 0 if out["ok"] else 1
        elif args.command == "accuracy-impact":
            out = ac.impact_for(args.storyboard, args.reject, log=log, repo_root=root)
        elif args.command == "accuracy-review":
            sha = args.sha256
            if args.run:
                sha = ac._run_hashes(args.run).get(args.anchor)
                if not sha:
                    raise ac.AccuracyError(f"run {args.run} has no recorded image for {args.anchor}")
            out = ac.record_verdict(log, ac.load_plan(args.storyboard, root), args.anchor, verdict=args.verdict,
                                    image_sha256=sha, image=args.image, failed=args.fail, note=args.note,
                                    reviewer=args.reviewer)
            out["log"] = str(log)
        else:
            out = ac.status(args.storyboard, log, run_dir=args.run, repo_root=root)
            print(json.dumps(out, indent=2, ensure_ascii=True))
            return 0 if out["gate"] else 1
    except ac.AccuracyError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2, ensure_ascii=True))
    return 0


def _film(args: argparse.Namespace) -> int:
    """F32 full-song film storyboard and dry-run report (offline; no GPU)."""
    from . import film as fm
    try:
        if args.command == "film-storyboard":
            data = fm.write_storyboard(args.plan, args.bank, args.acts, args.out, audio=args.audio)
            out = {"out": args.out, "anchors": len(data["anchors"]), "bridges": len(data["transitions"]),
                   "acts": list(dict.fromkeys(a["chapter"] for a in data["anchors"])),
                   "text_to_image": sum(a["generation"] == "text_to_image" for a in data["anchors"])}
        else:
            out = fm.film_report(args.storyboard, sync_plan=args.plan, history=args.history, repo_root=args.repo_root)
    except (fm.FilmError, FileExistsError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2, ensure_ascii=True))
    return 0


def _concepts(args: argparse.Namespace) -> int:
    """F31 engineering concept bank: validate and list for owner review (offline)."""
    from . import concepts as cc
    if args.command == "concepts-check":
        rep = cc.check(args.bank, target=args.target, plan=args.plan)
        print(json.dumps(rep, indent=2, ensure_ascii=True))
        return 0 if rep["ok"] else 1
    bank = cc.load_bank(args.bank)
    if args.json:
        print(json.dumps({"coverage": cc.coverage(bank), "entries": bank["entries"]}, indent=2, ensure_ascii=True))
    else:
        print(chr(10).join(cc.listing(bank)).encode("ascii", "replace").decode("ascii"))
    return 0


def _deliver(args: argparse.Namespace) -> int:
    """F30 multi-format delivery and release check (local FFmpeg; never tags)."""
    from . import delivery as dv
    from . import release as rel
    if args.command == "release-check":
        out = rel.release_check(args.ledger, args.repo_root, through=args.through)
        print(json.dumps(out, indent=2, ensure_ascii=True))
        return 0 if out["ready_for_owner_review"] else 1
    if args.list_presets:
        print(json.dumps({"presets": [{"name": n, "recipe_sha256": dv.recipe_sha256(n), **dv.recipe(n)}
                                      for n in dv.PRESETS]}, indent=2, ensure_ascii=True))
        return 0
    if not args.input or not args.out_dir or not args.preset:
        raise ValueError("deliver needs INPUT, --out-dir and at least one --preset (or --list-presets)")
    out = dv.deliver(args.input, args.out_dir, args.preset, audio=args.audio, audio_licensed=args.audio_licensed,
                     audio_offset=args.audio_offset)
    summary = {"results": [{"preset": r["preset"], "out": r["output"]["path"], "passed": r["verification"]["passed"],
                            "mismatches": r["verification"]["mismatches"], "crop": r["crop"],
                            "encoder": r["encoder"], "recipe_sha256": r["recipe_sha256"], "seconds": r["seconds"]}
                           for r in out["results"]], "errors": out["errors"]}
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    if out["errors"]:
        return 2
    return 0 if all(r["passed"] for r in summary["results"]) else 5


def _experiment(args: argparse.Namespace) -> int:
    """F29 bounded local A/B experiments on one bridge (GPU only with --confirm-gpu)."""
    from . import experiment as ex
    root = Path(args.repo_root)
    out_root = root / "outputs" / "experiments"
    try:
        defn = ex.load_definition(args.definition, repo_root=root)
        history = ex.load_history_file(getattr(args, "history", None) or root / "configs" / "perf_history.json")
        if args.command == "experiment-plan":
            out = ex.plan_summary(defn, ex.design(defn, history, repo_root=root), out_root)
        elif args.command == "experiment-run":
            executor = ex.bridge_executor(url=args.url, runs_root=args.runs_root, repo_root=root)
            out = ex.run(defn, executor, confirm_gpu=args.confirm_gpu, history=history, out_root=out_root,
                         repo_root=root)
        elif args.command == "experiment-rate":
            out = ex.rate(defn, args.candidate, args.score, args.note, out_root=out_root, repo_root=root)
        else:
            rep = ex.report(defn, out_root=out_root, repo_root=root)
            out = {k: rep[k] for k in ("experiment", "totals", "pareto", "pareto_dimensions", "mismatches")}
            out["report"] = str(ex.out_dir_for(defn, out_root) / "report.md")
    except ex.ExperimentError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2, ensure_ascii=True))
    return 0


def _project(args: argparse.Namespace) -> int:
    """F28 portable project packages: export, inspect, import (no inference, no downloads)."""
    from . import package as pk
    try:
        if args.command == "project-export":
            out = pk.export_project(args.storyboard, args.out, repo_root=args.repo_root, run_dir=args.run,
                                    include_media=args.include_media, include_audio=args.include_audio)
        elif args.command == "project-inspect":
            out = pk.inspect_package(args.package)
            print(json.dumps(out, indent=2, ensure_ascii=True))
            return 0 if out["ok"] else 2
        else:
            out = pk.import_project(args.package, args.dest, models_root=args.models_root)
    except (pk.PackageError, FileExistsError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2, ensure_ascii=True))
    return 0


def _registry(args: argparse.Namespace) -> int:
    """F27 capability registry, compatibility preview, approved selection and rollback (no downloads)."""
    from . import registry as rg
    root = Path(args.repo_root) if getattr(args, "repo_root", None) else None
    info = None
    if getattr(args, "object_info", None) or getattr(args, "live", False):
        info = _load_object_info(args)
    try:
        if args.command == "registry":
            entries = rg.build_registry(args.profiles, object_info=info, models_root=args.models_root, repo_root=root)
            print(json.dumps({"offline": info is None, "entries": entries}, indent=2, ensure_ascii=True))
            return 1 if args.strict and any(e["status"] != "ready" for e in entries) else 0
        if args.command == "registry-diff":
            cur, cand = (rg.build_entry(p, object_info=info, repo_root=root) for p in (args.current, args.candidate))
            for e in (cur, cand):
                if e["actual_sha256"] is None:  # profile unreadable or workflow missing: nothing to compare
                    print(f"ERROR: {e['path']}: {e['problems'][0]['message']}", file=sys.stderr)
                    return 2
            print(json.dumps(rg.compare(cur, cand), indent=2, ensure_ascii=True))
            return 0
        if args.command == "registry-select":
            out = rg.select(args.profile, approve=args.approve, note=args.note, object_info=info,
                            models_root=args.models_root, selection_path=args.selection, repo_root=root)
        else:
            out = rg.rollback(args.capability, args.selection)
    except rg.RegistryRefusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2, ensure_ascii=True))
    return 0


def _finish(args: argparse.Namespace) -> int:
    """F26 geometric HD finishing (CPU) and read-only listing of learned upscalers."""
    from . import finishing as fn
    if args.list_models:
        print(json.dumps({"models": fn.upscale_models(args.comfy_root),
                          "note": "learned upscalers need an owner-approved, hash-pinned workflow (F26 T016)"}, indent=2))
        return 0
    if not args.input or not args.out:
        raise ValueError("finish needs INPUT and --out (or --list-models)")
    try:
        rec = fn.finish(args.input, args.out, target=args.target, mode=args.mode, denoise=args.denoise,
                        deblock=args.deblock, sharpen=args.sharpen, match_anchor=args.match_anchor, crf=args.crf)
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"out": args.out, "size": f"{rec['output']['width']}x{rec['output']['height']}",
                      "frames_preserved": rec["frames_preserved"], "identity": rec["identity"],
                      "colour_gains": rec["colour_gains"], "seconds": rec["seconds"]}, indent=2))
    return 0 if rec["identity"]["passed"] and rec["frames_preserved"] else 5


def _interp(args: argparse.Namespace) -> int:
    """F25 delivery frame rates and energy-warped retiming (local FFmpeg)."""
    from . import interpolate as ip
    try:
        if args.command == "interpolate":
            rec = ip.convert(args.input, args.out, fps=args.fps, method=args.method, crf=args.crf)
            exact = sum(a["exact"] for a in rec["anchor_alignment"])
            print(json.dumps({"out": args.out, "ok": rec["ok"], "method_used": rec["method_used"],
                              "fallback": rec["fallback"], "duration_in": rec["input"]["duration"],
                              "duration_out": rec["output"]["duration"],
                              "anchors_exact": f"{exact}/{len(rec['anchor_alignment'])}"}, indent=2))
            return 0 if rec["ok"] else 5
        if args.plan:
            plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
            mapping = plan["bridges"][args.bridge]["warp"]["map"]
        else:
            mapping = json.loads(Path(args.map).read_text(encoding="utf-8"))
        rec = ip.apply_warp(args.clip, mapping, args.out, crf=args.crf)
        print(json.dumps({"out": args.out, "frames_in": rec["frames_in"], "frames_out": rec["frames_out"],
                          "endpoints_ok": rec["endpoints_ok"], "speed": rec["speed"]}, indent=2))
        return 0 if rec["endpoints_ok"] else 5
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _sync(args: argparse.Namespace) -> int:
    """F15 US5: audio feature track and event-locked sync plan (offline)."""
    from . import sync_features as sf
    out = Path(args.out)
    if out.exists():
        print(f"error: {out} exists; refusing to overwrite", file=sys.stderr)
        return 2
    if args.command == "audio-features":
        record = sf.track_record(args.file, fps=args.fps)
        out.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({"out": str(out), "frames": len(record["frames"]), "sections": len(record["sections"]),
                          "audio_sha256": record["audio_sha256"], "content_sha256": record["content_sha256"]}, indent=2))
        return 0
    record = json.loads(Path(args.features).read_text(encoding="utf-8"))
    beatmap = json.loads(Path(args.beatmap).read_text(encoding="utf-8")) if args.beatmap else None
    plan = sf.sync_plan(record, beatmap, preferred=args.preferred)
    out.write_text(json.dumps(plan, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    lengths = [b["frames"] for b in plan["bridges"]]
    chars: dict[str, int] = {}
    for b in plan["bridges"]:
        for word in b["character"]:
            chars[word] = chars.get(word, 0) + 1
    print(json.dumps({"out": str(out), **plan["summary"], "coverage": plan["coverage"],
                      "bridge_frames": {"min": min(lengths), "max": max(lengths), "mean": round(sum(lengths) / len(lengths), 1)},
                      "character": chars, "plan_sha256": plan["plan_sha256"]}, indent=2))
    return 0


def _continuity(args: argparse.Namespace) -> int:
    """F24 continuity diagnostics, evaluation, repair proposals and controlled comparison (offline)."""
    from . import continuity as ct
    if args.command == "continuity":
        report = ct.analyze_clip(args.clip, with_metrics=args.metrics)
        print(json.dumps(report, indent=2))
        return 13 if report["flags"] else 0
    if args.command == "continuity-eval":
        print(json.dumps(ct.evaluate(args.labels, args.repo_root), indent=2))
        return 0
    if args.command == "repair-propose":
        from .release import _stage_files
        out = Path(args.out)
        if out.exists():
            print(f"error: {out} exists; refusing to overwrite", file=sys.stderr)
            return 2
        stage = _stage_files(Path(args.run)).get(args.task)
        if not stage or not stage.get("file") or not Path(stage["file"]).is_file():
            print(f"error: no verified clip for {args.task} in {args.run}", file=sys.stderr)
            return 2
        plan = json.loads((Path(args.run) / "plan.json").read_text(encoding="utf-8"))
        proposal = ct.propose_repair(ct.analyze_clip(stage["file"]), plan["tasks"][args.task])
        out.write_text(json.dumps(proposal, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(proposal, indent=2))
        return 0
    from .qa_subject import decode_rgb_frames
    result = ct.compare_repair(decode_rgb_frames(args.original), decode_rgb_frames(args.repaired))
    print(json.dumps(result, indent=2))
    return 0 if result["verdict"] == ct.COMPARE_VERDICT_OK else 14


def _camera_check(args: argparse.Namespace) -> int:
    """F23: camera-move labels, endpoint satisfiability, framing and crops (offline)."""
    from .camera import camera_check
    report = camera_check(args.storyboard, run_dir=args.run, repo_root=args.repo_root)
    print(json.dumps(report, indent=2))  # ASCII-safe for Windows consoles and redirects
    return 12 if report["verdict"] == "issues" else 0


def _release(args: argparse.Namespace) -> int:
    """F20 production-acceptance commands (offline except `replay --confirm-gpu`)."""
    from . import release as rel
    try:
        if args.command == "run-compare":
            report = rel.compare_runs(args.run_a, args.run_b, frames=args.frames)
            print(json.dumps(report, indent=2))
            return 0 if report["verdict"] == "reproduced" else 10
        if args.command == "replay":
            out = rel.replay(args.storyboard, args.reference, args.runs_root, lambda: ComfyClient(args.url),
                             confirm_gpu=args.confirm_gpu, frames=args.frames)
            print(json.dumps(out, indent=2, ensure_ascii=False))
            if "comparison" in out:
                return 0 if out["comparison"]["verdict"] == "reproduced" else 10
            return RENDER_EXIT.get(out["render"]["status"], 5)  # did not finish: same codes as `render`
        if args.command == "audit":
            report = rel.audit_repo(args.repo_root)
            print(json.dumps(report, indent=2))
            return 11 if report["errors"] else 0
        if args.command == "run-backup":
            print(json.dumps(rel.backup_run(args.run, args.out, args.allow_missing_jobs), indent=2))
            return 0
        if args.command == "run-restore":
            print(json.dumps({"restored": str(rel.restore_run(args.archive, args.runs_root))}, indent=2))
            return 0
        if args.command == "acceptance":
            print(json.dumps(rel.acceptance_matrix(args.ledger, all_features=args.all, through=args.through),
                             indent=2))
            return 0
    except rel.ReleaseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    raise ValueError(f"unknown release command {args.command}")


def _draft_check(args: argparse.Namespace) -> int:
    """F22 US3: validate a brief or storyboard pre-drafted in a Claude Desktop session (offline)."""
    import yaml as _yaml
    from .brief import lint_draft
    report = lint_draft(_yaml.safe_load(Path(args.draft).read_text(encoding="utf-8")), repo_root=args.repo_root)
    print(json.dumps({"draft": args.draft, **report}, indent=2, ensure_ascii=False))
    return 3 if report["errors"] else 0


def _plan_diff(args: argparse.Namespace) -> int:
    """Which stages an edit re-runs (offline)."""
    from .longform import plan_diff
    old, new = (compile_plan(load_storyboard(s), repo_root=args.repo_root) for s in (args.old, args.new))
    report = plan_diff(old, new)
    print(json.dumps(report if args.all else {**report, "stages": [r for r in report["stages"]
                                                                    if r["status"] != "cached"]}, indent=2))
    return 0


def _timeline(args: argparse.Namespace) -> int:
    """Anchor/chapter timestamps of the final movie; optional FFmpeg chapters and proxy storyboard."""
    import yaml as _yaml
    from .longform import chapter_index, ffmetadata, plan_bytes, proxy_storyboard
    storyboard = load_storyboard(args.storyboard)
    plan = compile_plan(storyboard, repo_root=args.repo_root)
    index = chapter_index(storyboard, plan)
    if args.ffmetadata:
        Path(args.ffmetadata).write_text(ffmetadata(index), encoding="utf-8", newline="\n")
        index["ffmetadata"] = args.ffmetadata
    if args.write_proxy:
        out = Path(args.write_proxy)
        if out.exists():
            raise ValueError(f"{out} exists; refusing to overwrite")
        data = _yaml.safe_load(Path(args.storyboard).read_text(encoding="utf-8"))
        out.write_text(_yaml.safe_dump(proxy_storyboard(data), sort_keys=False, allow_unicode=True),
                       encoding="utf-8", newline="\n")
        index["proxy_storyboard"] = str(out)
    index["estimated_new_bytes"] = plan_bytes(plan)["total_bytes"]
    print(json.dumps(index, indent=2, ensure_ascii=False))
    return 0


def _storage(args: argparse.Namespace) -> int:
    from .longform import storage_report
    print(json.dumps(storage_report(args.runs_root), indent=2))
    return 0


def _review_ui(args: argparse.Namespace) -> int:
    """Strictly-loopback local review page (F18). Never renders or contacts ComfyUI."""
    from .review_ui import UiError, default_storyboards, make_server
    boards = default_storyboards(args.repo_root) + [s for s in args.storyboard or []]
    try:
        server = make_server(args.runs_root, host=args.host, port=args.port, storyboards=boards,
                             repo_root=args.repo_root)
    except UiError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    host = f"[{args.host}]" if ":" in args.host else args.host
    print(f"Review UI: http://{host}:{server.server_address[1]}/ (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def _schedule(args: argparse.Namespace) -> int:
    """Dependency-ordered stage list with estimates and what fits a budget (offline)."""
    plan = compile_plan(load_storyboard(args.storyboard))
    history = load_history(args.history) if Path(args.history).is_file() else []
    print(json.dumps(schedule_preview(plan, history, max_gpu_s=args.max_gpu_s, max_jobs=args.max_jobs), indent=2))
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
    render.add_argument("--max-jobs", type=int, help="Stop before more than N new GPU jobs (resumable)")
    render.add_argument("--min-free-gb", type=float, default=2.0,
                        help="Refuse GPU work if estimated outputs would leave less free disk (default 2)")
    render.add_argument("--max-gpu-s", type=float, help="Stop before estimated new GPU time exceeds S seconds")
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
    lr = subs.add_parser("ladder-risk", help="Per-transition morph risk (prompt distance, optional geometry)")
    lr.add_argument("storyboard")
    lr.add_argument("--run", help="Run dir whose generated anchors add F12 geometry evidence")
    lp = subs.add_parser("ladder-propose", help="Write a proposal storyboard with intermediate anchors")
    lp.add_argument("storyboard")
    lp.add_argument("--split", required=True, help="FROM->TO transition to split")
    lp.add_argument("--steps", type=int, default=1, help="Intermediate anchors to insert")
    lp.add_argument("--max-new", type=int, default=3)
    lp.add_argument("--max-gpu-s", type=float, help="Refuse if the ladder adds more GPU seconds")
    lp.add_argument("--history", default="configs/perf_history.json")
    lp.add_argument("--out", required=True, help="New storyboard path (refused if it exists)")
    sl = subs.add_parser("style-list", help="List style packs in configs/styles")
    sl.add_argument("--styles-dir", default="configs/styles")
    for name, help_text in (("style-show", "Show a resolved style pack, its prompt clause and SHA-256"),
                            ("style-check", "Check a style pack's reference assets in the private library")):
        sp = subs.add_parser(name, help=help_text)
        sp.add_argument("pack")
        sp.add_argument("--styles-dir", default="configs/styles")
        sp.add_argument("--library", default="library")
    bp = subs.add_parser("brief-plan", help="Turn a creative brief into an editable storyboard (offline)")
    bp.add_argument("brief")
    bp.add_argument("--out", required=True, help="Storyboard YAML to write (refused if it exists)")
    bp.add_argument("--history", default="configs/perf_history.json")
    for name, help_text in (("experiment-plan", "Plan a bounded A/B experiment on one bridge (F29; offline)"),
                            ("experiment-run", "Run experiment candidates one at a time (validate only without --confirm-gpu)"),
                            ("experiment-rate", "Record an owner rating (1-5) for a candidate"),
                            ("experiment-report", "Per-level summaries, Pareto choices and caveats")):
        esub = subs.add_parser(name, help=help_text)
        esub.add_argument("definition")
        esub.add_argument("--repo-root", default=".")
        if name in ("experiment-plan", "experiment-run"):
            esub.add_argument("--history", default=None, help="Measured history (default configs/perf_history.json)")
        if name == "experiment-run":
            esub.add_argument("--confirm-gpu", action="store_true")
            esub.add_argument("--url", default="http://127.0.0.1:8188")
            esub.add_argument("--runs-root", default="outputs/runs")
        if name == "experiment-rate":
            esub.add_argument("candidate")
            esub.add_argument("score", type=int)
            esub.add_argument("--note", default="")
    pex = subs.add_parser("project-export", help="Write a portable project package (F28; media opt-in)")
    pex.add_argument("storyboard")
    pex.add_argument("--out", required=True)
    pex.add_argument("--run", default=None, help="Run folder whose provenance to include (paths redacted)")
    pex.add_argument("--include-media", action="store_true", help="Owner authorizes including images/videos")
    pex.add_argument("--include-audio", action="store_true", help="Owner authorizes including the licensed music")
    pex.add_argument("--repo-root", default=".")
    pin = subs.add_parser("project-inspect", help="Verify a project package without extracting it")
    pin.add_argument("package")
    pim = subs.add_parser("project-import", help="Restore a verified package into a new folder; replay report")
    pim.add_argument("package")
    pim.add_argument("--dest", required=True)
    pim.add_argument("--models-root", default=None)
    reg = subs.add_parser("registry", help="Read-only capability registry of every binding profile (F27)")
    reg.add_argument("--profiles", default=None, help="Profiles folder (default configs/profiles)")
    reg.add_argument("--strict", action="store_true", help="Exit 1 if any entry is not ready")
    rdiff = subs.add_parser("registry-diff", help="Compatibility preview: current vs candidate profile")
    rdiff.add_argument("current")
    rdiff.add_argument("candidate")
    rsel = subs.add_parser("registry-select", help="Make a ready candidate profile active (owner approval)")
    rsel.add_argument("--profile", required=True)
    rsel.add_argument("--approve", action="store_true", help="Explicit owner approval")
    rsel.add_argument("--note", default="")
    rrb = subs.add_parser("registry-rollback", help="Restore the previously active profile for a capability")
    rrb.add_argument("--capability", required=True)
    for sub in (reg, rdiff, rsel):
        group = sub.add_mutually_exclusive_group()
        group.add_argument("--object-info", help="Saved /object_info snapshot (offline)")
        group.add_argument("--live", action="store_true", help="Read-only GET /object_info from local ComfyUI")
        sub.add_argument("--url", default="http://127.0.0.1:8188")
        sub.add_argument("--repo-root", default=None)
    for sub in (reg, rsel):
        sub.add_argument("--models-root", default=None, help="ComfyUI models folder (presence check only)")
    for sub in (rsel, rrb):
        sub.add_argument("--selection", default=None, help="Selection record (default configs/registry/selection.json)")
    fin = subs.add_parser("finish", help="Geometric 1080p/1440p finishing with identity check (CPU)")
    fin.add_argument("input", nargs="?")
    fin.add_argument("--target", default="1080p", choices=["1080p", "1440p"])
    fin.add_argument("--mode", default="fit", choices=["fit", "fill"])
    fin.add_argument("--denoise", action="store_true")
    fin.add_argument("--deblock", action="store_true")
    fin.add_argument("--sharpen", action="store_true")
    fin.add_argument("--match-anchor", help="Approved anchor image for per-channel colour match")
    fin.add_argument("--crf", type=int, default=16)
    fin.add_argument("--out")
    fin.add_argument("--list-models", action="store_true", help="List installed learned upscalers (read-only)")
    fin.add_argument("--comfy-root", default=r"C:\AI\ComfyUI_windows_portable\ComfyUI")
    ipl = subs.add_parser("interpolate", help="Convert a 16 fps clip/movie to 24/30/48/60 fps (new file + record)")
    ipl.add_argument("input")
    ipl.add_argument("--fps", type=int, required=True, choices=[24, 30, 48, 60])
    ipl.add_argument("--method", default="blend", choices=["repeat", "blend", "motion"])
    ipl.add_argument("--out", required=True)
    ipl.add_argument("--crf", type=int, default=16)
    wap = subs.add_parser("warp-apply", help="Retime a bridge with its energy-warp map (endpoints pinned)")
    wap.add_argument("clip")
    src = wap.add_mutually_exclusive_group(required=True)
    src.add_argument("--map", help="JSON list: source position per output frame")
    src.add_argument("--plan", help="sync-plan JSON (use with --bridge)")
    wap.add_argument("--bridge", type=int, default=0)
    wap.add_argument("--out", required=True)
    wap.add_argument("--crf", type=int, default=16)
    afx = subs.add_parser("audio-features", help="Per-video-frame audio feature track (bands, flux, onsets, sections)")
    afx.add_argument("file")
    afx.add_argument("--out", required=True)
    afx.add_argument("--fps", type=float, default=16.0)
    spl = subs.add_parser("sync-plan", help="Event-locked anchor plan with bridge character and energy warps")
    spl.add_argument("features", help="JSON written by audio-features")
    spl.add_argument("--out", required=True)
    spl.add_argument("--preferred", type=int, default=65, help="Preferred bridge length in frames (4n+1)")
    spl.add_argument("--beatmap", help="Optional verified/confident beat map JSON (adds a downbeat boost)")
    ct_ = subs.add_parser("continuity", help="Shape/topology/background/motion/colour continuity flags for a clip")
    ct_.add_argument("clip")
    ct_.add_argument("--metrics", action="store_true", help="Include per-frame metrics")
    ce = subs.add_parser("continuity-eval", help="Evaluate continuity + subject detectors on labelled clips")
    ce.add_argument("--labels", default="configs/qa_labels.json")
    ce.add_argument("--repo-root", default=".")
    rpp = subs.add_parser("repair-propose", help="Write a repair proposal for a flagged bridge (nothing renders)")
    rpp.add_argument("run")
    rpp.add_argument("task", help="e.g. bridge:orchid->butterfly")
    rpp.add_argument("--out", required=True)
    rcm = subs.add_parser("repair-compare", help="Controlled comparison of an original and a repaired clip")
    rcm.add_argument("original")
    rcm.add_argument("repaired")
    cc = subs.add_parser("camera-check", help="Camera-move labels, endpoint satisfiability, framing and crops")
    cc.add_argument("storyboard")
    cc.add_argument("--run", help="Run directory whose anchors to measure")
    cc.add_argument("--repo-root", default=".")
    rc = subs.add_parser("run-compare", help="Compare two runs stage by stage (bytes; --frames decodes)")
    rc.add_argument("run_a")
    rc.add_argument("run_b")
    rc.add_argument("--frames", action="store_true")
    rp = subs.add_parser("replay", help="Render into a fresh empty runs root, then compare with a reference run")
    rp.add_argument("storyboard")
    rp.add_argument("--reference", required=True)
    rp.add_argument("--runs-root", required=True, help="Must be empty or absent")
    rp.add_argument("--confirm-gpu", action="store_true")
    rp.add_argument("--frames", action="store_true")
    rp.add_argument("--url", default="http://127.0.0.1:8188")
    au = subs.add_parser("audit", help="Release audit: workflow pins, media licences, forbidden tracked files")
    au.add_argument("--repo-root", default=".")
    rb = subs.add_parser("run-backup", help="Archive a run and its job folders with SHA-256 checksums")
    rb.add_argument("run")
    rb.add_argument("--out", required=True)
    rb.add_argument("--allow-missing-jobs", action="store_true")
    rr = subs.add_parser("run-restore", help="Verify and restore a run archive (never overwrites)")
    rr.add_argument("archive")
    rr.add_argument("--runs-root", required=True)
    ac = subs.add_parser("acceptance", help="F01-F20/F30/F40 acceptance matrix from the ledger")
    ac.add_argument("--all", action="store_true", help="All forty features")
    ac.add_argument("--through", type=int, choices=[20, 30, 40], default=None)
    for name, help_text in (("accuracy-checklist", "Per-anchor accuracy checklist with concept context (F33)"),
                            ("accuracy-review", "Record an owner verdict (accurate / reject / waive) for an anchor image"),
                            ("accuracy-negatives", "Check every anchor/bridge prompt carries text/logo negatives"),
                            ("accuracy-impact", "Stages a rejection invalidates (transitive edits, bridges, final)"),
                            ("accuracy-status", "Accuracy sign-off status and gate for a storyboard/run")):
        asub = subs.add_parser(name, help=help_text)
        asub.add_argument("storyboard")
        asub.add_argument("--repo-root", default=".")
        if name in ("accuracy-review", "accuracy-impact", "accuracy-status"):
            asub.add_argument("--log", default=None, help="Review log (default outputs/reviews/<name>.accuracy.jsonl)")
        if name == "accuracy-checklist":
            asub.add_argument("--bank", default="configs/concepts/engineering-film.yaml")
        if name == "accuracy-review":
            asub.add_argument("anchor")
            asub.add_argument("--verdict", required=True, choices=["accurate", "reject", "waive"])
            grp = asub.add_mutually_exclusive_group(required=True)
            grp.add_argument("--sha256")
            grp.add_argument("--image")
            grp.add_argument("--run", help="Run folder whose recorded image hash to use")
            asub.add_argument("--fail", action="append", default=[], help="Failed checklist item (repeatable)")
            asub.add_argument("--note", default="")
            asub.add_argument("--reviewer", default="owner")
        if name == "accuracy-impact":
            asub.add_argument("--reject", action="append", required=True)
        if name == "accuracy-status":
            asub.add_argument("--run", default=None)
    fst = subs.add_parser("film-storyboard", help="Write the full-song film storyboard from sync plan + concepts + acts (F32)")
    fst.add_argument("--plan", default="configs/film/sync-plan.json")
    fst.add_argument("--bank", default="configs/concepts/engineering-film.yaml")
    fst.add_argument("--acts", default="configs/film/acts.yaml")
    fst.add_argument("--out", required=True)
    fst.add_argument("--audio", default=None, help="Owner-licensed track to reference (never fetched)")
    frp = subs.add_parser("film-report", help="Dry-run film report: per-act frames, coverage, GPU-hour estimate")
    frp.add_argument("storyboard")
    frp.add_argument("--plan", default="configs/film/sync-plan.json")
    frp.add_argument("--history", default="configs/perf_history.json")
    frp.add_argument("--repo-root", default=".")
    cck = subs.add_parser("concepts-check", help="Validate the F31 engineering concept bank")
    cck.add_argument("--bank", default="configs/concepts/engineering-film.yaml")
    grp = cck.add_mutually_exclusive_group()
    grp.add_argument("--plan", default=None, help="sync-plan JSON whose anchor count the bank must cover")
    grp.add_argument("--target", type=int, default=None, help="Required entry count (default 96)")
    cls = subs.add_parser("concepts-list", help="Numbered list of the concept bank for owner review")
    cls.add_argument("--bank", default="configs/concepts/engineering-film.yaml")
    cls.add_argument("--json", action="store_true")
    rc = subs.add_parser("release-check", help="Acceptance through F30 + repository audit (never tags)")
    rc.add_argument("--through", type=int, choices=[20, 30, 40], default=30)
    rc.add_argument("--ledger", default="docs/SPECKIT_FEATURE_LEDGER.md")
    rc.add_argument("--repo-root", default=".")
    dl = subs.add_parser("deliver", help="Versioned multi-format delivery presets with verification (F30)")
    dl.add_argument("input", nargs="?")
    dl.add_argument("--preset", action="append", default=[])
    dl.add_argument("--out-dir")
    dl.add_argument("--audio", default=None, help="Owner-licensed music for licensed-audio-1080p")
    dl.add_argument("--audio-licensed", action="store_true")
    dl.add_argument("--audio-offset", type=float, default=0.0)
    dl.add_argument("--list-presets", action="store_true")
    ac.add_argument("--ledger", default="docs/SPECKIT_FEATURE_LEDGER.md")
    dc = subs.add_parser("draft-check", help="Check a Claude-drafted brief or storyboard locally (offline)")
    dc.add_argument("draft", help="Brief or storyboard YAML")
    dc.add_argument("--repo-root", default=".")
    sc = subs.add_parser("schedule", help="Preview stage order, estimated GPU time and budget fit (offline)")
    sc.add_argument("storyboard")
    sc.add_argument("--max-gpu-s", type=float)
    sc.add_argument("--max-jobs", type=int)
    sc.add_argument("--history", default="configs/perf_history.json")
    pd = subs.add_parser("plan-diff", help="Which stages an edited storyboard re-runs, and why (offline)")
    pd.add_argument("old")
    pd.add_argument("new")
    pd.add_argument("--all", action="store_true", help="Also list cached stages")
    pd.add_argument("--repo-root", default=".")
    tl = subs.add_parser("timeline", help="Anchor/chapter timestamps, FFmpeg chapters, proxy storyboard (offline)")
    tl.add_argument("storyboard")
    tl.add_argument("--ffmetadata", help="Write an FFMETADATA1 chapter file")
    tl.add_argument("--write-proxy", help="Write a 640x368 '-proxy' preview storyboard")
    tl.add_argument("--repo-root", default=".")
    stg = subs.add_parser("storage", help="Bytes used in the runs root by job kind/state (read-only)")
    stg.add_argument("--runs-root", default="outputs/runs")
    rui = subs.add_parser("review-ui", help="Local loopback review page: runs, clips, QA, approve/reject")
    rui.add_argument("--runs-root", default="outputs/runs")
    rui.add_argument("--host", default="127.0.0.1", help="Loopback only: 127.0.0.1, ::1 or localhost")
    rui.add_argument("--port", type=int, default=8765)
    rui.add_argument("--storyboard", action="append", help="Extra storyboard for the plan view")
    rui.add_argument("--repo-root", default=".")
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
        elif args.command == "ladder-risk":
            return _ladder_risk(args)
        elif args.command == "ladder-propose":
            return _ladder_propose(args)
        elif args.command in {"style-list", "style-show", "style-check"}:
            return _style(args)
        elif args.command == "brief-plan":
            return _brief_plan(args)
        elif args.command == "finish":
            return _finish(args)
        elif args.command.startswith("accuracy-"):
            return _accuracy(args)
        elif args.command in ("film-storyboard", "film-report"):
            return _film(args)
        elif args.command in ("concepts-check", "concepts-list"):
            return _concepts(args)
        elif args.command in ("deliver", "release-check"):
            return _deliver(args)
        elif args.command in ("experiment-plan", "experiment-run", "experiment-rate", "experiment-report"):
            return _experiment(args)
        elif args.command in ("project-export", "project-inspect", "project-import"):
            return _project(args)
        elif args.command in ("registry", "registry-diff", "registry-select", "registry-rollback"):
            return _registry(args)
        elif args.command in ("interpolate", "warp-apply"):
            return _interp(args)
        elif args.command in ("audio-features", "sync-plan"):
            return _sync(args)
        elif args.command in ("continuity", "continuity-eval", "repair-propose", "repair-compare"):
            return _continuity(args)
        elif args.command == "camera-check":
            return _camera_check(args)
        elif args.command in ("run-compare", "replay", "audit", "run-backup", "run-restore", "acceptance"):
            return _release(args)
        elif args.command == "draft-check":
            return _draft_check(args)
        elif args.command == "plan-diff":
            return _plan_diff(args)
        elif args.command == "timeline":
            return _timeline(args)
        elif args.command == "storage":
            return _storage(args)
        elif args.command == "review-ui":
            return _review_ui(args)
        elif args.command == "schedule":
            return _schedule(args)
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
    except (ValidationError, ValueError, OSError, AudioError, LadderError, StyleError, BriefError, LockBusy, ComfyError, WorkflowBindingError, BridgeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
