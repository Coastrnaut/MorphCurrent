"""Local resolution enhancement and finishing (F26). Geometric, CPU (FFmpeg) only.

``finish`` resamples an approved clip or movie to 1080p / 1440p with Lanczos, fitting (black padding)
or filling (centre crop) the 832x480 aspect, with optional light denoise / deblock / sharpen and an
optional per-channel colour match to an approved anchor. It writes a *new* file plus a record and
verifies that the first and last frames - the approved anchors - still match the source when scaled
back (identity check). Learned (generative) upscalers are listed read-only and stay refused until an
owner-approved, hash-pinned ComfyUI workflow exists for them (tasks T016).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from .cache import sha256_file

TARGETS = {"1080p": (1920, 1080), "1440p": (2560, 1440)}
DENOISE, DEBLOCK, SHARPEN = "hqdn3d=1.5:1.5:6:6", "deblock=filter=weak", "unsharp=5:5:0.4"
IDENTITY_MAD = 4.0
GAIN_RANGE = (0.8, 1.25)


class FinishError(ValueError):
    pass


def _even(x: float) -> int:
    return max(2, int(round(x / 2)) * 2)


def geometry(src_w: int, src_h: int, target: str, mode: str) -> dict:
    tw, th = TARGETS[target]
    if mode not in ("fit", "fill"):
        raise FinishError("mode must be fit or fill")
    k = (min if mode == "fit" else max)(tw / src_w, th / src_h)
    sw, sh = _even(src_w * k), _even(src_h * k)
    if mode == "fit":
        sw, sh = min(sw, tw), min(sh, th)
    g = {"target": target, "mode": mode, "src_w": src_w, "src_h": src_h, "target_w": tw, "target_h": th,
         "scaled_w": sw, "scaled_h": sh, "pad_x": 0, "pad_y": 0, "crop_x": 0, "crop_y": 0}
    if mode == "fit":
        g["pad_x"], g["pad_y"] = (tw - sw) // 2, (th - sh) // 2
    else:
        g["crop_x"], g["crop_y"] = (sw - tw) // 2, (sh - th) // 2
    return g


def chain(g: dict, *, denoise: bool = False, deblock: bool = False, sharpen: bool = False,
          gains: tuple[float, float, float] | None = None) -> str:
    steps = []
    if denoise:
        steps.append(DENOISE)
    if deblock:
        steps.append(DEBLOCK)
    if gains:
        steps.append("colorchannelmixer=rr={:.4f}:gg={:.4f}:bb={:.4f}".format(*gains))
    steps.append(f"scale={g['scaled_w']}:{g['scaled_h']}:flags=lanczos")
    if g["mode"] == "fit":
        steps.append(f"pad={g['target_w']}:{g['target_h']}:{g['pad_x']}:{g['pad_y']}:black")
    else:
        steps.append(f"crop={g['target_w']}:{g['target_h']}:{g['crop_x']}:{g['crop_y']}")
    if sharpen:
        steps.append(SHARPEN)
    steps.append("format=yuv420p")
    return ",".join(steps)


def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise FinishError("ffmpeg not found on PATH")
    return exe


def _run(args: list[str]) -> None:
    done = subprocess.run(args, capture_output=True, text=True, shell=False, check=False)
    if done.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {done.stderr[-400:]}")


def _mean_rgb(path: Path) -> list[float]:
    from .qa_subject import decode_rgb_frames
    px = decode_rgb_frames(path)[0]
    return [sum(p[i] for p in px) / len(px) for i in range(3)]


def colour_gains(anchor: Path, clip: Path) -> tuple[float, float, float]:
    """Per-channel gain bringing the clip's first frame mean colour to the anchor's, clamped."""
    from .qa_subject import decode_rgb_frames
    a = decode_rgb_frames(anchor)[0]
    target = [sum(p[i] for p in a) / len(a) for i in range(3)]
    have = _mean_rgb(clip)
    lo, hi = GAIN_RANGE
    return tuple(round(min(hi, max(lo, t / h if h else 1.0)), 4) for t, h in zip(target, have))  # type: ignore[return-value]


def _frame_back(src: Path, out: Path, g: dict, index: str, tmp: Path) -> tuple[Path, Path]:
    """Extract source frame and the finished frame mapped back to source geometry (first/last)."""
    pick = ["-vf", "select=eq(n\\,0)"] if index == "first" else ["-sseof", "-0.2"]
    s_png, o_png = tmp / f"s_{index}.png", tmp / f"o_{index}.png"
    if index == "first":
        _run([_ffmpeg(), "-v", "error", "-y", "-i", str(src), *pick, "-frames:v", "1", str(s_png)])
    else:
        _run([_ffmpeg(), "-v", "error", "-y", *pick, "-i", str(src), "-update", "1", str(s_png)])
    if g["mode"] == "fit":
        undo = f"crop={g['scaled_w']}:{g['scaled_h']}:{g['pad_x']}:{g['pad_y']}"
    else:
        undo = f"pad={g['scaled_w']}:{g['scaled_h']}:{g['crop_x']}:{g['crop_y']}:black"
    back = f"{undo},scale={g['src_w']}:{g['src_h']}:flags=area"
    if index == "first":
        _run([_ffmpeg(), "-v", "error", "-y", "-i", str(out), "-vf", f"select=eq(n\\,0),{back}", "-frames:v", "1",
              str(o_png)])
    else:
        _run([_ffmpeg(), "-v", "error", "-y", "-sseof", "-0.2", "-i", str(out), "-vf", back, "-update", "1",
              str(o_png)])
    return s_png, o_png


def identity_check(src: Path, out: Path, g: dict) -> dict:
    """First/last frames of the finish, mapped back to source size, vs the source (grey MAD).
    In fill mode the cropped strips cannot be recovered, so only the visible region is compared."""
    import tempfile
    from .qa import decode_gray_frames
    result = {"tolerance": IDENTITY_MAD}
    with tempfile.TemporaryDirectory(prefix="mc-finish-") as tmp:
        for index in ("first", "last"):
            s_png, o_png = _frame_back(src, out, g, index, Path(tmp))
            s, o = decode_gray_frames(s_png)[0], decode_gray_frames(o_png)[0]
            if g["mode"] == "fill":  # ignore the rows/columns that were cropped away
                from .qa import H, W
                cy = round(g["crop_y"] / g["scaled_h"] * H) + 1
                cx = round(g["crop_x"] / g["scaled_w"] * W) + 1
                keep = [i for i in range(len(s)) if cy <= i // W < H - cy and cx <= i % W < W - cx]
                s, o = [s[i] for i in keep], [o[i] for i in keep]
            result[f"{index}_mad"] = round(sum(abs(a - b) for a, b in zip(s, o)) / len(s), 3)
    result["passed"] = result["first_mad"] <= IDENTITY_MAD and result["last_mad"] <= IDENTITY_MAD
    return result


def finish(src: str | Path, out: str | Path, *, target: str = "1080p", mode: str = "fit",
           denoise: bool = False, deblock: bool = False, sharpen: bool = False,
           match_anchor: str | Path | None = None, gains: tuple[float, float, float] | None = None,
           clamp: bool = True, crf: int = 16) -> dict:
    from .media import probe_video
    src, out = Path(src), Path(out)
    if out.exists():
        raise FileExistsError(f"{out} exists; refusing to overwrite")
    if target not in TARGETS:
        raise FinishError(f"target must be one of {sorted(TARGETS)}")
    p = probe_video(src)
    tw, th = TARGETS[target]
    if p["width"] > tw or p["height"] > th:
        raise FinishError(f"input {p['width']}x{p['height']} is larger than {target}; finishing never downsizes")
    before = sha256_file(src)
    if match_anchor:
        gains = colour_gains(Path(match_anchor), src)
    elif gains and clamp:
        gains = tuple(min(GAIN_RANGE[1], max(GAIN_RANGE[0], x)) for x in gains)  # type: ignore[assignment]
    g = geometry(p["width"], p["height"], target, mode)
    vf = chain(g, denoise=denoise, deblock=deblock, sharpen=sharpen, gains=gains)
    part = out.with_name(out.name + ".part.mp4")
    start = time.perf_counter()
    _run([_ffmpeg(), "-hide_banner", "-nostdin", "-v", "error", "-y", "-i", str(src), "-vf", vf,
          "-c:v", "libx264", "-crf", str(crf), "-color_primaries", "bt709", "-color_trc", "bt709",
          "-colorspace", "bt709", "-c:a", "copy", str(part)])
    os.replace(part, out)
    seconds = round(time.perf_counter() - start, 2)
    q = probe_video(out)
    if sha256_file(src) != before:
        raise RuntimeError("input changed during finishing")
    record = {"input": {"path": str(src), "sha256": before, "width": p["width"], "height": p["height"],
                        "frames": p["frame_count"], "duration_s": p["duration_s"]},
              "output": {"path": str(out), "sha256": sha256_file(out), "width": q["width"], "height": q["height"],
                         "frames": q["frame_count"], "duration_s": q["duration_s"]},
              "geometry": g, "steps": {"denoise": denoise, "deblock": deblock, "sharpen": sharpen},
              "colour_gains": list(gains) if gains else None, "chain": vf, "codec": "h264 (libx264)", "crf": crf,
              "colour_space": "bt709", "bit_depth": 8, "seconds": seconds, "device": "CPU (FFmpeg)",
              "frames_preserved": q["frame_count"] == p["frame_count"],
              "identity": identity_check(src, out, g),
              "note": "Geometric resampling only; no detail is invented."}
    Path(str(out) + ".finish.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def upscale_models(comfy_root: str | Path) -> list[str]:
    """Read-only listing of owner-installed learned upscalers (placeholder files ignored)."""
    folder = Path(comfy_root) / "models" / "upscale_models"
    if not folder.is_dir():
        return []
    return sorted(f.name for f in folder.iterdir()
                  if f.is_file() and f.suffix.lower() in (".pth", ".safetensors", ".pt", ".bin"))


def require_owner_approval(model: str) -> None:
    raise FinishError(f"learned upscaler {model!r} needs an owner-approved, hash-pinned ComfyUI workflow before use "
                      "(see specs/026-upscale-visual-finishing tasks T016); this tool never downloads models")
