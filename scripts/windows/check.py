"""Offline native Windows tests, storyboard planning, and optional ComfyUI probe.

    py -3 scripts/windows/check.py
    py -3 scripts/windows/check.py --check-comfy
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def check(*, check_comfy: bool = False) -> int:
    if sys.platform != "win32":
        print("This project targets native Windows 11 (no WSL).", file=sys.stderr)
        return 2
    py = ROOT / ".venv" / "Scripts" / "python.exe"
    if not py.is_file():
        print(f"Missing controller environment: {py}; run initialize.py.", file=sys.stderr)
        return 2
    calls = [
        [str(py), "-m", "pytest", "-m", "not integration and not gpu"],
        [str(py), "-m", "morph_studio.cli", "validate",
         "configs/sequences/organic-machines.yaml"],
        [str(py), "-m", "morph_studio.cli", "plan",
         "configs/sequences/organic-machines.yaml"],
        [str(py), "-m", "morph_studio.cli", "doctor",
         *( [] if check_comfy else ["--skip-comfy"] )],
    ]
    for cmd in calls:
        print(subprocess.list2cmdline(cmd), flush=True)
        try:
            subprocess.run(cmd, cwd=ROOT, check=True, shell=False)
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"Check failed: {exc}", file=sys.stderr)
            return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Windows-native MorphCurrent checks")
    parser.add_argument("--check-comfy", action="store_true")
    args = parser.parse_args(argv)
    return check(check_comfy=args.check_comfy)


if __name__ == "__main__":
    raise SystemExit(main())
