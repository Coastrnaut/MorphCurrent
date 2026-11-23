from morph_studio.cli import main


def test_validate_and_plan(capsys):
    path = "configs/sequences/organic-machines.yaml"
    assert main(["validate", path]) == 0
    assert "VALID:" in capsys.readouterr().out
    assert main(["plan", path]) == 0
    assert '"frame_total_if_matching_endpoints": 129' in capsys.readouterr().out
