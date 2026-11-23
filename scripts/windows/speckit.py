"""Windows-native Spec Kit initializer and repair tool (Python only).

Examples, from MorphCurrent repository root in Windows Command Prompt:
    python scripts/windows/speckit.py --status
    python scripts/windows/speckit.py --init
    python scripts/windows/speckit.py --repair
    python scripts/windows/speckit.py --verify

The official CLI may still unpack a PowerShell fallback even with "--script py".
This helper audits executable Python scripts and generated Claude instructions,
backs up managed files, then moves the unused fallback out of the active tree.

No WSL/PowerShell invocation. No automatic downloads of code/models.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_PYTHON = frozenset({
    "check_prerequisites.py",
    "common.py",
    "create_new_feature.py",
    "setup_plan.py",
    "setup_tasks.py",
})
GENERATED_SCRIPT = re.compile(r"\.specify[/\\]scripts[/\\]python[/\\]([\w-]+\.py)")
POWER_SHELL = re.compile(r"(?:\.ps1\b|\.specify[/\\]scripts[/\\]powershell[/\\]|"
                         r"\b(?:pwsh|powershell)(?:\.exe)?\b)", re.I)
PYTHON3 = re.compile(r"\bpython3(?=\s+\.specify[/\\]scripts[/\\]python[/\\])")


@dataclass(frozen=True)
class Inspection:
    installed: bool
    python_files: tuple[str, ...]
    generated_commands: tuple[str, ...]
    problems: tuple[str, ...]
    fallback_ps1: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return self.installed and not self.problems


def generated_command_paths(root: Path) -> list[Path]:
    """Only Claude Spec Kit generated command/skill markdown, not user files."""
    candidates = [
        *root.glob(".claude/skills/speckit-*/SKILL.md"),
        *root.glob(".claude/commands/speckit*.md"),
    ]
    return sorted({p for p in candidates if p.is_file()})


def inspect(root: Path) -> Inspection:
    specified = root / ".specify"
    directory = specified / "scripts" / "python"
    files = tuple(sorted(p.name for p in directory.glob("*.py"))) if directory.exists() else ()
    commands = generated_command_paths(root)
    errors: list[str] = []
    if not specified.is_dir():
        errors.append(".specify/ does not exist")
    if not directory.is_dir():
        errors.append(".specify/scripts/python/ missing (Python variant not installed)")
    missing = sorted(REQUIRED_PYTHON.difference(files))
    if missing:
        errors.append("Missing official Python core scripts: " + ", ".join(missing))
    if not commands:
        errors.append("No Claude Spec Kit commands/skills were generated")
    for path in commands:
        content = path.read_text(encoding="utf-8")
        relative = path.relative_to(root).as_posix()
        if POWER_SHELL.search(content):
            errors.append(f"{relative}: still invokes PowerShell / .ps1")
        if PYTHON3.search(content):
            errors.append(f"{relative}: invokes 'python3', not the Windows 'python' command")
        for script in GENERATED_SCRIPT.findall(content):
            if script not in files:
                errors.append(f"{relative}: referenced Python script {script} is missing")
    # Official Spec Kit often installs this fallback even with --script py.
    # It is not proof that Python wasn't selected, but strict MorphCurrent mode
    # keeps only the Python variant in the active .specify scripts directory.
    fallback = specified / "scripts" / "powershell"
    ps1 = tuple(sorted(p.relative_to(root).as_posix()
                        for p in fallback.rglob("*.ps1"))) if fallback.exists() else ()
    return Inspection(specified.is_dir(), files,
                      tuple(p.relative_to(root).as_posix() for p in commands),
                      tuple(errors), ps1)


def normalize_generated_python_calls(root: Path) -> list[str]:
    """Replace 'python3 .specify/scripts/python/' only in generated Spec Kit docs."""
    changed = []
    for path in generated_command_paths(root):
        original = path.read_text(encoding="utf-8")
        fixed = PYTHON3.sub("python", original)
        if fixed != original:
            path.write_text(fixed, encoding="utf-8", newline="\n")
            changed.append(str(path.relative_to(root)))
    return changed


def build_specify_command(executable: str = "specify",
                          *, ignore_agent_tools: bool = True) -> list[str]:
    """Explicit noninteractive Python, never Windows' implicit 'ps' default."""
    cmd = [executable, "init", "--here", "--force", "--non-interactive",
           "--integration", "claude", "--script", "py"]
    if ignore_agent_tools:
        cmd.append("--ignore-agent-tools")
    return cmd


def backup_managed_files(root: Path) -> Path:
    """Snapshot original Spec Kit and Claude commands before any modification."""
    backup = (root / ".local" / "spec-kit-backups" /
              (dt.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]))
    backup.mkdir(parents=True, exist_ok=False)
    for relative in [".specify", "CLAUDE.md", "README.md"]:
        source = root / relative
        dest = backup / relative
        if source.is_dir():
            shutil.copytree(source, dest)
        elif source.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
    for path in generated_command_paths(root):
        dest = backup / path.relative_to(root)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    return backup


def move_generated_powershell_fallback(root: Path, backup: Path) -> bool:
    """Move the *known generated* fallback to backup, never delete unknown files."""
    source = root / ".specify" / "scripts" / "powershell"
    if not source.exists():
        return False
    target = backup / "removed-from-active-tree" / "powershell"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(target))
    return True


def verify_report(report: Inspection) -> None:
    print(json.dumps({
        "python_core_files": list(report.python_files),
        "claude_spec_kit_files": list(report.generated_commands),
        "powershell_fallback_files": list(report.fallback_ps1),
        "ready_for_python_spec_kit": report.valid,
        "problems": list(report.problems),
    }, indent=2))


def run_init(root: Path, executable: str, *, force_repair: bool = False) -> int:
    before = inspect(root)
    # An already-working project only needs removal of generated fallback,
    # not a destructive re-init.
    must_reinitialize = force_repair or not before.valid
    backup = backup_managed_files(root)
    print("Backup of existing managed files:", backup, flush=True)
    if must_reinitialize:
        help_result = subprocess.run(
            [executable, "init", "--help"], cwd=root, text=True,
            capture_output=True, errors="replace", timeout=30, check=False,
        )
        help_text = help_result.stdout + help_result.stderr
        required = ("--here", "--force", "--non-interactive",
                    "--integration", "--script")
        if help_result.returncode or any(flag not in help_text for flag in required):
            print("Installed Spec Kit is too old for safe Python/Claude setup. "
                  "Upgrade official specify-cli before retrying.", file=sys.stderr)
            return 2
        command = build_specify_command(
            executable, ignore_agent_tools=("--ignore-agent-tools" in help_text)
        )
        print("Running:", subprocess.list2cmdline(command), flush=True)
        try:
            subprocess.run(command, cwd=root, check=True, shell=False)
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"Spec Kit init failed: {exc}. Original files backed up at {backup}",
                  file=sys.stderr)
            return 2

    changed = normalize_generated_python_calls(root)
    if changed:
        print("Normalized Windows Python command references:", ", ".join(changed))
    state = inspect(root)
    if not state.valid:
        verify_report(state)
        print("Python Spec Kit validation failed; kept original PowerShell fallback. "
              "Upgrade specify-cli and run --repair. Backup: " + str(backup),
              file=sys.stderr)
        return 2
    moved = move_generated_powershell_fallback(root, backup)
    if moved:
        print("Moved generated PowerShell fallback into ignored backup:", backup)
    verified = inspect(root)
    verify_report(verified)
    return 0 if verified.valid and not verified.fallback_ps1 else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Python-only Spec Kit on native Windows")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--status", action="store_true", help="Inspect existing Spec Kit")
    action.add_argument("--verify", action="store_true", help="Fail if Python setup invalid")
    action.add_argument("--init", action="store_true",
                        help="Initialize or safely repair an existing Python setup")
    action.add_argument("--repair", action="store_true",
                        help="Force regeneration, with a backup, using Python scripts")
    args = parser.parse_args(argv)
    if sys.platform != "win32":
        parser.error("Native Windows Python required; do not use WSL/Linux.")
    report = inspect(ROOT)
    executable = shutil.which("specify")
    print("Spec Kit executable:", executable or "NOT FOUND")
    if args.status or args.verify:
        verify_report(report)
        if report.fallback_ps1:
            print("PowerShell fallback exists (official CLI installs it on Windows "
                  "even for --script py). Use --init to move it to backup.")
        return 0 if args.status or (report.valid and not report.fallback_ps1) else 2
    if not executable:
        print("Install or upgrade official specify-cli and ensure specify.exe is on PATH. "
              "See docs/WINDOWS_DEVELOPMENT.md.", file=sys.stderr)
        return 2
    try:
        return run_init(ROOT, executable, force_repair=args.repair)
    except (OSError, subprocess.TimeoutExpired, UnicodeError, ValueError) as exc:
        print(f"Spec Kit setup error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
