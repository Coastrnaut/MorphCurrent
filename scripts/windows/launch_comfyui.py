"""Safely launch an EXISTING local native-Windows ComfyUI installation.

Examples:
    python scripts/windows/launch_comfyui.py --install-root C:\\AI\\ComfyUI_windows_portable
    python scripts/windows/launch_comfyui.py --install-root C:\\AI\\ComfyUI --distribution manual
    python scripts/windows/launch_comfyui.py --install-root C:\\AI\\ComfyUI --dry-run

Defaults: 127.0.0.1:8188, ComfyUI default memory management.
No dependency or model downloads. No GPU inference by this helper.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def build_launch_command(
    install_root: Path,
    *,
    distribution: str = "auto",
    memory_mode: str = "default",
    port: int = 8188,
    python_executable: Path | None = None,
) -> tuple[list[str], Path]:
    if distribution not in {"auto", "portable", "manual"}:
        raise ValueError("distribution must be auto, portable or manual")
    if memory_mode not in {"default", "highvram", "lowvram"}:
        raise ValueError("memory_mode must be default, highvram or lowvram")
    if not (1024 <= port <= 65535):
        raise ValueError("port must be between 1024 and 65535")
    root = install_root.expanduser().resolve(strict=True)
    p_main = root / "ComfyUI" / "main.py"
    p_python = root / "python_embeded" / "python.exe"
    m_main = root / "main.py"
    m_python = root / ".venv" / "Scripts" / "python.exe"
    if distribution == "auto":
        if p_main.is_file() and p_python.is_file():
            distribution = "portable"
        elif m_main.is_file():
            distribution = "manual"
        else:
            raise FileNotFoundError("No ComfyUI main.py in portable or manual layout")
    if distribution == "portable":
        if python_executable is not None:
            raise ValueError("Portable uses bundled python_embeded; no override allowed")
        main, python = p_main, p_python
        cmd = [str(python), "-s", str(main), "--windows-standalone-build"]
    else:
        main = m_main
        python = python_executable or m_python
        cmd = [str(python), str(main)]
    if not main.is_file():
        raise FileNotFoundError(f"ComfyUI entrypoint missing: {main}")
    if not python.is_file():
        raise FileNotFoundError(f"ComfyUI Python missing: {python}")
    cmd.extend(["--listen", "127.0.0.1", "--port", str(port)])
    if memory_mode != "default":
        cmd.append("--" + memory_mode)
    return cmd, main.parent


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Launch ComfyUI via native Windows Python")
    p.add_argument("--install-root", required=True, type=Path)
    p.add_argument("--distribution", choices=["auto", "portable", "manual"],
                   default="auto")
    p.add_argument("--memory-mode", choices=["default", "highvram", "lowvram"],
                   default="default")
    p.add_argument("--port", type=int, default=8188)
    p.add_argument("--python-executable", type=Path,
                   help="Override manual ComfyUI Python only")
    p.add_argument("--dry-run", action="store_true",
                   help="Display resolved command without starting ComfyUI")
    args = p.parse_args(argv)
    if sys.platform != "win32" and not args.dry_run:
        p.error("Windows native only. WSL/Linux cannot launch this runtime.")
    try:
        cmd, cwd = build_launch_command(
            args.install_root, distribution=args.distribution,
            memory_mode=args.memory_mode, port=args.port,
            python_executable=args.python_executable,
        )
        print("Working directory:", cwd)
        print("Command:", subprocess.list2cmdline(cmd))
        if args.memory_mode == "highvram":
            print("WARNING: --highvram does not fit two 14B FP16 experts in 48 GiB.")
        if args.dry_run:
            return 0
        subprocess.run(cmd, cwd=cwd, shell=False, check=True)
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ComfyUI launch failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
