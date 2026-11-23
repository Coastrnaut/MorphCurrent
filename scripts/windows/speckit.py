"""Safely initialize GitHub Spec Kit for Claude Desktop Code with PYTHON scripts.

    py -3 scripts/windows/speckit.py --status
    py -3 scripts/windows/speckit.py --init

This only invokes an already-installed 'specify' CLI. No auto-downloads.
Requires support for 'specify init --here --integration claude --script py'.
Never uses .ps1, bash or WSL.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def build_specify_command(executable: str = "specify") -> list[str]:
    return [executable, "init", "--here", "--integration", "claude", "--script", "py"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Windows-only Python Spec Kit setup")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--status", action="store_true")
    group.add_argument("--init", action="store_true")
    args = parser.parse_args(argv)
    if sys.platform != "win32":
        parser.error("Spec Kit setup must run in native Windows Python, never WSL.")
    existing = ROOT / ".specify"
    exe = shutil.which("specify")
    print("Spec Kit project:", "already initialized" if existing.exists() else "not initialized")
    print("Spec Kit CLI:", exe or "not installed")
    print("Preferred script variant: py (Python)")
    if not exe:
        print("Install the official CLI using 'uv tool install specify-cli', then rerun.")
        return 2 if args.init else 0
    version = subprocess.run([exe, "--version"], cwd=ROOT, capture_output=True, text=True,
                             errors="replace", check=False)
    print("CLI version:", (version.stdout or version.stderr).strip())
    if args.status:
        return 0
    if existing.exists():
        print("Preserving existing .specify; inspect its script preference before changes.")
        return 0
    help_output = subprocess.run([exe, "init", "--help"], cwd=ROOT, capture_output=True,
                                 text=True, errors="replace", check=False)
    help_text = help_output.stdout + help_output.stderr
    if help_output.returncode != 0 or not all(
        flag in help_text for flag in ("--script", "--integration", "--here")
    ):
        print("Installed Spec Kit CLI lacks the needed Python/Claude init flags.", file=sys.stderr)
        return 2
    command = build_specify_command(exe)
    print("Initializing Spec Kit using:", subprocess.list2cmdline(command))
    try:
        subprocess.run(command, cwd=ROOT, check=True, shell=False)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Initialization failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
