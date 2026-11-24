"""Conservative FFmpeg assembly: only join when endpoint duplication is verified (F09).

Adjacent Wan bridges share anchor B: the last frame of A→B and the first frame of
B→C depict the same image. After the decoded frames are verified to match, the
later clip's first frame is dropped and clips are concatenated — never
cross-faded. 65 + 65 frames → 129 unique frames.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

SEAM_TOLERANCE = 8.0  # mean abs diff, 64x36 gray levels (H.264 re-encode of the same anchor)


class SeamError(ValueError):
    pass


def build_join_command(clips: list[Path], output: Path, *,
                       fps: int, verified_matching_endpoints: bool,
                       overwrite: bool = False, audio: Path | None = None,
                       audio_offset: float = 0.0, video_seconds: float | None = None) -> list[str]:
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
    args = ["ffmpeg", "-hide_banner", "-nostdin", "-y" if overwrite else "-n"]
    for clip in clips:
        args.extend(["-i", str(clip)])
    if audio is not None:
        if video_seconds is None:
            raise ValueError("video_seconds is required to cut audio to the video length")
        args.extend(["-ss", f"{audio_offset:.6f}", "-i", str(audio)])
    args.extend(["-filter_complex", ";".join(filters), "-map", "[v]"])
    if audio is None:
        args.append("-an")
    else:
        args.extend(["-map", f"{len(clips)}:a:0", "-c:a", "aac", "-b:a", "192k",
                     "-t", f"{video_seconds:.6f}"])
    args.extend(["-r", str(fps), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output)])
    return args


def join_clips(clips: list[Path], output: Path, *,
               fps: int, verified_matching_endpoints: bool,
               overwrite: bool = False) -> Path:
    args = build_join_command(clips, output, fps=fps,
                              verified_matching_endpoints=verified_matching_endpoints,
                              overwrite=overwrite)
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(args, check=True, shell=False)
    return output


def check_seams(clips: list[Path], anchors: list[Path] | None = None,
                tolerance: float = SEAM_TOLERANCE) -> list[dict]:
    """Compare decoded boundary frames of consecutive clips (and the shared anchor if given)."""
    from .qa import _mad, decode_gray_frames
    frames = [decode_gray_frames(c) for c in clips]
    seams = []
    for i in range(len(clips) - 1):
        last, first = frames[i][-1], frames[i + 1][0]
        entry = {"seam": i, "between": [str(clips[i]), str(clips[i + 1])],
                 "boundary_diff": round(_mad(last, first), 3), "tolerance": tolerance}
        if anchors:
            ref = decode_gray_frames(anchors[i])[0]
            entry["anchor"] = str(anchors[i])
            entry["anchor_diff"] = [round(_mad(ref, last), 3), round(_mad(ref, first), 3)]
        entry["match"] = entry["boundary_diff"] <= tolerance and all(
            d <= tolerance for d in entry.get("anchor_diff", []))
        seams.append(entry)
    return seams


def join_verified(clips: list[Path], output: Path, *, fps: int,
                  anchors: list[Path] | None = None, audio: Path | None = None,
                  audio_offset: float = 0.0, probe=None) -> dict:
    """Verify seams and clip properties, join via ``.part`` + rename, verify the result."""
    from .media import probe_video
    probe = probe or probe_video
    if output.exists():
        raise FileExistsError(output)
    if audio is not None and (not Path(audio).is_file() or "://" in str(audio)):
        raise ValueError(f"audio must be an existing local file: {audio}")
    props = [probe(c) for c in clips]
    shapes = {(p["width"], p["height"], round(p["fps"] or 0, 3)) for p in props}
    if len(shapes) != 1:
        raise SeamError(f"clips differ in size/fps: {sorted(shapes)}")
    seams = check_seams(clips, anchors)
    bad = [s for s in seams if not s["match"]]
    if bad:
        raise SeamError(f"seam(s) do not match; refusing to drop frames: {bad}")
    expected = sum(p["frame_count"] for p in props) - (len(clips) - 1)
    part = output.with_name(output.stem + ".part" + output.suffix)
    if part.exists():
        part.unlink()
    args = build_join_command(clips, part, fps=fps, verified_matching_endpoints=True,
                              audio=audio, audio_offset=audio_offset, video_seconds=expected / fps)
    args[0] = shutil.which("ffmpeg") or "ffmpeg"
    output.parent.mkdir(parents=True, exist_ok=True)
    done = subprocess.run(args, capture_output=True, text=True, errors="replace", shell=False, check=False)
    if done.returncode != 0:
        raise RuntimeError(f"ffmpeg join failed: {done.stderr.strip()[:500]}")
    measured = probe(part)
    if measured["frame_count"] != expected:
        raise SeamError(f"joined movie has {measured['frame_count']} frames, expected {expected}")
    os.rename(part, output)
    return {"output": str(output), "frames": expected, "fps": fps,
            "anchor_span_seconds": (expected - 1) / fps, "nominal_duration_seconds": expected / fps,
            "seams": seams, "audio": str(audio) if audio else None,
            "audio_offset_seconds": audio_offset if audio else None, "measured": measured,
            "ffmpeg_args": args[1:], "crossfade": False}
