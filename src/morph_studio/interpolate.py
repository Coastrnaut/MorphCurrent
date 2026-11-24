"""Delivery frame rates and energy-warped retiming (F25). Local FFmpeg filters only; offline.

``convert`` turns an approved 16 fps clip or movie into 24/30/48/60 fps with frame repeat, frame
blending or motion-compensated interpolation, writing a *new* file (``.part`` then rename) plus a
provenance sidecar; the input is re-hashed to prove it is unchanged. Blending is refused across hard
cuts. ``anchor_alignment`` reports whether each quarter-second anchor mark lands on an output frame.
``apply_warp`` retimes a bridge with its energy-warp map (docs/MUSIC_SYNC.md): each source frame is
shown for a map-derived duration and the sequence is resampled to a constant 16 fps, so the first and
last frames and the total duration stay exact.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path

from .cache import sha256_file

FILTERS = {
    "repeat": "fps={fps}",
    "blend": "framerate=fps={fps}",
    "motion": "minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1:scd=fdiff",
}
RATES = (24, 30, 48, 60)
SOURCE_FPS = 16
ANCHOR_STEP = Fraction(1, 4)


def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg not found on PATH")
    return exe


def ffmpeg_version() -> str:
    done = subprocess.run([_ffmpeg(), "-version"], capture_output=True, text=True, shell=False, check=False)
    return (done.stdout.splitlines() or ["unknown"])[0]


def anchor_alignment(duration: Fraction, fps: int) -> list[dict]:
    """Every 0.25 s mark within the clip: exact output frame or offset to the nearest one."""
    out, t = [], Fraction(0)
    while t <= duration:
        frame = t * fps
        nearest = round(frame)
        offset = abs(frame - nearest) / fps
        out.append({"t": float(t), "exact": frame.denominator == 1, "offset_s": round(float(offset), 9)})
        t += ANCHOR_STEP
    return out


def _hard_cut(path: Path) -> int | None:
    from .qa import analyze_frames, decode_gray_frames
    frames = decode_gray_frames(path)
    if len(frames) < 3:
        return None
    cuts = [f["frame"] for f in analyze_frames(frames)["flags"] if f["type"] == "hard_cut"]
    return cuts[0] if cuts else None


def _probe(path: Path) -> dict:
    from .media import probe_video
    p = probe_video(path)
    return {"fps": p.get("fps"), "frames": p.get("frame_count"), "duration": p.get("duration_s"),
            "sha256": sha256_file(path)}


def _run(args: list[str]) -> None:
    done = subprocess.run(args, capture_output=True, text=True, shell=False, check=False)
    if done.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {done.stderr[-400:]}")


def convert(src: str | Path, out: str | Path, *, fps: int, method: str = "blend", crf: int = 16) -> dict:
    src, out = Path(src), Path(out)
    if out.exists():
        raise FileExistsError(f"{out} exists; refusing to overwrite")
    if fps not in RATES:
        raise ValueError(f"fps must be one of {RATES}")
    if method not in FILTERS:
        raise ValueError(f"method must be one of {sorted(FILTERS)}")
    before = _probe(src)
    used, fallback = method, None
    if method != "repeat":
        cut = _hard_cut(src)
        if cut is not None:
            used, fallback = "repeat", f"hard cut at frame {cut}: blending would mix two shots"
    # pad one cloned frame first (interpolators cannot synthesize past the last source frame), then trim
    # the output to the exact input duration so every method is duration-exact
    vf = "tpad=stop_mode=clone:stop=2," + FILTERS[used].format(fps=fps)
    part = out.with_name(out.name + ".part.mp4")
    length = before["duration"] or before["frames"] / SOURCE_FPS
    _run([_ffmpeg(), "-hide_banner", "-nostdin", "-v", "error", "-y", "-i", str(src), "-vf", vf, "-r", str(fps),
          "-t", f"{length:.6f}", "-c:v", "libx264", "-crf", str(crf), "-pix_fmt", "yuv420p", "-c:a", "copy",
          str(part)])
    os.replace(part, out)
    after = _probe(out)
    duration = Fraction(str(before["duration"])) if before["duration"] else Fraction(before["frames"], SOURCE_FPS)
    ok = (after["duration"] is not None and before["duration"] is not None
          and abs(after["duration"] - before["duration"]) <= 1 / fps + 1e-6)
    record = {"input": {"path": str(src), **before}, "output": {"path": str(out), **after},
              "fps": fps, "method_requested": method, "method_used": used, "fallback": fallback,
              "filter": vf, "crf": crf, "tool_version": ffmpeg_version(), "ok": ok,
              "anchor_alignment": anchor_alignment(duration, fps)}
    if sha256_file(src) != before["sha256"]:
        raise RuntimeError("input changed during conversion")
    Path(str(out) + ".interp.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def warp_times(mapping: list[float]) -> list[float]:
    """Inverse of a warp map: the output frame position at which each source frame k is reached."""
    n = len(mapping)
    times, i = [], 0
    for k in range(n):
        while i < n - 2 and mapping[i + 1] < k:
            i += 1
        a, b = mapping[i], mapping[i + 1] if i + 1 < n else mapping[i]
        frac = 0.0 if b == a else (k - a) / (b - a)
        times.append(i + max(0.0, min(1.0, frac)))
    times[0], times[-1] = 0.0, float(n - 1)
    return times


def apply_warp(src: str | Path, mapping: list[float], out: str | Path, *, crf: int = 16) -> dict:
    src, out = Path(src), Path(out)
    if out.exists():
        raise FileExistsError(f"{out} exists; refusing to overwrite")
    before = _probe(src)
    n = before["frames"]
    if len(mapping) != n:
        raise ValueError(f"warp map needs one entry per source frame ({n}), got {len(mapping)}")
    times = warp_times(mapping)
    with tempfile.TemporaryDirectory(prefix="mc-warp-") as tmp:
        tdir = Path(tmp)
        _run([_ffmpeg(), "-hide_banner", "-nostdin", "-v", "error", "-i", str(src), "-vsync", "0",
              str(tdir / "f%05d.png")])
        lines = ["ffconcat version 1.0"]
        for k in range(n):
            dur = (times[k + 1] - times[k]) / SOURCE_FPS if k + 1 < n else 1 / SOURCE_FPS
            lines += [f"file f{k + 1:05d}.png", f"duration {max(dur, 1e-4):.6f}"]
        lines.append(f"file f{n:05d}.png")  # concat demuxer needs the last file repeated
        (tdir / "list.ffconcat").write_text("\n".join(lines) + "\n", encoding="utf-8")
        part = out.with_name(out.name + ".part.mp4")
        _run([_ffmpeg(), "-hide_banner", "-nostdin", "-v", "error", "-y", "-f", "concat", "-safe", "0",
              "-i", str(tdir / "list.ffconcat"), "-vf", f"fps={SOURCE_FPS}:round=near", "-frames:v", str(n),
              "-c:v", "libx264", "-crf", str(crf), "-pix_fmt", "yuv420p", str(part)])
        os.replace(part, out)
    after = _probe(out)
    from .qa import decode_gray_frames
    a, b = decode_gray_frames(src), decode_gray_frames(out)
    mad = lambda x, y: sum(abs(p - q) for p, q in zip(x, y)) / len(x)  # noqa: E731
    endpoints_ok = bool(a and b) and mad(a[0], b[0]) <= 3 and mad(a[-1], b[-1]) <= 3
    steps = [y - x for x, y in zip(mapping, mapping[1:])]
    record = {"input": {"path": str(src), **before}, "output": {"path": str(out), **after},
              "frames_in": n, "frames_out": after["frames"], "endpoints_ok": endpoints_ok,
              "speed": {"min": round(min(steps), 3) if steps else 1.0, "max": round(max(steps), 3) if steps else 1.0},
              "tool_version": ffmpeg_version()}
    Path(str(out) + ".warp.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record
