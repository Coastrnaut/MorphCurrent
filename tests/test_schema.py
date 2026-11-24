from pathlib import Path

import pytest
from pydantic import ValidationError

from morph_studio.schema import Storyboard, load_storyboard


def test_sample_loads_and_references_are_valid():
    seq = load_storyboard("configs/sequences/organic-machines.yaml")
    assert len(seq.anchors) == 3
    assert seq.anchors[1].reference == "orchid"


def test_duplicate_anchors_rejected():
    model = load_storyboard("configs/sequences/organic-machines.yaml").model_dump(by_alias=True)
    model["anchors"][1]["id"] = "orchid"
    with pytest.raises(ValidationError):
        Storyboard.model_validate(model)


def test_dangling_reference_rejected():
    model = load_storyboard("configs/sequences/organic-machines.yaml").model_dump(by_alias=True)
    model["anchors"][1]["reference"] = "missing"
    with pytest.raises(ValidationError):
        Storyboard.model_validate(model)


def test_transition_chain_must_be_linear_v1():
    model = load_storyboard("configs/sequences/organic-machines.yaml").model_dump(by_alias=True)
    model["transitions"][0]["to"] = "phoenix"
    with pytest.raises(ValidationError):
        Storyboard.model_validate(model)


def test_extra_fields_rejected():
    model = load_storyboard("configs/sequences/organic-machines.yaml").model_dump(by_alias=True)
    model["unexpected"] = "not allowed"
    with pytest.raises(ValidationError):
        Storyboard.model_validate(model)


def test_non_mapping_yaml_rejected(tmp_path: Path):
    filename = tmp_path / "sequence.yaml"
    filename.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_storyboard(filename)


def test_independent_t2i_is_explicit_and_reference_optional():
    model = load_storyboard("configs/sequences/organic-machines.yaml").model_dump(by_alias=True)
    model["anchors"][2]["generation"] = "independent_t2i"
    assert Storyboard.model_validate(model).anchors[2].reference == "butterfly"
    model["anchors"][2]["reference"] = None
    assert Storyboard.model_validate(model).anchors[2].generation == "independent_t2i"
    model["anchors"][2]["reference"] = "phoenix"  # self/forward reference
    with pytest.raises(ValidationError):
        Storyboard.model_validate(model)


def test_negative_prompt_per_anchor():
    model = load_storyboard("configs/sequences/organic-machines.yaml").model_dump(by_alias=True)
    model["anchors"][0]["negative_prompt"] = "text, watermark"
    assert Storyboard.model_validate(model).anchors[0].negative_prompt == "text, watermark"
