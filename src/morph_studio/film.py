"""Full-song film storyboard: acts, frame-locked transitions and a dry-run film report (F32).

``build_storyboard`` turns the F15 sync plan (anchor frames and bridge lengths chosen on musical events), the
F31 concept bank (one subject per anchor) and the act definition into one standard storyboard: anchors in
bank order grouped into contiguous chapters (acts), each act opening with a fresh text-to-image anchor and
continuing with reference edits of the previous anchor, and transitions with the plan's exact 4n+1 lengths
(``frames``). ``film_report`` is a GPU-free dry run: per-act frames and seconds, act-boundary music events,
coverage of the song and labelled GPU-hour estimates from measured history.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

MIN_BRIDGE, MAX_BRIDGE = 33, 81
TEXT_NEGATIVES = ("text", "letters", "labels", "logo", "watermark")  # same terms as accuracy.TEXT_NEGATIVES
MASTER_SEED = 31415
STYLE_PACK = "engineering-noir"
DEFAULTS = {"plan": Path("configs/film/sync-plan.json"), "bank": Path("configs/concepts/engineering-film.yaml"),
            "acts": Path("configs/film/acts.yaml"), "history": Path("configs/perf_history.json")}


class FilmError(ValueError):
    pass


def _load(path: str | Path) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    return json.loads(text) if str(path).endswith(".json") else yaml.safe_load(text)


def load_acts(acts: dict, eras: list[str]) -> list[dict]:
    """Validate: every era in exactly one act, acts contiguous and in era order."""
    items = acts.get("acts") or []
    listed = [e for a in items for e in (a.get("eras") or [])]
    if sorted(listed) != sorted(eras) or len(listed) != len(set(listed)):
        missing = sorted(set(eras) - set(listed))
        extra = sorted({e for e in listed if listed.count(e) > 1} | (set(listed) - set(eras)))
        raise FilmError(f"each era must belong to exactly one act (missing {missing}, duplicated/unknown {extra})")
    if listed != eras:
        raise FilmError("acts must list the eras contiguously and in concept-bank era order")
    for a in items:
        if not a.get("id") or not a.get("eras"):
            raise FilmError(f"act {a!r} needs an id and at least one era")
    return items


def act_starts(items: list[dict], n_anchors: int) -> list[tuple[int, str]] | None:
    """F38 owner-approved act boundaries: optional ``start_anchor`` per act overrides era grouping.

    Either no act sets it (era grouping) or every act does: the first at 0, strictly increasing, < n_anchors.
    """
    given = [a.get("start_anchor") for a in items]
    if all(g is None for g in given):
        return None
    if any(g is None for g in given):
        raise FilmError("either every act sets start_anchor or none does")
    if given[0] != 0 or any(b <= a for a, b in zip(given, given[1:])) or given[-1] >= n_anchors:
        raise FilmError(f"act start_anchor values must start at 0 and increase below {n_anchors}: {given}")
    return [(int(g), a["id"]) for g, a in zip(given, items)]


def _anchor_prompt(e: dict) -> str:
    return (f"{e['subject']}: {e['description']}; dominant shapes: {', '.join(e['shapes'])}; "
            f"materials: {', '.join(e['materials'])}")


def _bridge_prompt(e: dict, character: list[str]) -> str:
    feel = ", ".join(character) if character else "steady"
    return (f"Continuous physical metamorphosis in one uninterrupted shot: {e['morph_to_next']}; "
            f"motion feel: {feel}. No cuts or dissolves.")


def build_storyboard(sync_plan: dict, bank: dict, acts: dict, *, audio: str | None = None,
                     master_seed: int = MASTER_SEED, language: dict | None = None,
                     look: str | None = None) -> tuple[dict, str]:
    entries = bank["entries"]
    anchors, bridges = sync_plan.get("anchors") or [], sync_plan.get("bridges") or []
    if len(anchors) != len(entries) or len(bridges) != len(entries) - 1:
        raise FilmError(f"sync plan has {len(anchors)} anchors / {len(bridges)} bridges but the concept bank has "
                        f"{len(entries)} subjects; re-plan or edit the bank so the counts match")
    for i, b in enumerate(bridges):
        frames = b["frames"]
        if not MIN_BRIDGE <= frames <= MAX_BRIDGE or (frames - 1) % 4:
            raise FilmError(f"bridge {i} is {frames} frames; the film needs 33-81-frame 4n+1 bridges")
        if i and b.get("from_frame") is not None and b["from_frame"] != bridges[i - 1].get("to_frame"):
            raise FilmError(f"bridge {i} does not start where bridge {i - 1} ends")
    act_items = load_acts(acts, bank["eras"])
    era_act = {era: a["id"] for a in act_items for era in a["eras"]}
    starts = act_starts(act_items, len(entries))
    out_anchors, prev = [], None
    for idx, e in enumerate(entries):
        act = era_act[e["era"]] if starts is None else next(a for s, a in reversed(starts) if s <= idx)
        anchor = {"id": e["id"], "prompt": _anchor_prompt(e), "chapter": act}
        if prev is not None and prev["chapter"] == act:
            anchor.update(generation="reference_edit", reference=prev["id"])
        else:
            anchor["generation"] = "text_to_image"
        out_anchors.append(anchor)
        prev = anchor
    # F33: bridges carry the text-free negatives too (anchors get them from the style pack)
    transitions = [{"from": entries[i]["id"], "to": entries[i + 1]["id"], "frames": b["frames"],
                    "prompt": _bridge_prompt(entries[i], b.get("character") or []),
                    "choreography": {"negative": list(TEXT_NEGATIVES)}}
                   for i, b in enumerate(bridges)]
    data = {"schema_version": 1, "name": "engineering-film",
            "render": {"width": 832, "height": 480, "generation_fps": 16, "delivery_fps": 24,
                       "anchor_profile": "anchor_t2i", "bridge_profile": "wan22_flf2v",
                       "master_seed": master_seed, "max_bridge_frames": MAX_BRIDGE},
            "style": {"description": "Cinematic macro engineering artifacts.", "pack": STYLE_PACK},
            "audio": ({"file": audio, "licensed": True, "synchronization": "none"} if audio else
                      {"synchronization": "none"}),
            "anchors": out_anchors, "transitions": transitions}
    look_line = "# look: none (no visual language applied)" + chr(10)
    if language is not None:  # F34: per-act palette/lighting overrides and bridge camera
        from .look import apply_look, choose
        name, spec, how = choose(language, look)
        data = apply_look(data, spec)
        look_line = f"# look: {name} ({how})" + chr(10)
    from .schema import Storyboard
    Storyboard.model_validate(data)
    header = (look_line + f"# Generated by `film-storyboard` (F32) - edit the sources, not this file, then regenerate.\n"
              f"# sync plan {sync_plan.get('plan_sha256')} (track {sync_plan.get('track_sha256')}), "
              f"{len(anchors)} anchors / {len(bridges)} bridges\n"
              f"# concept bank v{bank.get('version')} status {bank.get('status')}; acts: "
              f"{', '.join(a['id'] for a in acts['acts'])}\n"
              f"# Each act opens with a text-to-image anchor; anchors inside an act are reference edits.\n")
    return data, header


def apply_anchor_fixes(data: dict, fixes: list[dict]) -> list[str]:
    """Owner-chosen anchor repairs (configs/film/anchor-fixes.yaml, ``apply``): ``fresh`` renders the anchor as an
    independent text-to-image keyframe (``reference`` stays as the continuity parent only); ``instruction``
    replaces the edit prompt with the drafted remove/replace instruction. Returns the applied anchor ids."""
    by_id = {a["id"]: a for a in data["anchors"]}
    applied = []
    for f in fixes:
        how = f.get("apply")
        if not how:
            continue
        a = by_id.get(f.get("anchor"))
        if a is None:
            raise FilmError(f"anchor fix names unknown anchor {f.get('anchor')!r}")
        if f.get("prompt"):  # Claude-drafted revised prompt (with fresh, prompt, or alone)
            a["prompt"] = " ".join(str(f["prompt"]).split())
        if how == "fresh":
            a["generation"] = "independent_t2i"
        elif how == "prompt":
            if not f.get("prompt"):
                raise FilmError(f"{a['id']}: apply 'prompt' needs a prompt")
        elif how == "instruction":
            if a.get("generation") != "reference_edit":
                raise FilmError(f"{a['id']} is not a reference edit; an edit instruction does not apply")
            a["prompt"] = " ".join(str(f["instruction"]).split())
        else:
            raise FilmError(f"anchor fix apply must be 'fresh', 'prompt' or 'instruction', not {how!r}")
        applied.append(f"{a['id']}={how}")
    return applied


def write_storyboard(plan: str | Path, bank: str | Path, acts: str | Path, out: str | Path, *,
                     audio: str | None = None, language: str | Path | None = None, look: str | None = None,
                     fixes: str | Path | None = None) -> dict:
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"{out} exists; refusing to overwrite")
    acts_data = _load(acts)
    lang = None
    if language:
        from .look import load_language
        lang = load_language(language, [a["id"] for a in acts_data["acts"]])
    data, header = build_storyboard(_load(plan), _load(bank), acts_data, audio=audio, language=lang, look=look)
    if fixes and Path(fixes).is_file():
        applied = apply_anchor_fixes(data, _load(fixes).get("fixes") or [])
        if applied:
            header += f"# anchor fixes applied (configs/film/anchor-fixes.yaml): {', '.join(applied)}\n"
    from .schema import Storyboard
    Storyboard.model_validate(data)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(header + yaml.safe_dump(data, sort_keys=False, width=120), encoding="utf-8")
    return data


def film_report(storyboard: str | Path, *, sync_plan: str | Path | None = DEFAULTS["plan"],
                history: str | Path | None = DEFAULTS["history"], repo_root: str | Path = ".") -> dict:
    from .dag import compile_plan
    from .perf import ESTIMATED, EXTRAPOLATED, estimate, load_history
    from .schema import load_storyboard
    root = Path(repo_root)
    path = Path(storyboard)
    sb = load_storyboard(path)
    plan = compile_plan(sb, repo_root=root, storyboard_bytes=path.read_bytes())
    fps = sb.render.generation_fps
    sp = _load(sync_plan) if sync_plan and Path(sync_plan).is_file() else None
    hist = load_history(history) if history and Path(history).is_file() else []
    est = estimate(plan, hist, extrapolate=True)
    est_by_task = {r["task"]: r for r in est["stages"]}
    ids = [a.id for a in sb.anchors]
    acts: list[dict] = []
    for i, a in enumerate(sb.anchors):
        if not acts or acts[-1]["id"] != a.chapter:
            event = sp["anchors"][i].get("event") if sp and i < len(sp["anchors"]) else None
            acts.append({"id": a.chapter, "first_anchor": a.id, "anchors": 0, "bridges": 0, "frames": 0,
                         "seconds": 0.0, "boundary_event": event or "none", "gpu_s": 0.0})
        acts[-1]["anchors"] += 1
        acts[-1]["gpu_s"] += est_by_task.get(f"anchor:{a.id}", {}).get("exec_s") or 0.0
    chapter_of = {a.id: a.chapter for a in sb.anchors}
    for t in sb.transitions:  # a bridge belongs to the act of its start anchor (boundary bridges included)
        act = next(x for x in acts if x["id"] == chapter_of[t.from_anchor])
        task = plan["tasks"][f"bridge:{t.from_anchor}->{t.to_anchor}"]
        act["bridges"] += 1
        act["frames"] += task["frames"] - 1
        act["gpu_s"] += est_by_task.get(task["id"], {}).get("exec_s") or 0.0
    for act in acts:
        act["seconds"] = round(act["frames"] / fps, 3)
        act["gpu_hours"] = round(act.pop("gpu_s") / 3600, 2)
    unique = 1 + sum(plan["tasks"][f"bridge:{ids[i]}->{ids[i + 1]}"]["frames"] - 1 for i in range(len(ids) - 1))
    last_anchor_s = (unique - 1) / fps
    coverage = {"head_hold_s": None, "last_anchor_s": last_anchor_s, "tail_hold_s": None, "song_s": None,
                "matches": None}
    if sp and sp.get("coverage"):
        cov = sp["coverage"]
        head = float((sp.get("anchors") or [{}])[0].get("t") or 0.0)  # picture starts at the first anchor
        coverage.update(head_hold_s=head, last_anchor_s=head + last_anchor_s, tail_hold_s=cov.get("hold_s"),
                        song_s=cov.get("song_s"))
        gap = head + last_anchor_s + (cov.get("hold_s") or 0) - (cov.get("song_s") or 0)
        coverage["matches"] = abs(gap) <= 1 / fps + 1e-9
    labels = [r["label"] for r in est["stages"]]
    total_s = est["total_gpu_s"] if est["total_gpu_s"] is not None else est["partial_total_gpu_s"]
    return {"storyboard": str(path), "plan_sha256": plan["plan_sha256"], "acts": acts,
            "totals": {"anchors": len(ids), "bridges": len(sb.transitions), "unique_frames": unique,
                       "seconds": round(unique / fps, 3), "text_to_image": sum(a.generation == "text_to_image"
                                                                              for a in sb.anchors)},
            "coverage": coverage,
            "gpu": {"total_hours": round(total_s / 3600, 2),
                    "label": "estimate (measured medians; others extrapolated by pixels x frames)"
                    + ("" if est["total_gpu_s"] is not None else "; INCOMPLETE - some stages have no data"),
                    "stages_estimated": sum(lbl == ESTIMATED for lbl in labels),
                    "stages_extrapolated": sum(lbl == EXTRAPOLATED for lbl in labels),
                    "stages_no_data": sum(lbl == "NO DATA" for lbl in labels)},
            "note": "Dry run only: no ComfyUI request was made. GPU hours exclude model loading and queue waits."}
