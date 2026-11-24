"""Cross-process run lock, per-run GPU budgets and schedule previews (F17).

- ``RunLock``: one MorphCurrent GPU render per runs root at a time (exclusive lock file
  with pid/host/heartbeat; stale after a timeout so a crash cannot block forever).
- ``Budget``: caps on *new* GPU submissions and estimated GPU seconds. Checked before a
  stage is submitted; cached/verified stages are free; running jobs are never interrupted.
- ``schedule_preview``: dependency-ordered stages with F11 estimates and which fit a cap.
"""
from __future__ import annotations

import json
import os
import socket
import time
from datetime import datetime, timezone
from pathlib import Path

from .perf import estimate

LOCK_NAME = ".morphcurrent-gpu.lock"
STALE_S = 30 * 60


class LockBusy(RuntimeError):
    pass


class RunLock:
    def __init__(self, runs_root: str | Path, stale_s: float = STALE_S, clock=time.time):
        self.path = Path(runs_root) / LOCK_NAME
        self.stale_s = stale_s
        self.clock = clock
        self.held = False
        self.took_over: dict | None = None

    def _payload(self) -> dict:
        return {"pid": os.getpid(), "host": socket.gethostname(), "heartbeat": self.clock(),
                "started": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    def acquire(self) -> "RunLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(2):
            try:
                with self.path.open("x", encoding="utf-8") as stream:
                    json.dump(self._payload(), stream)
                self.held = True
                return self
            except FileExistsError:
                try:
                    current = json.loads(self.path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    current = {"heartbeat": 0}
                age = self.clock() - float(current.get("heartbeat", 0))
                if age <= self.stale_s:
                    raise LockBusy(f"another MorphCurrent GPU render holds {self.path} "
                                   f"(pid {current.get('pid')} on {current.get('host')}, "
                                   f"heartbeat {age:.0f} s ago); wait for it to finish")
                self.took_over = current  # stale: previous holder crashed
                self.path.unlink(missing_ok=True)
        raise LockBusy(f"could not acquire {self.path}")

    def heartbeat(self) -> None:
        if self.held:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._payload()), encoding="utf-8")
            os.replace(tmp, self.path)

    def release(self) -> None:
        if self.held:
            self.path.unlink(missing_ok=True)
            self.held = False

    def __enter__(self) -> "RunLock":
        return self.acquire()

    def __exit__(self, *exc: object) -> None:
        self.release()


class Budget:
    """Caps on new GPU submissions. ``cost_of(kind, task)`` returns estimated seconds or None."""

    def __init__(self, max_jobs: int | None = None, max_gpu_s: float | None = None,
                 cost_of=None, on_check=None):
        self.max_jobs = max_jobs
        self.max_gpu_s = max_gpu_s
        self.cost_of = cost_of or (lambda kind, task: None)
        self.on_check = on_check or (lambda: None)
        self.jobs = 0
        self.gpu_s = 0.0
        self.blocked: dict | None = None

    def allow(self, kind: str, task: dict) -> bool:
        """Charge and allow one new submission, or record why not (nothing is charged then)."""
        self.on_check()
        if self.max_jobs is not None and self.jobs + 1 > self.max_jobs:
            self.blocked = {"task": task.get("id"), "reason": f"max_jobs {self.max_jobs} reached"}
            return False
        cost = self.cost_of(kind, task)
        if self.max_gpu_s is not None:
            if cost is None:
                self.blocked = {"task": task.get("id"), "reason": "no measured cost for this stage "
                                "(NO DATA) under a finite --max-gpu-s"}
                return False
            if self.gpu_s + cost > self.max_gpu_s:
                self.blocked = {"task": task.get("id"),
                                "reason": f"would exceed max_gpu_s {self.max_gpu_s:.0f} "
                                          f"({self.gpu_s:.0f} used + {cost:.0f} estimated)"}
                return False
        self.jobs += 1
        self.gpu_s += cost or 0.0
        return True

    def summary(self) -> dict:
        return {"new_jobs": self.jobs, "estimated_gpu_s": round(self.gpu_s, 1),
                "max_jobs": self.max_jobs, "max_gpu_s": self.max_gpu_s, "blocked": self.blocked}


def cost_function(dag_plan: dict, history: list[dict]):
    """Map a stage to its F11 estimate (seconds) using the plan's own tasks."""
    if not history:
        return lambda kind, task: None
    rows = {r["task"]: r for r in estimate(dag_plan, history)["stages"]}

    def cost(kind: str, task: dict) -> float | None:
        return rows.get(task.get("id"), {}).get("exec_s")
    return cost


def schedule_preview(dag_plan: dict, history: list[dict], *, max_gpu_s: float | None = None,
                     max_jobs: int | None = None) -> dict:
    est = {r["task"]: r for r in estimate(dag_plan, history)["stages"]} if history else {}
    rows, total, jobs, fits = [], 0.0, 0, True
    for task_id in dag_plan["order"]:
        task = dag_plan["tasks"][task_id]
        if task["kind"] not in ("anchor", "bridge"):
            continue
        cost = est.get(task_id, {}).get("exec_s")
        jobs += 1
        if cost is not None:
            total += cost
        within = fits and (max_jobs is None or jobs <= max_jobs) and \
            (max_gpu_s is None or (cost is not None and total <= max_gpu_s))
        fits = within
        rows.append({"task": task_id, "estimated_s": cost, "label": est.get(task_id, {}).get("label", "NO DATA"),
                     "cumulative_s": round(total, 1), "fits_budget": within})
    return {"stages": rows, "total_estimated_s": round(total, 1),
            "fitting_stages": sum(r["fits_budget"] for r in rows),
            "note": "Estimates from measured history; cached stages cost nothing at render time."}
