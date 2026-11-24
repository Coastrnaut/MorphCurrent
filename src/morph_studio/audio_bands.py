"""Music-visualizer-style band loudness and a timeline visualisation (F15).

Independent Python implementation of classic music-visualizer band loudness. For every video
frame: Hann-windowed 1024-point FFT, sum the bass / mid / treble bands (0–3.7,
3.7–7.4 and 7.4–11 kHz — the first, second and third sixth of a 44.1 kHz spectrum),
then express each band relative to its long-term average. ``bass`` is the instant
value and ``bass_att`` the short-term smoothed one; both hover around 1.0 and > 1.3 is
a loud hit. Decay rates are frame-rate independent (``rate ** (30 * dt)``).
"""
from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

from .audio import load_mono_at

BAND_SR = 22050
FFT_N = 1024
BANDS_HZ = {"bass": (0.0, 3675.0), "mid": (3675.0, 7350.0), "treb": (7350.0, 11025.0)}


def fft_magnitudes(frame: list[float]) -> list[float]:
    """Magnitudes of the first N/2 bins (iterative radix-2 FFT; N a power of two)."""
    n = len(frame)
    a = [complex(x, 0.0) for x in frame]
    j = 0
    for i in range(1, n):  # bit-reversal permutation
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j |= bit
        if i < j:
            a[i], a[j] = a[j], a[i]
    size = 2
    while size <= n:
        half = size // 2
        tw = [complex(math.cos(-2 * math.pi * k / size), math.sin(-2 * math.pi * k / size)) for k in range(half)]
        for start in range(0, n, size):
            for k in range(half):
                u, v = a[start + k], a[start + k + half] * tw[k]
                a[start + k], a[start + k + half] = u + v, u - v
        size *= 2
    return [abs(c) for c in a[: n // 2]]


def band_levels(samples: list[float], fps: float = 30.0, rate: int = BAND_SR, on_frame=None) -> list[dict]:
    """Per-frame relative loudness for bass / mid / treble (relative-to-long-average semantics).

    ``on_frame(row, magnitudes)`` (optional) sees each frame's spectrum so callers (F15 US5 feature
    track) can derive more features from the same FFT; it may add keys to ``row``."""
    window = [0.5 - 0.5 * math.cos(2 * math.pi * i / (FFT_N - 1)) for i in range(FFT_N)]
    bin_hz = rate / FFT_N
    ranges = {b: (int(lo / bin_hz), max(int(lo / bin_hz) + 1, int(hi / bin_hz)))
              for b, (lo, hi) in BANDS_HZ.items()}
    dt = 1.0 / fps
    state = {b: {"avg": 0.0, "long": 0.0} for b in BANDS_HZ}
    frames = []
    for f in range(int(len(samples) / rate * fps)):
        start = int(f * rate / fps) - FFT_N // 2
        chunk = [samples[i] if 0 <= i < len(samples) else 0.0 for i in range(start, start + FFT_N)]
        mags = fft_magnitudes([x * w for x, w in zip(chunk, window)])
        row: dict = {"t": round(f * dt, 4)}
        for band, (lo, hi) in ranges.items():
            cur = sum(mags[lo:hi])
            s = state[band]
            r_avg = (0.2 if cur > s["avg"] else 0.5) ** (30 * dt)
            s["avg"] = s["avg"] * r_avg + cur * (1 - r_avg)
            r_long = (0.9 if f < 50 else 0.992) ** (30 * dt)
            s["long"] = s["long"] * r_long + cur * (1 - r_long)
            row[band] = round(1.0 if abs(s["long"]) < 1e-3 else cur / s["long"], 4)
            row[f"{band}_att"] = round(1.0 if abs(s["long"]) < 1e-3 else s["avg"] / s["long"], 4)
        row["vol"] = round((row["bass"] + row["mid"] + row["treb"]) / 3, 4)
        if on_frame is not None:
            on_frame(row, mags)
        frames.append(row)
    return frames


def analyze_bands(path: str | Path, fps: float = 30.0) -> list[dict]:
    return band_levels(load_mono_at(path, BAND_SR), fps=fps)


def band_hits(levels: list[dict], band: str = "bass", threshold: float = 1.3,
              min_gap_s: float = 0.2) -> list[float]:
    """Rising-edge times where a band exceeds ``threshold`` x its long-term level."""
    hits: list[float] = []
    for prev, row in zip(levels, levels[1:]):
        if row[band] > threshold >= prev[band] and (not hits or row["t"] - hits[-1] >= min_gap_s):
            hits.append(row["t"])
    return hits


def _png(width: int, height: int, rows: list[list[list[int]]]) -> bytes:
    raw = b"".join(b"\x00" + bytes(c for px in row for c in px) for row in rows)

    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def render_timeline_png(levels: list[dict], out: Path, *, beats: list[float] | None = None,
                        boundaries: list[float] | None = None, sections: list[float] | None = None,
                        height: int = 180, px_per_frame: int = 2) -> Path:
    """Bass (red), mid (green), treble (blue) relative levels; beats as dotted grey
    ticks; musical sections as amber lines; bridge boundaries as white lines; dim line
    at 1.0. Never overwrites."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    width = max(1, len(levels) * px_per_frame)
    img = [[[10, 10, 14] for _ in range(width)] for _ in range(height)]
    duration = levels[-1]["t"] if levels else 0.0

    def y_of(v: float) -> int:  # relative level 0..2.5 -> bottom..top
        return max(0, min(height - 1, height - 1 - int(min(v, 2.5) / 2.5 * (height - 1))))

    def x_of(t: float) -> int:
        return int(t / duration * (width - 1)) if duration else 0

    for x in range(width):
        img[y_of(1.0)][x] = [45, 45, 55]
    for t in beats or []:
        if 0 <= t <= duration:
            for y in range(0, height, 3):
                img[y][x_of(t)] = [95, 95, 95]
    for t in sections or []:  # musical sections/phrases: amber
        if 0 <= t <= duration:
            for y in range(height):
                img[y][x_of(t)] = [240, 180, 40]
    for t in boundaries or []:
        if 0 <= t <= duration:
            for y in range(height):
                img[y][x_of(t)] = [235, 235, 235]
    for band, colour in (("bass", [230, 70, 60]), ("mid", [80, 210, 90]), ("treb", [80, 140, 240])):
        prev = None
        for i, row in enumerate(levels):
            y = y_of(row[band])
            lo, hi = (min(prev, y), max(prev, y)) if prev is not None else (y, y)
            for dx in range(px_per_frame):
                for yy in range(lo, hi + 1):
                    img[yy][i * px_per_frame + dx] = colour
            prev = y
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(_png(width, height, img))
    return out
