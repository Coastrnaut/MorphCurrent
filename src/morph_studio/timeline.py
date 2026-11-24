"""Exact timing convention: anchor timestamps span (L - 1) / FPS."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_UP

from .schema import Storyboard


@dataclass(frozen=True)
class BridgePlan:
    from_anchor: str
    to_anchor: str
    frames: int
    fps: int
    requested_seconds: float
    actual_span_seconds: float
    timing_error_seconds: float
    seed: int
    candidates: int
    transition_prompt: str


def frame_count_for_beats(
    beats: float, bpm: float, fps: int, max_frames: int = 81
) -> int:
    """Nearest supported Wan length, ties rounded up; never exceed max frames.

    A bridge's timestamp span is (length-1)/fps. Thus 8 beats at 120 BPM
    and 16 FPS map to 65 frames with a 4-second endpoint-to-endpoint span.
    """
    if beats <= 0 or bpm <= 0 or fps < 1:
        raise ValueError("beats/bpm/fps must be strictly positive")
    if max_frames < 5 or (max_frames - 1) % 4:
        raise ValueError("max_frames must be 4n+1 and at least 5")
    wanted_intervals = Decimal(str(beats)) * Decimal(60) * Decimal(fps) / Decimal(str(bpm))
    n = int((wanted_intervals / 4).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if n < 1 or 4 * n + 1 > max_frames:
        raise ValueError(
            "requested beat duration is outside the configured Wan frame limit; "
            "use shorter beat span, segment the transition or explicitly retime"
        )
    return 4 * n + 1


def derived_seed(master_seed: int, key: str) -> int:
    digest = hashlib.sha256(f"{master_seed}:{key}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big") & ((1 << 63) - 1)


def compile_timeline(storyboard: Storyboard) -> list[BridgePlan]:
    items = []
    for i, t in enumerate(storyboard.transitions):
        if t.frames is not None:  # F32 frame-locked: exact length from the sync plan, zero timing error
            frames = t.frames
            requested = actual = (frames - 1) / storyboard.render.generation_fps
        else:
            assert storyboard.audio.bpm is not None  # guaranteed by Storyboard validation
            frames = frame_count_for_beats(
                t.duration_beats,
                storyboard.audio.bpm,
                storyboard.render.generation_fps,
                storyboard.render.max_bridge_frames,
            )
            requested = t.duration_beats * 60.0 / storyboard.audio.bpm
            actual = (frames - 1) / storyboard.render.generation_fps
        seed = t.seed if t.seed is not None else derived_seed(
            storyboard.render.master_seed, f"{i}:{t.from_anchor}:{t.to_anchor}"
        )
        items.append(BridgePlan(
            from_anchor=t.from_anchor,
            to_anchor=t.to_anchor,
            frames=frames,
            fps=storyboard.render.generation_fps,
            requested_seconds=requested,
            actual_span_seconds=actual,
            timing_error_seconds=actual - requested,
            seed=seed,
            candidates=t.candidates,
            transition_prompt=t.prompt,
        ))
    return items


def timeline_as_dict(storyboard: Storyboard) -> dict:
    bridges = compile_timeline(storyboard)
    return {
        "sequence": storyboard.name,
        "frame_total_if_matching_endpoints": 1 + sum(b.frames - 1 for b in bridges),
        "anchor_timestamp_span_seconds": sum(b.actual_span_seconds for b in bridges),
        "bridges": [asdict(b) for b in bridges],
        "note": "No GPU inference performed; endpoint de-dup requires visual verification.",
    }


def snap_frames(times: list[float], fps: float = 16.0, grid: int = 4) -> list[dict]:
    """F32: absolute frames on the grid, f = grid*round(t*fps/grid); errors never accumulate."""
    out = []
    for t in times:
        frame = grid * round(t * fps / grid)
        out.append({"t": t, "frame": frame, "error_frames": round(frame - t * fps, 4)})
    return out
