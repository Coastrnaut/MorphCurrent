"""F18 local review UI: run view, CLI parity, plan view and loopback security (no GPU, no ComfyUI)."""
from __future__ import annotations

import http.client
import json
import re
import sys
import threading
import time
from pathlib import Path

import pytest

from fake_comfy import make_png
from morph_studio import cli
from morph_studio.qa import load_reviews
from morph_studio.review_ui import (UiError, apply_review, default_storyboards, list_runs, make_handler,
                                    make_server, plan_summary, render_index, render_plan_page,
                                    render_run_page, run_view)

from conftest import REPO

RUN = "run-ba2d9dbedb6189be"
CSRF = "test-token"


def _job(root: Path, name: str, kind: str, payload: bytes) -> str:
    d = root / name
    (d / "outputs").mkdir(parents=True)
    file = d / "outputs" / ("anchor_00001_.png" if kind == "anchor" else "bridge_00001_.mp4")
    file.write_bytes(payload)
    record = {"job_id": name * 4, "kind": f"{kind}_job", "state": "verified"}
    if kind == "anchor":
        record["image"] = {"local_path": "outputs\\anchor_00001_.png"}
    else:
        record["outputs"] = [{"kind": "video", "local_path": "outputs\\bridge_00001_.mp4"}]
    (d / "job.json").write_text(json.dumps(record), encoding="utf-8")
    return f"outputs\\runs\\{name}"  # cwd-relative, as real manifests store it


@pytest.fixture()
def runs(tmp_path) -> Path:
    root = tmp_path / "runs"
    root.mkdir()
    png = make_png(16, 16)
    video = bytes(range(256)) * 40  # 10240 bytes, enough for Range tests
    stages = {}
    for i, anchor in enumerate(["orchid", "butterfly", "phoenix"]):
        stages[f"anchor:{anchor}"] = {"state": "verified", "job_dir": _job(root, f"a{i:015d}", "anchor", png)}
    stages["bridge:orchid->butterfly"] = {"state": "verified", "qa": "flags", "qa_flags": ["endpoint_mismatch_end"],
                                          "job_dir": _job(root, "b000000000000001", "bridge", video)}
    stages["bridge:butterfly->phoenix"] = {"state": "verified", "qa": "no_flags", "qa_flags": [],
                                           "job_dir": _job(root, "b000000000000002", "bridge", video)}
    stages["final:movie"] = {"state": "pending"}
    run = root / RUN
    run.mkdir()
    (run / "anchors_contact_sheet.png").write_bytes(png)
    manifest = {"schema": 1, "kind": "morphcurrent_run", "created_at": "2026-11-24T12:00:00+00:00",
                "storyboard": "configs/sequences/<b>organic</b>.yaml", "plan_sha256": "ba2d9dbe" + "0" * 56,
                "order": list(stages), "stages": stages, "status": "awaiting_review",
                "contact_sheet": str(run / "anchors_contact_sheet.png")}
    (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "run-0000000000000bad").mkdir()
    (root / "run-0000000000000bad" / "manifest.json").write_text("{corrupt", encoding="utf-8")
    return root


# --- US1 -----------------------------------------------------------------------------------------

def test_run_view_and_pages(runs):
    view = run_view(runs, RUN)
    kinds = [s["kind"] for s in view["stages"]]
    assert kinds == ["anchor"] * 3 + ["bridge"] * 2 + ["final"]
    assert all(s["media"] for s in view["stages"][:5]) and view["contact_sheet"]
    assert all(p.is_relative_to(runs.resolve()) for p in view["media"].values())
    page = render_run_page(view, CSRF)
    assert page.count("<video") == 2 and page.count("<img") == 4  # 3 anchors + contact sheet
    assert "endpoint_mismatch_end" in page and "no_flags" in page
    assert "&lt;b&gt;organic&lt;/b&gt;" in page and "<b>organic" not in page  # escaped
    assert [r["run"] for r in list_runs(runs)] == [RUN]  # corrupt manifest skipped
    assert "No runs yet." in render_index([], [])


def test_controls_are_labelled_and_keyboard_reachable(runs):
    page = render_run_page(run_view(runs, RUN), CSRF)
    for tag in re.findall(r"<(?:input|video)\b[^>]*>", page):
        assert "type=hidden" in tag or "aria-label" in tag or re.search(r"<label>[^<]*" + re.escape(tag), page)
    assert all(re.search(r">\w+</button>", b) for b in re.findall(r"<button[^>]*>[^<]*</button>", page))
    assert "tabindex" not in page and "<script" not in page


def test_missing_media_is_marked(runs):
    (runs / "b000000000000002" / "outputs" / "bridge_00001_.mp4").unlink()
    view = run_view(runs, RUN)
    stage = next(s for s in view["stages"] if s["task"] == "bridge:butterfly->phoenix")
    assert stage["media"] is None and stage["media_missing"]
    assert "clip missing" in render_run_page(view, CSRF)


def test_final_movie_resolved_inside_run_dir(runs, monkeypatch, tmp_path):
    manifest_path = runs / RUN / "manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["final"] = {"output": f"outputs\\runs\\{RUN}\\final\\organic_20261124-120000Z_ba2d9dbe.mp4"}
    manifest_path.write_text(json.dumps(data), encoding="utf-8")
    (runs / RUN / "final").mkdir()
    (runs / RUN / "final" / "organic_20261124-120000Z_ba2d9dbe.mp4").write_bytes(b"\0" * 64)
    monkeypatch.chdir(tmp_path)  # a cwd unrelated to where the render ran
    view = run_view(runs, RUN)
    assert view["final"] and "Final movie</h2><video" in render_run_page(view, CSRF)


def test_corrupt_files_give_error_pages(server, runs):
    (runs / RUN / "review.json").write_text("{not json", encoding="utf-8")
    resp, body = request(server, "GET", f"/run/{RUN}")
    assert resp.status == 422 and b"<h1>422</h1>" in body
    (runs / RUN / "review.json").unlink()
    (runs / RUN / "manifest.json").write_text("{corrupt", encoding="utf-8")
    assert request(server, "GET", f"/run/{RUN}")[0].status == 422
    assert request(server, "GET", "/")[0].status == 200  # index still works


def test_unknown_or_malformed_run(runs):
    for name in ("run-ffffffffffffffff", "../etc", "run-ba2d9dbedb6189be/../x"):
        with pytest.raises(UiError):
            run_view(runs, name)


# --- US2 -----------------------------------------------------------------------------------------

def test_review_parity_with_cli(runs, capsys):
    task = "bridge:orchid->butterfly"
    apply_review(runs, RUN, task, "approved", "looks physical")
    ui = load_reviews(runs / RUN / "review.json")[task]
    assert cli.main(["review", str(runs / RUN), task, "approved", "--note", "looks physical"]) == 0
    capsys.readouterr()
    cli_entry = load_reviews(runs / RUN / "review.json")[task]
    assert {k: ui[k] for k in ("decision", "note")} == {k: cli_entry[k] for k in ("decision", "note")}
    assert set(ui) == set(cli_entry)
    # a CLI decision shows on the next page view (pages re-read)
    assert cli.main(["review", str(runs / RUN), task, "rejected"]) == 0
    capsys.readouterr()
    assert "<strong>rejected</strong>" in render_run_page(run_view(runs, RUN), CSRF)


def test_review_refusals(runs):
    for task, decision in (("anchor:orchid", "approved"), ("bridge:x->y", "approved"),
                           ("bridge:orchid->butterfly", "maybe")):
        with pytest.raises(UiError):
            apply_review(runs, RUN, task, decision)
    assert not (runs / RUN / "review.json").exists()
    apply_review(runs, RUN, "bridge:orchid->butterfly", "pending", "x" * 900)
    assert len(load_reviews(runs / RUN / "review.json")["bridge:orchid->butterfly"]["note"]) == 500


@pytest.fixture()
def server(runs):
    srv = make_server(runs, port=0, storyboards=[str(REPO / "configs/sequences/organic-machines.yaml")],
                      repo_root=REPO)
    srv.RequestHandlerClass.csrf_token = CSRF
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield srv
    srv.shutdown()
    srv.server_close()


def request(srv, method, path, body=None, headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=10)
    conn.request(method, path, body=body, headers={"Host": f"127.0.0.1:{srv.server_address[1]}",
                                                   **(headers or {})})
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp, data


def form(task="bridge:orchid->butterfly", decision="approved", csrf=CSRF, note="ok"):
    from urllib.parse import urlencode
    return urlencode({"csrf": csrf, "task": task, "decision": decision, "note": note}), \
        {"Content-Type": "application/x-www-form-urlencoded"}


def test_live_server_flow_and_headers(server, runs):
    resp, body = request(server, "GET", "/")
    assert resp.status == 200 and RUN.encode() in body and b"organic-machines" in body
    assert "default-src 'self'" in resp.getheader("Content-Security-Policy")
    assert resp.getheader("X-Frame-Options") == "DENY" and resp.getheader("X-Content-Type-Options") == "nosniff"
    resp, body = request(server, "GET", f"/run/{RUN}")
    assert resp.status == 200
    token = re.search(rb"/media/" + RUN.encode() + rb"/([0-9a-f]{24})'", body).group(1).decode()
    resp, data = request(server, "GET", f"/media/{RUN}/{token}")
    assert resp.status == 200 and resp.getheader("Accept-Ranges") == "bytes"
    resp, body = request(server, "POST", f"/run/{RUN}/review", *form())
    assert resp.status == 303 and resp.getheader("Location").startswith(f"/run/{RUN}?msg=")
    assert load_reviews(runs / RUN / "review.json")["bridge:orchid->butterfly"]["decision"] == "approved"


def test_live_server_range(server, runs):
    _, body = request(server, "GET", f"/run/{RUN}")
    tokens = re.findall(rb"<video controls preload=metadata src='/media/" + RUN.encode() + rb"/([0-9a-f]{24})'", body)
    path = f"/media/{RUN}/{tokens[0].decode()}"
    resp, data = request(server, "GET", path, headers={"Range": "bytes=100-199"})
    assert resp.status == 206 and len(data) == 100 and data[0] == 100
    assert resp.getheader("Content-Range") == "bytes 100-199/10240"
    resp, data = request(server, "GET", path, headers={"Range": "bytes=-10"})
    assert resp.status == 206 and len(data) == 10
    resp, _ = request(server, "GET", path, headers={"Range": "bytes=20000-"})
    assert resp.status == 416


def test_live_server_refusals(server, runs):
    port = server.server_address[1]
    assert request(server, "GET", "/", headers={"Host": f"evil.example:{port}"})[0].status == 403
    assert request(server, "POST", f"/run/{RUN}/review", *form(csrf="wrong"))[0].status == 403
    body, headers = form()
    assert request(server, "POST", f"/run/{RUN}/review", body,
                   {**headers, "Origin": "https://evil.example"})[0].status == 403
    assert request(server, "POST", f"/run/{RUN}/review", *form(task="anchor:orchid"))[0].status == 400
    big = "x" * 20_000
    assert request(server, "POST", f"/run/{RUN}/review", *form(note=big))[0].status == 413
    assert not (runs / RUN / "review.json").exists()
    for path in (f"/media/{RUN}/{'0' * 24}", f"/media/{RUN}/..%2F..%2Fmanifest.json", "/media/../../etc",
                 "/run/run-ffffffffffffffff", "/nope"):
        assert request(server, "GET", path)[0].status == 404


def test_non_loopback_bind_refused(runs):
    with pytest.raises(UiError, match="loopback"):
        make_server(runs, host="0.0.0.0", port=0)


# --- US3 -----------------------------------------------------------------------------------------

def test_plan_page():
    page = render_plan_page(plan_summary(REPO / "configs/sequences/organic-machines.yaml", REPO))
    assert "organic-machines" in page and page.count("<td>65</td>") == 2
    for t in ("<td>0.0 s</td>", "<td>4.0 s</td>", "<td>8.0 s</td>"):
        assert t in page
    assert "present" in page


def test_plan_page_escapes_injection(tmp_path):
    import yaml
    data = yaml.safe_load((REPO / "configs/sequences/organic-machines.yaml").read_text(encoding="utf-8"))
    data["anchors"][0]["prompt"] = "<script>alert(1)</script> orchid"
    path = tmp_path / "evil.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    page = render_plan_page(plan_summary(path, REPO))
    assert "<script>" not in page and "&lt;script&gt;alert(1)&lt;/script&gt;" in page


def test_default_storyboards_and_cli_refusal(capsys):
    boards = default_storyboards(REPO)
    assert any(b.endswith("organic-machines.yaml") for b in boards)
    assert cli.main(["review-ui", "--host", "0.0.0.0"]) == 2
    assert "loopback" in capsys.readouterr().err


# --- Polish --------------------------------------------------------------------------------------

def test_no_render_path_no_logging_and_fast(runs, tmp_path):
    import morph_studio.review_ui as ui
    source = Path(ui.__file__).read_text(encoding="utf-8")
    for forbidden in ("comfy_client", "run_render", "pipeline", "anchors import", "httpx"):
        assert forbidden not in source
    handler = make_handler(runs)
    assert handler.log_message(None, "%s", "x") is None  # overridden: writes nothing
    start = time.perf_counter()
    render_run_page(run_view(runs, RUN), CSRF)
    assert time.perf_counter() - start < 1.0
