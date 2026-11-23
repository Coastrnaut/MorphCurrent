"""Stable content-addressing for immutable DAG tasks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cache_key(*, task: dict, dependencies: dict, workflow_sha256: str,
              model_sha256: dict[str, str], code_revision: str) -> str:
    payload = {
        "task": task,
        "dependencies": dependencies,
        "workflow_sha256": workflow_sha256,
        "model_sha256": model_sha256,
        "code_revision": code_revision,
    }
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()
