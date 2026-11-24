"""Transition risk and intermediate-anchor ladder proposals (F14).

A single Wan bridge morphs well between related forms and poorly between distant
ones. ``transition_risk`` gives an interpretable score with reasons; ``propose_ladder``
writes a *proposal* storyboard that splits one transition A→B into A→M1→…→B with
reference-edited intermediate anchors and valid 4n+1 segment lengths, and checks the
added GPU time against measured history. Nothing is rendered; proposals need review.
"""
from __future__ import annotations

import copy
import hashlib
import re
from pathlib import Path

import yaml

from .schema import Storyboard
from .timeline import derived_seed, frame_count_for_beats

STOPWORDS = {"a", "an", "the", "and", "or", "of", "with", "in", "on", "into", "as", "its", "same",
             "to", "from", "by", "for", "at", "is", "are", "that", "this", "previous", "s"}
MIN_FRAMES = 5


class LadderError(ValueError):
    pass


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOPWORDS and len(w) > 2}


def prompt_distance(a: str, b: str) -> float:
    """Content-word Jaccard distance (0 = same words, 1 = nothing shared)."""
    wa, wb = _words(a), _words(b)
    if not wa and not wb:
        return 0.0
    return round(1 - len(wa & wb) / len(wa | wb), 3)


def transition_risk(prompt_a: str, prompt_b: str, geometry: dict | None = None) -> dict:
    """Interpretable 0–1 risk with reasons (prompt distance + optional F12 geometry flags)."""
    distance = prompt_distance(prompt_a, prompt_b)
    reasons = []
    score = 0.6 * distance
    if distance >= 0.7:
        reasons.append(f"prompt_distance {distance}")
    weights = {"symmetry_drop": 0.25, "scale_change": 0.15, "centroid_shift": 0.15, "palette_shift": 0.1}
    for flag in (geometry or {}).get("flags", []):
        if flag in weights:
            score += weights[flag]
            reasons.append(f"geometry {flag}")
    score = round(min(1.0, score), 3)
    level = "high" if score >= 0.6 else "medium" if score >= 0.35 else "low"
    return {"risk": score, "level": level, "reasons": reasons, "method": "heuristic"}


def risk_report(storyboard: Storyboard, geometry_by_pair: dict[str, dict] | None = None) -> list[dict]:
    prompts = {a.id: a.prompt for a in storyboard.anchors}
    out = []
    for t in storyboard.transitions:
        pair = f"{t.from_anchor}->{t.to_anchor}"
        out.append({"transition": pair, **transition_risk(prompts[t.from_anchor], prompts[t.to_anchor],
                                                          (geometry_by_pair or {}).get(pair))})
    return out


def _mid_prompt(a: dict, b: dict, k: int, steps: int) -> str:
    """Deterministic halfway description; the edit model decides the actual form."""
    frac = round(k / (steps + 1), 2)
    pa = " ".join(a["prompt"].split()).rstrip(".")
    pb = " ".join(b["prompt"].split()).rstrip(".")
    return (f"Transform the subject {int(frac * 100)}% of the way from ({pa}) toward ({pb}): "
            f"a single coherent hybrid form that keeps the same centered composition, scale, "
            f"lighting and palette, physically plausible, no text.")


def _split_beats(beats: float, bpm: float, fps: int, max_frames: int, steps: int) -> list[float]:
    parts = [round(beats / (steps + 1), 6)] * (steps + 1)
    parts[-1] = round(beats - sum(parts[:-1]), 6)
    for p in parts:
        try:
            frames = frame_count_for_beats(p, bpm, fps, max_frames)
        except ValueError as exc:
            raise LadderError(f"cannot split {beats} beats into {steps + 1} segments: {exc}") from exc
        if frames < MIN_FRAMES:
            raise LadderError(f"segment of {p} beats is only {frames} frames (< {MIN_FRAMES})")
    return parts


def propose_ladder(data: dict, from_id: str, to_id: str, *, steps: int = 1,
                   history: list[dict] | None = None, max_new: int = 3,
                   max_gpu_s: float | None = None, source_sha256: str | None = None) -> tuple[dict, dict]:
    """Return (new storyboard dict, report). ``data`` is the parsed YAML; it is not modified."""
    if steps < 1 or steps > max_new:
        raise LadderError(f"steps must be 1..{max_new}")
    sb = copy.deepcopy(data)
    anchors = sb["anchors"]
    ids = [a["id"] for a in anchors]
    if from_id not in ids or to_id not in ids or ids.index(to_id) != ids.index(from_id) + 1:
        raise LadderError(f"{from_id}->{to_id} is not an adjacent transition")
    t_index = next(i for i, t in enumerate(sb["transitions"])
                   if t["from"] == from_id and t["to"] == to_id)
    trans = sb["transitions"][t_index]
    render, audio = sb["render"], sb.get("audio") or {}
    bpm = audio.get("bpm")
    if trans.get("duration_beats") is None:
        raise LadderError("ladders split beat-timed transitions; this transition is frame-locked (F32) - "
                          "re-plan its anchors with sync-plan instead")
    if not bpm:
        raise LadderError("storyboard needs audio.bpm to split beat budgets")
    parts = _split_beats(trans["duration_beats"], bpm, render.get("generation_fps", 16),
                         render.get("max_bridge_frames", 81), steps)
    a_def, b_def = anchors[ids.index(from_id)], anchors[ids.index(to_id)]
    master = render.get("master_seed", 0)
    new_anchors, chain = [], [from_id]
    for k in range(1, steps + 1):
        mid_id = f"{from_id}_to_{to_id}_{k}"
        if mid_id in ids:
            raise LadderError(f"anchor id {mid_id} already exists")
        new_anchors.append({"id": mid_id, "prompt": _mid_prompt(a_def, b_def, k, steps),
                            "negative_prompt": b_def.get("negative_prompt") or a_def.get("negative_prompt"),
                            "seed": derived_seed(master, f"ladder:{mid_id}"),
                            "generation": "reference_edit", "reference": chain[-1]})
        chain.append(mid_id)
    chain.append(to_id)
    for anchor in new_anchors:
        if anchor["negative_prompt"] is None:
            del anchor["negative_prompt"]
    pos = ids.index(to_id)
    sb["anchors"] = anchors[:pos] + new_anchors + anchors[pos:]
    target = sb["anchors"][pos + steps]
    if target.get("generation") == "reference_edit":
        target["reference"] = chain[-2]  # B now edits the last intermediate anchor
    segments = []
    for k, (src, dst) in enumerate(zip(chain, chain[1:])):
        seg = copy.deepcopy(trans)
        seg.update({"from": src, "to": dst, "duration_beats": parts[k],
                    "seed": derived_seed(master, f"ladder:{src}->{dst}")})
        segments.append(seg)
    sb["transitions"] = sb["transitions"][:t_index] + segments + sb["transitions"][t_index + 1:]
    Storyboard.model_validate(sb)  # proposal must be a valid storyboard
    frames = [frame_count_for_beats(p, bpm, render.get("generation_fps", 16),
                                    render.get("max_bridge_frames", 81)) for p in parts]
    report = {"split": f"{from_id}->{to_id}", "new_anchors": [a["id"] for a in new_anchors],
              "segments": [{"from": s["from"], "to": s["to"], "beats": s["duration_beats"], "frames": f}
                           for s, f in zip(segments, frames)],
              "source_sha256": source_sha256, "status": "PROPOSAL — review before rendering"}
    report["added_gpu_s"] = _added_cost(render, frames, trans, history)
    if max_gpu_s is not None:
        added = report["added_gpu_s"]
        if added is None:
            raise LadderError("no measured history for this size; cannot check --max-gpu-s")
        if added > max_gpu_s:
            raise LadderError(f"ladder adds ~{added:.0f} s GPU, above the {max_gpu_s:.0f} s budget")
    return sb, report


def _added_cost(render: dict, frames: list[int], trans: dict, history: list[dict] | None) -> float | None:
    if not history:
        return None
    w, h = render["width"], render["height"]
    def median(xs):
        xs = sorted(xs)
        return xs[len(xs) // 2] if xs else None
    edit = median([e["exec_s"] for e in history if e["kind"] == "anchor" and e.get("method") == "reference_edit"
                   and e["width"] == w and e["height"] == h])
    bridge = {f: median([e["exec_s"] for e in history if e["kind"] == "bridge" and e["width"] == w
                         and e["height"] == h and e.get("frames") == f]) for f in set(frames)}
    if edit is None or any(v is None for v in bridge.values()):
        return None
    original = median([e["exec_s"] for e in history if e["kind"] == "bridge" and e["width"] == w
                       and e["height"] == h])
    total = edit * (len(frames) - 1) + sum(bridge[f] for f in frames) - (original or 0.0)
    return round(total, 1)


def write_proposal(sb: dict, report: dict, out: Path) -> Path:
    if out.exists():
        raise FileExistsError(out)
    header = (f"# PROPOSAL generated by `morphcurrent ladder-propose` — review before rendering.\n"
              f"# split: {report['split']} -> {', '.join(report['new_anchors'])}\n"
              f"# source storyboard sha256: {report.get('source_sha256')}\n"
              f"# added GPU (ESTIMATED from measured history): {report.get('added_gpu_s')} s\n")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(header + yaml.safe_dump(sb, sort_keys=False, allow_unicode=True, width=100),
                   encoding="utf-8", newline="\n")
    return out


def sha256_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
