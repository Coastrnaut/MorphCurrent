"""Keep setup docs aligned with the official ComfyUI release and the recorded baseline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = (
    "https://github.com/Comfy-Org/ComfyUI/releases/latest/download/"
    "ComfyUI_windows_portable_nvidia.7z"
)
MODELS = r"C:\AI\ComfyUI_windows_portable\ComfyUI\models"


def test_official_portable_url_and_windows_root_documented():
    setup = (ROOT / "docs" / "COMFYUI_SETUP.md").read_text(encoding="utf-8")
    assert OFFICIAL in setup
    assert r"C:\AI\ComfyUI_windows_portable" in setup
    assert "python scripts\\windows\\launch_comfyui.py" in setup
    assert "--dry-run" in setup and "python_embeded" in setup
    assert not any("\\`" in line for line in setup.splitlines())


def test_readme_links_setup_and_docs():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for doc in ("docs/COMFYUI_SETUP.md", "docs/MODELS.md", "docs/ARCHITECTURE.md", "docs/DEVELOPMENT.md"):
        assert doc in readme
        assert (ROOT / doc).is_file()


def test_wan22_model_paths_documented():
    guide = (ROOT / "docs/COMFYUI_SETUP.md").read_text(encoding="utf-8")
    for model in (r"\diffusion_models\wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
                  r"\diffusion_models\wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors",
                  r"\text_encoders\umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                  r"\vae\wan_2.1_vae.safetensors"):
        assert MODELS + model in guide, model
    assert "Load CLIP" in guide and "Load Diffusion Model" in guide and "Load VAE" in guide


def test_video_baseline_evidence_preserved():
    experiments = (ROOT / "docs" / "EXPERIMENTS.md").read_text(encoding="utf-8")
    progress = (ROOT / "docs" / "PROGRESS.md").read_text(encoding="utf-8")
    for run in ("MC-FLF2V-001", "MC-FLF2V-002", "MC-FLF2V-003"):
        assert run in experiments and run in progress
    assert "640 × 368" in experiments
    assert "Every crystal petal gradually bends, folds, and reshapes" in experiments
    assert "a638f6e1d58d876670ddc72c0bb773f9f6c83d93076ac3a9403c41618823120c" in experiments
    assert "NOT MEASURED" in experiments


def test_docs_are_consolidated_under_docs():
    stray = [p.name for p in ROOT.glob("*.md") if p.name not in {"README.md", "CLAUDE.md"}]
    assert stray == []
