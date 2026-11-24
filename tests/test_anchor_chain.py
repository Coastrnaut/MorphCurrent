"""F04 A→B→C reference-edit chain, explicit fallback, contact sheet (offline)."""
from __future__ import annotations

import shutil

import pytest

from fake_comfy import FakeComfy, make_png
from morph_studio.anchors import AnchorSpec, anchor_image_path, run_anchor_chain
from morph_studio.bridge import BridgeError
from morph_studio.cache import sha256_file
from morph_studio.media import contact_sheet, inspect_image

T2I = "configs/profiles/test_t2i.binding.json"
EDIT = "configs/profiles/test_edit.binding.json"
SPECS = [AnchorSpec("orchid", "text_to_image", "glass orchid", 101),
         AnchorSpec("butterfly", "reference_edit", "metallic butterfly", 102, reference="orchid"),
         AnchorSpec("phoenix", "reference_edit", "mechanical phoenix", 103, reference="butterfly")]


def chain(repo, fake, specs=SPECS, edit=EDIT, **kw):
    return run_anchor_chain(specs, client=fake.client(), runs_root=repo / "outputs/runs",
                            t2i_profile=T2I, edit_profile=edit, width=832, height=480,
                            repo_root=repo, poll_seconds=0, **kw)


def test_chain_binds_each_child_to_parent_bytes(image_repo):
    fake = FakeComfy()
    result = chain(image_repo, fake, submit=True)
    assert result.complete, (result.blocked, {k: j.record.get("error") for k, j in result.jobs.items()})
    a, b, c = (result.jobs[k] for k in ("orchid", "butterfly", "phoenix"))
    assert b.record["parent"]["sha256"] == a.record["image"]["sha256"]
    assert c.record["parent"]["sha256"] == b.record["image"]["sha256"]
    assert b.record["method"] == "reference_edit" and b.record["continuity"]["conditioned_on_parent"]
    # the bytes uploaded as B's reference are exactly A's verified file
    assert sha256_file(anchor_image_path(a)) == b.record["inputs"]["reference_image"]["sha256"]
    assert {(j.record["image"]["width"], j.record["image"]["height"]) for j in (a, b, c)} == {(832, 480)}
    assert fake.prompt_posts == 3


def test_rerun_reuses_all_anchors(image_repo):
    fake = FakeComfy()
    chain(image_repo, fake, submit=True)
    result = chain(image_repo, fake, submit=True)
    assert result.complete and fake.prompt_posts == 3


def test_without_consent_children_wait_for_parent(image_repo):
    fake = FakeComfy()
    result = chain(image_repo, fake)
    assert result.jobs["orchid"].state == "validated"
    assert "not a verified anchor" in result.blocked["butterfly"] and fake.prompt_posts == 0


def test_missing_edit_profile_blocks_without_fallback(image_repo):
    fake = FakeComfy()
    result = chain(image_repo, fake, edit=None, submit=True)
    assert result.jobs["orchid"].state == "verified"
    assert set(result.blocked) == {"butterfly", "phoenix"}
    assert "independent_t2i" in result.blocked["butterfly"] and fake.prompt_posts == 1


def test_independent_t2i_is_labelled_and_needs_review(image_repo):
    fake = FakeComfy()
    specs = [SPECS[0], AnchorSpec("butterfly", "independent_t2i", "metallic butterfly", 102,
                                  reference="orchid")]
    result = chain(image_repo, fake, specs=specs, edit=None, submit=True)
    b = result.jobs["butterfly"]
    assert result.complete and b.record["method"] == "independent_t2i" and b.record["parent"] is None
    cont = b.record["continuity"]
    assert {k: cont[k] for k in ("parent", "parent_sha256", "conditioned_on_parent", "review")} == {
        "parent": "orchid", "parent_sha256": result.jobs["orchid"].record["image"]["sha256"],
        "conditioned_on_parent": False, "review": "required"}
    assert "geometry" in cont  # F12 heuristic comparison recorded (or marked unavailable)


def test_child_dimension_mismatch_fails(image_repo, monkeypatch):
    fake = FakeComfy()
    result = chain(image_repo, fake, specs=SPECS[:1], submit=True)
    assert result.complete
    fake.image_override = make_png(832, 480)
    # edit graph has no width/height binding -> size not checked per image; continuity must catch it
    fake.image_override = make_png(640, 368)
    with pytest.raises(BridgeError, match="both endpoints of a bridge must match"):
        run_anchor_chain(SPECS[:2], client=fake.client(), runs_root=image_repo / "outputs/runs",
                         t2i_profile=T2I, edit_profile=EDIT, width=None, height=None,
                         repo_root=image_repo, poll_seconds=0, submit=True)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_contact_sheet(tmp_path):
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    a.write_bytes(make_png(64, 32, (255, 0, 0)))
    b.write_bytes(make_png(64, 32, (0, 0, 255)))
    out = contact_sheet([a, b], tmp_path / "sheet.png", height=32)
    assert inspect_image(out) == {"format": "png", "width": 128, "height": 32}
    with pytest.raises(FileExistsError):
        contact_sheet([a, b], out)
