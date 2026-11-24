"""Verify deliberately committed example anchors and safe Python staging."""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANCHORS = {
    "01_glass_orchid.jpg": "8cdb3f53b119ff783a941f0e1ef2123b55dd7afdc45355f3fa7166f70809bfbb",
    "02_metallic_butterfly.jpg": "c7f2be088ac641945e468c97b800b04bec6d46698944b405205a7cefe54aaced",
}
STAGER = ROOT / "scripts" / "windows" / "stage_example_anchors.py"


def test_reviewed_image_assets_have_stable_bytes():
    for name, expected_sha256 in ANCHORS.items():
        raw = (ROOT / "assets" / "anchors" / name).read_bytes()
        assert len(raw) > 50000
        assert raw[:3] == b"\xff\xd8\xff"  # genuine JPEG, not text or LFS pointers
        assert hashlib.sha256(raw).hexdigest() == expected_sha256


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(STAGER), "--install-root", str(root), *args],
        capture_output=True, text=True, check=False,
    )


def test_stager_is_idempotent_and_no_overwrite_by_default(tmp_path: Path):
    portable = tmp_path / "portable"
    comfy = portable / "ComfyUI"
    comfy.mkdir(parents=True)
    (comfy / "main.py").write_text("# stub for path validation\n", encoding="utf-8")
    assert _run(portable, "--dry-run").returncode == 0
    assert not (comfy / "input").exists()

    first = _run(portable)
    assert first.returncode == 0, first.stderr
    for name in ANCHORS:
        assert (comfy / "input" / name).read_bytes() == (ROOT / "assets" / "anchors" / name).read_bytes()

    repeat = _run(portable)
    assert repeat.returncode == 0
    assert "unchanged" in repeat.stdout

    conflict = comfy / "input" / "02_metallic_butterfly.jpg"
    conflict.write_bytes(b"USER DATA")
    denied = _run(portable)
    assert denied.returncode == 2
    assert conflict.read_bytes() == b"USER DATA"

    assert _run(portable, "--overwrite").returncode == 0
    assert conflict.read_bytes() == (ROOT / "assets" / "anchors" / conflict.name).read_bytes()
