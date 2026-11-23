"""Windows Python helpers can be tested offline on CI (no GPU or Spec Kit CLI)."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.windows.launch_comfyui import build_launch_command
from scripts.windows.speckit import (
    REQUIRED_PYTHON,
    backup_managed_files,
    build_specify_command,
    generated_command_paths,
    inspect,
    move_generated_powershell_fallback,
    normalize_generated_python_calls,
    run_init,
)


def test_portable_comfyui_command_uses_embedded_python(tmp_path: Path):
    main = tmp_path / "ComfyUI" / "main.py"
    python_exe = tmp_path / "python_embeded" / "python.exe"
    main.parent.mkdir()
    python_exe.parent.mkdir()
    main.write_text("pass", encoding="utf-8")
    python_exe.write_bytes(b"placeholder")
    cmd, cwd = build_launch_command(tmp_path)
    assert cmd[0] == str(python_exe)
    assert cmd[1:3] == ["-s", str(main)]
    assert "--windows-standalone-build" in cmd
    assert cmd[-4:] == ["--listen", "127.0.0.1", "--port", "8188"]
    assert cwd == main.parent


def test_manual_install_and_opt_in_highvram(tmp_path: Path):
    main = tmp_path / "main.py"
    python_exe = tmp_path / ".venv" / "Scripts" / "python.exe"
    main.write_text("pass", encoding="utf-8")
    python_exe.parent.mkdir(parents=True)
    python_exe.write_bytes(b"placeholder")
    cmd, _ = build_launch_command(tmp_path, distribution="manual", memory_mode="highvram")
    assert cmd[0] == str(python_exe)
    assert "--highvram" in cmd


def test_bundled_python_cannot_be_overridden(tmp_path: Path):
    main = tmp_path / "ComfyUI" / "main.py"
    python_exe = tmp_path / "python_embeded" / "python.exe"
    main.parent.mkdir()
    python_exe.parent.mkdir()
    main.touch()
    python_exe.touch()
    with pytest.raises(ValueError):
        build_launch_command(tmp_path, distribution="portable",
                             python_executable=tmp_path / "wrong.exe")


def test_specify_command_forces_noninteractive_python():
    cmd = build_specify_command("specify.exe")
    assert cmd == ["specify.exe", "init", "--here", "--force", "--non-interactive",
                   "--integration", "claude", "--script", "py", "--ignore-agent-tools"]
    assert "ps" not in cmd and "sh" not in cmd


def create_python_fixture(root: Path, *, reference: str | None = None):
    directory = root / ".specify" / "scripts" / "python"
    directory.mkdir(parents=True)
    for name in REQUIRED_PYTHON:
        (directory / name).write_text("# official Python core test stub\n", encoding="utf-8")
    skill = root / ".claude" / "skills" / "speckit-plan" / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text(reference or "Run python .specify/scripts/python/setup_plan.py\n",
                     encoding="utf-8")
    return skill


def test_python_spec_kit_verification_checks_core_files_and_generated_skills(tmp_path: Path):
    skill = create_python_fixture(tmp_path)
    result = inspect(tmp_path)
    assert result.valid
    assert len(result.python_files) == len(REQUIRED_PYTHON)
    assert result.generated_commands == (".claude/skills/speckit-plan/SKILL.md",)
    assert generated_command_paths(tmp_path) == [skill]


def test_reject_powershell_command_reference_even_if_python_files_exist(tmp_path: Path):
    create_python_fixture(tmp_path, reference=(
        "Run powershell -File .specify/scripts/powershell/setup-plan.ps1\n"
    ))
    result = inspect(tmp_path)
    assert not result.valid
    assert any("PowerShell" in x for x in result.problems)


def test_missing_python_script_detected_even_when_generated_skills_reference_it(tmp_path: Path):
    create_python_fixture(tmp_path)
    (tmp_path / ".specify" / "scripts" / "python" / "setup_plan.py").unlink()
    result = inspect(tmp_path)
    assert not result.valid
    assert any("setup_plan.py" in x for x in result.problems)


def test_normalize_python3_only_in_generated_skill(tmp_path: Path):
    skill = create_python_fixture(tmp_path, reference=(
        "Run python3 .specify/scripts/python/setup_plan.py\n"
    ))
    assert not inspect(tmp_path).valid
    changed = normalize_generated_python_calls(tmp_path)
    assert changed == [".claude/skills/speckit-plan/SKILL.md"]
    assert "python3" not in skill.read_text(encoding="utf-8")
    assert inspect(tmp_path).valid


def test_backup_then_move_vendor_powershell_fallback(tmp_path: Path):
    create_python_fixture(tmp_path)
    ps = tmp_path / ".specify" / "scripts" / "powershell" / "setup-plan.ps1"
    ps.parent.mkdir()
    ps.write_text("Write-Host 'original'\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("user rules", encoding="utf-8")
    backup = backup_managed_files(tmp_path)
    assert (backup / ".specify" / "scripts" / "powershell" / "setup-plan.ps1").exists()
    assert (backup / "CLAUDE.md").read_text(encoding="utf-8") == "user rules"
    assert move_generated_powershell_fallback(tmp_path, backup)
    assert not ps.parent.exists()
    assert (backup / "removed-from-active-tree" / "powershell" / "setup-plan.ps1").exists()
    assert inspect(tmp_path).valid
    assert not inspect(tmp_path).fallback_ps1


def test_valid_existing_setup_does_not_force_reinitialize(tmp_path: Path):
    create_python_fixture(tmp_path)
    ps = tmp_path / ".specify" / "scripts" / "powershell" / "setup-plan.ps1"
    ps.parent.mkdir()
    ps.write_text("Write-Host 'fallback'\n", encoding="utf-8")
    with patch("scripts.windows.speckit.subprocess.run", side_effect=AssertionError(
        "Must not run specify init for a healthy Python installation"
    )):
        assert run_init(tmp_path, "specify.exe") == 0
    assert not ps.exists()
    assert inspect(tmp_path).valid


def test_existing_powershell_setup_is_repaired_and_backed_up(tmp_path: Path):
    shell_script = tmp_path / ".specify" / "scripts" / "powershell" / "setup-plan.ps1"
    shell_script.parent.mkdir(parents=True)
    shell_script.write_text("# old fallback", encoding="utf-8")
    skill = tmp_path / ".claude" / "skills" / "speckit-plan" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("powershell .specify/scripts/powershell/setup-plan.ps1", encoding="utf-8")

    def fake_specify(argv, **kwargs):
        if argv[-2:] == ["init", "--help"]:
            return subprocess.CompletedProcess(argv, 0, stdout=(
                "--here --force --non-interactive --integration --script --ignore-agent-tools"
            ), stderr="")
        assert "--script" in argv
        assert argv[argv.index("--script") + 1] == "py"
        assert "--non-interactive" in argv
        create_python_fixture(tmp_path, reference=(
            "Run python3 .specify/scripts/python/setup_plan.py\n"
        ))
        return subprocess.CompletedProcess(argv, 0)

    with patch("scripts.windows.speckit.subprocess.run", side_effect=fake_specify):
        assert run_init(tmp_path, "specify.exe") == 0
    assert not shell_script.exists()
    assert inspect(tmp_path).valid
    backups = list((tmp_path / ".local" / "spec-kit-backups").iterdir())
    assert len(backups) == 1
    assert (backups[0] / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()
    assert (backups[0] / "removed-from-active-tree" / "powershell" / "setup-plan.ps1").exists()


def test_failed_python_regeneration_preserves_existing_fallback(tmp_path: Path):
    shell_script = tmp_path / ".specify" / "scripts" / "powershell" / "setup-plan.ps1"
    shell_script.parent.mkdir(parents=True)
    shell_script.write_text("# existing", encoding="utf-8")
    skill = tmp_path / ".claude" / "skills" / "speckit-plan" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("powershell .specify/scripts/powershell/setup-plan.ps1", encoding="utf-8")

    def fake_specify(argv, **kwargs):
        if argv[-2:] == ["init", "--help"]:
            return subprocess.CompletedProcess(argv, 0, stdout=(
                "--here --force --non-interactive --integration --script"
            ), stderr="")
        return subprocess.CompletedProcess(argv, 0)

    with patch("scripts.windows.speckit.subprocess.run", side_effect=fake_specify):
        assert run_init(tmp_path, "specify.exe") == 2
    assert shell_script.exists()
