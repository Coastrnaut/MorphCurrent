"""F29: bounded local A/B experiments - design, budget, sequential resumable runner, ratings, Pareto report."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from morph_studio import cli
from morph_studio import experiment as ex

from conftest import REPO

WAN = "configs/profiles/wan22_flf2v.binding.json"


@pytest.fixture()
def repo(tmp_path) -> Path:
    root = tmp_path / "repo"
    for rel in (WAN, "workflows/03_wan22_flf2v.json"):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes((REPO / rel).read_bytes())
    (root / "img").mkdir()
    (root / "img/a.png").write_bytes(b"\x89PNG-a")
    (root / "img/b.png").write_bytes(b"\x89PNG-b")
    (root / "history.json").write_text(json.dumps({"entries": [
        {"run": "R1", "kind": "bridge", "width": 832, "height": 480, "frames": 65, "exec_s": 500.0},
        {"run": "R2", "kind": "bridge", "width": 832, "height": 480, "frames": 65, "exec_s": 520.0},
        {"run": "R3", "kind": "bridge", "width": 640, "height": 368, "frames": 65, "exec_s": 234.0}]}),
        encoding="utf-8")
    return root


def definition(repo: Path, **over) -> Path:
    data = {"name": "orchid-test",
            "subject": {"start_image": "img/a.png", "end_image": "img/b.png", "positive_prompt": "morph"},
            "controls": {"width": 832, "height": 480},
            "factors": {"length": [65, 81], "positive_prompt": ["slow fold", "fast fold"]},
            "seeds": [1, 2, 3], "budget": {}}
    data.update(over)
    path = repo / "exp.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def design(repo, **over):
    defn = ex.load_definition(definition(repo, **over), repo_root=repo)
    return defn, ex.design(defn, ex.load_history_file(repo / "history.json"), repo_root=repo)


# --- foundational / US1 ---------------------------------------------------------------------------

def test_design_order_and_ids(repo):
    defn, cands = design(repo)
    assert len(cands) == 13 and cands[0]["baseline"]
    assert cands[0]["seed"] == 1 and cands[0]["levels"] == {}
    levels = [(c["levels"]["length"], c["levels"]["positive_prompt"], c["seed"]) for c in cands[1:]]
    assert levels[:4] == [(65, "slow fold", 1), (65, "slow fold", 2), (65, "slow fold", 3), (65, "fast fold", 1)]
    assert len({c["id"] for c in cands}) == 13
    _, again = design(repo)
    assert [c["id"] for c in again] == [c["id"] for c in cands]
    assert cands[1]["estimate_s"] == 510.0 and cands[1]["estimate_label"] == "ESTIMATED (2 samples)"
    long = next(c for c in cands if c["levels"].get("length") == 81)
    assert long["estimate_s"] is None and long["estimate_label"] == "NO DATA"


def test_baseline_defaults_from_workflow(repo):
    defaults = ex.effective_defaults(WAN, repo_root=repo)
    graph = json.loads((repo / "workflows/03_wan22_flf2v.json").read_text(encoding="utf-8"))
    assert defaults["length"] == graph["81"]["inputs"]["length"]
    _, cands = design(repo)
    assert cands[0]["frames"] == defaults["length"] and cands[0]["width"] == 832


def test_duplicate_baseline_removed_and_single_value_warned(repo):
    defn = ex.load_definition(definition(repo, factors={"length": [ex.effective_defaults(WAN, repo_root=repo)["length"]]},
                                         seeds=[7]), repo_root=repo)
    cands = ex.design(defn, [], repo_root=repo)
    assert len(cands) == 1 and any("single value" in w for w in defn.warnings)


def test_budget_deferrals(repo):
    _, cands = design(repo, budget={"max_runs": 5})
    deferred = [c for c in cands if c["status"] == "deferred"]
    assert len(deferred) == 8 and {c["limit"] for c in deferred} == {"max_runs"}
    assert [c["status"] for c in cands[:5]] == ["planned"] * 5
    _, cands = design(repo, budget={"max_gpu_s": 1100})
    planned_known = [c for c in cands if c["status"] == "planned" and c["estimate_s"]]
    assert len(planned_known) == 2 and any(c["limit"] == "max_gpu_s" for c in cands if c["status"] == "deferred")
    _, cands = design(repo, budget={"max_frames": 200})
    assert sum(c["frames"] for c in cands if c["status"] == "planned") <= 200
    assert any(c["limit"] == "max_frames" for c in cands)


@pytest.mark.parametrize("over, match", [
    ({"controls": {"length": 65}}, "leakage"),
    ({"factors": {"steps": [10, 20]}}, "allowed"),
    ({"factors": {"length": [64]}}, "4n\\+1"),
    ({"factors": {"length": [1]}}, "4n\\+1"),
    ({"controls": {"width": 830}}, "16"),
    ({"factors": {"seed": [1, 2]}}, "seed"),
    ({"subject": {"start_image": "img/missing.png", "end_image": "img/b.png"}}, "not found"),
    ({"factors": {"fps": [0]}}, "fps"),
])
def test_refusals(repo, over, match):
    with pytest.raises(ex.ExperimentError, match=match):
        design(repo, **over)


def test_seed_count(repo):
    defn = ex.load_definition(definition(repo, seeds=None, seed_count=3, master_seed=42), repo_root=repo)
    assert len(defn.seed_block) == 3 and len(set(defn.seed_block)) == 3
    assert ex.load_definition(definition(repo, seeds=None, seed_count=3, master_seed=42),
                              repo_root=repo).seed_block == defn.seed_block


# --- US2 runner -----------------------------------------------------------------------------------

class FakeExecutor:
    def __init__(self, exec_s=40.0, flagged=lambda c: False, fail=lambda c: False):
        self.calls, self.exec_s, self.flagged, self.fail = [], exec_s, flagged, fail

    def __call__(self, cand, *, submit):
        self.calls.append((cand["id"], submit))
        if not submit:
            return {"status": "validated"}
        if self.fail(cand):
            return {"status": "failed", "error": "boom", "exec_s": None}
        return {"status": "done", "exec_s": self.exec_s, "frames_produced": cand["frames"], "bytes": 1000,
                "peak_vram": None, "flags": ["shape_substitution"] if self.flagged(cand) else []}


def run(repo, executor, confirm=True, **over):
    defn = ex.load_definition(definition(repo, **over), repo_root=repo)
    out = repo / "outputs" / "experiments"
    return defn, ex.run(defn, executor, confirm_gpu=confirm, history=[], out_root=out, repo_root=repo)


def test_validate_only(repo):
    fake = FakeExecutor()
    defn, res = run(repo, fake, confirm=False)
    assert all(submit is False for _, submit in fake.calls) and len(fake.calls) == 13
    assert res["ran"] == 0 and res["validated"] == 13
    defn, res = run(repo, FakeExecutor(), confirm=True)
    assert res["ran"] == 13  # validation outcomes are not "done"


def test_sequential_and_gpu_budget(repo):
    fake = FakeExecutor(exec_s=40)
    defn, res = run(repo, fake, budget={"max_gpu_s": 100})
    assert len(fake.calls) == 3 and res["stopped"] == "budget exhausted (max_gpu_s)"
    design_ids = [c["id"] for c in ex.design(defn, [], repo_root=repo)]
    assert [c for c, _ in fake.calls] == design_ids[:3]
    lines = (ex.out_dir_for(defn, repo / "outputs" / "experiments") / "results.jsonl").read_text().splitlines()
    assert len(lines) == 3 and all(json.loads(x)["status"] == "done" for x in lines)


def test_resume_reuses_and_run_budget_counts_failures(repo):
    fake = FakeExecutor(fail=lambda c: c["baseline"])
    run(repo, fake, budget={"max_runs": 4})
    assert len(fake.calls) == 4
    fake2 = FakeExecutor()
    _, res = run(repo, fake2, budget={"max_runs": 6})
    assert res["reused"] == 4 and len(fake2.calls) == 2
    fake3 = FakeExecutor()
    _, res = run(repo, fake3)
    assert res["reused"] == 6 and len(fake3.calls) == 7


def test_early_stop(repo):
    fake = FakeExecutor(flagged=lambda c: c["levels"].get("positive_prompt") == "fast fold")
    _, res = run(repo, fake, early_stop={"consecutive_flagged": 2})
    fast = [c for c, _ in fake.calls]
    assert res["skipped"] >= 1
    assert any("positive_prompt=fast fold" in s for s in res["skip_reasons"])


def test_deferred_never_run_and_approved_untouched(repo):
    approved = repo / "outputs" / "runs" / "run-approved"
    approved.mkdir(parents=True)
    (approved / "manifest.json").write_text("{}")
    before = (approved / "manifest.json").stat().st_mtime_ns
    fake = FakeExecutor()
    defn, res = run(repo, fake, budget={"max_runs": 2})
    assert len(fake.calls) == 2 and res["deferred"] == 11
    assert (approved / "manifest.json").stat().st_mtime_ns == before


def test_invalid_validation_reported(repo):
    _, res = run(repo, lambda c, submit: {"status": "invalid", "error": "node missing"}, confirm=False)
    assert res["invalid"] == 13 and res["validated"] == 0 and "node missing" in res["errors"][0]


def test_bridge_executor_mapping(repo, monkeypatch):
    import types
    import morph_studio.bridge as br
    import morph_studio.comfy_client as cc
    import morph_studio.qa as qa
    job_dir = repo / "outputs" / "runs" / "job"
    (job_dir / "outputs").mkdir(parents=True)
    state = {"state": "verified"}

    class Client:
        def __init__(self, url): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def object_info(self): return {}
    seen = {}
    monkeypatch.setattr(cc, "ComfyClient", Client)
    monkeypatch.setattr(br, "plan_bridge", lambda req, info, repo_root=None: seen.setdefault("req", req))
    record = {"timings": {"execution_seconds": 497.2}, "error": None,
              "outputs": [{"kind": "video", "local_path": "outputs\b.mp4", "bytes": 1381553,
                           "metadata": {"frame_count": 65}}]}
    monkeypatch.setattr(br, "run_bridge", lambda plan, client, runs_root, submit: types.SimpleNamespace(
        dir=job_dir, state=state["state"] if submit else "validated", record=record))
    monkeypatch.setattr(qa, "analyze_clip", lambda path: {"flags": ["motion_spike"]})
    defn = ex.load_definition(definition(repo), repo_root=repo)
    cand = ex.design(defn, [], repo_root=repo)[1]
    execute = ex.bridge_executor(repo_root=repo)
    assert execute(cand, submit=False)["status"] == "validated"
    out = execute(cand, submit=True)
    assert out == {"status": "done", "job_dir": str(job_dir), "exec_s": 497.2, "peak_vram": None,
                   "frames_produced": 65, "bytes": 1381553, "flags": ["motion_spike"], "error": None}
    assert seen["req"].length == 65 and seen["req"].seed == cand["seed"] and seen["req"].width == 832
    state["state"] = "failed"
    assert execute(cand, submit=True)["status"] == "failed"
    monkeypatch.setattr(br, "plan_bridge", lambda *a, **k: (_ for _ in ()).throw(ValueError("bad graph")))
    execute = ex.bridge_executor(repo_root=repo)
    assert execute(cand, submit=False) == {"status": "invalid", "error": "bad graph", "exec_s": None}


# --- US3 ratings / report -------------------------------------------------------------------------

def test_ratings_and_report(repo):
    defn, _ = run(repo, FakeExecutor(exec_s=40))
    out = ex.out_dir_for(defn, repo / "outputs" / "experiments")
    cands = ex.design(defn, [], repo_root=repo)
    with pytest.raises(ex.ExperimentError):
        ex.rate(defn, cands[1]["id"], 6, out_root=repo / "outputs" / "experiments", repo_root=repo)
    with pytest.raises(ex.ExperimentError):
        ex.rate(defn, "0" * 16, 3, out_root=repo / "outputs" / "experiments", repo_root=repo)
    # rewrite outcomes with distinct costs so Pareto is meaningful
    lines = [json.loads(x) for x in (out / "results.jsonl").read_text().splitlines()]
    costs = {cands[1]["id"]: (5, 100.0), cands[2]["id"]: (4, 50.0), cands[3]["id"]: (3, 60.0),
             cands[4]["id"]: (5, 120.0)}
    for line in lines:
        if line["id"] in costs:
            line["exec_s"] = costs[line["id"]][1]
    lines[5]["frames_produced"] = 7  # mismatch
    (out / "results.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines))
    for cid, (score, _) in costs.items():
        ex.rate(defn, cid, score, note="ok", out_root=repo / "outputs" / "experiments", repo_root=repo)
    rep = ex.report(defn, out_root=repo / "outputs" / "experiments", repo_root=repo)
    assert set(rep["pareto"]) == {cands[1]["id"], cands[2]["id"]}
    assert "memory" not in rep["pareto_dimensions"] and "peak_vram" in rep["not_measured"]
    assert lines[5]["id"] in rep["mismatches"]
    assert len(rep["unrated"]) == 13 - 4
    lvl = rep["levels"]["length"]["65"]
    assert lvl["rated"] == 4 and lvl["mean_rating"] == pytest.approx(4.25)
    assert lvl["n"] == 7  # 6 factor candidates + the baseline, whose exported length is 65
    assert "observational" in rep["caveat"].lower()
    md = (out / "report.md").read_text(encoding="utf-8")
    assert "Pareto" in md and "Controls" in md and "observational" in md.lower()
    md.encode("ascii")


def test_pareto_unit():
    rows = [{"id": "a", "rating": 5, "exec_s": 10, "bytes": 5}, {"id": "b", "rating": 5, "exec_s": 12, "bytes": 5},
            {"id": "c", "rating": 3, "exec_s": 5, "bytes": 9}, {"id": "d", "rating": 2, "exec_s": 6, "bytes": 9}]
    assert ex.pareto(rows, ["exec_s", "bytes"]) == ["a", "c"]


# --- CLI ------------------------------------------------------------------------------------------

def test_cli(repo, capsys, monkeypatch):
    path = definition(repo, budget={"max_runs": 2})
    hist = str(repo / "history.json")
    assert cli.main(["experiment-plan", str(path), "--history", hist, "--repo-root", str(repo)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert len(out["candidates"]) == 13 and out["deferred"] == 11
    calls = []
    monkeypatch.setattr(ex, "bridge_executor", lambda **kw: lambda c, submit: calls.append(submit) or
                        {"status": "validated"})
    assert cli.main(["experiment-run", str(path), "--history", hist, "--repo-root", str(repo)]) == 0
    assert calls and not any(calls)
    capsys.readouterr()
    assert cli.main(["experiment-rate", str(path), "0" * 16, "3", "--repo-root", str(repo)]) == 2
    assert cli.main(["experiment-report", str(path), "--repo-root", str(repo)]) == 0
    capsys.readouterr().out.encode("ascii")
    bad = definition(repo, factors={"steps": [1, 2]})
    assert cli.main(["experiment-plan", str(bad), "--repo-root", str(repo)]) == 2
