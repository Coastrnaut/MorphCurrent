"""F38: titles definition, timing, safe areas, deterministic overlay render and act-boundary proposals."""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from morph_studio import cli
from morph_studio import titles as tt
from morph_studio.media import probe_video

from conftest import REPO

FILM = REPO / "configs/sequences/engineering-film.yaml"
PLAN = REPO / "configs/film/sync-plan.json"
TITLES = REPO / "configs/film/titles.yaml"
ACTS = REPO / "configs/film/acts.yaml"
FONT = Path("C:/Windows/Fonts/arial.ttf")
needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="ffmpeg missing")
needs_font = pytest.mark.skipif(not FONT.is_file(), reason="Arial missing")


def mini(tmp_path, frames=(33, 37, 33), chapters=("one", "one", "two", "two")) -> Path:
    ids = ["a", "b", "c", "d"]
    anchors = []
    for k, c in zip(ids, chapters):
        a = {"id": k, "prompt": f"subject {k}"}
        if c:
            a["chapter"] = c
        anchors.append(a)
    sb = {"schema_version": 1, "name": "mini",
          "render": {"anchor_profile": "anchor_t2i", "bridge_profile": "wan22_flf2v"},
          "style": {"description": "x"}, "anchors": anchors,
          "transitions": [{"from": ids[i], "to": ids[i + 1], "frames": f, "prompt": "m"} for i, f in enumerate(frames)]}
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "mini.yaml"
    path.write_text(yaml.safe_dump(sb), encoding="utf-8")
    return path


def defn(**over) -> dict:
    d = {"version": 1, "font": str(FONT), "defaults": {"fade_s": 0.25},
         "opening": {"text": "Open", "start_s": 0, "duration_s": 1, "size": 0.1, "y": 0.45},
         "acts": {"duration_s": 1, "size": 0.08, "y": 0.8, "text": {"one": "First", "two": "Second"}},
         "lower_thirds": [], "end": {"text": "End", "duration_s": 1, "size": 0.1, "y": 0.45}}
    d.update(over)
    return d


def write_defn(tmp_path, d, name="titles.yaml") -> Path:
    p = tmp_path / name
    p.write_text(yaml.safe_dump(d, sort_keys=False), encoding="utf-8")
    return p


def movie(tmp_path, seconds=6.5, name="in.mp4") -> Path:
    path = tmp_path / name
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc=size=320x184:rate=16:duration={seconds}",
                    "-pix_fmt", "yuv420p", "-c:v", "libx264", str(path)], check=True)
    return path


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# --- foundational ---------------------------------------------------------------------------------

def test_load_real_titles():
    d = tt.load_titles(TITLES)
    assert d["opening"]["text"] == "From Lightning to Silicon" and d["end"]["text"] == "MorphCurrent"
    assert d["lower_thirds"] == []


@pytest.mark.parametrize("mut,msg", [
    (lambda d: d["opening"].update(text="  "), "empty"),
    (lambda d: d["end"].update(duration_s=0), "duration"),
    (lambda d: d["opening"].update(size=0.5), "size"),
    (lambda d: d["opening"].update(y=1.2), "y must"),
    (lambda d: d["defaults"].update(fade_s=0.8), "fade"),
    (lambda d: d["acts"]["text"].update(one=" "), "empty"),
    (lambda d: d.update(version=2), "version"),
    (lambda d: d.update(lower_thirds=[{"text": "x", "duration_s": 1, "size": 0.05, "y": 0.88}]), "start_s or anchor"),
])
def test_load_refusals(tmp_path, mut, msg):
    d = defn()
    mut(d)
    with pytest.raises(tt.TitlesError, match=msg):
        tt.load_titles(write_defn(tmp_path, d))


# --- US1 timing -----------------------------------------------------------------------------------

def test_resolve_timing(tmp_path):
    sb = mini(tmp_path)
    r = tt.resolve(defn(), sb, duration_s=6.5)
    ov = {o["id"]: o for o in r["overlays"]}
    # chapter one starts at anchor 0 (inside the opening card) -> deferred to 1.0 s
    assert ov["act-one"]["start_s"] == 1.0 and ov["act-one"]["end_s"] == 2.0
    assert any("deferred" in w for w in r["warnings"])
    # chapter two starts at anchor c: frame 32 + 36 = 68 -> 4.25 s
    assert ov["act-two"]["start_s"] == 4.25 and ov["act-two"]["end_s"] == 5.25
    assert ov["act-two"]["text"] == "Second"
    assert ov["act-two"]["anchors"] == [{"index": 2, "id": "c", "frame": 68, "t": 4.25}]
    assert ov["end"]["start_s"] == 5.5 and ov["end"]["end_s"] == 6.5
    assert [a["id"] for a in ov["opening"]["anchors"]] == ["a"]


def test_resolve_defaults_overlap_clip(tmp_path):
    sb = mini(tmp_path)
    # default duration = (last anchor frame + 1) / fps = 101 / 16
    d = defn(acts={"duration_s": 2, "size": 0.08, "y": 0.8})
    d["lower_thirds"] = [{"text": "Late", "start_s": 6.0, "duration_s": 2, "size": 0.05, "y": 0.88},
                         {"text": "Gone", "start_s": 9.0, "duration_s": 1, "size": 0.05, "y": 0.88},
                         {"text": "At c", "anchor": 2, "duration_s": 1, "size": 0.05, "y": 0.88}]
    r = tt.resolve(d, sb, acts_path=ACTS)
    assert r["duration_s"] == 101 / 16
    ov = {o["id"]: o for o in r["overlays"]}
    assert ov["act-one"]["text"] == "One"  # no act definition for "one" -> title-cased chapter id
    assert ov["lower-00"]["end_s"] == round(101 / 16, 3) and "clipped" in " ".join(ov["lower-00"]["notes"])
    assert "lower-01" not in ov and any("dropped" in w for w in r["warnings"])
    assert ov["lower-02"]["start_s"] == 4.25
    assert any("overlaps" in w for w in r["warnings"])
    d["lower_thirds"] = [{"text": "x", "anchor": 9, "duration_s": 1, "size": 0.05, "y": 0.88}]
    with pytest.raises(tt.TitlesError, match="anchor 9"):
        tt.resolve(d, sb)


def test_lower_third_defaults(tmp_path):
    d = defn(lower_thirds=[{"text": "Note", "start_s": 2, "duration_s": 1}])
    lt = tt.load_titles(write_defn(tmp_path, d))["lower_thirds"][0]
    assert (lt["size"], lt["y"]) == (0.05, 0.88)


def test_resolve_without_chapters(tmp_path):
    sb = mini(tmp_path, chapters=(None, None, None, None))
    ids = [o["id"] for o in tt.resolve(defn(), sb, duration_s=6.5)["overlays"]]
    assert ids == ["opening", "end"]


def test_resolve_film_default_act_titles():
    r = tt.resolve(tt.load_titles(TITLES), FILM)
    acts = [o for o in r["overlays"] if o["kind"] == "act"]
    assert [o["text"] for o in acts] == ["Spark", "Power", "Signal", "Logic", "Scale"]
    assert acts[0]["start_s"] == 5.0  # deferred after the opening card
    assert [o["start_s"] for o in acts[1:]] == [48.25, 105.25, 162.75, 266.5]  # F38 owner-approved boundaries
    assert r["overlays"][-1]["end_s"] == round(5741 / 16, 3)


# --- US1 recipe and render ------------------------------------------------------------------------

@needs_font
def test_recipe_deterministic(tmp_path):
    sb = mini(tmp_path)
    r = tt.resolve(defn(), sb, duration_s=6.5)
    sizes = tt.safe_check(r["overlays"], 320, 184)["sizes"]
    a = tt.build_recipe(r, 320, 184, 16, FONT, sizes)
    b = tt.build_recipe(tt.resolve(defn(), sb, duration_s=6.5), 320, 184, 16, FONT, sizes)
    assert tt.recipe_sha256(a) == tt.recipe_sha256(b)
    assert "fontfile=font.ttf" in a["filter"] and "textfile=t00.txt" in a["filter"] and "expansion=none" in a["filter"]
    assert str(tmp_path) not in a["filter"] and "C:" not in a["filter"]
    d = defn()
    d["end"]["text"] = "Other"
    c = tt.build_recipe(tt.resolve(d, sb, duration_s=6.5), 320, 184, 16, FONT, sizes | {"end": sizes["end"]})
    assert tt.recipe_sha256(c) != tt.recipe_sha256(a)
    with pytest.raises(tt.TitlesError, match="font"):
        tt.build_recipe(r, 320, 184, 16, tmp_path / "nofont.ttf", sizes)


def test_verify_media():
    p = {"frame_count": 104, "fps": 16.0, "duration_s": 6.5}
    assert tt.verify_media(p, dict(p)) == []
    assert "frame count" in tt.verify_media(p, dict(p, frame_count=103))[0]
    assert "duration" in tt.verify_media(p, dict(p, duration_s=6.7))[0]
    assert tt.verify_media(p, dict(p, duration_s=6.55)) == []


@needs_ffmpeg
@needs_font
def test_render(tmp_path):
    sb = mini(tmp_path)
    prompts_before = sb.read_text(encoding="utf-8")
    src = movie(tmp_path)
    before = sha(src)
    d = defn()
    d["opening"]["text"] = "Volts: 100% 'quoted' \\ back"
    rec = tt.render(src, tmp_path / "out" / "titled.mp4", d, sb)
    out = Path(rec["output"])
    assert out.is_file() and sha(src) == before == rec["input_sha256"]
    pi, po = probe_video(src), probe_video(out)
    assert po["frame_count"] == pi["frame_count"] == 104
    assert abs(po["duration_s"] - pi["duration_s"]) <= 1 / 16
    assert Path(rec["record"]).is_file()
    saved = json.loads(Path(rec["record"]).read_text(encoding="utf-8"))
    assert saved["recipe_sha256"] == tt.recipe_sha256(saved["recipe"])
    assert [o["id"] for o in saved["overlays"]] == ["opening", "act-one", "act-two", "end"]
    assert saved["overlays"][2]["anchors"][0]["frame"] == 68
    # FR-002: the storyboard (and its prompts) is untouched and no title text is in any prompt
    assert sb.read_text(encoding="utf-8") == prompts_before
    sbd = yaml.safe_load(prompts_before)
    texts = [o["text"] for o in saved["overlays"]]
    assert not any(t in a["prompt"] for t in texts for a in sbd["anchors"])
    # text is visible inside its window (bright pixels differ from the input) and absent outside
    def frame(path, t):
        return subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1",
                               "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    assert frame(src, 0.5) != frame(out, 0.5)
    diff = sum(abs(a - b) for a, b in zip(frame(src, 3.0), frame(out, 3.0))) / (320 * 184)
    assert diff < 4  # only encoding noise between windows
    # same inputs -> same recipe checksum
    rec2 = tt.render(src, tmp_path / "out" / "titled2.mp4", d, sb)
    assert rec2["recipe_sha256"] == rec["recipe_sha256"]
    # refusals
    with pytest.raises(FileExistsError):
        tt.render(src, out, d, sb)
    with pytest.raises(tt.TitlesError, match="font"):
        tt.render(src, tmp_path / "x.mp4", dict(d, font=str(tmp_path / "missing.ttf")), sb)
    with pytest.raises(tt.TitlesError, match="empty"):
        tt.render(src, tmp_path / "y.mp4", write_defn(tmp_path, defn(end={"text": "", "duration_s": 1, "size": 0.1, "y": 0.45})), sb)
    with pytest.raises(tt.TitlesError, match="movie"):
        tt.render(tmp_path / "none.mp4", tmp_path / "z.mp4", d, sb)


# --- US2 safe areas -------------------------------------------------------------------------------

def test_safe_check():
    short = {"id": "s", "text": "Spark", "size": 0.08, "y": 0.8}
    long = {"id": "l", "text": "From Lightning to Silicon", "size": 0.1, "y": 0.45}
    huge = {"id": "h", "text": "x" * 80, "size": 0.1, "y": 0.45}
    r = tt.safe_check([short, long], 832, 480)
    assert r["ok"] and r["sizes"] == {"s": 38, "l": 48}
    v = tt.safe_check([short, long, huge], 832, 480, vertical=True)
    rows = {(x["id"], x["area"]): x for x in v["rows"]}
    assert rows[("s", "9:16")]["fits"] and rows[("s", "9:16")]["size_used_px"] == 38.4
    assert rows[("l", "9:16")]["fits"] and rows[("l", "9:16")]["size_used_px"] < 48 and not rows[("l", "9:16")]["flagged"]
    assert v["sizes"]["l"] == 18
    assert rows[("h", "9:16")]["flagged"] and not v["ok"]
    low = {"id": "b", "text": "Low", "size": 0.1, "y": 0.97}
    assert not tt.safe_check([low], 832, 480)["ok"]


def test_film_titles_fit_both_areas():
    r = tt.resolve(tt.load_titles(TITLES), FILM)
    v = tt.safe_check(r["overlays"], 832, 480, vertical=True)
    assert v["ok"] and len(v["rows"]) == 14
    assert v["sizes"]["opening"] < 48 and v["sizes"]["act-spark"] == 38


@needs_font
def test_vertical_sizes_feed_recipe(tmp_path):
    sb = mini(tmp_path)
    d = defn()
    d["opening"]["text"] = "A considerably longer opening line"
    r = tt.resolve(d, sb, duration_s=6.5)
    wide = tt.safe_check(r["overlays"], 832, 480)["sizes"]
    tall = tt.safe_check(r["overlays"], 832, 480, vertical=True)["sizes"]
    assert tall["opening"] < wide["opening"]
    rec = tt.build_recipe(r, 832, 480, 16, FONT, tall)
    assert f"fontsize={tall['opening']}" in rec["filter"]


# --- US3 boundaries -------------------------------------------------------------------------------

def test_act_boundaries_film():
    before = (sha(FILM), sha(PLAN))
    rep = tt.act_boundaries(FILM, PLAN)
    rows = {r["anchor"]: r for r in rep["boundaries"]}
    # owner applied the proposals 18->13, 38->43, 67->70 (2026-11-24): three acts now open on section starts
    assert list(rows) == [13, 28, 43, 70]
    assert [rows[k]["act"] for k in rows] == ["power", "signal", "logic", "scale"]
    assert all(rows[k]["offset"] == 0 and rows[k]["event"] == "section" for k in (13, 43, 70))
    assert rows[28]["section_anchor"] is None and rows[28]["proposal"] is None
    assert rep["proposals"] == 0
    assert (sha(FILM), sha(PLAN)) == before


def test_act_boundaries_proposals(tmp_path):
    # the pre-decision film layout (era grouping) produced the three proposals
    from morph_studio import film
    acts = yaml.safe_load(ACTS.read_text(encoding="utf-8"))
    for a in acts["acts"]:
        a.pop("start_anchor", None)
    ap = tmp_path / "acts.yaml"
    ap.write_text(yaml.safe_dump(acts), encoding="utf-8")
    sb = film.write_storyboard(PLAN, REPO / "configs/concepts/engineering-film.yaml", ap, tmp_path / "f.yaml")
    rep = tt.act_boundaries(sb if isinstance(sb, Path) else tmp_path / "f.yaml", PLAN)
    rows = {r["anchor"]: r for r in rep["boundaries"]}
    assert list(rows) == [18, 28, 38, 67]
    assert (rows[18]["section_anchor"], rows[18]["offset"]) == (13, -5)
    assert (rows[38]["section_anchor"], rows[38]["offset"]) == (43, 5)
    assert (rows[67]["section_anchor"], rows[67]["offset"]) == (70, 3)
    assert rep["proposals"] == 3 and "anchor 13" in rows[18]["proposal"]
    assert tt.act_boundaries(tmp_path / "f.yaml", PLAN, window=2)["proposals"] == 0


def test_act_boundaries_mismatch(tmp_path):
    sb = mini(tmp_path)
    with pytest.raises(tt.TitlesError, match="anchors"):
        tt.act_boundaries(sb, PLAN)
    plan = {"anchors": [{"t": 0, "event": None}, {"t": 2, "event": "section"},
                        {"t": 4.25, "event": "onset"}, {"t": 6.25, "event": "section"}]}
    pp = tmp_path / "p.json"
    pp.write_text(json.dumps(plan), encoding="utf-8")
    rep = tt.act_boundaries(sb, pp, window=1)
    assert rep["boundaries"][0]["anchor"] == 2 and rep["boundaries"][0]["section_anchor"] == 1  # tie -> earlier


# --- CLI ------------------------------------------------------------------------------------------

def test_cli_check_and_boundaries(tmp_path, capsys):
    assert cli.main(["titles-check", "--vertical", "--json"]) == 0
    out = capsys.readouterr().out
    out.encode("ascii")
    assert json.loads(out)["safe_area"]["ok"]
    assert cli.main(["titles-check", "--vertical"]) == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 8 and lines[0].startswith("opening") and "From Lightning / to Silicon" in lines[0]
    assert lines[-1].startswith("warning: act-spark")
    bad = defn(opening={"text": "x" * 90, "start_s": 0, "duration_s": 2, "size": 0.1, "y": 0.45})
    assert cli.main(["titles-check", "--titles", str(write_defn(tmp_path, bad)), "--vertical"]) == 1
    capsys.readouterr()
    empty = defn(end={"text": " ", "duration_s": 1, "size": 0.1, "y": 0.45})
    assert cli.main(["titles-check", "--titles", str(write_defn(tmp_path, empty, "e.yaml"))]) == 2
    capsys.readouterr()
    assert cli.main(["act-boundaries"]) == 0
    text = capsys.readouterr().out
    text.encode("ascii")
    assert len(text.strip().splitlines()) == 4 and text.count("on the section start") == 3
    assert cli.main(["act-boundaries", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["proposals"] == 0
    assert cli.main(["act-boundaries", "--storyboard", str(mini(tmp_path / "m"))]) == 2


@needs_ffmpeg
@needs_font
def test_cli_render(tmp_path, capsys):
    sb = mini(tmp_path)
    src = movie(tmp_path)
    titles = write_defn(tmp_path, defn())
    out = tmp_path / "t.mp4"
    assert cli.main(["titles-render", str(src), str(out), "--titles", str(titles), "--storyboard", str(sb)]) == 0
    rec = json.loads(capsys.readouterr().out)
    assert rec["ok"] and out.is_file()
    assert cli.main(["titles-render", str(src), str(out), "--titles", str(titles), "--storyboard", str(sb)]) == 2


@needs_font
def test_vertical_two_line_text(tmp_path):
    """Owner decision 2026-11-24: the opening uses two lines in the 9:16-safe copy."""
    d = tt.load_titles(TITLES)
    assert d["opening"]["text_vertical"] == "From Lightning\nto Silicon"
    wide = tt.resolve(d, FILM)
    tall = tt.resolve(d, FILM, vertical=True)
    assert wide["overlays"][0]["text"] == "From Lightning to Silicon"
    assert tall["overlays"][0]["text"] == "From Lightning\nto Silicon"
    v = tt.safe_check(tall["overlays"], 832, 480, vertical=True)
    assert v["ok"] and v["sizes"]["opening"] == 32  # longest line (14 chars) sets the width
    rec = tt.build_recipe(tall, 832, 480, 16, FONT, v["sizes"])
    first = rec["filter"].split(",drawtext")[0]
    assert "text_align=C" in first and "line_spacing=6" in first
    assert "text_align" not in tt.build_recipe(wide, 832, 480, 16, FONT, v["sizes"])["filter"]
    bad = copy.deepcopy(d)
    bad["opening"]["text_vertical"] = " "
    with pytest.raises(tt.TitlesError, match="text_vertical"):
        tt.load_titles(write_defn(tmp_path, bad))


@needs_ffmpeg
@needs_font
def test_render_two_lines(tmp_path):
    sb = mini(tmp_path)
    d = defn()
    d["opening"]["text_vertical"] = "Two\nLines"
    rec = tt.render(movie(tmp_path), tmp_path / "v.mp4", d, sb, vertical=True)
    assert rec["overlays"][0]["text"] == "Two\nLines" and rec["probe_out"]["frame_count"] == 104
