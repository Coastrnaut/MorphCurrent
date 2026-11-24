"""Anchor composition geometry and parent/child continuity heuristics (F12).

Works on a small RGB copy decoded locally by FFmpeg. The subject is separated
from the (dark) background by an Otsu luminance threshold. Measures: centroid,
bounding extent, area, left-right mirror symmetry (a proxy for frontal vs profile
view) and a coarse palette. These are **heuristics**: they flag likely framing,
scale or viewpoint drift for human review; they do not understand anatomy.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .media import ProbeUnavailable

W, H = 128, 74
CENTROID_MAX = 0.08
EXTENT_RANGE = (0.75, 1.33)
SYMMETRY_DROP = 0.15
PALETTE_MAX = 60.0
MIN_AREA, MAX_AREA = 0.01, 0.90


def decode_rgb_small(path: str | Path, *, ffmpeg: str | None = None) -> list[tuple[int, int, int]]:
    executable = ffmpeg or shutil.which("ffmpeg")
    if not executable:
        raise ProbeUnavailable("ffmpeg not found on PATH")
    args = [executable, "-hide_banner", "-nostdin", "-v", "error", "-i", str(path), "-frames:v", "1",
            "-vf", f"scale={W}:{H}:flags=area,format=rgb24", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    done = subprocess.run(args, capture_output=True, timeout=60, shell=False, check=False)
    if done.returncode != 0 or len(done.stdout) < W * H * 3:
        raise RuntimeError(f"ffmpeg could not decode {path}: {done.stderr.decode(errors='replace')[:200]}")
    data = done.stdout[:W * H * 3]
    return [tuple(data[i:i + 3]) for i in range(0, len(data), 3)]  # type: ignore[misc]


def _otsu(values: list[int]) -> int:
    hist = [0] * 256
    for v in values:
        hist[v] += 1
    total, sum_all = len(values), sum(i * h for i, h in enumerate(hist))
    best, threshold, w_b, sum_b = -1.0, 0, 0, 0
    for t in range(256):
        w_b += hist[t]
        if not w_b or w_b == total:
            continue
        sum_b += t * hist[t]
        m_b, m_f = sum_b / w_b, (sum_all - sum_b) / (total - w_b)
        between = w_b * (total - w_b) * (m_b - m_f) ** 2
        if between > best:
            best, threshold = between, t
    return threshold


def anchor_geometry(pixels: list[tuple[int, int, int]], width: int = W, height: int = H) -> dict:
    lum = [round(0.299 * r + 0.587 * g + 0.114 * b) for r, g, b in pixels]
    threshold = max(_otsu(lum), 24)  # never treat near-black noise as subject
    mask = [v > threshold for v in lum]
    area = sum(mask) / len(mask)
    result: dict = {"width": width, "height": height, "threshold": threshold, "area": round(area, 4),
                    "method": "heuristic (Otsu luminance mask on dark background)"}
    if area > MAX_AREA or area < MIN_AREA:
        result["mask_unreliable" if area > MAX_AREA else "subject_too_small"] = True
        if area == 0:
            return result
    xs = [i % width for i, m in enumerate(mask) if m]
    ys = [i // width for i, m in enumerate(mask) if m]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    # robust extent: 2nd..98th percentile, so stray glints don't inflate the box
    sx, sy = sorted(xs), sorted(ys)
    pick = lambda arr, q: arr[min(len(arr) - 1, int(q * len(arr)))]  # noqa: E731
    ext_w = (pick(sx, 0.98) - pick(sx, 0.02) + 1) / width
    ext_h = (pick(sy, 0.98) - pick(sy, 0.02) + 1) / height
    # mirror symmetry of the mask about the subject's own vertical centre line
    axis = round(cx)
    agree = total = 0
    for y in range(height):
        row = mask[y * width:(y + 1) * width]
        for dx in range(1, width):
            left, right = axis - dx, axis + dx
            if left < 0 or right >= width:
                break
            if row[left] or row[right]:
                total += 1
                agree += row[left] == row[right]
    subject = [p for p, m in zip(pixels, mask) if m]
    palette = [round(sum(c[k] for c in subject) / len(subject)) for k in range(3)]
    result.update(centroid=[round(cx / width, 4), round(cy / height, 4)],
                  extent=[round(ext_w, 4), round(ext_h, 4)],
                  symmetry=round(agree / total, 4) if total else 1.0,
                  mean_colour=palette)
    return result


def image_geometry(path: str | Path) -> dict:
    return {"file": str(path), **anchor_geometry(decode_rgb_small(path))}


def compare_geometry(parent: dict, child: dict) -> dict:
    flags: list[str] = []
    for side, geo in (("parent", parent), ("child", child)):
        for key in ("mask_unreliable", "subject_too_small"):
            if geo.get(key):
                flags.append(f"{key}:{side}")
    out: dict = {"method": "heuristic", "flags": flags}
    if "centroid" in parent and "centroid" in child:
        shift = ((parent["centroid"][0] - child["centroid"][0]) ** 2 +
                 (parent["centroid"][1] - child["centroid"][1]) ** 2) ** 0.5
        ratio = [round(child["extent"][i] / parent["extent"][i], 3) if parent["extent"][i] else None
                 for i in (0, 1)]
        sym_delta = round(child["symmetry"] - parent["symmetry"], 4)
        colour = round(sum((a - b) ** 2 for a, b in zip(parent["mean_colour"], child["mean_colour"])) ** 0.5, 1)
        out.update(centroid_shift=round(shift, 4), extent_ratio=ratio,
                   area_ratio=round(child["area"] / parent["area"], 3) if parent["area"] else None,
                   symmetry_delta=sym_delta, palette_distance=colour)
        if shift > CENTROID_MAX:
            flags.append("centroid_shift")
        if any(r is not None and not EXTENT_RANGE[0] <= r <= EXTENT_RANGE[1] for r in ratio):
            flags.append("scale_change")
        if sym_delta < -SYMMETRY_DROP:
            flags.append("symmetry_drop")
        if colour > PALETTE_MAX:
            flags.append("palette_shift")
    out["review"] = "required" if flags else "recommended"
    return out


def compare_images(parent: str | Path, child: str | Path) -> dict:
    p, c = image_geometry(parent), image_geometry(child)
    return {"parent": p, "child": c, "comparison": compare_geometry(p, c)}
