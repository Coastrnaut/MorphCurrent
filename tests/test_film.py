"""F32: frame-locked transitions, act structure, film storyboard generator and dry-run film report."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml

from morph_studio import cli
from morph_studio import film
from morph_studio.dag import compile_plan
from morph_studio.ladder import LadderError
from morph_studio.longform import plan_diff
from morph_studio.schema import Storyboard, load_storyboard
from morph_studio.timeline import compile_timeline, snap_frames

from conftest import REPO

PLAN = REPO / "configs/film/sync-plan.json"
BANK = REPO / "configs/concepts/engineering-film.yaml"
ACTS = REPO / "configs/film/acts.yaml"
HASHES = {"configs/sequences/organic-machines.yaml": "ba2d9dbedb6189beaef6c39a8e5e2a06caef260a2729620c7e8ffa1071bb4bdf",
          "configs/sequences/engineering-pilot.yaml": "91630ded740299c633c3d45ca87d960aea78857d139e6aca168a7458747651a9"}


def sync_plan() -> dict:
    return json.loads(PLAN.read_text(encoding="utf-8"))


def bank() -> dict:
    return yaml.safe_load(BANK.read_text(encoding="utf-8"))


def acts() -> dict:
    return yaml.safe_load(ACTS.read_text(encoding="utf-8"))


def mini_storyboard(frames=(61, 33), beats=None, bpm=None, max_frames=81) -> dict:
    trans = []
    ids = ["a", "b", "c"]
    for i, f in enumerate(frames):
        t = {"from": ids[i], "to": ids[i + 1], "prompt": "morph"}
        if beats:
            t["duration_beats"] = beats[i]
        if f is not None:
            t["frames"] = f
        trans.append(t)
    data = {"schema_version": 1, "name": "mini",
            "render": {"anchor_profile": "anchor_t2i", "bridge_profile": "wan22_flf2v", "max_bridge_frames": max_frames},
            "style": {"description": "x"}, "audio": {"bpm": bpm} if bpm else {},
            "anchors": [{"id": "a", "prompt": "a"}, {"id": "b", "prompt": "b", "generation": "reference_edit", "reference": "a"},
                        {"id": "c", "prompt": "c", "generation": "reference_edit", "reference": "b"}],
            "transitions": trans}
    return data


# --- foundational / US1 ---------------------------------------------------------------------------

@pytest.mark.parametrize("path, digest", sorted(HASHES.items()))
def test_existing_plan_hashes_unchanged(path, digest):
    raw = (REPO / path).read_bytes()
    assert compile_plan(load_storyboard(REPO / path), storyboard_bytes=raw, repo_root=REPO)["plan_sha256"] == digest


def test_frame_locked_compile():
    sb = Storyboard.model_validate(mini_storyboard())
    bridges = compile_timeline(sb)
    assert [b.frames for b in bridges] == [61, 33]
    assert all(b.timing_error_seconds == 0 for b in bridges)
    anchor_frames = [0]
    for b in bridges:
        anchor_frames.append(anchor_frames[-1] + b.frames - 1)
    assert anchor_frames == [0, 60, 92]


@pytest.mark.parametrize("frames, match", [((64, 33), "4n\\+1"), ((61, 3), "greater than or equal"),
                                            ((61, 85), "max_bridge_frames"), ((None, 33), "exactly one")])
def test_frame_locked_refusals(frames, match):
    with pytest.raises(ValueError, match=match):
        Storyboard.model_validate(mini_storyboard(frames=frames))


def test_both_lengths_and_bpm_rule():
    with pytest.raises(ValueError, match="exactly one"):
        Storyboard.model_validate(mini_storyboard(frames=(61, 33), beats=(8, 4), bpm=120))
    with pytest.raises(ValueError, match="bpm"):
        Storyboard.model_validate(mini_storyboard(frames=(None, None), beats=(8, 4)))
    assert Storyboard.model_validate(mini_storyboard(frames=(None, None), beats=(8, 4), bpm=120))


def test_snap_frames_rubato_no_drift():
    times, t = [], 0.0
    for k in range(400):  # rubato: beat period drifts between 0.42 and 0.61 s
        t += 0.5 + 0.09 * ((k * 37) % 11 - 5) / 5
        times.append(t)
    snapped = snap_frames(times, 16.0)
    assert all(abs(s["error_frames"]) <= 2 for s in snapped)
    assert all(s["frame"] % 4 == 0 for s in snapped)
    assert abs(snapped[-1]["error_frames"]) <= 2  # no accumulation after 400 beats


def test_ladder_refuses_frame_locked():
    from morph_studio import ladder
    data = mini_storyboard()
    with pytest.raises(LadderError, match="frame-locked"):
        ladder.propose_ladder(data, "a", "b")


# --- US2 generator --------------------------------------------------------------------------------

def test_build_storyboard_real_inputs():
    data, header = film.build_storyboard(sync_plan(), bank(), acts())
    sb = Storyboard.model_validate(data)
    b = bank()["entries"]
    assert [a.id for a in sb.anchors] == [e["id"] for e in b]
    assert [t.frames for t in sb.transitions] == [x["frames"] for x in sync_plan()["bridges"]]
    t2i = [a for a in sb.anchors if a.generation == "text_to_image"]
    assert len(t2i) == 5
    for prev, a in zip(sb.anchors, sb.anchors[1:]):
        if a.generation == "reference_edit":
            assert a.reference == prev.id and a.chapter == prev.chapter
        else:
            assert a.chapter != prev.chapter
    chapters = [a.chapter for a in sb.anchors]
    assert list(dict.fromkeys(chapters)) == ["spark", "power", "signal", "logic", "scale"]
    assert b[0]["subject"] in sb.anchors[0].prompt
    assert b[0]["morph_to_next"] in sb.transitions[0].prompt and "motion feel" in sb.transitions[0].prompt
    assert sb.audio.file is None and sb.style.pack == "engineering-noir"
    assert sync_plan()["plan_sha256"] in header and "status approved" in header


def test_build_storyboard_audio_and_refusals(tmp_path):
    data, _ = film.build_storyboard(sync_plan(), bank(), acts(), audio="C:/music/track.wav")
    assert data["audio"] == {"file": "C:/music/track.wav", "licensed": True, "synchronization": "none"}
    short = copy.deepcopy(sync_plan())
    short["anchors"] = short["anchors"][:-1]
    short["bridges"] = short["bridges"][:-1]
    with pytest.raises(film.FilmError, match="96"):
        film.build_storyboard(short, bank(), acts())
    wide = copy.deepcopy(sync_plan())
    wide["bridges"][3]["frames"] = 85
    with pytest.raises(film.FilmError, match="33-81"):
        film.build_storyboard(wide, bank(), acts())
    bad = acts()
    bad["acts"][1]["eras"] = []
    with pytest.raises(film.FilmError, match="era"):
        film.build_storyboard(sync_plan(), bank(), bad)
    dup = acts()
    dup["acts"][1]["eras"] = ["generation and grid", "early storage"]
    with pytest.raises(film.FilmError, match="era"):
        film.build_storyboard(sync_plan(), bank(), dup)
    out = tmp_path / "film.yaml"
    film.write_storyboard(PLAN, BANK, ACTS, out)
    assert load_storyboard(out)
    with pytest.raises(FileExistsError):
        film.write_storyboard(PLAN, BANK, ACTS, out)


# --- US3 report -----------------------------------------------------------------------------------

def generated(tmp_path) -> Path:
    out = tmp_path / "engineering-film.yaml"
    film.write_storyboard(PLAN, BANK, ACTS, out)
    return out


def test_film_report(tmp_path):
    rep = film.film_report(generated(tmp_path), sync_plan=PLAN, history=REPO / "configs/perf_history.json",
                           repo_root=REPO)
    sp = sync_plan()
    total_frames = 1 + sum(b["frames"] - 1 for b in sp["bridges"])
    assert rep["totals"]["unique_frames"] == total_frames and rep["totals"]["anchors"] == 96
    assert sum(a["anchors"] for a in rep["acts"]) == 96 and sum(a["bridges"] for a in rep["acts"]) == 95
    assert [a["id"] for a in rep["acts"]] == ["spark", "power", "signal", "logic", "scale"]
    cov = rep["coverage"]
    assert abs(cov["last_anchor_s"] + cov["tail_hold_s"] - cov["song_s"]) <= 1 / 16 + 1e-9 and cov["matches"]
    assert rep["gpu"]["total_hours"] > 0 and "estimate" in rep["gpu"]["label"].lower()
    assert rep["gpu"]["stages_extrapolated"] + rep["gpu"]["stages_estimated"] == 96 + 95
    assert all("boundary_event" in a for a in rep["acts"])
    assert cov["head_hold_s"] == 0.0
    shifted = sync_plan()
    shifted["anchors"][0]["t"] = 0.5  # picture would start half a second in: reported, coverage mismatch
    alt = tmp_path / "shifted.json"
    alt.write_text(json.dumps(shifted), encoding="utf-8")
    rep2 = film.film_report(generated(tmp_path / "x"), sync_plan=alt, history=None, repo_root=REPO)
    assert rep2["coverage"]["head_hold_s"] == 0.5 and rep2["coverage"]["matches"] is False


def test_editing_one_act_is_isolated(tmp_path):
    path = generated(tmp_path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    before = compile_plan(Storyboard.model_validate(data), repo_root=REPO)
    signal = [i for i, a in enumerate(data["anchors"]) if a.get("chapter") == "signal"]
    edited = signal[3]
    data["anchors"][edited]["prompt"] += " (edited)"
    after = compile_plan(Storyboard.model_validate(data), repo_root=REPO)
    diff = plan_diff(before, after)
    changed = {r["task"] for r in diff["stages"] if r["status"] == "rerun"}
    ids = [a["id"] for a in data["anchors"]]
    inside = set(ids[edited:signal[-1] + 1])
    allowed = {f"anchor:{i}" for i in inside} | {t for t in changed if t.startswith("bridge:")
                                                  and (t.split(":", 1)[1].split("->")[0] in inside
                                                       or t.split(":", 1)[1].split("->")[1] in inside)}
    assert changed and changed <= allowed | {"final:movie"}
    others = {a["id"] for a in data["anchors"] if a.get("chapter") != "signal"}
    assert not any(f"anchor:{o}" in changed for o in others)


# --- CLI ------------------------------------------------------------------------------------------

def test_cli(tmp_path, capsys):
    out = tmp_path / "f.yaml"
    assert cli.main(["film-storyboard", "--out", str(out)]) == 0
    res = json.loads(capsys.readouterr().out)
    assert res["anchors"] == 96 and res["bridges"] == 95 and res["text_to_image"] == 5
    assert cli.main(["film-storyboard", "--out", str(out)]) == 2
    capsys.readouterr()
    assert cli.main(["film-report", str(out)]) == 0
    text = capsys.readouterr().out
    text.encode("ascii")
    assert json.loads(text)["totals"]["anchors"] == 96


def test_act_start_anchor_override():
    """F38: owner-approved act boundaries via start_anchor (all acts or none)."""
    from morph_studio import film as fm
    items = [{"id": "a", "eras": ["x"]}, {"id": "b", "eras": ["y"]}]
    assert fm.act_starts(items, 10) is None
    assert fm.act_starts([dict(items[0], start_anchor=0), dict(items[1], start_anchor=4)], 10) == [(0, "a"), (4, "b")]
    for bad in ([0, None], [1, 4], [0, 0], [0, 10]):
        with pytest.raises(fm.FilmError):
            fm.act_starts([dict(i, start_anchor=s) for i, s in zip(items, bad)], 10)



def test_anchor_fixes_applied(tmp_path):
    """Owner 2026-11-24: fresh keyframes for the four weak Spark anchors."""
    from morph_studio import film as fm
    data = yaml.safe_load((REPO / "configs/sequences/engineering-film.yaml").read_text(encoding="utf-8"))
    gens = {a["id"]: a["generation"] for a in data["anchors"]}
    for k in ("forked-lightning-bolt", "rubbed-amber-and-fur", "aurora-curtain", "charged-dust-cloud"):
        assert gens[k] == "independent_t2i"
    assert gens["fulgurite-glass-tube"] == "reference_edit"
    d = {"anchors": [{"id": "a", "generation": "text_to_image", "prompt": "x"},
                     {"id": "b", "generation": "reference_edit", "reference": "a", "prompt": "y"}]}
    assert fm.apply_anchor_fixes(d, [{"anchor": "b", "apply": "instruction", "instruction": "Show  only b."}]) == ["b=instruction"]
    assert d["anchors"][1]["prompt"] == "Show only b."
    for bad in ({"anchor": "zz", "apply": "fresh"}, {"anchor": "a", "apply": "instruction", "instruction": "x"},
                {"anchor": "b", "apply": "maybe"}):
        with pytest.raises(fm.FilmError):
            fm.apply_anchor_fixes(d, [bad])
    assert fm.apply_anchor_fixes(d, [{"anchor": "b", "instruction": "x"}]) == []  # no pick, no change


def test_anchor_fix_prompt_kind():
    from morph_studio import film as fm
    d = {"anchors": [{"id": "a", "generation": "text_to_image", "prompt": "x"},
                     {"id": "b", "generation": "reference_edit", "reference": "a", "prompt": "y"}]}
    assert fm.apply_anchor_fixes(d, [{"anchor": "a", "apply": "prompt", "prompt": "new  a"},
                                     {"anchor": "b", "apply": "fresh", "prompt": "fresh b"}]) == ["a=prompt", "b=fresh"]
    assert d["anchors"][0]["prompt"] == "new a" and d["anchors"][1] == {
        "id": "b", "generation": "independent_t2i", "reference": "a", "prompt": "fresh b"}
    with pytest.raises(fm.FilmError, match="needs a prompt"):
        fm.apply_anchor_fixes(d, [{"anchor": "a", "apply": "prompt"}])


def test_fresh_refused_on_act_root():
    from morph_studio import film as fm
    d = {"anchors": [{"id": "a", "generation": "text_to_image", "prompt": "x"}]}
    with pytest.raises(fm.FilmError, match="apply: prompt"):
        fm.apply_anchor_fixes(d, [{"anchor": "a", "apply": "fresh"}])


def test_anchor_fix_seed():
    from morph_studio import film as fm
    d = {"anchors": [{"id": "a", "generation": "text_to_image", "prompt": "x"}]}
    assert fm.apply_anchor_fixes(d, [{"anchor": "a", "apply": "prompt", "prompt": "y", "seed": 4242}]) == ["a=prompt"]
    assert d["anchors"][0]["seed"] == 4242
    for bad in (-1, "7", True):
        with pytest.raises(fm.FilmError, match="seed"):
            fm.apply_anchor_fixes(d, [{"anchor": "a", "apply": "prompt", "prompt": "y", "seed": bad}])


def test_anchor_fix_adjust():
    from morph_studio import film as fm
    d = {"anchors": [{"id": "a", "generation": "text_to_image", "prompt": "x"}]}
    assert fm.apply_anchor_fixes(d, [{"anchor": "a", "apply": "adjust", "seed": 9}]) == ["a=adjust"]
    assert d["anchors"][0] == {"id": "a", "generation": "text_to_image", "prompt": "x", "seed": 9}
    with pytest.raises(fm.FilmError, match="adjust"):
        fm.apply_anchor_fixes(d, [{"anchor": "a", "apply": "adjust"}])
