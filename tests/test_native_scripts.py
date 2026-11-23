"""Native Windows helper behavior can be tested on CI without ComfyUI."""
from pathlib import Path

import pytest

from scripts.windows.launch_comfyui import build_launch_command
from scripts.windows.speckit import build_specify_command


def test_portable_comfyui_command_uses_embedded_python(tmp_path: Path):
    main = tmp_path / "ComfyUI" / "main.py"
    python = tmp_path / "python_embeded" / "python.exe"
    main.parent.mkdir()
    python.parent.mkdir()
    main.write_text("pass", encoding="utf-8")
    python.write_bytes(b"placeholder")
    cmd, cwd = build_launch_command(tmp_path)
    assert cmd[0] == str(python)
    assert cmd[1:3] == ["-s", str(main)]
    assert "--windows-standalone-build" in cmd
    assert cmd[-4:] == ["--listen", "127.0.0.1", "--port", "8188"]
    assert cwd == main.parent


def test_manual_install_and_opt_in_highvram(tmp_path: Path):
    main = tmp_path / "main.py"
    python = tmp_path / ".venv" / "Scripts" / "python.exe"
    main.write_text("pass", encoding="utf-8")
    python.parent.mkdir(parents=True)
    python.write_bytes(b"placeholder")
    cmd, _ = build_launch_command(tmp_path, distribution="manual", memory_mode="highvram")
    assert cmd[0] == str(python)
    assert "--highvram" in cmd


def test_bundled_python_cannot_be_overridden(tmp_path: Path):
    main = tmp_path / "ComfyUI" / "main.py"
    py = tmp_path / "python_embeded" / "python.exe"
    main.parent.mkdir()
    py.parent.mkdir()
    main.touch()
    py.touch()
    with pytest.raises(ValueError):
        build_launch_command(tmp_path, distribution="portable",
                             python_executable=tmp_path / "wrong.exe")


def test_specify_command_selects_python_scripts():
    assert build_specify_command() == [
        "specify", "init", "--here", "--integration", "claude", "--script", "py"
    ]
