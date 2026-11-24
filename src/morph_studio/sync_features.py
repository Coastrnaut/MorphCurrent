"""Layered music-synchronization foundation (F15 US5; strategy in docs/MUSIC_SYNC.md).

A real-time music visualizer stays in sync with any song without a beat grid: it follows band
energies normalized to their own long-term level, and onsets. This module computes the same kind of
**feature track** per video frame (relative bass/mid/treb with smoothed versions, volume, spectral
flux, onset strength, brightness, sections), then plans **event-locked anchors** (onsets, section
starts, energy peaks; downbeats only as an optional boost), describes each bridge's **character**
and computes an **energy-warp** time map per bridge (applied later by F25). Offline; heuristic.
"""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

from .audio_bands import BAND_SR, band_levels

GRID = 4
MIN_FRAMES, MAX_FRAMES, PREFERRED = 33, 81, 65
LENGTH_PENALTY = 1.5  # calibrated on the Mozart track: 0.5 packed 129 short bridges
SECTION_SCORE, DOWNBEAT_BOOST, ONSET_REF = 1.0, 0.25, 12.0  # scores normalized to <= 1
WARP_MIN, WARP_MAX, WARP_FLOOR = 0.5, 2.0, 0.2
VERSION = 1


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def feature_track(samples: list[float], fps: float = 16.0, rate: int = BAND_SR) -> dict:
    prev: list[float] | None = None
    fluxes: list[float] = []

    def extra(row: dict, mags: list[float]) -> None:
        nonlocal prev
        flux = 0.0 if prev is None else sum(max(0.0, m - p) for m, p in zip(mags, prev))
        total = sum(mags) or 1.0
        row["brightness"] = round(sum(i * m for i, m in enumerate(mags)) / total / len(mags), 4)
        row["flux"] = round(flux, 4)
        fluxes.append(flux)
        prev = mags

    frames = band_levels(samples, fps=fps, rate=rate, on_frame=extra)
    positive = sorted(f for f in fluxes if f > 0)
    median = positive[len(positive) // 2] if positive else 1.0
    for row in frames:
        row["vol_att"] = round((row["bass_att"] + row["mid_att"] + row["treb_att"]) / 3, 4)
        row["onset"] = round(row["flux"] / median if median else 0.0, 4)
    return {"fps": fps, "frames": frames, "sections": _sections(samples, rate)}


def _sections(samples: list[float], rate: int) -> list[dict]:
    from .beat_analysis import SR, sections, subband_frames
    step = max(1, round(rate / SR))
    _, loudness, brightness = subband_frames(samples[::step])
    return sections(loudness, brightness)


def track_record(path: str | Path, fps: float = 16.0) -> dict:
    from .audio import load_mono_at
    p = Path(path)
    fps = float(fps)  # 16 and 16.0 must hash identically
    track = feature_track(load_mono_at(p, BAND_SR), fps=fps)
    record = {"version": VERSION, "audio": p.name, "audio_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
              "settings": {"fps": fps, "sample_rate": BAND_SR, "fft": 1024}, **track}
    record["content_sha256"] = hashlib.sha256(_canonical(record).encode("utf-8")).hexdigest()
    return record


def _local_max(values: list[float], k: int, radius: int) -> bool:
    lo, hi = max(0, k - radius), min(len(values), k + radius + 1)
    return values[k] == max(values[lo:hi]) and (k == lo or values[k] > values[k - 1])


def events(track: dict, beatmap: dict | None = None) -> list[dict]:
    """Scored event candidates (spec Clarifications)."""
    fps = track["fps"]
    frames = track["frames"]
    onset = [r["onset"] for r in frames]
    vol_att = [r["vol_att"] for r in frames]
    med = statistics.median(onset) if onset else 0.0
    mad = statistics.median(abs(o - med) for o in onset) if onset else 0.0
    limit = max(med + 1.5 * mad, 3.0)  # onset is already flux / median flux: require >= 3x typical change
    out: list[dict] = []
    for k in range(1, len(frames)):
        if onset[k] > limit and onset[k] > 0 and _local_max(onset, k, 3):
            out.append({"frame": k, "kind": "onset", "score": round(min(1.0, onset[k] / ONSET_REF), 3)})
        if vol_att[k] > 1.1 and _local_max(vol_att, k, 8):
            out.append({"frame": k, "kind": "energy_peak", "score": round(min(1.0, vol_att[k] - 1), 3)})
    for s in track.get("sections", []):
        out.append({"frame": int(round(s["t"] * fps)), "kind": "section", "score": SECTION_SCORE})
    if beatmap and (beatmap.get("verified") or beatmap.get("confidence", 0) >= 0.5):
        for t in beatmap.get("downbeats", []):
            out.append({"frame": int(round(t * fps)), "kind": "downbeat", "score": DOWNBEAT_BOOST})
    return sorted(out, key=lambda e: (e["frame"], e["kind"]))


def plan_anchors(track: dict, evts: list[dict], *, min_frames: int = MIN_FRAMES, max_frames: int = MAX_FRAMES,
                 preferred: int = PREFERRED) -> dict:
    """Dynamic program over 4-frame grid points: maximize event score at anchors minus a length penalty."""
    n = len(track["frames"])
    last = n - 1
    if last < min_frames - 1:
        raise ValueError(f"song is shorter than one bridge ({n} frames < {min_frames})")
    end = last // GRID * GRID  # final anchor on the last grid point at/before the end; a hold covers the rest
    grid = list(range(0, end + 1, GRID))
    score = {g: 0.0 for g in grid}
    best_event: dict[int, dict] = {}
    for e in evts:
        for g in (e["frame"] - e["frame"] % GRID, e["frame"] - e["frame"] % GRID + GRID):
            dist = abs(g - e["frame"])
            # nearer grid points score higher; ties go to the earlier point (onsets register up to
            # half a frame late because a frame's analysis window is centred after the attack)
            weighted = e["score"] * (1 - 0.05 * dist - (0.01 if g > e["frame"] else 0.0))
            if g in score and dist <= 2 and weighted > score[g]:
                score[g], best_event[g] = weighted, e
    lengths = range(min_frames - 1, max_frames, GRID)  # frame distance between anchors (L - 1)
    best = {0: (0.0, None)}
    for g in grid[1:]:
        cand = None
        for d in lengths:
            p = g - d
            if p in best and best[p][0] is not None:
                value = best[p][0] + score[g] - LENGTH_PENALTY * abs(d + 1 - preferred) / 64
                if cand is None or value > cand[0] + 1e-12:
                    cand = (value, p)
        if cand:
            best[g] = cand
    if end not in best:
        raise ValueError("no valid anchor sequence covers the song with the allowed bridge lengths")
    chain, g = [], end
    while g is not None:
        chain.append(g)
        g = best[g][1]
    chain.reverse()
    fps = track["fps"]
    anchors = [{"frame": g, "t": round(g / fps, 4), "event": best_event.get(g, {}).get("kind"),
                "score": round(score[g], 3)} for g in chain]
    return {"anchors": anchors, "total": round(best[end][0], 3)}


def _mean(track: dict, key: str, a: int, b: int) -> float:
    rows = track["frames"][a:b + 1]
    return sum(r[key] for r in rows) / len(rows)


def bridge_character(track: dict, a: int, b: int) -> list[str]:
    a, b = max(0, a), min(len(track["frames"]) - 1, b)
    words = []
    bass, treb = _mean(track, "bass_att", a, b), _mean(track, "treb_att", a, b)
    if bass >= 1.15 and bass - treb >= 0.10:
        words.append("bass-heavy")
    if treb >= 1.15 and treb - bass >= 0.10:
        words.append("treble-heavy")
    q = max(1, (b - a + 1) // 4)
    rise = _mean(track, "vol_att", b - q + 1, b) - _mean(track, "vol_att", a, a + q - 1)
    if rise > 0.15:
        words.append("building")
    elif rise < -0.15:
        words.append("settling")
    return words or ["steady"]


def energy_warp(track: dict, a: int, b: int) -> dict:
    """Output frame i of the bridge shows source position map[i]; endpoints pinned, speed 0.5x-2x."""
    frames = track["frames"]
    w = [max(frames[min(k, len(frames) - 1)]["vol_att"], WARP_FLOOR) for k in range(a, b)]
    speed = [1.0] * len(w)
    if w:
        mean = sum(w) / len(w)
        speed = [x / mean for x in w]
        n = len(speed)
        for _ in range(50):  # water-filling: clamp, then rescale only the frames still free
            speed = [min(WARP_MAX, max(WARP_MIN, s)) for s in speed]
            total = sum(speed)
            if abs(total - n) < 1e-9:
                break
            # short of the bridge length: frames below the cap may speed up; over: frames above the floor slow down
            free = [i for i, s in enumerate(speed) if (s < WARP_MAX if total < n else s > WARP_MIN)]
            free_set = set(free)
            fixed = sum(s for i, s in enumerate(speed) if i not in free_set)
            free_sum = sum(speed[i] for i in free)
            if not free_sum:
                break
            k = (n - fixed) / free_sum
            for i in free:
                speed[i] *= k
    pos, exact = 0.0, [0.0]
    for s in speed:
        pos += s
        exact.append(pos)
    scale = (b - a) / pos if pos else 1.0  # remove float drift so the last frame is pinned exactly
    mapping = [round(x * scale, 6) for x in exact]
    mapping[-1] = float(b - a)
    return {"min_speed": round(min(speed), 3) if speed else 1.0, "max_speed": round(max(speed), 3) if speed else 1.0,
            "map": mapping, "note": "applied by F25 retiming with interpolation; anchors pinned"}


def sync_plan(record: dict, beatmap: dict | None = None, *, preferred: int = PREFERRED,
              min_frames: int = MIN_FRAMES, max_frames: int = MAX_FRAMES) -> dict:
    planned = plan_anchors(record, events(record, beatmap), min_frames=min_frames, max_frames=max_frames,
                           preferred=preferred)
    anchors = planned["anchors"]
    bridges = []
    for x, y in zip(anchors, anchors[1:]):
        bridges.append({"from_frame": x["frame"], "to_frame": y["frame"], "frames": y["frame"] - x["frame"] + 1,
                        "character": bridge_character(record, x["frame"], y["frame"]),
                        "warp": energy_warp(record, x["frame"], y["frame"])})
    fps = record["fps"]
    song_s = round(len(record["frames"]) / fps, 4)
    plan = {"version": VERSION, "track_sha256": record.get("content_sha256"), "fps": fps,
            "settings": {"preferred": preferred, "min_frames": min_frames, "max_frames": max_frames,
                         "beatmap": bool(beatmap)},
            "anchors": anchors, "bridges": bridges,
            "coverage": {"song_s": song_s, "last_anchor_s": anchors[-1]["t"],
                         "hold_s": round(max(0.0, song_s - anchors[-1]["t"]), 4)},
            "summary": {"bridges": len(bridges), "anchors": len(anchors),
                        "events_at_anchors": sum(a["event"] is not None for a in anchors)}}
    plan["plan_sha256"] = hashlib.sha256(_canonical(plan).encode("utf-8")).hexdigest()
    return plan
