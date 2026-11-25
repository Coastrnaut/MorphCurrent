"""F34: engineering visual language - definition, enforcement in compiled prompts, drift, A/B test."""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from morph_studio import accuracy, cli, film
from morph_studio import look as lk
from morph_studio.dag import compile_plan
from morph_studio.longform import plan_diff
from morph_studio.schema import Storyboard, load_storyboard

from conftest import REPO

LANG = REPO / "configs/film/visual-language.yaml"
FILM = REPO / "configs/sequences/engineering-film.yaml"
ACT_IDS = ["spark", "power", "signal", "logic", "scale"]
needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


def lang() -> dict:
    return yaml.safe_load(LANG.read_text(encoding="utf-8"))


def write(tmp_path, data, name="lang.yaml") -> Path:
    p = tmp_path / name
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    return p


def plan_of(data: dict) -> dict:
    return compile_plan(Storyboard.model_validate(data), repo_root=REPO)


def film_data(look_name=None) -> dict:
    sp = json.loads((REPO / "configs/film/sync-plan.json").read_text(encoding="utf-8"))
    bank = yaml.safe_load((REPO / "configs/concepts/engineering-film.yaml").read_text(encoding="utf-8"))
    acts = yaml.safe_load((REPO / "configs/film/acts.yaml").read_text(encoding="utf-8"))
    language = lk.load_language(LANG, ACT_IDS) if look_name != "none" else None
    return film.build_storyboard(sp, bank, acts, language=language,
                                 look=None if look_name in (None, "none") else look_name)[0]


# --- foundational ---------------------------------------------------------------------------------

def test_definition_valid_and_choice():
    language = lk.load_language(LANG, ACT_IDS)
    assert set(language["looks"]) == {"copper-to-silicon", "steel-accent"}
    name, look, how = lk.choose(language)
    assert name == "copper-to-silicon" and how == "owner-selected"
    unselected = dict(language, selected=None)
    assert lk.choose(unselected)[2] == "default (not owner-selected)"
    assert lk.choose(language, "steel-accent")[2] == "requested"
    with pytest.raises(lk.LookError, match="unknown look"):
        lk.choose(language, "neon")


@pytest.mark.parametrize("mutate, match", [
    (lambda d: d["looks"]["steel-accent"]["acts"].pop("logic"), "logic"),
    (lambda d: d["looks"]["steel-accent"]["acts"]["power"].update(palette=["copper"]), "2 colours"),
    (lambda d: d["looks"]["steel-accent"]["acts"]["power"].update(camera="orbit_left"), "camera"),
    (lambda d: d["looks"]["copper-to-silicon"]["acts"]["power"].update(palette=["red", "green"]), "share"),
])
def test_definition_refusals(tmp_path, mutate, match):
    data = copy.deepcopy(lang())
    mutate(data)
    with pytest.raises(lk.LookError, match=match):
        lk.load_language(write(tmp_path, data), ACT_IDS)


def test_shared_colour_normalized(tmp_path):
    data = copy.deepcopy(lang())
    data["looks"]["steel-accent"]["acts"]["spark"]["palette"] = ["Brushed  Steel", "hot amber"]
    assert lk.load_language(write(tmp_path, data), ACT_IDS)


# --- US1/US2 --------------------------------------------------------------------------------------

def test_film_storyboard_enforces_default_look():
    sb = load_storyboard(FILM)
    plan = compile_plan(sb, repo_root=REPO, storyboard_bytes=FILM.read_bytes())
    language = lk.load_language(LANG, ACT_IDS)
    rep = lk.look_check(plan, sb, language)
    assert rep["ok"], rep["mismatches"][:3]
    assert rep["stages"] == 191 and rep["look"] == "copper-to-silicon"
    assert accuracy.text_free_check(plan)["ok"]


def test_deterministic_and_unstyled_fails():
    a, b = film_data(), film_data()
    assert plan_of(a)["plan_sha256"] == plan_of(b)["plan_sha256"]
    bare = film_data("none")
    rep = lk.look_check(plan_of(bare), Storyboard.model_validate(bare), lk.load_language(LANG, ACT_IDS))
    assert not rep["ok"] and rep["mismatches"]


def test_changing_one_act_palette_is_local(tmp_path):
    language = lk.load_language(LANG, ACT_IDS)
    base = film_data()
    changed_lang = copy.deepcopy(language)
    changed_lang["looks"]["copper-to-silicon"]["acts"]["signal"]["palette"] = ["brushed steel", "emerald green"]
    sp = json.loads((REPO / "configs/film/sync-plan.json").read_text(encoding="utf-8"))
    bank = yaml.safe_load((REPO / "configs/concepts/engineering-film.yaml").read_text(encoding="utf-8"))
    acts = yaml.safe_load((REPO / "configs/film/acts.yaml").read_text(encoding="utf-8"))
    other = film.build_storyboard(sp, bank, acts, language=changed_lang)[0]
    diff = plan_diff(plan_of(base), plan_of(other))
    rerun_anchors = {r["task"] for r in diff["stages"] if r["status"] == "rerun" and r["kind"] == "anchor"}
    signal = {f"anchor:{a['id']}" for a in base["anchors"] if a["chapter"] == "signal"}
    assert rerun_anchors == signal


# --- US3 drift ------------------------------------------------------------------------------------

def png(path: Path, x: int, colour: str) -> Path:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x080808:size=832x480",
                    "-vf", f"drawbox=x={x}:y=180:w=120:h=120:color={colour}:t=fill", "-frames:v", "1", str(path)],
                   check=True)
    return path


def drift_fixture(tmp_path) -> tuple[Path, Path]:
    """Six anchors in two acts; anchor 'c' off-centre, act boundary c->d a big colour jump."""
    ids = ["a", "b", "c", "d", "e", "f"]
    chapters = ["one"] * 3 + ["two"] * 3
    xs = {"a": 356, "b": 356, "c": 20, "d": 356, "e": 356, "f": 356}
    colours = {"a": "0xC87830", "b": "0xC07028", "c": "0xC87830", "d": "0x2850E0", "e": "0x3058E8", "f": "0x2850E0"}
    runs = tmp_path / "runs"
    run = runs / "run-test"
    run.mkdir(parents=True)
    stages = {}
    for i, k in enumerate(ids):
        job = runs / f"job{i}"
        (job / "outputs").mkdir(parents=True)
        png(job / "outputs" / "anchor.png", xs[k], colours[k])
        (job / "job.json").write_text(json.dumps({"image": {"local_path": "outputs\\anchor.png"}}), encoding="utf-8")
        stages[f"anchor:{k}"] = {"state": "verified", "job_dir": f"outputs\\runs\\{job.name}"}
    (run / "manifest.json").write_text(json.dumps({"order": list(stages), "stages": stages}), encoding="utf-8")
    sb = {"schema_version": 1, "name": "drift", "render": {"anchor_profile": "anchor_t2i", "bridge_profile": "wan22_flf2v"},
          "style": {"description": "x"},
          "anchors": [{"id": k, "prompt": k, "chapter": c} for k, c in zip(ids, chapters)],
          "transitions": [{"from": ids[i], "to": ids[i + 1], "frames": 33, "prompt": "m"} for i in range(5)]}
    path = tmp_path / "drift.yaml"
    path.write_text(yaml.safe_dump(sb), encoding="utf-8")
    return path, run


@needs_ffmpeg
def test_drift_flags(tmp_path):
    path, run = drift_fixture(tmp_path)
    rep = lk.drift_report(path, run, lk.load_language(LANG, ACT_IDS))
    assert [o["anchor"] for o in rep["off_centre"]] == ["c"]
    jumps = {(b["from_anchor"], b["to_anchor"]): b for b in rep["boundaries"]}
    assert jumps[("c", "d")]["flag"] is True
    assert [a["id"] for a in rep["acts"]] == ["one", "two"] and not rep["missing"]
    assert rep["ok"] is False
    # remove one anchor's output -> listed as missing
    (run.parent / "job5" / "outputs" / "anchor.png").unlink()
    assert lk.drift_report(path, run, lk.load_language(LANG, ACT_IDS))["missing"] == ["f"]


@needs_ffmpeg
def test_drift_no_chapters_and_scale_jump(tmp_path):
    runs = tmp_path / "runs"
    run = runs / "run-s"
    run.mkdir(parents=True)
    stages = {}
    for i, (k, size) in enumerate((("a", 120), ("b", 300))):  # area ratio (300/120)^2 -> scale jump 2.5
        job = runs / f"job{i}"
        (job / "outputs").mkdir(parents=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x080808:size=832x480",
                        "-vf", f"drawbox=x={416 - size // 2}:y={240 - size // 2}:w={size}:h={size}:color=0xC87830:t=fill",
                        "-frames:v", "1", str(job / "outputs" / "anchor.png")], check=True)
        (job / "job.json").write_text(json.dumps({"image": {"local_path": "outputs/anchor.png"}}), encoding="utf-8")
        stages[f"anchor:{k}"] = {"state": "verified", "job_dir": f"outputs/runs/{job.name}"}
    (run / "manifest.json").write_text(json.dumps({"order": list(stages), "stages": stages}), encoding="utf-8")
    sb = {"schema_version": 1, "name": "s", "render": {"anchor_profile": "anchor_t2i", "bridge_profile": "wan22_flf2v"},
          "style": {"description": "x"}, "anchors": [{"id": "a", "prompt": "a"}, {"id": "b", "prompt": "b"}],
          "transitions": [{"from": "a", "to": "b", "frames": 33, "prompt": "m"}]}
    path = tmp_path / "s.yaml"
    path.write_text(yaml.safe_dump(sb), encoding="utf-8")
    rep = lk.drift_report(path, run, lk.load_language(LANG, ACT_IDS))
    assert [a["id"] for a in rep["acts"]] == ["(whole film)"] and rep["boundaries"] == []
    assert rep["scale_jumps"] and rep["scale_jumps"][0]["from"] == "a" and rep["scale_jumps"][0]["ratio"] > 1.33


# --- US4 A/B --------------------------------------------------------------------------------------

def test_look_test(tmp_path):
    out = tmp_path / "ab"
    files = lk.look_test(FILM, lk.load_language(LANG, ACT_IDS), act="spark", count=5, out_dir=out)
    assert sorted(Path(f).name for f in files) == ["copper-to-silicon.yaml", "steel-accent.yaml"]
    a, b = (load_storyboard(f) for f in sorted(files))
    assert [x.id for x in a.anchors] == [x.id for x in b.anchors] and len(a.anchors) == 5
    assert [t.frames for t in a.transitions] == [t.frames for t in b.transitions]
    assert a.anchors[0].generation == "text_to_image"
    pa, pb = (compile_plan(s, repo_root=REPO) for s in (a, b))
    assert [pa["tasks"][t]["seed"] for t in pa["order"] if t.startswith("anchor:")] == \
           [pb["tasks"][t]["seed"] for t in pb["order"] if t.startswith("anchor:")]
    assert a.anchors[1].style_override != b.anchors[1].style_override
    with pytest.raises(FileExistsError):
        lk.look_test(FILM, lk.load_language(LANG, ACT_IDS), act="spark", count=5, out_dir=out)
    with pytest.raises(lk.LookError, match="act"):
        lk.look_test(FILM, lk.load_language(LANG, ACT_IDS), act="finale", count=5, out_dir=tmp_path / "x")


# --- CLI ------------------------------------------------------------------------------------------

def test_cli(tmp_path, capsys):
    assert cli.main(["look-check", str(FILM)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] and out["selection"] == "owner-selected"
    assert cli.main(["look-check", str(FILM), "--look", "steel-accent"]) == 1
    capsys.readouterr()
    assert cli.main(["look-check", str(FILM), "--look", "neon"]) == 2
    assert cli.main(["look-test", "--out-dir", str(tmp_path / "ab")]) == 0
    assert len(json.loads(capsys.readouterr().out)["files"]) == 2
    assert cli.main(["film-storyboard", "--out", str(tmp_path / "f.yaml"), "--look", "steel-accent"]) == 0
    capsys.readouterr()
    assert cli.main(["look-check", str(tmp_path / "f.yaml"), "--look", "steel-accent"]) == 0
    capsys.readouterr().out.encode("ascii")


def test_setting_override_keeps_look(tmp_path):
    """Anchor review 2026-11-24: natural-scene anchors override description/composition, not palette/lighting."""
    import yaml as _yaml
    from morph_studio import look as lk
    from morph_studio.accuracy import load_plan
    from morph_studio.schema import load_storyboard
    film = REPO / "configs/sequences/engineering-film.yaml"
    data = _yaml.safe_load(film.read_text(encoding="utf-8"))
    natural = [a["id"] for a in data["anchors"] if "description" in (a.get("style_override") or {})]
    assert "aurora-curtain" in natural and "storm-cell-over-plain" in natural
    language = lk.load_language(REPO / "configs/film/visual-language.yaml",
                                ["spark", "power", "signal", "logic", "scale"])
    rep = lk.look_check(load_plan(film, REPO), load_storyboard(film), language)
    assert rep["ok"], rep["mismatches"][:3]
