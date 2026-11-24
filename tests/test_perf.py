"""F11 performance reports, whole-GPU sample analysis and estimates (offline)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from morph_studio import cli
from morph_studio.dag import compile_plan
from morph_studio.perf import (NOT_MEASURED, WHOLE_GPU, analyze_samples, build_report, estimate,
                               load_history)
from morph_studio.schema import load_storyboard
from morph_studio.vram import VramSampler

REPO = Path(__file__).resolve().parents[1]
HISTORY = REPO / "configs" / "perf_history.json"
T0 = datetime(2026, 11, 24, 15, 0, 0, tzinfo=timezone.utc)


def iso(seconds: float) -> str:
    return (T0 + timedelta(seconds=seconds)).isoformat(timespec="seconds")


def epoch(seconds: float) -> float:
    return (T0 + timedelta(seconds=seconds)).timestamp()


# ------------------------------------------------------------------ sample analysis

def test_empty_samples_are_not_measured():
    assert analyze_samples([], 0.5)["status"] == NOT_MEASURED


def test_gap_detection_and_coverage():
    samples = [[epoch(i * 0.5), 1000] for i in range(20)]           # 0..9.5 s
    samples += [[epoch(15 + i * 0.5), 1000] for i in range(10)]     # gap 9.5 -> 15 s
    result = analyze_samples(samples, 0.5)
    assert result["gaps"] == [[round(epoch(9.5), 3), round(epoch(15), 3)]]
    assert result["max_gap_s"] == 5.5 and result["coverage_pct"] < 80
    assert result["status"] == WHOLE_GPU


def test_external_baseline_from_samples_before_first_submission():
    # 35 GiB held by another app before the run; it ramps up during the run too
    samples = [[epoch(i), 35_000] for i in range(5)] + [[epoch(5 + i), 40_000 + 100 * i] for i in range(5)]
    result = analyze_samples(samples, 1.0, before=epoch(4))
    assert result["external_baseline_mib"] == 35_000
    assert result["peak_mib"] == 40_400 and result["peak_rise_mib"] == 5_400
    assert "median of samples before first submission" == result["baseline_source"]


def test_sampler_records_utc_samples_and_writes_file(tmp_path):
    values = iter(["0, 1000, 49140"] + ["0, 2000, 49140"] * 50)
    sampler = VramSampler(interval=0.01, query=lambda: next(values))
    with sampler:
        pass
    path = sampler.write(tmp_path / "vram_samples.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["samples"][0][1] == 1000 and data["interval_s"] == 0.01
    assert abs(data["samples"][0][0] - datetime.now(timezone.utc).timestamp()) < 60


# ---------------------------------------------------------------- run report fixtures

def make_job(root: Path, name: str, *, kind: str, created: float, submitted: float, exec_s: float,
             width=832, height=480, frames=65, method=None) -> Path:
    job_dir = root / name
    job_dir.mkdir(parents=True)
    events = [{"t": iso(created), "event": "planned"}, {"t": iso(submitted), "event": "submitted"},
              {"t": iso(submitted + exec_s), "event": "completed"},
              {"t": iso(submitted + exec_s + 2), "event": "verified"}]
    record = {"job_id": name * 4, "kind": kind, "created_at": iso(created), "events": events,
              "timings": {"execution_seconds": exec_s},
              "models": {"1.unet_name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"},
              "comfyui": {"validated": {"comfyui_version": "0.46.0", "pytorch_version": "2.14.1+cu130",
                                        "devices": [{"name": "cuda:0 NVIDIA RTX A6000"}]}}}
    if kind == "anchor_image":
        record.update(method=method, image={"width": width, "height": height}, values={})
    else:
        record["values"] = {"width": width, "height": height, "length": frames}
    (job_dir / "job.json").write_text(json.dumps(record), encoding="utf-8")
    return job_dir


@pytest.fixture()
def run_dir(tmp_path):
    """MC-RUN-002 shape: orchid/butterfly/A->B reused, phoenix + B->C fresh."""
    jobs = tmp_path / "runs"
    reused = dict(created=-3600, submitted=-3500)
    dirs = {
        "anchor:orchid": make_job(jobs, "a1a1", kind="anchor_image", method="text_to_image", exec_s=18.7, **reused),
        "anchor:butterfly": make_job(jobs, "b2b2", kind="anchor_image", method="reference_edit", exec_s=51.7, **reused),
        "anchor:phoenix": make_job(jobs, "c3c3", kind="anchor_image", method="reference_edit",
                                   created=10, submitted=12, exec_s=54.1),
        "bridge:orchid->butterfly": make_job(jobs, "d4d4", kind="wan22_flf2v_bridge", exec_s=497.2, **reused),
        "bridge:butterfly->phoenix": make_job(jobs, "e5e5", kind="wan22_flf2v_bridge",
                                              created=70, submitted=72, exec_s=496.8),
    }
    run = jobs / "run-ba2d9dbedb6189be"
    run.mkdir()
    order = list(dirs) + ["final:movie"]
    stages = {k: {"state": "verified", "job_dir": str(v)} for k, v in dirs.items()}
    stages["final:movie"] = {"state": "verified"}
    (run / "manifest.json").write_text(json.dumps({
        "created_at": iso(0), "plan_sha256": "ba2d9dbe" + "0" * 56, "order": order, "stages": stages}),
        encoding="utf-8")
    return run


def test_report_matches_records_and_marks_reuse(run_dir):
    report = build_report(run_dir)
    rows = {r["task"]: r for r in report["stages"]}
    assert rows["anchor:phoenix"]["exec_s"] == 54.1 and rows["anchor:phoenix"]["reused"] is False
    assert rows["anchor:orchid"]["reused"] is True
    assert rows["bridge:butterfly->phoenix"]["wall_s"] == 498.0  # events have 1 s resolution
    assert rows["bridge:butterfly->phoenix"]["overhead_s"] == 1.2
    assert report["totals"] == {"gpu_exec_s": 550.9, "fresh_stages": 2, "reused_stages": 3, "label": "MEASURED"}
    assert rows["final:movie"]["labels"]["time"] == NOT_MEASURED
    assert report["vram"]["status"] == NOT_MEASURED  # not sampled
    assert report["provenance"]["comfyui"] == "0.46.0"
    assert report["provenance"]["models_sha256"]["wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"] == NOT_MEASURED
    assert not any("per-process" in json.dumps(r).lower() and "no per-process" not in json.dumps(r).lower()
                   for r in report["stages"])


def test_report_window_peaks_are_whole_gpu(run_dir):
    samples = [[epoch(t), 35_000] for t in range(0, 12)]                  # before first submission
    samples += [[epoch(t), 47_000] for t in range(12, 67)]                # phoenix window
    samples += [[epoch(t), 36_000] for t in range(67, 72)]
    samples += [[epoch(t), 48_000] for t in range(72, 569)]               # bridge window
    (run_dir / "vram_samples.json").write_text(json.dumps({"interval_s": 1.0, "samples": samples}),
                                               encoding="utf-8")
    report = build_report(run_dir)
    rows = {r["task"]: r for r in report["stages"]}
    assert report["vram"]["external_baseline_mib"] == 35_000
    assert rows["anchor:phoenix"]["vram_window_peak_mib"] == 47_000
    assert rows["anchor:phoenix"]["vram_window_rise_mib"] == 12_000
    assert rows["bridge:butterfly->phoenix"]["vram_window_peak_mib"] == 48_000
    assert rows["anchor:phoenix"]["labels"]["vram"] == WHOLE_GPU
    assert "vram_window_peak_mib" not in rows["anchor:orchid"]  # reused: no window


def test_cli_perf_report(run_dir, capsys):
    assert cli.main(["perf-report", str(run_dir), "--models-cache", str(run_dir / "none.json")]) == 0
    assert json.loads(capsys.readouterr().out)["totals"]["fresh_stages"] == 2


# ------------------------------------------------------------------------ estimates

def test_estimate_sample_storyboard_from_history():
    plan = compile_plan(load_storyboard(REPO / "configs/sequences/organic-machines.yaml"), repo_root=REPO)
    result = estimate(plan, load_history(HISTORY))
    rows = {r["task"]: r for r in result["stages"]}
    assert 18 <= rows["anchor:orchid"]["exec_s"] <= 21
    assert 49 <= rows["anchor:phoenix"]["exec_s"] <= 55
    assert abs(rows["bridge:orchid->butterfly"]["exec_s"] - 496.8) / 496.8 < 0.10
    assert result["label"] == "ESTIMATED" and result["total_gpu_s"] > 1000


def test_unknown_size_is_no_data_unless_extrapolated():
    plan = compile_plan(load_storyboard(REPO / "configs/sequences/organic-machines.yaml"), repo_root=REPO)
    for task in plan["tasks"].values():
        if task["kind"] in ("anchor", "bridge"):
            task.update(width=1280, height=720)
    result = estimate(plan, load_history(HISTORY))
    assert result["total_gpu_s"] is None and {r["label"] for r in result["stages"]} == {"NO DATA"}
    scaled = estimate(plan, load_history(HISTORY), extrapolate=True)
    bridge = next(r for r in scaled["stages"] if r["kind"] == "bridge")
    assert bridge["label"] == "ESTIMATED-EXTRAPOLATED" and "scaled" in bridge["basis"]


def test_cli_estimate(capsys, monkeypatch):
    monkeypatch.chdir(REPO)
    assert cli.main(["estimate", "configs/sequences/organic-machines.yaml"]) == 0
    assert json.loads(capsys.readouterr().out)["label"] == "ESTIMATED"
