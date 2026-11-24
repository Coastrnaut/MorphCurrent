"""Guard the ten-feature spec ledger, direct-paste one-shot, and honest onboarding."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_ten_features_have_unique_ordered_ids_and_explicit_model_gates():
    ledger = (ROOT / "docs" / "SPECKIT_FEATURE_LEDGER.md").read_text(encoding="utf-8")
    feature_ids = re.findall(r"^### (F\d{2}) — ", ledger, re.MULTILINE)
    assert feature_ids == [f"F{i:02d}" for i in range(1, 11)]
    assert "01_anchor_t2i.json" in ledger
    assert "02_anchor_edit.json" in ledger
    assert "03_wan22_flf2v.json" in ledger
    assert "GPU-VERIFIED" in ledger and "BLOCKED" in ledger


def test_claude_one_shot_is_directly_pasteable_and_preserves_current_work():
    one_shot = (ROOT / "docs" / "CLAUDE_DESKTOP_ONESHOT.md").read_text(encoding="utf-8")
    assert one_shot.startswith("You are the autonomous")
    assert one_shot.rstrip().endswith("Do not pretend to have worked after the current session ends.")
    assert not one_shot.lstrip().startswith("#")
    assert "ONE-SHOT PROMPT (copy from here)" not in one_shot
    assert "## END ONE-SHOT PROMPT" not in one_shot
    assert "MC-FLF2V-003" in one_shot
    assert "no new GPU" in one_shot.lower() or "do not" in one_shot.lower()
    for i in range(1, 11):
        assert f"F{i:02d}" in one_shot


def test_constitution_is_not_unfilled_template_and_image_workflows_not_faked():
    constitution = (ROOT / ".specify" / "memory" / "constitution.md").read_text(encoding="utf-8")
    onboarding = (ROOT / "docs" / "ANCHOR_MODEL_ONBOARDING.md").read_text(encoding="utf-8")
    full_design = (ROOT / "docs" / "FULL_PIPELINE_DESIGN.md").read_text(encoding="utf-8")
    assert "[PRINCIPLE_1_NAME]" not in constitution
    assert "model" in constitution.lower() and "ComfyUI" in constitution
    assert "NOT" in onboarding or "not" in onboarding
    assert "01_anchor_t2i.json" in onboarding and "02_anchor_edit.json" in onboarding
    assert "byte" in full_design.lower() and "129" in full_design


def test_runtime_exports_and_existing_bridge_remain_untouched():
    """Docs-driven changes must never delete the working Wan API binding."""
    assert (ROOT / "workflows" / "03_wan22_flf2v.json").is_file()
    assert (ROOT / "configs" / "profiles" / "wan22_flf2v.binding.json").is_file()
    assert (ROOT / "src" / "morph_studio" / "bridge.py").is_file()
