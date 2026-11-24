"""F12 anchor composition geometry and parent/child continuity heuristics."""
from __future__ import annotations

import json
import shutil

import pytest

from morph_studio import cli
from morph_studio.geometry import H, W, anchor_geometry, compare_geometry, compare_images

BG = (8, 8, 12)
FG = (120, 160, 230)


def canvas(boxes, bg=BG, fg=FG):
    """Pixels list W x H with filled rectangles (x0, y0, x1, y1) in fractions."""
    px = [bg] * (W * H)
    for x0, y0, x1, y1 in boxes:
        for y in range(int(y0 * H), int(y1 * H)):
            for x in range(int(x0 * W), int(x1 * W)):
                px[y * W + x] = fg
    return px


CENTRED = [(0.35, 0.25, 0.65, 0.75)]


def geo(boxes, **kw):
    return anchor_geometry(canvas(boxes, **kw))


def test_centred_symmetric_subject():
    g = geo(CENTRED)
    assert abs(g["centroid"][0] - 0.5) < 0.02 and abs(g["centroid"][1] - 0.5) < 0.02
    assert g["symmetry"] > 0.95 and abs(g["extent"][0] - 0.30) < 0.03


def test_identical_pair_is_clean():
    g = geo(CENTRED)
    assert compare_geometry(g, g)["flags"] == []


def test_shifted_subject_flags_centroid():
    moved = geo([(0.55, 0.25, 0.85, 0.75)])
    assert "centroid_shift" in compare_geometry(geo(CENTRED), moved)["flags"]


def test_enlarged_subject_flags_scale():
    big = geo([(0.15, 0.10, 0.85, 0.90)])
    result = compare_geometry(geo(CENTRED), big)
    assert "scale_change" in result["flags"] and result["review"] == "required"


def test_lopsided_profile_flags_symmetry_drop():
    # body plus one wing to the right only (side view proxy)
    lopsided = geo([(0.40, 0.30, 0.50, 0.80), (0.50, 0.20, 0.75, 0.45)])
    result = compare_geometry(geo([(0.35, 0.25, 0.65, 0.75)]), lopsided)
    assert "symmetry_drop" in result["flags"]


def test_palette_shift_flag():
    other = geo(CENTRED, fg=(230, 120, 40))
    assert "palette_shift" in compare_geometry(geo(CENTRED), other)["flags"]


def test_bright_background_and_tiny_subject():
    assert geo(CENTRED, bg=(200, 200, 200), fg=(220, 220, 220)).get("mask_unreliable") or \
        geo([(0, 0, 1, 1)]).get("mask_unreliable")
    tiny = geo([(0.5, 0.5, 0.505, 0.51)])
    assert tiny.get("subject_too_small")
    assert "subject_too_small:child" in compare_geometry(geo(CENTRED), tiny)["flags"]


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_compare_images_and_cli(tmp_path, capsys):
    from fake_comfy import make_png
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    a.write_bytes(make_png(64, 64, (10, 10, 10)))
    b.write_bytes(make_png(64, 64, (10, 10, 10)))
    report = compare_images(a, b)
    assert "subject_too_small:parent" in report["comparison"]["flags"]  # all-dark image
    assert cli.main(["anchor-check", str(a), str(b)]) == 0
    assert json.loads(capsys.readouterr().out)["comparison"]["method"] == "heuristic"
