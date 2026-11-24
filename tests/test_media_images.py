"""F03 stdlib PNG/JPEG integrity checks."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from fake_comfy import make_png
from morph_studio.media import ImageInvalid, inspect_image

REPO = Path(__file__).resolve().parents[1]


def test_valid_png(tmp_path):
    path = tmp_path / "a.png"
    path.write_bytes(make_png(64, 32))
    assert inspect_image(path) == {"format": "png", "width": 64, "height": 32}


def test_truncated_png(tmp_path):
    path = tmp_path / "a.png"
    path.write_bytes(make_png(64, 32)[:-20])
    with pytest.raises(ImageInvalid):
        inspect_image(path)


def test_corrupt_png_crc(tmp_path):
    data = bytearray(make_png(16, 16))
    data[40] ^= 0xFF  # inside IDAT
    path = tmp_path / "a.png"
    path.write_bytes(bytes(data))
    with pytest.raises(ImageInvalid, match="CRC"):
        inspect_image(path)


def _jpeg(tmp_path):
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not installed")
    path = tmp_path / "frame.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=blue:s=96x54", "-frames:v", "1",
                    str(path)], check=True, shell=False)
    return path


def test_real_jpeg_dimensions(tmp_path):
    info = inspect_image(_jpeg(tmp_path))
    assert info == {"format": "jpeg", "width": 96, "height": 54}


def test_truncated_jpeg(tmp_path):
    data = _jpeg(tmp_path).read_bytes()
    path = tmp_path / "t.jpg"
    path.write_bytes(data[: len(data) // 2])
    with pytest.raises(ImageInvalid, match="EOI"):
        inspect_image(path)


def test_not_an_image(tmp_path):
    path = tmp_path / "x.png"
    path.write_bytes(b"\x00\x00\x00\x18ftypmp42")
    with pytest.raises(ImageInvalid, match="not a PNG"):
        inspect_image(path)
