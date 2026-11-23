"""Conservative FFmpeg assembly: only join when endpoint duplication is verified."""
from __future__ import annotations

import subprocess
from pathlib import Path


def build_join_command(clips: list[Path], output: Path, *,
                       fps: int, verified_matching_endpoints: bool) -> list[str]:
    if len(clips) < 2:
        raise ValueError("at least two clips required")
    if fps <= 0:
        raise ValueError("fps must be positive")
    if not verified_matching_endpoints:
        raise ValueError("manual/automated endpoint verification required before join")
    filters = []
    labels = []
    for i in range(len(clips)):
        label = f"v{i}"
        # Drop the first frame only from later clips: shared anchor timestamp.
        chain = "setpts=PTS-STARTPTS" if i == 0 else "trim=start_frame=1,setpts=PTS-STARTPTS"
        filters.append(f"[{i}:v]{chain}[{label}]")
        labels.append(f"[{label}]")
    filters.append("".join(labels) + f"concat=n={len(clips)}:v=1:a=0[v]")
    args = ["ffmpeg", "-hide_banner", "-nostdin", "-y"]
    for clip in clips:
        args.extend(["-i", str(clip)])
    args.extend(["-filter_complex", ";".join(filters), "-map", "[v]",
                 "-an", "-r", str(fps), "-c:v", "libx264",
                 "-pix_fmt", "yuv420p", str(output)])
    return args


def join_clips(clips: list[Path], output: Path, *,
               fps: int, verified_matching_endpoints: bool) -> Path:
    args = build_join_command(clips, output, fps=fps,
                              verified_matching_endpoints=verified_matching_endpoints)
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(args, check=True, shell=False)
    return output
