"""Guard the ten-feature spec ledger, constitution and model/workflow docs."""
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


def test_constitution_is_not_unfilled_template_and_image_workflows_not_faked():
    constitution = (ROOT / ".specify" / "memory" / "constitution.md").read_text(encoding="utf-8")
    models = (ROOT / "docs" / "MODELS.md").read_text(encoding="utf-8")
    architecture = (ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "[PRINCIPLE_1_NAME]" not in constitution
    assert "model" in constitution.lower() and "ComfyUI" in constitution
    assert "NOT MEASURED" in models
    assert "01_anchor_t2i.json" in models and "02_anchor_edit.json" in models
    assert "byte" in architecture.lower() and "129" in architecture


def test_runtime_exports_and_existing_bridge_remain_untouched():
    """Docs-driven changes must never delete the working Wan API binding."""
    assert (ROOT / "workflows" / "03_wan22_flf2v.json").is_file()
    assert (ROOT / "configs" / "profiles" / "wan22_flf2v.binding.json").is_file()
    assert (ROOT / "src" / "morph_studio" / "bridge.py").is_file()
