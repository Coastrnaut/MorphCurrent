"""F39: film review state across batch runs, decisions, rerender queue, review aids and the act page."""
from __future__ import annotations

import hashlib
import http.client
import json
import shutil
import subprocess
import threading
from pathlib import Path
from urllib.parse import urlencode

import pytest
import yaml

from morph_studio import batch_review as br
from morph_studio import cli
from morph_studio.media import probe_video
from morph_studio.review_ui import make_server

from conftest import REPO

FILM = REPO / "configs/sequences/engineering-film.yaml"
needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="ffmpeg missing")
IDS = ["a", "b", "c", "d", "e", "f"]


def storyboard(tmp_path: Path) -> Path:
    anchors = []
    for i, k in enumerate(IDS):
        a = {"id": k, "prompt": f"subject {k}", "chapter": "x" if i < 3 else "y"}
        if i % 3:
            a.update(generation="reference_edit", reference=IDS[i - 1])
        else:
            a["generation"] = "text_to_image"
        anchors.append(a)
    sb = {"schema_version": 1, "name": "mini-film",
          "render": {"anchor_profile": "anchor_t2i", "bridge_profile": "wan22_flf2v", "master_seed": 7},
          "style": {"description": "x"}, "anchors": anchors,
          "transitions": [{"from": IDS[i], "to": IDS[i + 1], "frames": 33, "prompt": "m"} for i in range(5)]}
    path = tmp_path / "mini-film.yaml"
    path.write_text(yaml.safe_dump(sb, sort_keys=False), encoding="utf-8")
    return path


def clip(path: Path, color: str = "red", seconds: float = 1.0) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"color=c={color}:size=96x64:rate=16:duration={seconds}", "-pix_fmt", "yuv420p", str(path)],
                   check=True)


class Runs:
    """Builds fake run folders (manifest + job dirs) in a runs root."""

    def __init__(self, root: Path, media: bool = False):
        self.root, self.media, self.n = root, media, 0
        root.mkdir(parents=True, exist_ok=True)

    def run(self, stages: dict[str, dict], created: str, name: str | None = None, review: dict | None = None,
            storyboard: str = "mini-film") -> Path:
        self.n += 1
        run_dir = self.root / (name or f"run-{self.n:016x}")
        run_dir.mkdir()
        out = {}
        for tid, spec in stages.items():
            tag = spec.get("tag", "v1")
            job = self.root / hashlib.sha256(f"{tid}:{tag}".encode()).hexdigest()[:16]
            job.mkdir(exist_ok=True)
            kind = tid.split(":")[0]
            if kind == "bridge":
                rec = {"outputs": [{"kind": "video", "local_path": "out.mp4"}]}
                if self.media and not (job / "out.mp4").exists():
                    clip(job / "out.mp4", spec.get("color", "red"), spec.get("seconds", 1.0))
                else:
                    (job / "out.mp4").write_bytes(tag.encode())
                key = "video_sha256"
            else:
                rec = {"image": {"local_path": "a.png"}}
                (job / "a.png").write_bytes(tag.encode())
                key = "image_sha256"
            (job / "job.json").write_text(json.dumps(rec), encoding="utf-8")
            st = {"state": spec.get("state", "verified"), "job_dir": f"outputs\\runs\\{job.name}",
                  "job_id": hashlib.sha256(f"job:{tid}:{tag}".encode()).hexdigest(),
                  key: hashlib.sha256(f"{tid}:{tag}".encode()).hexdigest()}
            if kind == "bridge":
                st.update(qa="flagged" if spec.get("flags") else "no_flags", qa_flags=spec.get("flags", []))
            out[tid] = st
        manifest = {"created_at": created, "storyboard": storyboard, "order": list(stages), "stages": out}
        (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        if review:
            (run_dir / "review.json").write_text(json.dumps(review), encoding="utf-8")
        return run_dir


def A(k):
    return f"anchor:{k}"


def B(x, y):
    return f"bridge:{x}->{y}"


def state(tmp_path, sb, root):
    return br.film_state(sb, root, tmp_path / "log.jsonl", repo_root=REPO)


def by(st, stage):
    return next(s for s in st["stages"] if s["stage"] == stage)


# --- US1 ------------------------------------------------------------------------------------------

def test_no_runs_all_missing(tmp_path):
    st = state(tmp_path, storyboard(tmp_path), tmp_path / "runs")
    assert st["total"] == 11 and all(s["state"] == "missing" for s in st["stages"])
    assert st["acts"]["x"] == {"anchors": 3, "bridges": 3, "verified": 0, "approved": 0, "rejected": 0,
                               "stale": 0, "flagged": 0, "missing": 6}
    assert by(st, B("c", "d"))["act"] == "x"  # a bridge belongs to its start anchor's act


def test_state_across_runs(tmp_path):
    sb = storyboard(tmp_path)
    runs = Runs(tmp_path / "runs")
    runs.run({A("a"): {}, A("b"): {}, B("a", "b"): {}}, "2026-11-24T10:00:00+00:00")
    runs.run({A("a"): {}, A("b"): {}, B("a", "b"): {"tag": "v2", "flags": [{"type": "hard_cut"}, {"type": "freeze"}]},
              A("c"): {}, B("b", "c"): {}}, "2026-11-24T11:00:00+00:00")
    runs.run({A("a"): {}}, "2026-11-24T12:00:00+00:00", storyboard="other")  # same ids -> still counted
    runs.run({"anchor:zzz": {}}, "2026-11-24T13:00:00+00:00")  # unrelated storyboard: ignored
    st = state(tmp_path, sb, tmp_path / "runs")
    ab = by(st, B("a", "b"))
    assert [v["run"] for v in ab["versions"]] == ["run-0000000000000001", "run-0000000000000002"]
    assert ab["current"] == ab["versions"][-1]["sha256"] and ab["score"] == 4
    assert len(by(st, A("a"))["versions"]) == 1  # cache hits add no version
    assert by(st, A("d"))["state"] == "missing"
    assert st["acts"]["x"]["verified"] == 5 and st["acts"]["x"]["flagged"] == 1
    assert len(st["runs"]) == 3


def test_real_film_191_stages(tmp_path):
    st = br.film_state(FILM, tmp_path / "none", tmp_path / "log.jsonl", repo_root=REPO)
    assert st["total"] == 191 and sum(a["anchors"] for a in st["acts"].values()) == 96
    assert list(st["acts"]) == ["spark", "power", "signal", "logic", "scale"]


# --- US2 ------------------------------------------------------------------------------------------

def test_decisions_stale_and_versions_kept(tmp_path):
    sb = storyboard(tmp_path)
    runs = Runs(tmp_path / "runs")
    runs.run({A("a"): {}, A("b"): {}, B("a", "b"): {}}, "2026-11-24T10:00:00+00:00")
    st = state(tmp_path, sb, tmp_path / "runs")
    e = br.record(st, B("a", "b"), "rejected", "x" * 600, "owner")
    assert len(e["note"]) == 500 and e["version"] == by(st, B("a", "b"))["current"]
    for bad in [(B("d", "e"), "approved"), ("bridge:q->r", "approved"), (B("a", "b"), "maybe")]:
        with pytest.raises(br.ReviewError):
            br.record(st, *bad)
    with pytest.raises(br.ReviewError, match="reviewer"):
        br.record(st, B("a", "b"), "approved", reviewer=" ")
    log = tmp_path / "log.jsonl"
    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    old_version = e["version"]
    runs.run({A("a"): {}, A("b"): {}, B("a", "b"): {"tag": "v2"}}, "2026-11-24T11:00:00+00:00")
    st = state(tmp_path, sb, tmp_path / "runs")
    ab = by(st, B("a", "b"))
    assert ab["stale"] and ab["decision"]["version"] == old_version
    assert old_version in [v["sha256"] for v in ab["versions"]] and len(ab["versions"]) == 2
    assert st["acts"]["x"]["stale"] == 1 and st["acts"]["x"]["rejected"] == 0
    br.record(st, B("a", "b"), "approved")
    assert log.read_text(encoding="utf-8").splitlines()[0] == lines[0]  # append-only
    assert not state(tmp_path, sb, tmp_path / "runs")["stages"][0]["stale"]


def test_run_review_json_imported(tmp_path):
    sb = storyboard(tmp_path)
    runs = Runs(tmp_path / "runs")
    runs.run({A("a"): {}, A("b"): {}, B("a", "b"): {}}, "2026-11-24T10:00:00+00:00",
             review={B("a", "b"): {"decision": "approved", "note": "ok", "t": "2026-11-24T10:30:00+00:00"}})
    ab = by(state(tmp_path, sb, tmp_path / "runs"), B("a", "b"))
    assert ab["decision"]["decision"] == "approved" and ab["decision"]["source"] == "run-review" and not ab["stale"]


def test_bulk_approval_and_order(tmp_path):
    sb = storyboard(tmp_path)
    runs = Runs(tmp_path / "runs")
    runs.run({A(k): {} for k in IDS} | {B("a", "b"): {}, B("b", "c"): {"flags": [{"type": "flare"}]},
                                        B("c", "d"): {"flags": [{"type": "hard_cut"}]}, B("d", "e"): {}},
             "2026-11-24T10:00:00+00:00")
    st = state(tmp_path, sb, tmp_path / "runs")
    order = [s["stage"] for s in br.review_order(st, "x")]
    assert order[:2] == [B("c", "d"), B("b", "c")]  # flagged, worst score first
    assert order[2:] == [A("a"), B("a", "b"), A("b"), A("c")]  # then film order
    br.record(st, A("a"), "approved")
    res = br.approve_act(st, "x")
    assert res["stages"] == [B("a", "b")] and res["approved"] == 1  # flagged and anchors untouched
    assert br.approve_act(st, "x")["approved"] == 0
    assert by(st, B("d", "e"))["decision"] is None  # other act untouched; e->f missing
    with pytest.raises(br.ReviewError):
        br.approve_act(st, "nope")


# --- US3 ------------------------------------------------------------------------------------------

def rendered_all(tmp_path):
    sb = storyboard(tmp_path)
    runs = Runs(tmp_path / "runs")
    runs.run({A(k): {} for k in IDS} | {B(IDS[i], IDS[i + 1]): {} for i in range(5)}, "2026-11-24T10:00:00+00:00")
    return sb, state(tmp_path, sb, tmp_path / "runs")


def test_rerender_queue_closure(tmp_path):
    sb, st = rendered_all(tmp_path)
    assert br.rerender_queue(st) == {"stages": [], "total_s": 0.0, "labels": {}, "rejected": []}
    br.record(st, B("d", "e"), "rejected")
    q = br.rerender_queue(st)
    assert [r["stage"] for r in q["stages"]] == [B("d", "e")] and q["total_s"] > 0
    assert set(q["labels"]) <= {"ESTIMATED", "INTERPOLATED", "EXTRAPOLATED"}
    br.record(st, A("b"), "rejected")
    q = br.rerender_queue(st)
    stages = {r["stage"]: r["reason"] for r in q["stages"]}
    assert stages == {A("b"): "rejected", A("c"): "depends on b", B("a", "b"): "touches b",
                      B("b", "c"): "touches b", B("c", "d"): "touches c", B("d", "e"): "rejected"}
    assert A("d") not in stages  # act y opens with a fresh text-to-image anchor


def test_rerender_act_opening_anchor(tmp_path):
    sb, st = rendered_all(tmp_path)
    br.record(st, A("d"), "rejected")
    stages = {r["stage"] for r in br.rerender_queue(st)["stages"]}
    assert stages == {A("d"), A("e"), A("f"), B("c", "d"), B("d", "e"), B("e", "f")}


def test_write_rerender(tmp_path):
    sb, st = rendered_all(tmp_path)
    br.record(st, B("d", "e"), "rejected")
    q = br.rerender_queue(st)
    out = br.write_rerender(st, q, tmp_path / "re.yaml")
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert [a["id"] for a in data["anchors"]] == ["d", "e"]  # from act y's first anchor to the bridge end
    plan = st["_plan"]
    assert data["anchors"][0]["seed"] == plan["tasks"][A("d")]["seed"]
    assert data["transitions"][0]["seed"] != plan["tasks"][B("d", "e")]["seed"]
    assert "rerender" in out.read_text(encoding="utf-8").splitlines()[0]
    with pytest.raises(FileExistsError):
        br.write_rerender(st, q, out)
    with pytest.raises(br.ReviewError, match="empty"):
        br.write_rerender(st, {"stages": []}, tmp_path / "none.yaml")


# --- US4 ------------------------------------------------------------------------------------------

@needs_ffmpeg
def test_act_sheet_and_compare(tmp_path):
    sb = storyboard(tmp_path)
    runs = Runs(tmp_path / "runs", media=True)
    runs.run({A(k): {} for k in IDS} | {B("a", "b"): {"color": "red"}, B("b", "c"): {"color": "blue"}},
             "2026-11-24T10:00:00+00:00")
    runs.run({A(k): {} for k in IDS} | {B("a", "b"): {"tag": "v2", "color": "green", "seconds": 1.5}},
             "2026-11-24T11:00:00+00:00")
    st = state(tmp_path, sb, tmp_path / "runs")
    rec = br.act_sheet(st, "x", tmp_path / "sheet.png")
    assert [r["stage"] for r in rec["rows"]] == [B("a", "b"), B("b", "c")]
    assert rec["missing"] == [B("c", "d")] and rec["rows"][0]["frames"] == [0, 11, 23]
    info = probe_video(tmp_path / "sheet.png")
    assert (info["width"], info["height"]) == (3 * br.SHEET_W, 2 * br.SHEET_H)
    assert (tmp_path / "sheet.sheet.json").is_file()
    with pytest.raises(FileExistsError):
        br.act_sheet(st, "x", tmp_path / "sheet.png")
    with pytest.raises(br.ReviewError, match="no rendered"):
        br.act_sheet(st, "y", tmp_path / "y.png")
    cmp_ = br.compare(st, B("a", "b"), tmp_path / "cmp.mp4")
    v = probe_video(tmp_path / "cmp.mp4")
    assert v["height"] == 240 and v["width"] == 2 * 360 and abs(v["duration_s"] - 1.5) <= 0.07
    assert cmp_["b"] == by(st, B("a", "b"))["current"]
    with pytest.raises(br.ReviewError, match="two are needed"):
        br.compare(st, B("b", "c"), tmp_path / "c2.mp4")
    with pytest.raises(br.ReviewError, match="version"):
        br.compare(st, B("a", "b"), tmp_path / "c3.mp4", a="ffff")
    with pytest.raises(FileExistsError):
        br.compare(st, B("a", "b"), tmp_path / "cmp.mp4")


# --- US5 ------------------------------------------------------------------------------------------

@pytest.fixture
def film_server(tmp_path):
    sb = storyboard(tmp_path)
    runs = Runs(tmp_path / "runs")
    runs.run({A(k): {} for k in IDS} | {B("a", "b"): {}, B("b", "c"): {"flags": [{"type": "hard_cut"}]}},
             "2026-11-24T10:00:00+00:00")
    log = tmp_path / "log.jsonl"
    srv = make_server(tmp_path / "runs", port=0, repo_root=REPO, film_storyboard=sb, film_log=log)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield srv, log
    srv.shutdown()
    srv.server_close()


def req(srv, method, path, body=None, headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=10)
    conn.request(method, path, body=body, headers=headers or {})
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp, data.decode("utf-8", "replace")


def test_act_page_keyboard_review(film_server):
    srv, log = film_server
    resp, page = req(srv, "GET", "/film/x")
    assert resp.status == 200 and "Keys: A approve, R reject, N next" in page
    assert page.index("bridge:b-&gt;c") < page.index("bridge:a-&gt;b")  # flagged first
    assert "/film.js" in page
    js_resp, js = req(srv, "GET", "/film.js")
    assert js_resp.status == 200 and "keydown" in js
    token = srv.RequestHandlerClass.csrf_token
    form = {"act": "x", "stage": B("a", "b"), "decision": "approved"}
    hdr = {"Content-Type": "application/x-www-form-urlencoded"}
    assert req(srv, "POST", "/film/review", urlencode(form), hdr)[0].status == 403
    resp, _ = req(srv, "POST", "/film/review", urlencode(dict(form, csrf=token)), hdr)
    assert resp.status == 303 and resp.getheader("Location").startswith("/film/x?msg=")
    entry = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
    assert entry["stage"] == B("a", "b") and entry["decision"] == "approved"
    assert req(srv, "POST", "/film/review", urlencode(dict(form, csrf=token, stage=B("d", "e"))), hdr)[0].status == 400
    assert req(srv, "GET", "/film/nope")[0].status == 404


# --- CLI ------------------------------------------------------------------------------------------

def test_cli(tmp_path, capsys):
    sb, st = rendered_all(tmp_path)
    common = ["--storyboard", str(sb), "--runs-root", str(tmp_path / "runs"), "--log", str(tmp_path / "log.jsonl")]
    assert cli.main(["film-review-status", *common]) == 0
    text = capsys.readouterr().out
    text.encode("ascii")
    assert text.startswith("act x") and "11 stage(s) to review" in text
    assert cli.main(["film-review", B("a", "b"), "rejected", "--note", "wobble", *common]) == 0
    assert json.loads(capsys.readouterr().out)["decision"] == "rejected"
    assert cli.main(["film-review-status", "--json", *common]) == 1
    assert json.loads(capsys.readouterr().out)["acts"]["x"]["rejected"] == 1
    assert cli.main(["film-review", "bridge:q->r", "approved", *common]) == 2
    capsys.readouterr()
    assert cli.main(["film-review-approve-act", "y", *common]) == 0
    assert json.loads(capsys.readouterr().out)["approved"] == 2
    assert cli.main(["film-rerender-queue", *common]) == 0
    assert "1 stage(s)" in capsys.readouterr().out
    out = tmp_path / "re.yaml"
    assert cli.main(["film-rerender-queue", "--write", str(out), *common]) == 0
    capsys.readouterr()
    assert out.is_file() and cli.main(["film-rerender-queue", "--write", str(out), *common]) == 2
    capsys.readouterr()
    assert cli.main(["film-compare", B("a", "b"), "--out", str(tmp_path / "c.mp4"), *common]) == 2
    capsys.readouterr()
    assert cli.main(["film-act-sheet", "nope", "--out", str(tmp_path / "s.png"), *common]) == 2
    capsys.readouterr()
    if shutil.which("ffprobe"):  # fake (unreadable) clips count as missing: nothing to show, no traceback
        assert cli.main(["film-act-sheet", "x", "--out", str(tmp_path / "s.png"), *common]) == 1


def test_review_ui_film_options(monkeypatch, tmp_path):
    import morph_studio.review_ui as ui
    seen = {}

    class Stop(Exception):
        pass

    def fake(runs_root, **kw):
        seen.update(kw)
        raise Stop

    monkeypatch.setattr(ui, "make_server", fake)
    with pytest.raises(Stop):
        cli.main(["review-ui", "--film", "configs/sequences/engineering-film.yaml", "--film-log", "x.jsonl"])
    assert seen["film_storyboard"] == "configs/sequences/engineering-film.yaml" and seen["film_log"] == "x.jsonl"
