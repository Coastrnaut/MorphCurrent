"""Opt-in sampled GPU memory observations via nvidia-smi (F07).

Reports *overall* GPU memory used by all processes (the A6000 is shared with
other apps), sampled at a fixed interval — not per-process allocation and not a
guaranteed true peak between samples. ``/system_stats`` snapshots are never used.
"""
from __future__ import annotations

import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from typing import Callable

LABEL = "overall GPU memory used (all processes), sampled via nvidia-smi"
QUERY = ["nvidia-smi", "--query-gpu=index,memory.used,memory.total", "--format=csv,noheader,nounits"]


def _query() -> str | None:
    if not shutil.which("nvidia-smi"):
        return None
    try:
        done = subprocess.run(QUERY, capture_output=True, text=True, timeout=10, shell=False, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def parse(output: str, gpu_index: int = 0) -> tuple[int, int] | None:
    for line in output.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 3 and parts[0] == str(gpu_index) and parts[1].isdigit() and parts[2].isdigit():
            return int(parts[1]), int(parts[2])
    return None


class VramSampler:
    def __init__(self, interval: float = 0.5, gpu_index: int = 0,
                 query: Callable[[], str | None] = _query):
        self.interval = interval
        self.gpu_index = gpu_index
        self.query = query
        self.samples: list[tuple[float, int]] = []
        self.total_mib: int | None = None
        self.started: str | None = None
        self.ended: str | None = None
        self.unavailable = False
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def sample_once(self) -> None:
        out = self.query()
        parsed = parse(out, self.gpu_index) if out else None
        if parsed is None:
            self.unavailable = self.unavailable or out is None
            return
        self.samples.append((time.monotonic(), parsed[0]))
        self.total_mib = parsed[1]

    def _loop(self) -> None:
        while not self._stop.is_set():
            self.sample_once()
            self._stop.wait(self.interval)

    def __enter__(self) -> "VramSampler":
        self.started = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.sample_once()  # baseline before the stage starts
        self._thread = threading.Thread(target=self._loop, name="vram-sampler", daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=self.interval * 4 + 10)
        self.sample_once()
        self.ended = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def summary(self) -> dict:
        if not self.samples:
            return {"status": "NOT MEASURED", "reason": "nvidia-smi unavailable" if self.unavailable
                    else "no samples", "label": LABEL}
        used = [s[1] for s in self.samples]
        return {"status": "sampled", "label": LABEL, "gpu_index": self.gpu_index,
                "interval_s": self.interval, "samples": len(used),
                "baseline_mib": used[0], "peak_mib": max(used), "min_mib": min(used),
                "peak_above_baseline_mib": max(used) - used[0], "total_mib": self.total_mib,
                "started": self.started, "ended": self.ended,
                "caveat": "peaks between samples are not observed; includes other processes"}
