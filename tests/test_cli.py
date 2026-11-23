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
