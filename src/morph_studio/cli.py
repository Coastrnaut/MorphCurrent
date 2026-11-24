"""Small, operational offline CLI; no pretend GPU integration."""
from __future__ import annotations

import argparse
import json
import sys
from pydantic import ValidationError

from .schema import load_storyboard
from .timeline import timeline_as_dict
from .comfy_client import ComfyClient, ComfyError
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
        elif args.command == "health":
            with ComfyClient(args.url) as client:
                print(json.dumps(client.health(), indent=2))
        return 0
    except (ValidationError, ValueError, OSError, ComfyError, WorkflowBindingError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
