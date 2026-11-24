"""Opt-in SHA-256 provenance for ComfyUI model files (F07).

Hashing multi-GB weights is heavy disk I/O, so it runs only when asked
(``morphcurrent models-hash``), only for files a binding profile's graph actually
references, and never while ComfyUI has queued work. Results are cached by
(path, size, mtime) so an unchanged file is never read twice.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .cache import sha256_file

DEFAULT_MODELS_ROOT = Path(r"C:\AI\ComfyUI_windows_portable\ComfyUI\models")
MODEL_FOLDERS = {"unet_name": "diffusion_models", "clip_name": "text_encoders",
                 "clip_name1": "text_encoders", "clip_name2": "text_encoders",
                 "vae_name": "vae", "ckpt_name": "checkpoints", "lora_name": "loras"}
NOT_RECORDED = "NOT RECORDED"


def models_in_graph(graph: dict) -> list[tuple[str, str]]:
    """(folder, filename) pairs referenced by loader inputs of an API graph."""
    found = set()
    for node in graph.values():
        for key, value in node["inputs"].items():
            if key in MODEL_FOLDERS and isinstance(value, str):
                found.add((MODEL_FOLDERS[key], value))
    return sorted(found)


def load_cache(cache_file: Path) -> dict:
    try:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"schema": 1, "files": {}}


def _stat_key(path: Path) -> dict:
    stat = path.stat()
    return {"bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def hash_models(pairs: list[tuple[str, str]], models_root: Path, cache_file: Path,
                hasher=sha256_file) -> dict:
    """Hash (folder, filename) pairs under ``models_root``; reuse unchanged cache entries."""
    cache = load_cache(cache_file)
    results = {}
    for folder, name in pairs:
        path = models_root / folder / name
        key = f"{folder}/{name}"
        if not path.is_file():
            results[key] = {"status": "missing", "path": str(path)}
            continue
        stat = _stat_key(path)
        cached = cache["files"].get(key)
        if cached and {k: cached.get(k) for k in stat} == stat:
            results[key] = {**cached, "status": "cached"}
            continue
        entry = {**stat, "sha256": hasher(path),
                 "hashed_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        cache["files"][key] = entry
        results[key] = {**entry, "status": "hashed"}
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache_file.with_name(cache_file.name + ".tmp")
    tmp.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, cache_file)
    return results


def recorded_hashes(models: dict[str, str], cache_file: Path, models_root: Path) -> dict:
    """Map a job's ``models`` (``node.input`` -> filename) to cached SHA-256 when still valid."""
    cache = load_cache(cache_file)
    out = {}
    for where, name in models.items():
        key = f"{MODEL_FOLDERS.get(where.split('.', 1)[-1], '?')}/{name}"
        entry = cache["files"].get(key)
        path = models_root / key
        valid = entry and path.is_file() and {k: entry.get(k) for k in ("bytes", "mtime_ns")} == _stat_key(path)
        out[where] = entry["sha256"] if valid else NOT_RECORDED
    return out
