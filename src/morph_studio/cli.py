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
        elif args.command == "health":
            with ComfyClient(args.url) as client:
                print(json.dumps(client.health(), indent=2))
        return 0
    except (ValidationError, ValueError, OSError, ComfyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
