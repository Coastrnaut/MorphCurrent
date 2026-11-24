"""Shared offline fixtures: a temporary repo root holding synthetic image profiles."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from image_graphs import edit_graph, edit_profile_dict, t2i_graph, t2i_profile_dict
from morph_studio.workflow_adapter import graph_sha256

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture()
def image_repo(tmp_path) -> Path:
    """tmp repo with workflows/test_{t2i,edit}.json + configs/profiles/test_{t2i,edit}.binding.json,
    plus the real Wan workflow/profile copied verbatim."""
    (tmp_path / "workflows").mkdir()
    (tmp_path / "configs" / "profiles").mkdir(parents=True)
    for name, graph, make in (("t2i", t2i_graph(), t2i_profile_dict), ("edit", edit_graph(), edit_profile_dict)):
        (tmp_path / "workflows" / f"test_{name}.json").write_text(json.dumps(graph), encoding="utf-8")
        (tmp_path / "configs" / "profiles" / f"test_{name}.binding.json").write_text(
            json.dumps(make(graph_sha256(graph))), encoding="utf-8")
    for rel in ("workflows/03_wan22_flf2v.json", "configs/profiles/wan22_flf2v.binding.json"):
        (tmp_path / rel).write_bytes((REPO / rel).read_bytes())
    return tmp_path
