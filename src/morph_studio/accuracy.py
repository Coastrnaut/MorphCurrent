"""Technical accuracy and visual-plausibility review (F33). Offline; verdicts are the owner's.

Each anchor image gets a five-item checklist (component class, geometry, no gibberish text, no fake schematic
symbols, era materials) and an owner verdict - accurate / reject / waive - tied to the image's SHA-256 in an
append-only JSON Lines log, so a re-render makes the verdict stale. ``text_free_check`` verifies that every
anchor and bridge prompt carries the text/logo negatives. ``impact`` lists what a rejection invalidates:
the anchor, every reference-edited descendant (stopping at separately generated anchors), every bridge
touching them and the final movie, with deterministic regeneration seeds.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from .cache import sha256_file
from .timeline import derived_seed

CHECKLIST = {
    "component_class": "Is it the right kind of component or object for this subject?",
    "plausible_geometry": "Is its geometry physically plausible (parts, proportions, connections)?",
    "no_text": "Is it free of gibberish text, letters or labels?",
    "no_fake_symbols": "Is it free of fake schematic symbols or impossible markings?",
    "era_materials": "Are its materials and finish right for the era?",
}
TEXT_NEGATIVES = ("text", "letters", "labels", "logo", "watermark")
VERDICTS = ("accurate", "reject", "waive")
_SHA = re.compile(r"^[0-9a-f]{64}$")


class AccuracyError(ValueError):
    pass


def default_log(storyboard_name: str, repo_root: str | Path = ".") -> Path:
    return Path(repo_root) / "outputs" / "reviews" / f"{storyboard_name}.accuracy.jsonl"


def load_plan(storyboard: str | Path, repo_root: str | Path = ".") -> dict:
    from .dag import compile_plan
    from .schema import load_storyboard
    path = Path(storyboard)
    plan = compile_plan(load_storyboard(path), repo_root=repo_root, storyboard_bytes=path.read_bytes())
    plan["_storyboard_path"] = str(path)
    return plan


def _anchor_ids(plan: dict) -> list[str]:
    return [plan["tasks"][t]["anchor"] for t in plan["order"] if plan["tasks"][t]["kind"] == "anchor"]


def checklist(storyboard: str | Path, bank: str | Path | None = None, *, repo_root: str | Path = ".") -> list[dict]:
    plan = load_plan(storyboard, repo_root)
    concepts = {}
    if bank and Path(bank).is_file():
        from .concepts import load_bank
        concepts = {e["id"]: e for e in load_bank(bank)["entries"]}
    rows = []
    for anchor in _anchor_ids(plan):
        task = plan["tasks"][f"anchor:{anchor}"]
        c = concepts.get(anchor, {})
        rows.append({"anchor": anchor, "chapter": task.get("chapter"), "method": task["method"],
                     "subject": c.get("subject"), "description": c.get("description"),
                     "accuracy_note": c.get("accuracy_note"), "era": c.get("era"),
                     "items": [{"key": k, "question": q} for k, q in CHECKLIST.items()]})
    return rows


# --------------------------------------------------------------------------------------------- log

def load_log(log: str | Path) -> tuple[list[dict], list[int]]:
    path = Path(log)
    if not path.is_file():
        return [], []
    entries, corrupt = [], []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except ValueError:
            corrupt.append(number)
    return entries, corrupt


def latest(entries: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for e in entries:
        out[e["anchor"]] = e
    return out


def record_verdict(log: str | Path, plan: dict, anchor: str, *, verdict: str, image_sha256: str | None = None,
                   image: str | Path | None = None, failed: list[str] | tuple = (), note: str = "",
                   reviewer: str = "owner") -> dict:
    if anchor not in _anchor_ids(plan):
        raise AccuracyError(f"anchor {anchor!r} is not in storyboard {plan.get('storyboard')!r}")
    if verdict not in VERDICTS:
        raise AccuracyError(f"verdict must be one of {VERDICTS}")
    if image is not None:
        image_sha256 = sha256_file(Path(image))
    if not image_sha256 or not _SHA.match(image_sha256):
        raise AccuracyError("a verdict needs the anchor image hash (64 hex) or the image file; verdicts are about pixels")
    unknown = [f for f in failed if f not in CHECKLIST]
    if unknown:
        raise AccuracyError(f"unknown checklist item(s) {unknown}; valid: {list(CHECKLIST)}")
    if verdict == "accurate" and failed:
        raise AccuracyError("an accurate verdict needs every checklist item to pass")
    if verdict == "reject" and not failed and not note.strip():
        raise AccuracyError("a reject verdict needs at least one failed item or a note")
    if verdict == "waive" and not note.strip():
        raise AccuracyError("a waiver needs a reason (--note)")
    record = {"t": datetime.now(timezone.utc).isoformat(timespec="seconds"), "storyboard": plan.get("storyboard"),
              "anchor": anchor, "image_sha256": image_sha256, "verdict": verdict,
              "items": {k: ("fail" if k in failed else "pass") for k in CHECKLIST}, "note": note, "reviewer": reviewer}
    path = Path(log)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return record


# ------------------------------------------------------------------------------------- negatives

def has_terms(text: str | None) -> list[str]:
    """Missing text-free negative terms (whole words, any case)."""
    words = set(re.findall(r"[a-z]+", (text or "").lower()))
    return [t for t in TEXT_NEGATIVES if t not in words]


def text_free_check(plan: dict) -> dict:
    missing, stages = [], 0
    for task_id in plan["order"]:
        task = plan["tasks"][task_id]
        if task["kind"] not in ("anchor", "bridge"):
            continue
        stages += 1
        lacking = has_terms(task.get("negative_prompt"))
        if lacking:
            missing.append({"stage": task_id, "terms": lacking,
                            "negative_prompt": "(workflow default)" if not task.get("negative_prompt") else "own"})
    return {"ok": not missing, "stages": stages, "missing": missing, "terms": list(TEXT_NEGATIVES)}


# ----------------------------------------------------------------------------------------- impact

def impact(plan: dict, rejected: list[str], *, prior_rejections: dict[str, int] | None = None) -> dict:
    anchors = _anchor_ids(plan)
    for a in rejected:
        if a not in anchors:
            raise AccuracyError(f"anchor {a!r} is not in the plan")
    invalid = set(rejected)
    for anchor in anchors:  # plan order is topological: references always precede
        task = plan["tasks"][f"anchor:{anchor}"]
        if task.get("conditioned_on_parent") and task.get("reference") in invalid:
            invalid.add(anchor)
    bridges = [t for t in plan["order"] if plan["tasks"][t]["kind"] == "bridge"
               and (plan["tasks"][t]["from"] in invalid or plan["tasks"][t]["to"] in invalid)]
    master = plan.get("_master_seed")
    regen = []
    for anchor in [a for a in anchors if a in set(rejected)]:
        task = plan["tasks"][f"anchor:{anchor}"]
        retry = (prior_rejections or {}).get(anchor, 0) + 1
        seed = derived_seed(master or 0, f"anchor:{anchor}:retry{retry}")
        while seed == task["seed"]:
            retry += 1
            seed = derived_seed(master or 0, f"anchor:{anchor}:retry{retry}")
        regen.append({"anchor": anchor, "current_seed": task["seed"], "new_seed": seed, "retry": retry})
    ordered_anchors = [a for a in anchors if a in invalid]
    rerender = [f"anchor:{a}" for a in ordered_anchors] + bridges + ["final:movie"]
    gpu_total = sum(plan["tasks"][t]["kind"] in ("anchor", "bridge") for t in plan["order"])
    return {"rejected": list(dict.fromkeys(rejected)), "invalidated_anchors": ordered_anchors,
            "invalidated_bridges": bridges, "final": True, "preserved": gpu_total - len(ordered_anchors) - len(bridges),
            "regenerate": regen, "rerender_order": rerender,
            "note": "Reference-edited descendants are invalidated transitively; separately generated "
                    "(text-to-image / independent) anchors stop the chain."}


def impact_for(storyboard: str | Path, rejected: list[str], *, log: str | Path | None = None,
               repo_root: str | Path = ".") -> dict:
    from .schema import load_storyboard
    plan = load_plan(storyboard, repo_root)
    plan["_master_seed"] = load_storyboard(storyboard).render.master_seed
    prior: dict[str, int] = {}
    if log:
        for e in load_log(log)[0]:
            if e.get("verdict") == "reject":
                prior[e["anchor"]] = prior.get(e["anchor"], 0) + 1
    return impact(plan, rejected, prior_rejections=prior)


# ----------------------------------------------------------------------------------------- status

def _run_hashes(run_dir: str | Path | None) -> dict[str, str]:
    if not run_dir:
        return {}
    manifest = json.loads((Path(run_dir) / "manifest.json").read_text(encoding="utf-8"))
    return {k.split(":", 1)[1]: v.get("image_sha256") for k, v in (manifest.get("stages") or {}).items()
            if k.startswith("anchor:") and v.get("image_sha256")}


def status(storyboard: str | Path, log: str | Path, *, run_dir: str | Path | None = None,
           repo_root: str | Path = ".") -> dict:
    plan = load_plan(storyboard, repo_root)
    current = _run_hashes(run_dir)
    entries, corrupt = load_log(log)
    last = latest(entries)
    rows = []
    for anchor in _anchor_ids(plan):
        image = current.get(anchor)
        v = last.get(anchor)
        if not image:
            state = "pending"
        elif not v:
            state = "pending"
        elif v["image_sha256"] != image:
            state = "stale"
        else:
            state = {"accurate": "accurate", "waive": "waived", "reject": "rejected"}[v["verdict"]]
        rows.append({"anchor": anchor, "state": state, "image_sha256": image,
                     "verdict_sha256": v["image_sha256"] if v else None})
    counts = {s: sum(r["state"] == s for r in rows) for s in ("accurate", "waived", "rejected", "stale", "pending")}
    return {"storyboard": plan["storyboard"], "anchors": rows, "counts": counts, "corrupt_log_lines": corrupt,
            "gate": counts["accurate"] + counts["waived"] == len(rows) and not corrupt,
            "note": "Verdicts are the owner's; the gate needs every anchor accurate or waived for its current image."}
