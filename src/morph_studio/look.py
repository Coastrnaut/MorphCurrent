"""Engineering visual language for the full-song film (F34).

``configs/film/visual-language.yaml`` holds candidate looks: per act a palette, lighting and bridge camera,
on top of the engineering-noir style pack. ``apply_look`` writes the chosen look into a storyboard (anchor
style overrides, bridge choreography camera), ``look_check`` verifies it in the compiled prompts,
``drift_report`` measures subject colour and geometry of rendered anchors against the thresholds, and
``look_test`` writes two short storyboards for an owner A/B comparison.
"""
from __future__ import annotations

import copy
import math
from pathlib import Path

import yaml

from .prompt_compiler import CAMERA

DEFAULT_LANGUAGE = Path("configs/film/visual-language.yaml")
CAMERAS = ("static", "slow_push", "slow_pull")


class LookError(ValueError):
    pass


def _norm(colour: str) -> str:
    return " ".join(str(colour).lower().split())


def load_language(path: str | Path = DEFAULT_LANGUAGE, act_ids: list[str] | None = None) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    looks = data.get("looks") or {}
    if len(looks) < 2:
        raise LookError("the visual language needs at least two candidate looks")
    if data.get("default_look") not in looks:
        raise LookError("default_look must name one of the looks")
    if data.get("selected") not in (None, *looks):
        raise LookError("selected must be null or one of the looks")
    for name, look in looks.items():
        acts = look.get("acts") or {}
        order = act_ids or list(acts)
        for act in order:
            spec = acts.get(act)
            if not spec:
                raise LookError(f"look {name!r} does not define act {act!r}")
            if len(spec.get("palette") or []) < 2:
                raise LookError(f"look {name!r} act {act!r}: palette needs at least 2 colours")
            if not str(spec.get("lighting") or "").strip():
                raise LookError(f"look {name!r} act {act!r}: lighting is required")
            if spec.get("camera") not in CAMERAS:
                raise LookError(f"look {name!r} act {act!r}: camera must be one of {CAMERAS}")
        for left, right in zip(order, order[1:]):
            shared = {_norm(c) for c in acts[left]["palette"]} & {_norm(c) for c in acts[right]["palette"]}
            if not shared:
                raise LookError(f"look {name!r}: acts {left!r} and {right!r} must share at least one palette colour")
    return data


def choose(language: dict, look: str | None = None) -> tuple[str, dict, str]:
    if look is not None:
        if look not in language["looks"]:
            raise LookError(f"unknown look {look!r}; available: {sorted(language['looks'])}")
        return look, language["looks"][look], "requested"
    if language.get("selected"):
        return language["selected"], language["looks"][language["selected"]], "owner-selected"
    name = language["default_look"]
    return name, language["looks"][name], "default (not owner-selected)"


def apply_look(storyboard: dict, look: dict) -> dict:
    """Return a copy with per-anchor palette/lighting overrides and per-bridge camera by act."""
    data = copy.deepcopy(storyboard)
    acts = look["acts"]
    chapter = {}
    for anchor in data["anchors"]:
        spec = acts.get(anchor.get("chapter"))
        chapter[anchor["id"]] = anchor.get("chapter")
        if spec:
            anchor["style_override"] = {"palette": list(spec["palette"]), "lighting": spec["lighting"]}
    for t in data["transitions"]:
        spec = acts.get(chapter.get(t["from"]))
        if spec:
            chor = dict(t.get("choreography") or {})
            chor["camera"] = spec["camera"]
            t["choreography"] = chor
    return data


def look_check(plan: dict, storyboard, language: dict, look: str | None = None) -> dict:
    name, spec, how = choose(language, look)
    chapter = {a.id: a.chapter for a in storyboard.anchors}
    mismatches, stages, style_by_act = [], 0, {}
    for task_id in plan["order"]:
        task = plan["tasks"][task_id]
        if task["kind"] == "anchor":
            stages += 1
            act = spec["acts"].get(chapter.get(task["anchor"]))
            if not act:
                mismatches.append({"stage": task_id, "problem": f"act {chapter.get(task['anchor'])!r} not in look"})
                continue
            prompt = _norm(task["positive_prompt"])
            for colour in act["palette"]:
                if _norm(colour) not in prompt:
                    mismatches.append({"stage": task_id, "problem": f"palette colour {colour!r} missing"})
            if _norm(act["lighting"]) not in prompt:
                mismatches.append({"stage": task_id, "problem": "act lighting missing"})
            sha = task.get("style_sha256")
            prev = style_by_act.setdefault(chapter[task["anchor"]], sha)
            if prev != sha:
                mismatches.append({"stage": task_id, "problem": "style identity differs within the act"})
        elif task["kind"] == "bridge":
            stages += 1
            act = spec["acts"].get(chapter.get(task["from"]))
            if act and CAMERA[act["camera"]] not in task["positive_prompt"]:
                mismatches.append({"stage": task_id, "problem": f"bridge camera {act['camera']!r} missing"})
    return {"look": name, "selection": how, "stages": stages, "mismatches": mismatches, "ok": not mismatches}


def _distance(a: list[float], b: list[float]) -> float:
    return round(math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b))), 1)


def drift_report(storyboard: str | Path, run_dir: str | Path, language: dict) -> dict:
    from .geometry import image_geometry
    from .release import _stage_files
    from .schema import load_storyboard
    sb = load_storyboard(storyboard)
    files = _stage_files(Path(run_dir))
    geo, missing = {}, []
    for a in sb.anchors:
        file = (files.get(f"anchor:{a.id}") or {}).get("file")
        if file and Path(file).is_file():
            geo[a.id] = image_geometry(file)
        else:
            missing.append(a.id)
    g, d = language["geometry"], language["drift"]
    acts: list[dict] = []
    for a in sb.anchors:
        act = a.chapter or "(whole film)"
        if not acts or acts[-1]["id"] != act:
            acts.append({"id": act, "anchors": [], "measured": 0})
        acts[-1]["anchors"].append(a.id)
    for act in acts:
        colours = [geo[x]["mean_colour"] for x in act["anchors"] if x in geo and "mean_colour" in geo[x]]
        act["measured"] = len(colours)
        if colours:
            mean = [round(sum(c[i] for c in colours) / len(colours), 1) for i in range(3)]
            spread = max(_distance(c, mean) for c in colours)
            act.update(mean_colour=mean, spread=spread, spread_flag=spread > d["act_spread_max"])
    boundaries = []
    for left, right in zip(acts, acts[1:]):
        x, y = left["anchors"][-1], right["anchors"][0]
        if x in geo and y in geo and "mean_colour" in geo[x] and "mean_colour" in geo[y]:
            jump = _distance(geo[x]["mean_colour"], geo[y]["mean_colour"])
            boundaries.append({"from_act": left["id"], "to_act": right["id"], "from_anchor": x, "to_anchor": y,
                               "jump": jump, "flag": jump > d["boundary_jump_max"]})
    off_centre = []
    for a in sb.anchors:
        c = geo.get(a.id, {}).get("centroid")
        if c:
            offset = round(math.hypot(c[0] - 0.5, c[1] - 0.5), 4)
            if offset > g["centroid_max"]:
                off_centre.append({"anchor": a.id, "offset": offset})
    scale_jumps = []
    lo, hi = g["scale_ratio"]
    for p, q in zip(sb.anchors, sb.anchors[1:]):
        ep, eq = geo.get(p.id, {}).get("extent"), geo.get(q.id, {}).get("extent")
        if ep and eq and ep[0] and ep[1]:
            ratio = round(math.sqrt((eq[0] * eq[1]) / (ep[0] * ep[1])), 3)
            if not lo <= ratio <= hi:
                scale_jumps.append({"from": p.id, "to": q.id, "ratio": ratio})
    flagged = any(a.get("spread_flag") for a in acts) or any(b["flag"] for b in boundaries) or off_centre or scale_jumps
    return {"storyboard": sb.name, "acts": acts, "boundaries": boundaries, "off_centre": off_centre,
            "scale_jumps": scale_jumps, "missing": missing, "ok": not flagged,
            "note": "Subject colour from the F12 luminance mask; thresholds are starting points for owner calibration."}


def look_test(storyboard: str | Path, language: dict, *, act: str = "spark", count: int = 5,
              out_dir: str | Path = "outputs/look-test") -> list[str]:
    data = yaml.safe_load(Path(storyboard).read_text(encoding="utf-8"))
    anchors = [a for a in data["anchors"] if a.get("chapter") == act][:count]
    if not anchors:
        raise LookError(f"act {act!r} has no anchors in {storyboard}")
    ids = [a["id"] for a in anchors]
    base = copy.deepcopy(data)
    base["anchors"] = copy.deepcopy(anchors)
    base["anchors"][0].pop("reference", None)
    base["anchors"][0]["generation"] = "text_to_image"
    base["transitions"] = [copy.deepcopy(t) for t in data["transitions"] if t["from"] in ids and t["to"] in ids]
    out = Path(out_dir)
    targets = {name: out / f"{name}.yaml" for name in sorted(language["looks"])}
    for path in targets.values():
        if path.exists():
            raise FileExistsError(f"{path} exists; refusing to overwrite")
    out.mkdir(parents=True, exist_ok=True)
    from .schema import Storyboard
    written = []
    for name, path in targets.items():
        sb = apply_look(base, language["looks"][name])
        sb["name"] = f"look-test-{name}"
        Storyboard.model_validate(sb)
        path.write_text(f"# F34 A/B look test: act {act}, first {len(ids)} anchors, look {name!r}.\n"
                        + yaml.safe_dump(sb, sort_keys=False, width=120), encoding="utf-8")
        written.append(str(path))
    return written
