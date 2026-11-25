"""F36: cost history ingest, per-length budget, approved act batches with pinned seeds, status checks."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from morph_studio import cli
from morph_studio import production as pr
from morph_studio.dag import compile_plan
from morph_studio.schema import load_storyboard

from conftest import REPO

FILM = REPO / "configs/sequences/engineering-film.yaml"


def history(tmp_path, entries=None) -> Path:
    data = {"schema": 1, "source": "test", "entries": entries if entries is not None else [
        {"run": "R", "kind": "bridge", "width": 832, "height": 480, "frames": 65, "exec_s": 490.0, "job": "a" * 16},
        {"run": "R", "kind": "bridge", "width": 832, "height": 480, "frames": 65, "exec_s": 500.0, "job": "b" * 16},
        {"run": "R", "kind": "bridge", "width": 832, "height": 480, "frames": 81, "exec_s": 660.0, "job": "c" * 16},
        {"run": "R", "kind": "anchor", "method": "text_to_image", "width": 832, "height": 480, "exec_s": 19.0, "job": "d" * 16},
        {"run": "R", "kind": "anchor", "method": "reference_edit", "width": 832, "height": 480, "exec_s": 52.0, "job": "e" * 16}]}
    p = tmp_path / "hist.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def job(runs: Path, name: str, *, kind="wan22_flf2v_bridge", state="verified", exec_s=500.0, length=65,
        method=None, prompt="p-" + "0"):
    d = runs / name
    d.mkdir(parents=True)
    rec = {"kind": kind, "state": state, "values": {"width": 832, "height": 480, "length": length},
           "request": {"method": method} if method else {}, "prompt_id": prompt,
           "timings": {"execution_seconds": exec_s} if exec_s is not None else {}}
    (d / "job.json").write_text(json.dumps(rec), encoding="utf-8")
    return d


@pytest.fixture()
def film_plan():
    return compile_plan(load_storyboard(FILM), repo_root=REPO, storyboard_bytes=FILM.read_bytes())


# --- US1 ------------------------------------------------------------------------------------------

def test_ingest(tmp_path):
    runs = tmp_path / "runs"
    job(runs, "1111111111111111", length=81, exec_s=655.0, prompt="p1")
    job(runs, "2222222222222222", kind="anchor_image", method="text_to_image", exec_s=18.0, prompt="p2")
    job(runs, "3333333333333333", state="failed", prompt="p3")
    job(runs, "4444444444444444", exec_s=None, prompt="p4")
    h = history(tmp_path, entries=[])
    rep = pr.ingest(runs, h)
    assert rep["added"] == 2 and rep["skipped"] == 2
    entries = json.loads(h.read_text())["entries"]
    assert {(e["kind"], e.get("frames"), e.get("method")) for e in entries} == {("bridge", 81, None),
                                                                                ("anchor", None, "text_to_image")}
    assert pr.ingest(runs, h)["added"] == 0
    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    with pytest.raises(pr.ProductionError):
        pr.ingest(runs, bad)


# --- US2 ------------------------------------------------------------------------------------------

def bridge(frames, w=832, h=480):
    return {"kind": "bridge", "frames": frames, "width": w, "height": h}


def test_stage_cost(tmp_path):
    hist = json.loads(history(tmp_path).read_text())["entries"]
    s, label = pr.stage_cost(bridge(65), hist)
    assert (s, label) == (495.0, "ESTIMATED")
    s, label = pr.stage_cost(bridge(73), hist)
    assert label == "INTERPOLATED" and 495 < s < 660 and s == pytest.approx(577.5)
    s, label = pr.stage_cost(bridge(33), hist)
    assert label == "EXTRAPOLATED" and 0 <= s < 495
    s, label = pr.stage_cost(bridge(65, 640, 368), hist)
    assert label == "EXTRAPOLATED" and s < 495
    assert pr.stage_cost({"kind": "anchor", "method": "reference_edit", "width": 832, "height": 480}, hist) == (52.0, "ESTIMATED")
    assert pr.stage_cost(bridge(65), [])[1] == "NO DATA"


def test_film_budget(tmp_path, film_plan):
    hist = json.loads(history(tmp_path).read_text())["entries"]
    b = pr.budget(film_plan, hist)
    assert [a["id"] for a in b["acts"]] == ["spark", "power", "signal", "logic", "scale"]
    assert sum(a["anchors"] for a in b["acts"]) == 96 and sum(a["bridges"] for a in b["acts"]) == 95
    assert sum(a["seconds"] for a in b["acts"]) == pytest.approx(b["totals"]["seconds"], abs=1)
    assert b["storage_bytes"] > 0 and all(sum(a["labels"].values()) == a["anchors"] + a["bridges"] for a in b["acts"])


# --- US3 ------------------------------------------------------------------------------------------

def test_batches_caps(tmp_path, film_plan):
    hist = json.loads(history(tmp_path).read_text())["entries"]
    b = pr.budget(film_plan, hist, max_batch_s=3600, max_jobs=10)
    for act in b["acts"]:
        stages = [s for batch in act["batches"] for s in batch["stages"]]
        assert len(stages) == act["anchors"] + act["bridges"]
        for batch in act["batches"]:
            assert len(batch["stages"]) <= 10
            assert batch["seconds"] <= 3600 or batch["oversized"]
    spark_last = b["acts"][0]["batches"][-1]
    assert spark_last["early_stages"] == ["anchor:porous-pot-wet-cell"]  # next act's first anchor
    assert spark_last["eta_s"] == pytest.approx(spark_last["seconds"] + 19.0 + 60.0, abs=0.2)
    tiny = pr.budget(film_plan, hist, max_batch_s=100)
    assert any(batch["oversized"] for a in tiny["acts"] for batch in a["batches"])


def test_approval_and_batch_storyboards(tmp_path, film_plan):
    log = tmp_path / "appr.jsonl"
    hist = history(tmp_path)
    with pytest.raises(pr.ProductionError, match="approved"):
        pr.write_batches(FILM, "power", tmp_path / "out", approvals_log=log, history=hist)
    with pytest.raises(pr.ProductionError, match="act"):
        pr.approve(log, FILM, "finale", "x")
    pr.approve(log, FILM, "power", "pilot", owner="owner")
    files = pr.write_batches(FILM, "power", tmp_path / "out", approvals_log=log, history=hist, max_jobs=8)
    assert len(files) >= 2
    full = film_plan["tasks"]
    keys = ("seed", "positive_prompt", "negative_prompt", "width", "height", "frames", "reference", "method")
    seen = set()
    for f in files:
        sb = load_storyboard(f)
        plan = compile_plan(sb, repo_root=REPO)
        for task_id in plan["order"]:
            t = plan["tasks"][task_id]
            if t["kind"] == "final":
                continue
            assert {k: t.get(k) for k in keys} == {k: full[task_id].get(k) for k in keys}, task_id
            seen.add(task_id)
    power = {f"anchor:{a.id}" for a in load_storyboard(FILM).anchors if a.chapter == "power"}
    assert power <= seen
    with pytest.raises(FileExistsError):
        pr.write_batches(FILM, "power", tmp_path / "out", approvals_log=log, history=hist, max_jobs=8)
    pr.approve(log, FILM, "power", "hold", revoke=True)
    with pytest.raises(pr.ProductionError, match="approved"):
        pr.write_batches(FILM, "power", tmp_path / "out2", approvals_log=log, history=hist)


# --- US4 ------------------------------------------------------------------------------------------

def test_status_and_duplicates(tmp_path, film_plan):
    runs = tmp_path / "runs"
    job(runs, "1111111111111111", length=65, exec_s=900.0, prompt="dup")
    job(runs, "2222222222222222", length=65, exec_s=500.0, prompt="dup")
    st = pr.status(film_plan, runs, json.loads(history(tmp_path).read_text())["entries"])
    assert st["remaining"] == 191 and st["finished"] == 0
    assert st["duplicates"] and st["duplicates"][0]["prompt_id"] == "dup"
    flagged = [r for r in st["ratios"] if r["flag"]]
    assert flagged and flagged[0]["actual"] == 900.0
    assert st["ok"] is False


def test_real_runs_no_duplicates(film_plan):
    st = pr.status(film_plan, REPO / "outputs/runs", json.loads((REPO / "configs/perf_history.json").read_text())["entries"])
    assert st["duplicates"] == []


# --- CLI ------------------------------------------------------------------------------------------

def test_cli(tmp_path, capsys):
    hist = history(tmp_path)
    assert cli.main(["prod-budget", str(FILM), "--history", str(hist)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert len(out["acts"]) == 5
    log = tmp_path / "a.jsonl"
    assert cli.main(["prod-batch", str(FILM), "--act", "signal", "--history", str(hist), "--approvals", str(log),
                     "--out-dir", str(tmp_path / "o")]) == 2
    capsys.readouterr()
    assert cli.main(["prod-approve", str(FILM), "--act", "signal", "--note", "ok", "--approvals", str(log)]) == 0
    capsys.readouterr()
    assert cli.main(["prod-batch", str(FILM), "--act", "signal", "--history", str(hist), "--approvals", str(log),
                     "--out-dir", str(tmp_path / "o")]) == 0
    assert json.loads(capsys.readouterr().out)["files"]
    runs = tmp_path / "runs"
    runs.mkdir()
    assert cli.main(["history-ingest", "--runs-root", str(runs), "--history", str(hist)]) == 0
    capsys.readouterr().out.encode("ascii")


def test_produce_runs_batches_in_order(tmp_path):
    """Owner 2026-11-24: automate rendering of every batch; one job at a time, stop at the first failure."""
    log = tmp_path / "appr.jsonl"
    for act in ("spark", "power"):
        pr.approve(log, FILM, act, "test", owner="owner")
    with pytest.raises(pr.ProductionError, match="unknown act"):
        pr.produce(FILM, ["finale"], tmp_path / "b", approvals_log=log, history=history(tmp_path))
    dry = pr.produce(FILM, ["power", "spark"], tmp_path / "b", approvals_log=log, history=history(tmp_path),
                     dry_run=True)
    assert dry["acts"] == ["spark", "power"]  # film order regardless of input order
    assert all(Path(b).is_file() for b in dry["batches"]) and dry["ran"] == []
    calls, codes = [], iter([0, 7, 5, 0, 0])

    def runner(args):
        calls.append(args)
        return next(codes)

    out = pr.produce(FILM, ["spark", "power"], tmp_path / "b", approvals_log=log, history=history(tmp_path),
                     log=tmp_path / "produce.jsonl", runner=runner, python="py")
    assert len(calls) == 3 and calls[0][1:4] == ["-m", "morph_studio.cli", "render"] and calls[0][-1] == "--confirm-gpu"
    assert [e["status"] for e in out["ran"]] == ["complete", "awaiting_review", "failed"]
    assert out["stopped"]["exit"] == 5 and "re-run" in out["next"]
    assert len((tmp_path / "produce.jsonl").read_text(encoding="utf-8").splitlines()) == 3
    with pytest.raises(pr.ProductionError, match="approved"):
        pr.produce(FILM, ["logic"], tmp_path / "b", approvals_log=log, history=history(tmp_path), dry_run=True)


def test_cli_film_produce_dry_run(tmp_path, capsys):
    log = tmp_path / "appr.jsonl"
    pr.approve(log, FILM, "spark", "test", owner="owner")
    assert cli.main(["film-produce", "spark", "--batch-dir", str(tmp_path / "b"), "--approvals", str(log),
                     "--dry-run"]) == 0
    assert json.loads(capsys.readouterr().out)["acts"] == ["spark"]
    assert cli.main(["film-produce", "nope", "--batch-dir", str(tmp_path / "b"), "--approvals", str(log)]) == 2



def test_wait_for_previous_run(tmp_path):
    """Owner 2026-11-24: start the fixed-anchor film run automatically after the current run frees the GPU."""
    log = tmp_path / "prev.jsonl"
    ticks = {"n": 0}

    def sleep(_):
        ticks["n"] += 1
        with log.open("a", encoding="utf-8") as fh:  # the earlier run finishes one batch per poll
            fh.write(json.dumps({"batch": f"b{ticks['n']}", "status": "complete"}) + "\n")

    idle_answers = iter([False, True])  # queue still busy right after the last batch, then idle
    out = pr.wait_for_previous(log, 2, poll_s=0, idle=lambda: next(idle_answers) if ticks["n"] >= 2 else False,
                               sleep=sleep, now=lambda: float(ticks["n"]))
    assert out["previous_batches"] >= 2 and not out["previous_failed"] and ticks["n"] >= 2
    fail = tmp_path / "fail.jsonl"
    fail.write_text(json.dumps({"status": "failed"}) + "\n", encoding="utf-8")
    assert pr.wait_for_previous(fail, 12, poll_s=0, idle=lambda: True)["previous_failed"]
    with pytest.raises(pr.ProductionError, match="still busy"):
        pr.wait_for_previous(tmp_path / "none.jsonl", 3, poll_s=0, idle=lambda: True, sleep=lambda _: None,
                             now=iter(range(100)).__next__, max_wait_s=5)



def test_wait_queue_quiet_ignores_short_gaps():
    """Owner 2026-11-24: after the owner stops a run, start the anchor render only once the queue is truly idle."""
    clock = {"t": 0.0}
    pattern = [False, True, False, True, True, True, True, True, True, True]  # a 1-poll gap does not count
    answers = iter(pattern + [True] * 50)

    def sleep(s):
        clock["t"] += s

    waited = pr.wait_queue_quiet(2, poll_s=30, idle=lambda: next(answers), sleep=sleep, now=lambda: clock["t"])
    assert waited >= 2 * 60 + 90  # quiet only counted from the third True after the last busy poll
    with pytest.raises(pr.ProductionError, match="not quiet"):
        pr.wait_queue_quiet(1, poll_s=30, idle=lambda: False, sleep=sleep, now=lambda: clock["t"], max_wait_s=60)
