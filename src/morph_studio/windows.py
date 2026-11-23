"""Native Windows 11 development diagnostics; no WSL, CUDA toolkit or torch dependency."""
from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

from .comfy_client import ComfyClient, ComfyError, validate_local_url


def _capture(executable: str, args: list[str], *, timeout: float = 8.0) -> dict:
    """Capture a local program without invoking cmd.exe or PowerShell."""
    try:
        p = subprocess.run(
            [executable, *args],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
            shell=False,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc)}
    return {
        "ok": p.returncode == 0,
        "returncode": p.returncode,
        "stdout": p.stdout.strip()[:3000],
        "stderr": p.stderr.strip()[:1000],
    }


def windows_diagnostics(
    comfy_url: str = "http://127.0.0.1:8188", *, check_comfy: bool = True
) -> dict:
    """Inspect the host safely; never install drivers, modify paths or load models.

    PyTorch is checked separately in ComfyUI's *own* Python environment:
    MorphCurrent's controller intentionally does not require torch.
    """
    validate_local_url(comfy_url)
    host_is_windows = platform.system() == "Windows"
    report: dict = {
        "target": "Native Windows 11 with NVIDIA RTX A6000 (no Linux/WSL backend)",
        "supported_host": host_is_windows,
        "host": {"system": platform.system(), "release": platform.release(),
                 "machine": platform.machine()},
        "controller_python": {
            "executable": sys.executable, "version": sys.version.split()[0],
            "virtual_environment": sys.prefix != sys.base_prefix,
        },
        "tools": {},
        "gpu": {"detected": False, "note": "Driver check, not a PyTorch CUDA inference test."},
        "comfyui": {"url": comfy_url, "checked": check_comfy, "reachable": False},
        "notes": [
            "ComfyUI Portable has its own embedded Python; do not pip-install its "
            "models/dependencies into MorphCurrent's .venv.",
            "Native Windows driver CUDA support does not prove torch.cuda.is_available() "
            "inside the selected ComfyUI Python interpreter.",
            "All GPU inference requires a user-verified API workflow and checkpoint inventory.",
        ],
    }
    for name in ("git", "ffmpeg", "ffprobe", "nvidia-smi"):
        report["tools"][name] = shutil.which(name)
    smi = report["tools"]["nvidia-smi"]
    if smi:
        output = _capture(smi, [
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ])
        report["gpu"]["nvidia_smi"] = output
        if output["ok"] and output.get("stdout"):
            rows = [x.strip() for x in output["stdout"].splitlines() if x.strip()]
            report["gpu"]["detected"] = bool(rows)
            report["gpu"]["devices"] = rows
    if check_comfy:
        try:
            with ComfyClient(comfy_url, timeout=5) as client:
                stats = client.health()
                report["comfyui"]["reachable"] = True
                report["comfyui"]["devices"] = stats.get("devices", [])
        except (ComfyError, OSError) as exc:
            report["comfyui"]["error"] = str(exc)
    report["ready_for_offline_development"] = host_is_windows and all(
        report["tools"][name] for name in ("git", "ffmpeg", "ffprobe")
    )
    report["ready_for_local_gpu_workflows"] = (
        report["ready_for_offline_development"]
        and report["gpu"]["detected"]
        and report["comfyui"]["reachable"]
    )
    return report
