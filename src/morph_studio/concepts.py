"""Engineering concept bank for the full-song film and its validator (F31).

The bank (``configs/concepts/engineering-film.yaml``) lists one subject per anchor in film order across ten
eras, each with physical description, shapes, materials, scale and a morph-affinity note to the next subject.
It is Claude-drafted text (owner rule: no local LLM), generic (no brands, logos or real people) and stays
``draft`` with ``accuracy: unverified`` until the owner approves it and F33 reviews accuracy.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

DEFAULT_BANK = Path("configs/concepts/engineering-film.yaml")
DEFAULT_TARGET = 96  # anchors in the current Mozart sync plan (95 bridges)
MIN_PER_ERA = 5
ERAS = ["natural electricity", "early storage", "generation and grid", "signals and communication",
        "vacuum-tube computing", "solid state", "integrated circuits", "microprocessors",
        "parallel and GPU compute", "data centers and AI hardware"]
TEXT_FIELDS = ("id", "subject", "description", "scale", "morph_to_next", "accuracy_note", "sources")
LIST_FIELDS = ("shapes", "materials")
# Brand / mark terms: whole words, any case.
BRANDS = ("intel", "amd", "nvidia", "ibm", "microsoft", "google", "samsung", "qualcomm", "arm holdings",
          "tsmc", "cray", "dell", "hewlett", "packard", "siemens", "westinghouse", "general electric", "philips",
          "sony", "motorola", "texas instruments", "fairchild", "bell labs", "duracell", "energizer", "tesla motors",
          "logo", "logos", "trademark", "trademarked", "branded", "brand")
# Real people's surnames: capitalized whole words only (lower-case units/adjectives stay allowed).
PEOPLE = ("Franklin", "Volta", "Galvani", "Faraday", "Edison", "Tesla", "Westinghouse", "Morse", "Bell", "Marconi",
          "Babbage", "Lovelace", "Turing", "Shannon", "Neumann", "Eckert", "Mauchly", "Shockley", "Bardeen",
          "Brattain", "Kilby", "Noyce", "Moore", "Ampere", "Ohm", "Maxwell", "Hertz", "Watt", "Kelvin", "Coulomb",
          "Henry", "Oersted", "Hopper", "Jobs", "Wozniak", "Gates", "Huang", "Elmo",
          "Apple")  # brand names that are also ordinary words match only when capitalized
EXCEPTIONS = {"voltaic", "galvanic", "galvanized", "ohmic"}
_BRAND_RE = re.compile(r"\b(" + "|".join(re.escape(b) for b in BRANDS) + r")\b", re.I)
_PEOPLE_RE = re.compile(r"\b(" + "|".join(PEOPLE) + r")\b")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ConceptEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,80}$")
    era: str
    follows: str | None = None
    subject: str = Field(min_length=1)
    description: str = Field(min_length=1)
    shapes: list[str] = Field(min_length=1)
    materials: list[str] = Field(min_length=1)
    scale: str = Field(min_length=1)
    morph_to_next: str | None = None
    accuracy_note: str = Field(min_length=1)
    sources: str = Field(min_length=1)
    accuracy: str = Field(pattern=r"^(unverified|reviewed)$")


class ConceptBank(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(ge=1)
    status: str = Field(pattern=r"^(draft|approved)$")
    approval: dict | None = None
    drafted_by: str | None = None
    eras: list[str]
    entries: list[dict]


def banned_terms(text: str) -> list[str]:
    found = [m.group(0) for m in _BRAND_RE.finditer(text)]
    found += [m.group(0) for m in _PEOPLE_RE.finditer(text)]
    return [f for f in found if f.lower() not in EXCEPTIONS]


def load_bank(path: str | Path = DEFAULT_BANK) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _target_from_plan(plan: str | Path) -> int:
    data = json.loads(Path(plan).read_text(encoding="utf-8"))
    summary = data.get("summary") or {}
    if "anchors" in summary:
        return int(summary["anchors"])
    if isinstance(data.get("anchors"), list):
        return len(data["anchors"])
    raise ValueError("sync plan has no anchors")


def check(path: str | Path = DEFAULT_BANK, *, target: int | None = None, plan: str | Path | None = None) -> dict:
    problems: list[dict] = []

    def add(eid, field, message):
        problems.append({"id": eid, "field": field, "message": message})

    try:
        raw = load_bank(path)
        bank = ConceptBank.model_validate(raw)
    except (ValidationError, yaml.YAMLError, OSError) as exc:
        return {"ok": False, "problems": [{"id": "-", "field": "bank", "message": str(exc)}], "counts": {},
                "total": 0, "status": None, "target": target}
    if bank.eras != ERAS:
        add("-", "eras", f"eras must be exactly, in order: {ERAS}")
    if plan is not None:
        try:
            target = _target_from_plan(plan)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            add("-", "plan", f"cannot read anchor count from sync plan {plan}: {exc}")
    target = DEFAULT_TARGET if target is None else target
    entries: list[ConceptEntry] = []
    for i, item in enumerate(bank.entries):
        try:
            entries.append(ConceptEntry.model_validate(item))
        except ValidationError as exc:
            for err in exc.errors():
                add(item.get("id", f"#{i + 1}"), ".".join(str(x) for x in err["loc"]), err["msg"])
    if len(entries) != len(bank.entries):
        return _report(False, problems, entries, bank, target)
    seen: set[str] = set()
    last_era = 0
    for i, e in enumerate(entries):
        if e.id in seen:
            add(e.id, "id", "duplicate id")
        seen.add(e.id)
        if e.era not in ERAS:
            add(e.id, "era", f"unknown era {e.era!r}")
        else:
            idx = ERAS.index(e.era)
            if idx < last_era:
                add(e.id, "era", f"era goes backwards ({e.era!r} after {ERAS[last_era]!r})")
            last_era = max(last_era, idx)
        expected = entries[i - 1].id if i else None
        if e.follows != expected:
            add(e.id, "follows", f"must follow {expected!r} (single ordered chain), got {e.follows!r}")
        if i < len(entries) - 1 and not (e.morph_to_next or "").strip():
            add(e.id, "morph_to_next", "missing morph-affinity note to the next subject")
        for field in TEXT_FIELDS:
            for term in banned_terms(getattr(e, field) or ""):
                add(e.id, field, f"banned term {term!r} (no brands, logos or real people)")
        for field in LIST_FIELDS:
            for term in banned_terms(" ".join(getattr(e, field))):
                add(e.id, field, f"banned term {term!r} (no brands, logos or real people)")
    counts = {era: sum(1 for e in entries if e.era == era) for era in ERAS}
    for era, n in counts.items():
        if n < MIN_PER_ERA:
            add("-", "era", f"era {era!r} has {n} entries; needs at least {MIN_PER_ERA}")
    if len(entries) < target:
        add("-", "entries", f"{len(entries)} entries for {target} anchors; need at least {target}")
    approval = bank.approval
    approval_ok = isinstance(approval, dict) and str(approval.get("owner") or "").strip() \
        and _DATE.match(str(approval.get("date") or ""))
    if bank.status == "approved" and not approval_ok:
        add("-", "approval", "status approved needs approval {owner: name, date: YYYY-MM-DD}")
    if approval is not None and not approval_ok:
        add("-", "approval", "approval record needs a non-empty owner and an ISO date")
    return _report(not problems, problems, entries, bank, target)


def _report(ok, problems, entries, bank, target) -> dict:
    return {"ok": ok, "total": len(entries), "target": target, "status": bank.status,
            "counts": {era: sum(1 for e in entries if e.era == era) for era in ERAS}, "problems": problems,
            "note": "Trademarked product designs cannot be detected automatically; owner review covers them."}


def coverage(bank: dict) -> dict:
    return {era: sum(1 for e in bank["entries"] if e["era"] == era) for era in ERAS}


def listing(bank: dict) -> list[str]:
    width = len(str(len(bank["entries"])))
    return [f"{i:0{max(2, width)}d} [{e['era']}] {e['subject']} -> {e.get('morph_to_next', '(end)')}"
            for i, e in enumerate(bank["entries"], 1)]
