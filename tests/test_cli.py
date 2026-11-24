from morph_studio.cli import main


def test_validate_and_plan(capsys):
    path = "configs/sequences/organic-machines.yaml"
    assert main(["validate", path]) == 0
    assert "VALID:" in capsys.readouterr().out
    assert main(["plan", path]) == 0
    assert '"frame_total_if_matching_endpoints": 129' in capsys.readouterr().out

def test_doctor_strict_can_report_missing_gpu(monkeypatch, capsys):
    import morph_studio.cli as cli
    monkeypatch.setattr(cli, "windows_diagnostics", lambda *args, **kwargs: {
        "ready_for_offline_development": True,
        "ready_for_local_gpu_workflows": False,
    })
    assert main(["doctor", "--skip-comfy", "--strict"]) == 0
    assert main(["doctor", "--strict"]) == 3
    assert '"ready_for_local_gpu_workflows": false' in capsys.readouterr().out


def test_workflow_check_and_patch_offline(tmp_path, capsys):
    import json
    fixture = "tests/fixtures/object_info_wan22_flf2v.json"
    assert main(["workflow-check", "--object-info", fixture]) == 0
    assert '"ok": true' in capsys.readouterr().out
    out = tmp_path / "patched.json"
    assert main(["workflow-patch", "--object-info", fixture, "--set", "seed=7",
                 "--set", "length=81", "--set", "fps=24", "--out", str(out)]) == 0
    patched = json.loads(out.read_text(encoding="utf-8"))
    assert patched["84"]["inputs"]["noise_seed"] == 7
    assert patched["81"]["inputs"]["length"] == 81
    assert patched["86"]["inputs"]["fps"] == 24.0
    # refuses to overwrite, and rejects values outside the schema
    assert main(["workflow-patch", "--object-info", fixture, "--out", str(out)]) == 2
    assert main(["workflow-patch", "--object-info", fixture, "--set", "length=64"]) == 2
