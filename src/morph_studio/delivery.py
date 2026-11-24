"""Versioned multi-format delivery presets with measured verification (F30). Local FFmpeg only.

Each preset is a deterministic recipe - optional frame-rate step (F25 blend), geometry (F26 Lanczos fit, or
a centre crop at full height to the target aspect), an audio policy (copy / drop / owner-licensed track) and
fixed encode settings - identified by a recipe checksum. ``deliver_one`` writes a new file plus
``<file>.delivery.json`` and probes the result against the preset's expectations; crop presets also report
whether the subject in the first and last frames (the approved anchors) stays inside the crop's safe area.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

from .cache import sha256_file

RECIPE_VERSION = 1
SAFE_MARGIN = 0.05
VIDEO = {"libx264": ["-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
                     "-color_trc", "bt709", "-colorspace", "bt709"],
         "mpeg4": ["-c:v", "mpeg4", "-q:v", "2", "-pix_fmt", "yuv420p"]}
CODEC_NAME = {"libx264": "h264", "mpeg4": "mpeg4"}
AUDIO = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
AUDIO_SLACK_S = 0.025  # AAC priming/padding
PRESETS = {
    "landscape-1080p": {"target": [1920, 1080], "geometry": "fit", "fps": None, "audio": "copy"},
    "vertical-1080x1920": {"target": [1080, 1920], "geometry": "crop", "aspect": "9:16", "fps": None, "audio": "copy"},
    "square-1080": {"target": [1080, 1080], "geometry": "crop", "aspect": "1:1", "fps": None, "audio": "copy"},
    "video-only-1080p": {"target": [1920, 1080], "geometry": "fit", "fps": None, "audio": "drop"},
    "licensed-audio-1080p": {"target": [1920, 1080], "geometry": "fit", "fps": None, "audio": "licensed"},
    "hires-1440p": {"target": [2560, 1440], "geometry": "fit", "fps": None, "audio": "copy"},
    "smooth-24fps-1080p": {"target": [1920, 1080], "geometry": "fit", "fps": 24, "audio": "copy"},
}


class DeliveryError(ValueError):
    pass


def recipe(name: str) -> dict:
    if name not in PRESETS:
        raise DeliveryError(f"unknown preset {name!r}; valid: {', '.join(PRESETS)}")
    p = PRESETS[name]
    steps = [f"fps: {'blend to ' + str(p['fps']) if p['fps'] else 'none (source rate)'}",
             f"geometry: {'Lanczos fit + black pad' if p['geometry'] == 'fit' else 'centre crop ' + p['aspect'] + ' at full height + Lanczos scale'} to {p['target'][0]}x{p['target'][1]}",
             f"audio: {p['audio']}", "encode: libx264 crf 16 yuv420p bt709 (fallback mpeg4 q2); aac 192k 48 kHz"]
    return {"version": RECIPE_VERSION, "preset": name, **p, "steps": steps}


def recipe_sha256(name: str) -> str:
    return hashlib.sha256(json.dumps(recipe(name), sort_keys=True).encode("utf-8")).hexdigest()


def _aspect(aspect: str) -> Fraction:
    w, h = aspect.split(":")
    return Fraction(int(w), int(h))


def crop_rect(src_w: int, src_h: int, aspect: str) -> tuple[int, int, int, int]:
    """(w, h, x, y) of a centre crop at full height (even sizes) for the target aspect."""
    a = _aspect(aspect)
    w = min(src_w, int(round(src_h * a / 2)) * 2)
    return w, src_h, (src_w - w) // 2, 0


def safe_area(geo: dict, src_w: int, src_h: int, aspect: str, margin: float = SAFE_MARGIN) -> str:
    """inside / outside / unknown: subject box (centroid +/- extent/2) within the crop's inset safe area."""
    if "centroid" not in geo:
        return "unknown"
    cw = crop_rect(src_w, src_h, aspect)[0] / src_w
    (cx, cy), (ex, ey) = geo["centroid"], geo["extent"]
    x0, x1 = 0.5 - cw / 2 + margin * cw, 0.5 + cw / 2 - margin * cw
    inside = cx - ex / 2 >= x0 - 1e-9 and cx + ex / 2 <= x1 + 1e-9 and cy - ey / 2 >= margin - 1e-9 \
        and cy + ey / 2 <= 1 - margin + 1e-9
    return "inside" if inside else "outside"


def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise DeliveryError("ffmpeg not found on PATH")
    return exe


@lru_cache(maxsize=1)
def _encoder_list() -> frozenset:
    done = subprocess.run([_ffmpeg(), "-hide_banner", "-encoders"], capture_output=True, text=True,
                          errors="replace", shell=False, check=False)
    names = set()
    for line in done.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and len(parts[0]) == 6 and parts[0][0] in "VAS":
            names.add(parts[1])
    return frozenset(names)


def available_encoders() -> set:
    return set(_encoder_list())


def _run(args: list[str]) -> None:
    done = subprocess.run(args, capture_output=True, text=True, errors="replace", shell=False, check=False)
    if done.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {done.stderr[-400:]}")


def _audio_duration(path: Path) -> float | None:
    """Duration of the first audio stream (None when there is none)."""
    exe = shutil.which("ffprobe")
    done = subprocess.run([exe, "-v", "error", "-select_streams", "a:0", "-show_entries",
                           "stream=duration:format=duration", "-of", "json", str(path)],
                          capture_output=True, text=True, errors="replace", shell=False, check=False)
    data = json.loads(done.stdout or "{}")
    streams = data.get("streams") or []
    if not streams:
        return None
    value = streams[0].get("duration") or (data.get("format") or {}).get("duration")
    return float(value) if value not in (None, "N/A") else 0.0


def _measure(path: Path) -> dict:
    from .media import probe_video
    p = probe_video(path)
    audio = _audio_duration(path)
    return {"path": str(path), "sha256": sha256_file(path), "width": p["width"], "height": p["height"],
            "fps": p["fps"], "codec": p["codec"], "frames": p["frame_count"], "duration_s": p["duration_s"],
            "audio": audio is not None, "audio_duration_s": audio}


def verify(expected: dict, measured: dict) -> dict:
    mismatches = []
    for key in ("width", "height", "codec", "audio"):
        if measured.get(key) != expected[key]:
            mismatches.append({"key": key, "expected": expected[key], "measured": measured.get(key)})
    if measured.get("fps") is None or abs(measured["fps"] - expected["fps"]) > 1e-3:
        mismatches.append({"key": "fps", "expected": expected["fps"], "measured": measured.get("fps")})
    tol = expected["frame_s"] + AUDIO_SLACK_S
    if measured.get("duration_s") is None or abs(measured["duration_s"] - expected["duration_s"]) > tol:
        mismatches.append({"key": "duration_s", "expected": expected["duration_s"],
                           "measured": measured.get("duration_s")})
    return {"passed": not mismatches, "mismatches": mismatches}


def _anchor_frames(src: Path, tmp: Path) -> tuple[Path, Path]:
    first, last = tmp / "first.png", tmp / "last.png"
    _run([_ffmpeg(), "-v", "error", "-y", "-i", str(src), "-frames:v", "1", str(first)])
    _run([_ffmpeg(), "-v", "error", "-y", "-sseof", "-0.25", "-i", str(src), "-update", "1", str(last)])
    return first, last


def deliver_one(src: str | Path, out_dir: str | Path, preset: str, *, audio: str | Path | None = None,
                audio_licensed: bool = False, audio_offset: float = 0.0) -> dict:
    from .finishing import TARGETS, chain, geometry
    from .geometry import image_geometry
    rec_def = recipe(preset)
    src, out_dir = Path(src), Path(out_dir)
    out = out_dir / f"{src.stem}_{preset}.mp4"
    if out.exists():
        raise FileExistsError(f"{out} exists; refusing to overwrite")
    tw, th = rec_def["target"]
    source = _measure(src)
    if rec_def["geometry"] == "fit" and (source["width"] > tw or source["height"] > th):
        raise DeliveryError(f"input {source['width']}x{source['height']} is larger than {preset}; deliveries never downsize")
    if rec_def["geometry"] == "crop":
        cw, ch, _, _ = crop_rect(source["width"], source["height"], rec_def["aspect"])
        if cw > tw or ch > th:
            raise DeliveryError(f"crop {cw}x{ch} is larger than {preset}; deliveries never downsize")
    audio_path = None
    if rec_def["audio"] == "licensed":
        if not audio:
            raise DeliveryError("licensed-audio preset needs --audio")
        if not audio_licensed:
            raise DeliveryError("the audio track must be marked licensed by the owner (--audio-licensed)")
        audio_path = Path(audio)
        if not audio_path.is_file():
            raise DeliveryError(f"audio file not found: {audio_path}")
        available = (_audio_duration(audio_path) or 0.0) - audio_offset
        if available + 1 / (source["fps"] or 16) < (source["duration_s"] or 0):
            raise DeliveryError(f"licensed audio after the {audio_offset}s offset is {available:.3f}s, shorter than the "
                                f"picture ({source['duration_s']:.3f}s); refusing to pad silently")
    encoders = available_encoders()
    video_encoder = "libx264" if "libx264" in encoders else "mpeg4"
    out_dir.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="mc-deliver-") as tmpname:
        tmp = Path(tmpname)
        work, fps = src, source["fps"]
        fps_step = "none (source rate)"
        if rec_def["fps"] and abs((source["fps"] or 0) - rec_def["fps"]) <= 1e-3:
            fps_step = f"none (already {rec_def['fps']} fps)"
        if rec_def["fps"] and abs((source["fps"] or 0) - rec_def["fps"]) > 1e-3:
            fps_step = f"blend {source['fps']:g}->{rec_def['fps']}"
            from .interpolate import convert
            work = tmp / "rate.mp4"
            convert(src, work, fps=rec_def["fps"], method="blend")
            fps = rec_def["fps"]
        crop_info = None
        if rec_def["geometry"] == "fit":
            target_name = next(k for k, v in TARGETS.items() if v == (tw, th))
            g = geometry(source["width"], source["height"], target_name, "fit")
            vf = chain(g)
        else:
            cw, ch, cx, cy = crop_rect(source["width"], source["height"], rec_def["aspect"])
            vf = f"crop={cw}:{ch}:{cx}:{cy},scale={tw}:{th}:flags=lanczos,setsar=1,format=yuv420p"
            first, last = _anchor_frames(src, tmp)
            anchors = {k: safe_area(image_geometry(p), source["width"], source["height"], rec_def["aspect"])
                       for k, p in (("first", first), ("last", last))}
            crop_info = {"rect": {"w": cw, "h": ch, "x": cx, "y": cy}, "anchors": anchors}
            if "outside" in anchors.values():
                crop_info["warning"] = "subject leaves the crop's safe area; consider reframing before publishing"
        args = [_ffmpeg(), "-hide_banner", "-nostdin", "-v", "error", "-y", "-i", str(work)]
        if audio_path:
            args += ["-ss", f"{audio_offset:.6f}", "-i", str(audio_path)]
        args += ["-vf", vf, *VIDEO[video_encoder]]
        if rec_def["audio"] == "drop" or (rec_def["audio"] == "copy" and not source["audio"]):
            args += ["-an"]
        elif audio_path:
            args += ["-map", "0:v:0", "-map", "1:a:0", *AUDIO, "-t", f"{source['duration_s']:.6f}"]
        else:
            args += ["-map", "0:v:0", "-map", "0:a:0", *AUDIO]
        part = out.with_name(out.name + ".part.mp4")
        try:
            _run([*args, str(part)])
            os.replace(part, out)
        finally:
            part.unlink(missing_ok=True)
    if sha256_file(src) != source["sha256"]:
        raise RuntimeError("input changed during delivery")
    measured = _measure(out)
    expect_audio = rec_def["audio"] == "licensed" or (rec_def["audio"] == "copy" and source["audio"])
    expected = {"width": tw, "height": th, "fps": fps, "codec": CODEC_NAME[video_encoder], "audio": expect_audio,
                "duration_s": source["duration_s"], "frame_s": 1 / fps if fps else 0.0625}
    record = {"preset": preset, "recipe_version": RECIPE_VERSION, "recipe_sha256": recipe_sha256(preset),
              "steps": rec_def["steps"], "fps_step": fps_step, "filter": vf, "input": source, "output": measured,
              "encoder": {"video": video_encoder, "fallback": video_encoder != "libx264", "audio": "aac"},
              "expected": expected, "verification": verify(expected, measured), "crop": crop_info,
              "audio_source": ({"path": str(audio_path), "sha256": sha256_file(audio_path), "offset_s": audio_offset,
                                "licensed": True} if audio_path else None),
              "seconds": round(time.perf_counter() - start, 2), "device": "CPU (FFmpeg)",
              "note": "Geometric resampling only; no detail is invented."}
    Path(str(out) + ".delivery.json").write_text(json.dumps(record, indent=2, ensure_ascii=True) + "\n",
                                                 encoding="utf-8")
    return record


def deliver(src: str | Path, out_dir: str | Path, presets: list[str], **kwargs) -> dict:
    """Run each preset; one preset's refusal or failure never stops the others."""
    results, errors = [], []
    for name in presets:
        try:
            results.append(deliver_one(src, out_dir, name, **kwargs))
        except (DeliveryError, FileExistsError, RuntimeError) as exc:
            errors.append({"preset": name, "error": str(exc)})
    return {"results": results, "errors": errors}
