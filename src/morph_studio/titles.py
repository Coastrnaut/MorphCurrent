"""F38: act titles, opening/end cards and lower thirds as a finishing layer, plus act-boundary proposals.

Titles are drawn with local FFmpeg ``drawtext`` onto a *copy* of the joined movie (or the F37 animatic):
the input stays byte-identical, the output is new (``.part`` + rename) and is probe-verified to keep the
input's frame count and duration. The filter only uses relative names (``font.ttf``, ``tNN.txt``) inside a
temporary working directory, so it is deterministic and part of a checksummed recipe. Text never enters a
generation prompt.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

RECIPE_VERSION = 1
CHAR_WIDTH = 0.55      # average advance of Arial as a fraction of the font size
TITLE_SAFE = 0.90      # central fraction of the frame that is title-safe
MIN_SIZE = 0.035       # smallest size (fraction of frame height) when shrinking
LINE_GAP = 1.2         # line pitch as a multiple of the font size for multi-line blocks
ENCODER = ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy"]
DEFAULT_ACTS = Path("configs/film/acts.yaml")


class TitlesError(ValueError):
    pass


# ------------------------------------------------------------------------------------------ definition

def _check_block(where: str, block: dict, *, need_text: bool = True, fade: float = 0.5) -> None:
    if need_text and not str(block.get("text") or "").strip():
        raise TitlesError(f"{where}: text must not be empty")
    if "text_vertical" in block and not str(block.get("text_vertical") or "").strip():
        raise TitlesError(f"{where}: text_vertical must not be empty")
    dur = block.get("duration_s")
    if not isinstance(dur, (int, float)) or dur <= 0:
        raise TitlesError(f"{where}: duration_s must be > 0")
    if fade > dur / 2:
        raise TitlesError(f"{where}: fade {fade} s is longer than half the duration {dur} s")
    size = block.get("size")
    if not isinstance(size, (int, float)) or not 0 < size <= 0.3:
        raise TitlesError(f"{where}: size must be in (0, 0.3]")
    y = block.get("y")
    if not isinstance(y, (int, float)) or not 0 < y < 1:
        raise TitlesError(f"{where}: y must be in (0, 1)")


def load_titles(path: str | Path) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if data.get("version") != 1:
        raise TitlesError("titles definition must have version: 1")
    if not data.get("font"):
        raise TitlesError("titles definition needs a font file")
    fade = float((data.get("defaults") or {}).get("fade_s", 0.5))
    if fade < 0:
        raise TitlesError("defaults.fade_s must be >= 0")
    if data.get("opening"):
        _check_block("opening", data["opening"], fade=fade)
    if data.get("end"):
        _check_block("end", data["end"], fade=fade)
    if data.get("acts"):
        _check_block("acts", data["acts"], need_text=False, fade=fade)
        for act_id, text in (data["acts"].get("text") or {}).items():
            if text is not None and not str(text).strip():
                raise TitlesError(f"acts.text.{act_id}: text must not be empty")
    for i, lt in enumerate(data.get("lower_thirds") or []):
        lt.setdefault("size", 0.05)
        lt.setdefault("y", 0.88)
        _check_block(f"lower_thirds[{i}]", lt, fade=fade)
        if "start_s" not in lt and "anchor" not in lt:
            raise TitlesError(f"lower_thirds[{i}]: needs start_s or anchor")
    return data


# ------------------------------------------------------------------------------------------ timing

def _storyboard(storyboard):
    from .schema import load_storyboard
    return load_storyboard(storyboard) if isinstance(storyboard, (str, Path)) else storyboard


def anchor_times(storyboard) -> list[dict]:
    """Anchor index, id, chapter, frame and time (frame / generation fps) from the frame-locked timeline."""
    from .soundtrack import anchor_frames
    sb = _storyboard(storyboard)
    fps = float(sb.render.generation_fps)
    return [{"index": i, "id": a.id, "chapter": a.chapter, "frame": f, "t": round(f / fps, 6)}
            for i, (a, f) in enumerate(zip(sb.anchors, anchor_frames(sb)))]


def _act_titles(acts_path: str | Path | None) -> dict:
    path = Path(acts_path) if acts_path else DEFAULT_ACTS
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {a["id"]: a.get("title") or a["id"] for a in data.get("acts") or [] if a.get("id")}


def resolve(titles: dict, storyboard, *, duration_s: float | None = None,
            acts_path: str | Path | None = None, vertical: bool = False) -> dict:
    """Overlays with resolved start/end seconds, covered anchors, and warnings (deferred, clipped, overlap).

    With ``vertical`` a block's optional ``text_vertical`` (may contain line breaks) replaces its text so one
    copy serves 16:9 and the 9:16 crop.
    """
    sb = _storyboard(storyboard)
    fps = float(sb.render.generation_fps)
    anchors = anchor_times(sb)
    if duration_s is None:
        duration_s = (anchors[-1]["frame"] + 1) / fps
    fade = float((titles.get("defaults") or {}).get("fade_s", 0.5))
    act_names = _act_titles(acts_path)
    overlays: list[dict] = []
    warnings: list[str] = []

    def add(oid, kind, block, start, text=None):
        if text is None:
            text = block["text_vertical"] if vertical and block.get("text_vertical") else block["text"]
        lines = [ln.strip() for ln in str(text).strip().splitlines() if ln.strip()]
        overlays.append({"id": oid, "kind": kind, "text": "\n".join(lines),
                         "start_s": round(float(start), 3),
                         "end_s": round(float(start) + float(block["duration_s"]), 3),
                         "fade_s": fade, "size": float(block["size"]), "y": float(block["y"]), "notes": []})

    opening = titles.get("opening")
    if opening:
        add("opening", "opening", opening, opening.get("start_s", 0))
    acts = titles.get("acts")
    if acts:
        texts = acts.get("text") or {}
        seen: list[str] = []
        for a in anchors:
            ch = a["chapter"]
            if ch is None or ch in seen:
                continue
            seen.append(ch)
            text = texts.get(ch) or act_names.get(ch) or ch.replace("-", " ").title()
            add(f"act-{ch}", "act", acts, a["t"], text)
            if opening and overlays[0]["start_s"] <= a["t"] < overlays[0]["end_s"]:
                ov = overlays[-1]
                length = ov["end_s"] - ov["start_s"]
                ov["start_s"] = overlays[0]["end_s"]
                ov["end_s"] = round(ov["start_s"] + length, 3)
                ov["notes"].append(f"deferred to {ov['start_s']} s (after the opening card)")
    for i, lt in enumerate(titles.get("lower_thirds") or []):
        if "anchor" in lt:
            idx = int(lt["anchor"])
            if not 0 <= idx < len(anchors):
                raise TitlesError(f"lower_thirds[{i}]: anchor {idx} is not in the storyboard")
            start = anchors[idx]["t"]
        else:
            start = lt["start_s"]
        add(f"lower-{i:02d}", "lower_third", lt, start)
    end = titles.get("end")
    if end:
        add("end", "end", end, max(0.0, duration_s - float(end["duration_s"])))

    kept = []
    for ov in overlays:
        if ov["start_s"] >= duration_s:
            warnings.append(f"{ov['id']} starts at {ov['start_s']} s, after the movie ends ({duration_s:.3f} s): dropped")
            continue
        if ov["end_s"] > duration_s + 1e-9:
            ov["end_s"] = round(duration_s, 3)
            ov["notes"].append(f"clipped at the movie end {ov['end_s']} s")
            warnings.append(f"{ov['id']} clipped at the movie end")
        ov["anchors"] = [{k: a[k] for k in ("index", "id", "frame", "t")}
                         for a in anchors if ov["start_s"] <= a["t"] < ov["end_s"]]
        kept.append(ov)
    for i, a in enumerate(kept):
        for b in kept[i + 1:]:
            if a["start_s"] < b["end_s"] and b["start_s"] < a["end_s"]:
                warnings.append(f"{a['id']} overlaps {b['id']}")
    for ov in kept:
        warnings.extend(f"{ov['id']}: {n}" for n in ov["notes"] if n.startswith("deferred"))
    return {"overlays": kept, "warnings": warnings, "duration_s": round(duration_s, 6), "fps": fps}


# ------------------------------------------------------------------------------------------ safe areas

def safe_check(overlays: list[dict], width: int, height: int, *, vertical: bool = False,
               min_size: float = MIN_SIZE) -> dict:
    """Fit each block into the 16:9 title-safe area (and the 9:16 centre crop when ``vertical``)."""
    areas = [("16:9", TITLE_SAFE * width)]
    if vertical:
        areas.append(("9:16", TITLE_SAFE * round(height * 9 / 16)))
    rows, sizes, ok = [], {}, True
    floor_px = min_size * height
    for ov in overlays:
        size_px = ov["size"] * height
        lines = ov["text"].split("\n")
        chars = max(1, max(len(ln) for ln in lines))
        used = size_px
        flagged_any = False
        for name, limit in areas:
            width_px = CHAR_WIDTH * size_px * chars
            fit = limit / (CHAR_WIDTH * chars)
            if size_px <= fit:
                fits, size_area, flagged = True, size_px, False
            elif fit >= floor_px:
                fits, size_area, flagged = True, math.floor(fit * 10) / 10, False
            else:
                fits, size_area, flagged = False, floor_px, True
            used = min(used, size_area)
            flagged_any |= flagged
            rows.append({"id": ov["id"], "area": name, "fits": fits, "size_px": round(size_px, 1),
                         "size_used_px": round(size_area, 1), "width_px": round(width_px, 1),
                         "limit_px": round(limit, 1), "flagged": flagged})
        block_h = used * (1 + LINE_GAP * (len(lines) - 1)) if len(lines) > 1 else used
        top, bottom = ov["y"] * height - block_h / 2, ov["y"] * height + block_h / 2
        margin = (1 - TITLE_SAFE) / 2 * height
        if top < margin - 1e-6 or bottom > height - margin + 1e-6:
            rows.append({"id": ov["id"], "area": "vertical", "fits": False, "size_px": round(size_px, 1),
                         "size_used_px": round(used, 1), "width_px": None, "limit_px": round(height - 2 * margin, 1),
                         "flagged": True})
            flagged_any = True
        ok &= not flagged_any
        sizes[ov["id"]] = int(round(used))
    return {"ok": ok, "rows": rows, "sizes": sizes, "vertical": vertical}


# ------------------------------------------------------------------------------------------ recipe

def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _alpha(s: float, e: float, f: float) -> str:
    if f <= 0:
        return "1"
    return (f"if(lt(t,{s:.3f}),0,if(lt(t,{s + f:.3f}),(t-{s:.3f})/{f:.3f},"
            f"if(lt(t,{e - f:.3f}),1,if(lt(t,{e:.3f}),({e:.3f}-t)/{f:.3f},0))))")


def build_filter(overlays: list[dict], sizes: dict, height: int, color: str = "white") -> str:
    parts = []
    for n, ov in enumerate(overlays):
        s, e = ov["start_s"], ov["end_s"]
        y = round(ov["y"] * height)
        size = sizes[ov["id"]]
        multi = (f":text_align=C:line_spacing={round(size * (LINE_GAP - 1))}" if "\n" in ov["text"] else "")
        parts.append(
            f"drawtext=fontfile=font.ttf:textfile=t{n:02d}.txt:expansion=none:fontsize={size}{multi}"
            f":fontcolor={color}:borderw=2:bordercolor=black@0.6:x=(w-text_w)/2:y={y}-text_h/2"
            f":alpha='{_alpha(s, e, ov['fade_s'])}':enable='between(t,{s:.3f},{e:.3f})'")
    return ",".join(parts) if parts else "null"


def build_recipe(resolved: dict, width: int, height: int, fps: float, font: str | Path, sizes: dict,
                 color: str = "white") -> dict:
    font = Path(font)
    if not font.is_file():
        raise TitlesError(f"font file not found: {font}")
    overlays = resolved["overlays"]
    return {
        "version": RECIPE_VERSION, "width": width, "height": height, "fps": round(float(fps), 6),
        "font_sha256": _file_sha256(font),
        "overlays": [{"id": o["id"], "text": o["text"], "start_s": o["start_s"], "end_s": o["end_s"],
                      "fade_s": o["fade_s"], "size_px": sizes[o["id"]], "y": o["y"]} for o in overlays],
        "filter": build_filter(overlays, sizes, height, color),
        "encoder": list(ENCODER),
    }


def recipe_sha256(recipe: dict) -> str:
    return hashlib.sha256(json.dumps(recipe, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True).encode("ascii")).hexdigest()


# ------------------------------------------------------------------------------------------ render

def verify_media(probe_in: dict, probe_out: dict) -> list[str]:
    """Frame count must match exactly; duration within one frame."""
    problems = []
    if probe_in.get("frame_count") != probe_out.get("frame_count"):
        problems.append(f"frame count {probe_out.get('frame_count')} != input {probe_in.get('frame_count')}")
    fps = probe_in.get("fps") or 0
    di, do = probe_in.get("duration_s"), probe_out.get("duration_s")
    if di is not None and do is not None and fps and abs(di - do) > 1.0 / fps + 1e-3:
        problems.append(f"duration {do:.3f} s != input {di:.3f} s")
    return problems


def render(movie: str | Path, out: str | Path, titles: str | Path | dict, storyboard, *,
           vertical: bool = False, acts_path: str | Path | None = None) -> dict:
    from .media import probe_video
    movie, out = Path(movie), Path(out)
    if not movie.is_file():
        raise TitlesError(f"movie not found: {movie}")
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    defn = load_titles(titles) if isinstance(titles, (str, Path)) else titles
    font = Path(defn["font"])
    if not font.is_file():
        raise TitlesError(f"font file not found: {font}")
    exe = shutil.which("ffmpeg")
    if not exe:
        raise TitlesError("ffmpeg not found on PATH")
    probe_in = probe_video(movie)
    duration = probe_in["duration_s"] or (probe_in["frame_count"] / probe_in["fps"])
    resolved = resolve(defn, storyboard, duration_s=duration, acts_path=acts_path, vertical=vertical)
    safe = safe_check(resolved["overlays"], probe_in["width"], probe_in["height"], vertical=vertical)
    color = str((defn.get("defaults") or {}).get("color", "white"))
    rec = build_recipe(resolved, probe_in["width"], probe_in["height"], probe_in["fps"], font, safe["sizes"], color)
    digest = recipe_sha256(rec)
    input_sha = _file_sha256(movie)
    out.parent.mkdir(parents=True, exist_ok=True)
    part = out.with_name(out.name + ".part")
    with tempfile.TemporaryDirectory(prefix="mc-titles-") as tmp:
        tmpdir = Path(tmp)
        shutil.copyfile(font, tmpdir / "font.ttf")
        for n, ov in enumerate(resolved["overlays"]):
            (tmpdir / f"t{n:02d}.txt").write_bytes(ov["text"].encode("utf-8"))
        args = [exe, "-hide_banner", "-nostdin", "-v", "error", "-y", "-i", str(movie.resolve()),
                "-map", "0:v:0", "-map", "0:a?", "-vf", rec["filter"], "-fps_mode", "passthrough",
                *ENCODER, "-f", "mp4", str(part.resolve())]
        done = subprocess.run(args, capture_output=True, text=True, errors="replace", shell=False,
                              check=False, cwd=tmpdir)
    if done.returncode != 0:
        part.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg failed: {done.stderr[-400:]}")
    probe_out = probe_video(part)
    problems = verify_media(probe_in, probe_out)
    if problems:
        part.unlink(missing_ok=True)
        raise TitlesError("titled copy failed verification: " + "; ".join(problems))
    part.replace(out)
    if _file_sha256(movie) != input_sha:
        raise TitlesError("input movie changed during rendering")
    record = {"input": str(movie), "input_sha256": input_sha, "output": str(out),
              "output_sha256": _file_sha256(out), "recipe": rec, "recipe_sha256": digest,
              "probe_in": probe_in, "probe_out": probe_out, "safe_area": safe,
              "overlays": resolved["overlays"], "warnings": resolved["warnings"], "ok": safe["ok"]}
    rec_path = out.with_name(out.stem + ".titles.json")
    rec_path.write_text(json.dumps(record, indent=2, ensure_ascii=True), encoding="utf-8")
    record["record"] = str(rec_path)
    return record


# ------------------------------------------------------------------------------------------ boundaries

def act_boundaries(storyboard, sync_plan: str | Path, *, window: int = 6) -> dict:
    """For each act boundary: music event, nearest section-start anchor within the window, move proposal."""
    sb = _storyboard(storyboard)
    plan = json.loads(Path(sync_plan).read_text(encoding="utf-8"))
    targets = plan.get("anchors") or []
    anchors = anchor_times(sb)
    if len(targets) != len(anchors):
        raise TitlesError(f"storyboard has {len(anchors)} anchors but the sync plan has {len(targets)}")
    sections = [i for i, a in enumerate(targets) if a.get("event") == "section"]
    rows = []
    for a in anchors[1:]:
        prev = anchors[a["index"] - 1]
        if a["chapter"] is None or a["chapter"] == prev["chapter"]:
            continue
        b = a["index"]
        near = sorted((s for s in sections if abs(s - b) <= window), key=lambda s: (abs(s - b), s))
        sec = near[0] if near else None
        offset = None if sec is None else sec - b
        proposal = None
        if sec is not None and offset != 0:
            proposal = (f"move the start of act {a['chapter']} from anchor {b} to anchor {sec} "
                        f"({offset:+d}) to land on the section start at {targets[sec]['t']:.2f} s")
        rows.append({"act": a["chapter"], "anchor": b, "anchor_id": a["id"], "t": a["t"],
                     "event": targets[b].get("event"), "section_anchor": sec, "offset": offset,
                     "proposal": proposal})
    return {"boundaries": rows, "sections": sections, "window": window,
            "proposals": sum(1 for r in rows if r["proposal"])}
