"""Committed music assets must match their provenance records and be public domain / CC0."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUSIC = ROOT / "assets" / "music"


def test_every_audio_file_has_matching_provenance():
    audio = sorted(p for p in MUSIC.iterdir() if p.suffix.lower() in {".opus", ".ogg", ".mp3", ".flac", ".wav", ".m4a"})
    assert audio, "expected at least one committed music file"
    for path in audio:
        record = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
        assert record["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest(), path.name
        assert record["bytes"] == path.stat().st_size
        lic = record["license"]
        assert "Public domain" in lic["recording"] or "CC0" in lic["recording"]
        assert "Public domain" in lic["composition"] or "CC0" in lic["composition"]
        assert record["approval"]["by"] and record["source"]["original"]["sha1"]
        assert path.name in (MUSIC / "README.md").read_text(encoding="utf-8")
