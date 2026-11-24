"""Soundtrack sync verification, animatic, narration timing, captions and beat-map review (F37). Offline.

``sync_report`` compares each storyboard anchor's frame time with the sync plan's target musical event.
``warp_report`` checks the energy-warp maps (speed range, pinned endpoints). ``animatic`` cuts one still per
anchor (rendered image when available, otherwise a plain act-coloured card - never rendered text) exactly at
the anchor frames and muxes the owner's licensed audio. Captions and narration are separate SRT tracks.
``click_track`` places clicks on beat-map downbeats for listening; ``verify_beatmap`` records owner sign-off.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import struct
import subprocess
import tempfile
import wave
from datetime import date
from pathlib import Path

import yaml

FPS_DEFAULT = 16
SIZE = (832, 480)
ACT_TONES = {"spark": "0x4a2a14", "power": "0x40321e", "signal": "0x163a28", "logic": "0x162c4a", "scale": "0x22203e"}
CLICK_RATE, CLICK_S, CLICK_HZ = 48000, 0.03, 1000.0


class SoundtrackError(ValueError):
    pass


def _load_json(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def anchor_frames(storyboard) -> list[int]:
    from .timeline import compile_timeline
    frames = [0]
    for b in compile_timeline(storyboard):
        frames.append(frames[-1] + b.frames - 1)
    return frames


# ------------------------------------------------------------------------------------- sync / warp

def sync_report(storyboard: str | Path, sync_plan: str | Path) -> dict:
    from .schema import load_storyboard
    sb = load_storyboard(storyboard)
    plan = _load_json(sync_plan)
    fps = float(plan.get("fps") or sb.render.generation_fps)
    targets = plan.get("anchors") or []
    frames = anchor_frames(sb)
    if len(targets) != len(frames):
        raise SoundtrackError(f"storyboard has {len(frames)} anchors but the sync plan has {len(targets)}")
    start = targets[0].get("frame", round(targets[0]["t"] * fps))
    rows = []
    for a, f, tgt in zip(sb.anchors, frames, targets):
        actual = f + start
        err = round(actual - tgt["t"] * fps, 3)
        rows.append({"anchor": a.id, "event": tgt.get("event") or "none", "target_s": tgt["t"],
                     "actual_s": round(actual / fps, 4), "error_frames": int(err) if err == int(err) else err})
    errors = [abs(r["error_frames"]) for r in rows]
    drift = rows[-1]["error_frames"] - rows[0]["error_frames"]
    mean = round(sum(errors) / len(errors), 3)
    return {"storyboard": sb.name, "rows": rows, "mean_abs_error": mean, "max_abs_error": max(errors),
            "drift_frames": drift, "gate": max(errors) <= 2 and mean <= 1 and drift == 0,
            "note": "Errors in frames at the generation rate; gate: every anchor <= 2 frames, mean <= 1, zero drift."}


def warp_report(sync_plan: str | Path, lo: float = 0.5, hi: float = 2.0) -> dict:
    plan = _load_json(sync_plan)
    rows = []
    for i, b in enumerate(plan.get("bridges") or []):
        m = (b.get("warp") or {}).get("map") or []
        frames = b.get("frames") or len(m)
        speeds = [m[j + 1] - m[j] for j in range(len(m) - 1)]
        flags = []
        pinned = bool(m) and abs(m[0]) < 1e-6 and abs(m[-1] - (frames - 1)) < 1e-6
        if not pinned:
            flags.append("unpinned")
        if speeds and (min(speeds) < lo - 1e-6 or max(speeds) > hi + 1e-6):
            flags.append(f"speed outside {lo}-{hi}")
        rows.append({"bridge": i, "frames": frames, "min_speed": round(min(speeds), 3) if speeds else None,
                     "max_speed": round(max(speeds), 3) if speeds else None, "pinned": pinned, "flags": flags})
    return {"rows": rows, "ok": all(not r["flags"] for r in rows)}


# ----------------------------------------------------------------------------------------- animatic

def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise SoundtrackError("ffmpeg not found on PATH")
    return exe


def _run(args: list[str]) -> None:
    done = subprocess.run(args, capture_output=True, text=True, errors="replace", shell=False, check=False)
    if done.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {done.stderr[-400:]}")


def _tone(chapter: str | None) -> str:
    if chapter in ACT_TONES:
        return ACT_TONES[chapter]
    h = hashlib.sha256(str(chapter).encode()).hexdigest()
    return "0x" + "".join(f"{int(h[i:i + 2], 16) // 3:02x}" for i in (0, 2, 4))


def _audio_duration(path: Path) -> float | None:
    exe = shutil.which("ffprobe")
    done = subprocess.run([exe, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=duration",
                           "-of", "json", str(path)], capture_output=True, text=True, shell=False, check=False)
    streams = json.loads(done.stdout or "{}").get("streams") or []
    if not streams:
        return None
    return float(streams[0].get("duration") or 0.0)


def animatic(storyboard: str | Path, out: str | Path, *, plan: str | Path | None = None,
             run_dir: str | Path | None = None, audio: str | Path | None = None, licensed: bool = False,
             offset: float = 0.0) -> dict:
    from .cache import sha256_file
    from .media import probe_video
    from .release import _stage_files
    from .schema import load_storyboard
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"{out} exists; refusing to overwrite")
    if audio and not licensed:
        raise SoundtrackError("audio must be marked licensed by the owner (--audio-licensed)")
    sb = load_storyboard(storyboard)
    fps = sb.render.generation_fps
    frames = anchor_frames(sb)
    tail_s = 0.0
    if plan and Path(plan).is_file():
        tail_s = float((_load_json(plan).get("coverage") or {}).get("hold_s") or 0.0)
    expected = frames[-1] / fps + tail_s
    stills = {}
    if run_dir:
        for key, info in _stage_files(Path(run_dir)).items():
            f = info.get("file")
            if key.startswith("anchor:") and f and Path(f).is_file():
                stills[key.split(":", 1)[1]] = Path(f)
    cuts = []
    with tempfile.TemporaryDirectory(prefix="mc-animatic-") as tmpname:
        tmp = Path(tmpname)
        lines = ["ffconcat version 1.0"]
        for i, a in enumerate(sb.anchors):
            if a.id in stills:
                img, source = stills[a.id], "still"
            else:
                img, source = tmp / f"card_{i:03d}.png", "card"
                _run([_ffmpeg(), "-v", "error", "-y", "-f", "lavfi", "-i",
                      f"color=c={_tone(a.chapter)}:size={SIZE[0]}x{SIZE[1]}", "-frames:v", "1", str(img)])
            hold = (frames[i + 1] - frames[i]) / fps if i + 1 < len(frames) else max(tail_s, 1 / fps)
            lines += [f"file '{img.resolve().as_posix()}'", f"duration {hold:.6f}"]
            cuts.append({"anchor": a.id, "frame": frames[i], "seconds": round(frames[i] / fps, 4), "source": source})
        lines.append(f"file '{(stills.get(sb.anchors[-1].id) or tmp / f'card_{len(sb.anchors) - 1:03d}.png').resolve().as_posix()}'")
        concat = tmp / "list.ffconcat"
        concat.write_text("\n".join(lines) + "\n", encoding="utf-8")
        vf = (f"scale={SIZE[0]}:{SIZE[1]}:force_original_aspect_ratio=decrease,pad={SIZE[0]}:{SIZE[1]}:(ow-iw)/2:"
              f"(oh-ih)/2:black,setsar=1,fps={fps}:round=near,format=yuv420p")
        args = [_ffmpeg(), "-hide_banner", "-nostdin", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                "-i", str(concat)]
        if audio:
            args += ["-ss", f"{offset:.6f}", "-i", str(audio)]
        args += ["-vf", vf, "-t", f"{expected:.6f}", "-c:v", "libx264", "-crf", "20"]
        args += (["-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-b:a", "192k"] if audio else ["-an"])
        out.parent.mkdir(parents=True, exist_ok=True)
        part = out.with_name(out.name + ".part.mp4")
        try:
            _run([*args, str(part)])
            os.replace(part, out)
        finally:
            part.unlink(missing_ok=True)
    p = probe_video(out)
    audio_s = _audio_duration(out)
    measured = {"duration_s": p["duration_s"], "frames": p["frame_count"], "audio": audio_s is not None,
                "audio_duration_s": audio_s}
    ok = abs((p["duration_s"] or 0) - expected) <= 1 / fps + 1e-6 and measured["audio"] == bool(audio)
    rec = {"storyboard": sb.name, "out": str(out), "fps": fps, "cuts": cuts, "expected_s": round(expected, 4),
           "audio": ({"path": str(audio), "sha256": sha256_file(Path(audio)), "offset_s": offset} if audio else None),
           "measured": measured, "ok": ok,
           "note": "Timing animatic: stills or plain act-coloured cards, no rendered text."}
    Path(str(out) + ".animatic.json").write_text(json.dumps(rec, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return rec


# -------------------------------------------------------------------------------------------- SRT

def _ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _parse_ts(text: str) -> float:
    hms, ms = text.strip().split(",")
    h, m, s = (int(x) for x in hms.split(":"))
    return h * 3600 + m * 60 + s + int(ms) / 1000


def srt_write(cues: list[dict], path: str | Path) -> Path:
    blocks = []
    for i, c in enumerate(cues, 1):
        text = "\n".join(line for line in str(c["text"]).splitlines() if line.strip()) or "-"
        blocks.append(f"{i}\n{_ts(c['start_s'])} --> {_ts(c['end_s'])}\n{text}\n")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(blocks), encoding="utf-8")
    return path


def srt_parse(path: str | Path) -> list[dict]:
    cues = []
    for block in Path(path).read_text(encoding="utf-8").strip().split("\n\n"):
        lines = block.strip().splitlines()
        start, end = (part.strip() for part in lines[1].split("-->"))
        cues.append({"index": int(lines[0]), "start_s": round(_parse_ts(start), 3), "end_s": round(_parse_ts(end), 3),
                     "text": "\n".join(lines[2:])})
    return cues


def captions(storyboard: str | Path, bank: str | Path | None = None) -> list[dict]:
    from .schema import load_storyboard
    sb = load_storyboard(storyboard)
    fps = sb.render.generation_fps
    frames = anchor_frames(sb)
    subjects = {}
    if bank and Path(bank).is_file():
        subjects = {e["id"]: e["subject"] for e in yaml.safe_load(Path(bank).read_text(encoding="utf-8"))["entries"]}
    cues = []
    for i, a in enumerate(sb.anchors):
        start = frames[i] / fps
        end = frames[i + 1] / fps if i + 1 < len(frames) else start + 2.0
        cues.append({"start_s": start, "end_s": end, "text": subjects.get(a.id, a.id)})
    return cues


def narration_check(script: str | Path, storyboard: str | Path, srt_out: str | Path) -> dict:
    from .schema import load_storyboard
    sb = load_storyboard(storyboard)
    fps = sb.render.generation_fps
    frames = anchor_frames(sb)
    at = {a.id: frames[i] / fps for i, a in enumerate(sb.anchors)}
    end_of_picture = frames[-1] / fps
    data = yaml.safe_load(Path(script).read_text(encoding="utf-8")) or {}
    lines = []
    for i, line in enumerate(data.get("lines") or [], 1):
        if "at" in line:
            if line["at"] not in at:
                raise SoundtrackError(f"narration line {i}: unknown anchor {line['at']!r}")
            start = at[line["at"]]
        else:
            start = float(line["t"])
        end = start + float(line["duration"])
        lines.append({"index": i, "start_s": round(start, 3), "end_s": round(end, 3), "text": line["text"], "flags": []})
    ordered = sorted(lines, key=lambda x: x["start_s"])
    gaps = []
    for prev, cur in zip(ordered, ordered[1:]):
        if cur["start_s"] < prev["end_s"] - 1e-9:
            cur["flags"].append("overlap")
        elif cur["start_s"] > prev["end_s"]:
            gaps.append({"after": prev["index"], "seconds": round(cur["start_s"] - prev["end_s"], 3)})
    for line in lines:
        if line["end_s"] > end_of_picture + 1e-9:
            line["flags"].append("past_end")
    srt = srt_write(ordered, srt_out)
    return {"lines": lines, "gaps": gaps, "picture_end_s": end_of_picture, "srt": str(srt),
            "ok": not any(line["flags"] for line in lines)}


# ------------------------------------------------------------------------------------- beat map

def click_track(beatmap: str | Path, out: str | Path, *, music: str | Path | None = None) -> dict:
    data = _load_json(beatmap)
    beats = [float(t) for t in data.get("downbeats") or []]
    out = Path(out)
    length = (max(beats) if beats else 0) + 1.0
    n = int(length * CLICK_RATE)
    samples = [0] * n
    click_n = int(CLICK_S * CLICK_RATE)
    for t in beats:
        start = int(round(t * CLICK_RATE))
        for j in range(click_n):
            if start + j < n:
                env = 1.0 - j / click_n
                samples[start + j] = int(16000 * env * math.sin(2 * math.pi * CLICK_HZ * j / CLICK_RATE))
    clicks_path = out if not music else out.with_name(out.stem + ".clicks.wav")
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(clicks_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(CLICK_RATE)
        w.writeframes(struct.pack(f"<{n}h", *samples))
    if music:
        _run([_ffmpeg(), "-v", "error", "-y", "-i", str(music), "-i", str(clicks_path), "-filter_complex",
              "[0:a]volume=0.5[m];[m][1:a]amix=inputs=2:duration=longest:normalize=0[a]", "-map", "[a]",
              "-ar", str(CLICK_RATE), str(out)])
    return {"out": str(out), "clicks": len(beats), "music": str(music) if music else None}


def verify_beatmap(beatmap: str | Path, out: str | Path, *, owner: str,
                   corrections: dict[int, float] | None = None) -> dict:
    if not owner or not owner.strip():
        raise SoundtrackError("beat-map verification needs the owner's name")
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"{out} exists; refusing to overwrite")
    data = _load_json(beatmap)
    beats = [float(t) for t in data.get("downbeats") or []]
    applied = []
    for index, value in sorted((corrections or {}).items()):
        if not 0 <= index < len(beats):
            raise SoundtrackError(f"correction index {index} out of range (0..{len(beats) - 1})")
        applied.append({"index": index, "from": beats[index], "to": float(value)})
        beats[index] = float(value)
    if any(b2 <= b1 for b1, b2 in zip(beats, beats[1:])):
        raise SoundtrackError("downbeats must be strictly increasing after corrections")
    new = dict(data)
    new.update(downbeats=beats, verified=True, verified_by=owner.strip(), verified_on=date.today().isoformat(),
               corrections=(data.get("corrections") or []) + applied)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(new, indent=2) + "\n", encoding="utf-8")
    return new
