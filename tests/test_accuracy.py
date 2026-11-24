"""F33: accuracy checklist, owner verdict log, text-free prompting check, rejection impact and status."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from morph_studio import accuracy as ac
from morph_studio import cli
from morph_studio.dag import compile_plan
from morph_studio.schema import Storyboard, load_storyboard

from conftest import REPO

FILM = REPO / "configs/sequences/engineering-film.yaml"
ORGANIC = REPO / "configs/sequences/organic-machines.yaml"


def h(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def synthetic() -> dict:
    """a -> b -> c (edits) | d (text_to_image) -> e (edit) | f (independent, continuity ref e) -> g (edit of f)."""
    anchors = [{"id": "a", "prompt": "a"},
               {"id": "b", "prompt": "b", "generation": "reference_edit", "reference": "a"},
               {"id": "c", "prompt": "c", "generation": "reference_edit", "reference": "b"},
               {"id": "d", "prompt": "d"},
               {"id": "e", "prompt": "e", "generation": "reference_edit", "reference": "d"},
               {"id": "f", "prompt": "f", "generation": "independent_t2i", "reference": "e"},
               {"id": "g", "prompt": "g", "generation": "reference_edit", "reference": "f"}]
    ids = [a["id"] for a in anchors]
    return {"schema_version": 1, "name": "synthetic",
            "render": {"anchor_profile": "anchor_t2i", "bridge_profile": "wan22_flf2v", "master_seed": 7},
            "style": {"description": "x"}, "anchors": anchors,
            "transitions": [{"from": ids[i], "to": ids[i + 1], "frames": 33, "prompt": "m"} for i in range(6)]}


def plan_of(data: dict) -> dict:
    return compile_plan(Storyboard.model_validate(data), repo_root=REPO)


@pytest.fixture()
def film_plan() -> dict:
    return compile_plan(load_storyboard(FILM), repo_root=REPO, storyboard_bytes=FILM.read_bytes())


# --- US1 ------------------------------------------------------------------------------------------

def test_checklist_has_concept_context():
    rows = ac.checklist(FILM, REPO / "configs/concepts/engineering-film.yaml", repo_root=REPO)
    assert len(rows) == 96
    first = rows[0]
    assert first["subject"] and first["accuracy_note"] and [i["key"] for i in first["items"]] == list(ac.CHECKLIST)
    assert len(ac.CHECKLIST) == 5


def test_verdict_rules_and_log(tmp_path):
    log = tmp_path / "rev.jsonl"
    sb = ac.load_plan(FILM, REPO)
    with pytest.raises(ac.AccuracyError, match="every"):
        ac.record_verdict(log, sb, "forked-lightning-bolt", verdict="accurate", image_sha256=h("x"), failed=["no_text"])
    with pytest.raises(ac.AccuracyError, match="failed item or a note"):
        ac.record_verdict(log, sb, "forked-lightning-bolt", verdict="reject", image_sha256=h("x"))
    with pytest.raises(ac.AccuracyError, match="reason"):
        ac.record_verdict(log, sb, "forked-lightning-bolt", verdict="waive", image_sha256=h("x"))
    with pytest.raises(ac.AccuracyError, match="not in"):
        ac.record_verdict(log, sb, "unicorn", verdict="accurate", image_sha256=h("x"))
    with pytest.raises(ac.AccuracyError, match="hash"):
        ac.record_verdict(log, sb, "forked-lightning-bolt", verdict="accurate")
    with pytest.raises(ac.AccuracyError, match="checklist"):
        ac.record_verdict(log, sb, "forked-lightning-bolt", verdict="reject", image_sha256=h("x"), failed=["vibes"])
    assert not log.exists()
    ac.record_verdict(log, sb, "forked-lightning-bolt", verdict="reject", image_sha256=h("x"), failed=["no_text"])
    img = tmp_path / "a.png"
    img.write_bytes(b"pixels")
    rec = ac.record_verdict(log, sb, "forked-lightning-bolt", verdict="accurate", image=img, reviewer="owner")
    assert rec["image_sha256"] == hashlib.sha256(b"pixels").hexdigest()
    entries, corrupt = ac.load_log(log)
    assert len(entries) == 2 and corrupt == []
    assert ac.latest(entries)["forked-lightning-bolt"]["verdict"] == "accurate"
    with log.open("a", encoding="utf-8") as f:
        f.write("{not json\n")
    assert ac.load_log(log)[1] == [3]


# --- US2 ------------------------------------------------------------------------------------------

def test_text_free_check(film_plan):
    rep = ac.text_free_check(film_plan)
    assert rep["ok"], rep["missing"][:3]
    assert rep["stages"] == 191
    organic = compile_plan(load_storyboard(ORGANIC), repo_root=REPO)
    bad = ac.text_free_check(organic)
    assert not bad["ok"] and any(m["stage"].startswith("anchor:") for m in bad["missing"])
    assert any(m["stage"].startswith("bridge:") for m in bad["missing"])
    assert ac.has_terms("no text, letters, labels, logo, watermark") == []
    assert ac.has_terms("textures, lettering") == list(ac.TEXT_NEGATIVES)


# --- US3 ------------------------------------------------------------------------------------------

def test_impact_transitive_and_boundaries():
    plan = plan_of(synthetic())
    imp = ac.impact(plan, ["b"])
    assert imp["invalidated_anchors"] == ["b", "c"]
    assert imp["invalidated_bridges"] == ["bridge:a->b", "bridge:b->c", "bridge:c->d"]
    assert imp["final"] is True and imp["preserved"] == len(plan["order"]) - 6
    imp2 = ac.impact(plan, ["d"])
    assert imp2["invalidated_anchors"] == ["d", "e"]  # f is independent: chain stops; g follows f, untouched
    assert "bridge:e->f" in imp2["invalidated_bridges"] and "bridge:f->g" not in imp2["invalidated_bridges"]
    both = ac.impact(plan, ["b", "c"])
    assert both["invalidated_anchors"] == ["b", "c"]
    with pytest.raises(ac.AccuracyError):
        ac.impact(plan, ["zzz"])


def test_regeneration_seeds():
    plan = plan_of(synthetic())
    imp = ac.impact(plan, ["b"], prior_rejections={"b": 2})
    regen = imp["regenerate"]
    assert [r["anchor"] for r in regen] == ["b"]
    assert regen[0]["new_seed"] != regen[0]["current_seed"] and regen[0]["retry"] == 3
    assert ac.impact(plan, ["b"], prior_rejections={"b": 2})["regenerate"] == regen  # deterministic
    assert imp["rerender_order"][0] == "anchor:b" and imp["rerender_order"][-1] == "final:movie"


def test_film_rejection_stays_in_act(film_plan):
    sb = load_storyboard(FILM)
    chapter = {a.id: a.chapter for a in sb.anchors}
    signal = [a.id for a in sb.anchors if a.chapter == "signal"]
    imp = ac.impact(film_plan, [signal[2]])
    assert imp["invalidated_anchors"] == signal[2:]
    for stage in imp["invalidated_bridges"]:
        a, b = stage.split(":", 1)[1].split("->")
        assert chapter[a] == "signal" or chapter[b] == "signal"


# --- US4 ------------------------------------------------------------------------------------------

def fake_run(tmp_path, hashes: dict) -> Path:
    run = tmp_path / "run-x"
    run.mkdir()
    stages = {f"anchor:{k}": {"state": "verified", "image_sha256": v} for k, v in hashes.items()}
    (run / "manifest.json").write_text(json.dumps({"stages": stages, "order": list(stages)}), encoding="utf-8")
    return run


def test_status(tmp_path):
    data = synthetic()
    path = tmp_path / "sb.yaml"
    import yaml
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    log = tmp_path / "rev.jsonl"
    st = ac.status(path, log, repo_root=REPO)
    assert st["counts"]["pending"] == 7 and not st["gate"]
    hashes = {k: h(k) for k in "abcdefg"}
    run = fake_run(tmp_path, hashes)
    sb = ac.load_plan(path, REPO)
    ac.record_verdict(log, sb, "a", verdict="accurate", image_sha256=hashes["a"])
    ac.record_verdict(log, sb, "b", verdict="waive", image_sha256=hashes["b"], note="stylized")
    ac.record_verdict(log, sb, "c", verdict="reject", image_sha256=hashes["c"], note="fake labels")
    ac.record_verdict(log, sb, "d", verdict="accurate", image_sha256=h("old render"))
    st = ac.status(path, log, run_dir=run, repo_root=REPO)
    states = {r["anchor"]: r["state"] for r in st["anchors"]}
    assert states == {"a": "accurate", "b": "waived", "c": "rejected", "d": "stale", "e": "pending",
                      "f": "pending", "g": "pending"}
    assert not st["gate"]
    for k in "cdefg":
        ac.record_verdict(log, sb, k, verdict="accurate", image_sha256=hashes[k])
    assert ac.status(path, log, run_dir=run, repo_root=REPO)["gate"] is True


# --- CLI ------------------------------------------------------------------------------------------

def test_cli(tmp_path, capsys):
    log = tmp_path / "r.jsonl"
    assert cli.main(["accuracy-negatives", str(FILM)]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True
    assert cli.main(["accuracy-negatives", str(ORGANIC)]) == 1
    capsys.readouterr()
    assert cli.main(["accuracy-checklist", str(FILM)]) == 0
    assert len(json.loads(capsys.readouterr().out)["anchors"]) == 96
    assert cli.main(["accuracy-impact", str(FILM), "--reject", "telegraph-sounder"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["invalidated_anchors"][0] == "telegraph-sounder"
    assert cli.main(["accuracy-review", str(FILM), "forked-lightning-bolt", "--verdict", "waive",
                     "--sha256", h("x"), "--log", str(log)]) == 2
    capsys.readouterr()
    assert cli.main(["accuracy-review", str(FILM), "forked-lightning-bolt", "--verdict", "accurate",
                     "--sha256", h("x"), "--log", str(log)]) == 0
    capsys.readouterr()
    assert cli.main(["accuracy-status", str(FILM), "--log", str(log)]) == 1
    text = capsys.readouterr().out
    text.encode("ascii")
    assert json.loads(text)["counts"]["pending"] == 96  # no run: verdicts cannot be matched to images


def test_cli_run_hash_and_retry_numbering(tmp_path, capsys):
    import yaml
    path = tmp_path / "sb.yaml"
    path.write_text(yaml.safe_dump(synthetic()), encoding="utf-8")
    run = fake_run(tmp_path, {"a": h("a"), "b": h("b")})
    log = tmp_path / "r.jsonl"
    assert cli.main(["accuracy-review", str(path), "b", "--verdict", "reject", "--run", str(run), "--note",
                     "fake labels", "--log", str(log), "--repo-root", str(REPO)]) == 0
    assert json.loads(capsys.readouterr().out)["image_sha256"] == h("b")
    assert cli.main(["accuracy-review", str(path), "c", "--verdict", "accurate", "--run", str(run),
                     "--log", str(log), "--repo-root", str(REPO)]) == 2  # no recorded image for c
    capsys.readouterr()
    assert cli.main(["accuracy-impact", str(path), "--reject", "b", "--log", str(log), "--repo-root", str(REPO)]) == 0
    assert json.loads(capsys.readouterr().out)["regenerate"][0]["retry"] == 2  # one earlier rejection in the log
