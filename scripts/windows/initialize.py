"""Initialize the MorphCurrent *controller* environment on native Windows 11.

Run with an existing Windows Python 3.11+:
    py -3 scripts/windows/initialize.py
This does NOT install ComfyUI, custom nodes, CUDA drivers, or checkpoint weights.
"""
from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def require_windows() -> None:
    if sys.platform != "win32":
        raise SystemExit("MorphCurrent supports only native Windows 11. Do not use WSL/Linux.")


def run(argv: list[str], *, cwd: Path = ROOT) -> None:
    print("Executing:", subprocess.list2cmdline(argv), flush=True)
    subprocess.run(argv, cwd=cwd, check=True, shell=False)


def controller_python(root: Path = ROOT) -> Path:
    return root / ".venv" / "Scripts" / "python.exe"


def initialize(root: Path, *, skip_tests: bool = False) -> Path:
    require_windows()
    if sys.version_info < (3, 11):
        raise SystemExit("MorphCurrent requires Python 3.11 or newer.")
    venv = controller_python(root)
    if not venv.exists():
        run([sys.executable, "-m", "venv", str(root / ".venv")], cwd=root)
    if not venv.is_file():
        raise FileNotFoundError(f"Virtualenv Python missing: {venv}")
    run([str(venv), "-m", "pip", "install", "-e", str(root) + "[dev]"], cwd=root)
    if not skip_tests:
        run([str(venv), "-m", "pytest", "-m", "not integration and not gpu"], cwd=root)
        run([str(venv), "-m", "morph_studio.cli", "doctor", "--skip-comfy"], cwd=root)
    return venv


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Prepare native Windows MorphCurrent controller")
    p.add_argument("--skip-tests", action="store_true",
                   help="Skip offline tests (not recommended)")
    args = p.parse_args(argv)
    try:
        result = initialize(ROOT, skip_tests=args.skip_tests)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Setup failed: {exc}", file=sys.stderr)
        return 1
    print(f"Controller ready: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
