"""Root run manifest tying a storyboard plan to its stage jobs (F07).

``outputs/runs/run-<plan_sha16>/manifest.json`` is rewritten atomically after every
change. Stage jobs stay in their own content-addressed directories; the manifest
points at them and mirrors their state, so a crash at any point loses nothing.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RunManifest:
    def __init__(self, run_dir: Path, data: dict):
        self.dir = run_dir
        self.data = data

    @property
    def path(self) -> Path:
        return self.dir / "manifest.json"

    @classmethod
    def open(cls, runs_root: str | Path, plan: dict, *, storyboard: str | None = None,
             repo_head: str | None = None) -> "RunManifest":
        run_dir = Path(runs_root) / f"run-{plan['plan_sha256'][:16]}"
        if (run_dir / "manifest.json").exists():
            manifest = cls.load(run_dir)
            if manifest.data["plan_sha256"] != plan["plan_sha256"]:
                raise ValueError(f"{run_dir} belongs to plan {manifest.data['plan_sha256']}")
            return manifest
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n",
                                           encoding="utf-8", newline="\n")
        manifest = cls(run_dir, {
            "schema": 1, "kind": "morphcurrent_run", "created_at": _now(),
            "morphcurrent_version": __version__, "repo_head": repo_head,
            "storyboard": storyboard, "storyboard_sha256": plan.get("storyboard_sha256"),
            "plan_sha256": plan["plan_sha256"], "order": plan["order"],
            "requirements": plan.get("requirements"),
            "stages": {task_id: {"state": "pending"} for task_id in plan["order"]},
            "consent": [], "vram": [], "events": [{"t": _now(), "event": "created"}],
        })
        manifest.save()
        return manifest

    @classmethod
    def load(cls, run_dir: str | Path) -> "RunManifest":
        run_dir = Path(run_dir)
        return cls(run_dir, json.loads((run_dir / "manifest.json").read_text(encoding="utf-8")))

    def save(self) -> None:
        tmp = self.path.with_name("manifest.json.tmp")
        tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8", newline="\n")
        os.replace(tmp, self.path)

    def record_stage(self, task_id: str, job: Any = None, **extra: Any) -> None:
        entry = dict(self.data["stages"].get(task_id, {}))
        if job is not None:
            record = job.record
            entry.update(job_dir=str(job.dir), job_id=record["job_id"], state=record["state"],
                         prompt_id=record.get("prompt_id"), error=record.get("error"))
            image = record.get("image")
            if image:
                entry["image_sha256"] = image["sha256"]
            videos = [o for o in record.get("outputs", []) if o.get("kind") == "video" and o.get("sha256")]
            if videos:
                entry["video_sha256"] = videos[0]["sha256"]
        entry.update(extra)
        self.data["stages"][task_id] = entry
        self.data["events"].append({"t": _now(), "event": "stage", "task": task_id,
                                    "state": entry.get("state")})
        self.save()

    def record(self, key: str, value: Any) -> None:
        if isinstance(self.data.get(key), list):
            self.data[key].append(value)
        else:
            self.data[key] = value
        self.save()
