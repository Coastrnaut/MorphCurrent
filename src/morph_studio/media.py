"""ffprobe inspection of rendered clips (native Windows binary, argument arrays only)."""
from __future__ import annotations

import json
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path


class ProbeUnavailable(RuntimeError):
    """ffprobe is not on PATH; verification must be reported as skipped, not passed."""


def probe_video(path: str | Path, *, ffprobe: str | None = None, timeout: float = 120) -> dict:
    """Return width, height, decoded frame count, fps and codec of the first video stream."""
    executable = ffprobe or shutil.which("ffprobe")
    if not executable:
        raise ProbeUnavailable("ffprobe not found on PATH")
    args = [executable, "-v", "error", "-select_streams", "v:0", "-count_frames",
            "-show_entries", "stream=width,height,r_frame_rate,avg_frame_rate,nb_read_frames,codec_name",
            "-show_entries", "format=duration", "-of", "json", str(path)]
    completed = subprocess.run(args, capture_output=True, text=True, errors="replace",
                               timeout=timeout, shell=False, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"ffprobe failed ({completed.returncode}): {completed.stderr.strip()[:500]}")
    payload = json.loads(completed.stdout or "{}")
    streams = payload.get("streams") or []
    if not streams:
        raise RuntimeError(f"no video stream in {path}")
    stream = streams[0]
    rate = stream.get("r_frame_rate") or stream.get("avg_frame_rate") or "0/1"
    frames = stream.get("nb_read_frames")
    duration = (payload.get("format") or {}).get("duration")
    return {
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "frame_count": int(frames) if frames not in (None, "N/A") else None,
        "fps": float(Fraction(rate)) if rate != "0/0" else None,
        "codec": stream.get("codec_name"),
        "duration_s": float(duration) if duration not in (None, "N/A") else None,
    }
