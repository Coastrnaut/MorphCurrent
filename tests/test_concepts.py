"""F31: engineering concept bank (Claude-drafted) and its validator."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml

from morph_studio import cli
from morph_studio import concepts as cc

from conftest import REPO

BANK = REPO / "configs/concepts/engineering-film.yaml"


def load() -> dict:
    return yaml.safe_load(BANK.read_text(encoding="utf-8"))


def write(tmp_path: Path, data: dict, name: str = "bank.yaml") -> Path:
    path = tmp_path / name
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def problems(path, **kw) -> str:
    rep = cc.check(path, **kw)
    assert not rep["ok"]
    return " | ".join(f"{p['id']}:{p['field']}:{p['message']}" for p in rep["problems"])


# --- foundational ---------------------------------------------------------------------------------

def test_banned_terms():
    assert cc.banned_terms("a sleek Intel-style chip") == ["Intel"]
    assert cc.banned_terms("an apple-shaped logo on the lid") == ["logo"]
    assert cc.banned_terms("a portrait of Faraday at his bench") == ["Faraday"]
    assert cc.banned_terms("a voltaic pile measured in volts, ohms and teslas") == []
    assert cc.banned_terms("a bell jar and a morse-like rhythm") == []  # lower-case generic words
    assert cc.banned_terms("Bell") == ["Bell"]


# --- US1 real bank --------------------------------------------------------------------------------

def test_real_bank_passes():
    rep = cc.check(BANK, target=96)
    assert rep["ok"], rep["problems"]
    assert rep["total"] == 96 and rep["status"] == "approved"  # owner blanket approval 2026-11-24
    assert list(rep["counts"]) == cc.ERAS and all(n >= 5 for n in rep["counts"].values())
    data = load()
    assert data["approval"] == {"owner": "owner", "date": "2026-11-24"}
    assert all(e["accuracy"] == "unverified" and "F33" in e["sources"] for e in data["entries"])
    assert "morph_to_next" not in data["entries"][-1]


# --- US2 failure modes ----------------------------------------------------------------------------

def mutate(tmp_path, fn, **kw):
    data = copy.deepcopy(load())
    fn(data)
    return problems(write(tmp_path, data), **kw)


def test_duplicate_and_missing_field(tmp_path):
    def dup(d):
        d["entries"][5]["id"] = d["entries"][4]["id"]
    assert "duplicate" in mutate(tmp_path, dup)
    assert "materials" in mutate(tmp_path, lambda d: d["entries"][3].pop("materials"))


def test_era_order_and_coverage(tmp_path):
    def backwards(d):
        d["entries"][20]["era"] = "natural electricity"
    assert "era" in mutate(tmp_path, backwards)

    def thin(d):
        keep = [e for e in d["entries"] if e["era"] != "solid state"][:]
        solid = [e for e in d["entries"] if e["era"] == "solid state"][:3]
        d["entries"] = [e for e in d["entries"] if e["era"] != "solid state" or e in solid]
        for i, e in enumerate(d["entries"][1:], 1):
            e["follows"] = d["entries"][i - 1]["id"]
        del keep
    assert "at least 5" in mutate(tmp_path, thin, target=1)


def test_link_notes_and_chain(tmp_path):
    assert "morph_to_next" in mutate(tmp_path, lambda d: d["entries"][10].pop("morph_to_next"))
    assert "follows" in mutate(tmp_path, lambda d: d["entries"][12].update(follows="nowhere"))
    assert "follows" in mutate(tmp_path, lambda d: d["entries"][12].update(follows=d["entries"][3]["id"]))


def test_banned_in_fields(tmp_path):
    out = mutate(tmp_path, lambda d: d["entries"][40].update(description="a chip with a NVIDIA logo"))
    assert "NVIDIA" in out and "description" in out
    assert "Edison" in mutate(tmp_path, lambda d: d["entries"][2].update(subject="Edison's lamp"))


def test_counts_against_target_and_plan(tmp_path):
    assert "97" in problems(BANK, target=97)
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"anchors": [{"frame": i} for i in range(100)],
                                "summary": {"anchors": 100, "bridges": 99}}), encoding="utf-8")
    assert "100" in problems(BANK, plan=plan)
    plan.write_text(json.dumps({"summary": {"anchors": 96}}), encoding="utf-8")
    assert cc.check(BANK, plan=plan)["ok"]
    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    assert "plan" in problems(BANK, plan=bad)


def test_approval_rules(tmp_path):
    assert "approval" in mutate(tmp_path, lambda d: d.update(status="approved", approval=None))
    assert "approval" in mutate(tmp_path, lambda d: d.update(status="approved", approval={"owner": "", "date": "2026-11-24"}))
    assert "approval" in mutate(tmp_path, lambda d: d.update(status="approved", approval={"owner": "x", "date": "24/11/2026"}))
    data = copy.deepcopy(load())
    data.update(status="approved", approval={"owner": "owner", "date": "2026-11-25"})
    rep = cc.check(write(tmp_path, data, "ok.yaml"), target=96)
    assert rep["ok"] and rep["status"] == "approved"


# --- US3 review -----------------------------------------------------------------------------------

def test_coverage_and_listing():
    bank = cc.load_bank(BANK)
    cov = cc.coverage(bank)
    assert sum(cov.values()) == 96 and list(cov) == cc.ERAS
    lines = cc.listing(bank)
    assert len(lines) == 96 and lines[0].startswith("01 ") and "->" in lines[0]
    assert lines[-1].startswith("96 ")


# --- CLI ------------------------------------------------------------------------------------------

def test_cli(tmp_path, capsys):
    assert cli.main(["concepts-check"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] and out["total"] == 96
    assert cli.main(["concepts-check", "--target", "120"]) == 1
    capsys.readouterr()
    assert cli.main(["concepts-list"]) == 0
    text = capsys.readouterr().out
    text.encode("ascii")
    assert len(text.strip().splitlines()) == 96
    assert cli.main(["concepts-list", "--json"]) == 0
    assert len(json.loads(capsys.readouterr().out)["entries"]) == 96
