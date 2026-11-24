"""Guard the 30-feature Spec Kit program, workflow contracts and paste-only Claude prompt."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_thirty_features_have_unique_ordered_ids_and_explicit_model_gates():
    ledger = (ROOT / "docs" / "SPECKIT_FEATURE_LEDGER.md").read_text(encoding="utf-8")
    feature_ids = re.findall(r"^### (F\d{2}) — ", ledger, re.MULTILINE)
    assert feature_ids == [f"F{i:02d}" for i in range(1, 31)]
    assert "01_anchor_t2i.json" in ledger
    assert "02_anchor_edit.json" in ledger
    assert "03_wan22_flf2v.json" in ledger
    assert "GPU-VERIFIED" in ledger and "BLOCKED" in ledger
    assert "MC-RUN-001" in ledger and "MC-RUN-002" in ledger
    assert "F11–F30" in ledger


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


def test_claude_handoff_is_paste_ready_and_references_existing_runtime():
    prompt = (ROOT / "docs" / "CLAUDE_DESKTOP_ONESHOT.md").read_text(encoding="utf-8")
    assert prompt.startswith("You are Claude Desktop Code")
    assert "## ONE-SHOT PROMPT" not in prompt
    assert "copy from here" not in prompt.lower()
    assert "F11" in prompt and "F20" in prompt and "F30" in prompt
    assert "MC-RUN-001" in prompt and "MC-RUN-002" in prompt
    assert "--confirm-gpu" in prompt and "python scripts\\windows\\speckit.py --status" in prompt
    assert "Co-Authored-By" in prompt and "no" in prompt.lower()
    assert "specs/001" in prompt and "specs/010" in prompt

def test_thirty_feature_scope_is_synced_across_supporting_docs():
    assert "F01–F30" in (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "F11–F30" in (ROOT / ".specify" / "memory" / "constitution.md").read_text(encoding="utf-8")
    assert "F11–F30" in (ROOT / "docs" / "DEVELOPMENT.md").read_text(encoding="utf-8")
    assert "F11–F30" in (ROOT / "README.md").read_text(encoding="utf-8")
    assert "F30" in (ROOT / "docs" / "PROGRESS.md").read_text(encoding="utf-8")
    assert (ROOT / "workflows" / "01_anchor_t2i.json").is_file()
    assert (ROOT / "workflows" / "02_anchor_edit.json").is_file()


def test_latest_reproduction_and_twenty_new_feature_roadmap_are_grounded():
    ledger = (ROOT / "docs" / "SPECKIT_FEATURE_LEDGER.md").read_text(encoding="utf-8")
    progress = (ROOT / "docs" / "PROGRESS.md").read_text(encoding="utf-8")
    experiments = (ROOT / "docs" / "EXPERIMENTS.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "MC-RUN-003" in ledger and "MC-RUN-003" in progress
    assert "MC-RUN-003" in experiments and "MC-RUN-003" in readme
    assert "byte-identical" in ledger and "byte-identical" in progress
    assert len(re.findall(r"^### F(?:1[1-9]|2[0-9]|30) — ", ledger, re.MULTILINE)) == 20
    for n in range(11, 31):
        assert f"| F{n:02d} | PLANNED |" in progress
