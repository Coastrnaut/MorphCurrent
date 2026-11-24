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


def test_wan_21_vae_setup_path_and_node_documented():
    """The user-installed Wan VAE belongs under ComfyUI Portable models/vae."""
    vae_path = r"C:\AI\ComfyUI_windows_portable\ComfyUI\models\vae\wan_2.1_vae.safetensors"
    for document in (
        "docs/COMFYUI_PORTABLE_WINDOWS.md",
        "docs/SETUP_WINDOWS.md",
        "docs/WINDOWS_DEVELOPMENT.md",
    ):
        content = (ROOT / document).read_text(encoding="utf-8")
        assert vae_path in content
        assert "Load VAE" in content


def test_wan22_i2v_fp8_checkpoints_and_encoder_documented():
    """Both I2V experts and the matching text encoder must have Windows paths."""
    common = r"C:\AI\ComfyUI_windows_portable\ComfyUI\models"
    expected = (
        common + r"\diffusion_models\wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
        common + r"\diffusion_models\wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors",
        common + r"\text_encoders\umt5_xxl_fp8_e4m3fn_scaled.safetensors",
        common + r"\vae\wan_2.1_vae.safetensors",
    )
    for document in (
        "docs/COMFYUI_PORTABLE_WINDOWS.md",
        "docs/SETUP_WINDOWS.md",
        "docs/WINDOWS_DEVELOPMENT.md",
    ):
        contents = (ROOT / document).read_text(encoding="utf-8")
        for model in expected:
            assert model in contents, (document, model)
    guide = (ROOT / "docs/COMFYUI_PORTABLE_WINDOWS.md").read_text(encoding="utf-8")
    assert "Load CLIP" in guide and "Load Diffusion Model" in guide
    assert "not independently verified" not in guide or "Installation evidence" in guide


def test_first_real_video_baseline_and_refinement_documented():
    """Protect baseline evidence and avoid silently losing the revised prompt."""
    baseline = (ROOT / "docs" / "RENDER_BASELINE_001.md").read_text(encoding="utf-8")
    progress = (ROOT / "PROGRESS.md").read_text(encoding="utf-8")
    experiments = (ROOT / "docs" / "EXPERIMENTS.md").read_text(encoding="utf-8")
    assert "MC-FLF2V-001" in baseline and "MC-FLF2V-002" in baseline
    assert "640 × 368" in baseline and "65" in baseline
    assert "Every crystal petal gradually bends, folds, and reshapes" in baseline
    assert "a638f6e1d58d876670ddc72c0bb773f9f6c83d93076ac3a9403c41618823120c" in baseline
    assert "NOT MEASURED" in baseline or "not retrieved" in baseline
    assert "RENDER_BASELINE_001.md" in progress and "RENDER_BASELINE_001.md" in experiments
    assert "not yet rendered" in progress
