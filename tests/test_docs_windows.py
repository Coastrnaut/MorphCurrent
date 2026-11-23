"""Keep documented Windows Portable onboarding aligned with official release URL."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = (
    "https://github.com/Comfy-Org/ComfyUI/releases/latest/download/"
    "ComfyUI_windows_portable_nvidia.7z"
)


def test_official_portable_url_and_windows_root_documented():
    setup = (ROOT / "docs" / "COMFYUI_PORTABLE_WINDOWS.md").read_text(encoding="utf-8")
    assert OFFICIAL in setup
    assert r"C:\AI\ComfyUI_windows_portable" in setup
    assert "python scripts\\windows\\launch_comfyui.py" in setup
    assert "--dry-run" in setup
    assert "python_embeded" in setup
    assert not any("\\`" in line for line in setup.splitlines())


def test_readme_references_portable_guide_and_official_url():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert OFFICIAL in readme
    assert "docs/COMFYUI_PORTABLE_WINDOWS.md" in readme
