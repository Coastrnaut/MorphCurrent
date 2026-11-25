"""Anchor fix tests: two candidate repairs per weak film anchor, rendered as single-anchor GPU jobs.

Variant A ("instruction") re-edits the anchor from its parent's rendered image with an explicit
replace/remove instruction; variant B ("fresh") renders an independent text-to-image keyframe from the
anchor's planned prompt. Both use the anchor's planned seed and size, so the only difference is the method.
The owner picks per anchor; applying a pick is a separate, explicit step.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

from .batch_review import ReviewError, film_state

DEFAULT_FIXES = Path("configs/film/anchor-fixes.yaml")


def load_fixes(path: str | Path = DEFAULT_FIXES) -> list[dict]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if data.get("version") != 1:
        raise ReviewError("anchor fixes need version: 1")
    fixes = data.get("fixes") or []
    for f in fixes:
        if not f.get("anchor") or not any(str(f.get(k) or "").strip() for k in ("instruction", "prompt", "apply")):
            raise ReviewError(f"each fix needs an anchor and an instruction, prompt or apply: {f!r}")
    return fixes


def plan_tests(storyboard: str | Path, fixes: list[dict], out_dir: str | Path, *, runs_root: str | Path = "outputs/runs",
               log: str | Path | None = None, repo_root: str | Path = ".") -> list[dict]:
    """One `anchor` CLI job per fix and variant; refuses when a parent image is not rendered yet."""
    state = film_state(storyboard, runs_root, log, repo_root=repo_root)
    tasks = state["_plan"]["tasks"]
    current = {s["stage"]: s for s in state["stages"]}
    out_dir = Path(out_dir)
    jobs = []
    for f in fixes:
        tid = f"anchor:{f['anchor']}"
        if tid not in tasks:
            raise ReviewError(f"{f['anchor']} is not an anchor of {state['film']}")
        t = tasks[tid]
        common = ["--seed", str(t["seed"]), "--width", str(t["width"]), "--height", str(t["height"]),
                  "--negative", t["negative_prompt"] or ""]
        parent = current.get(f"anchor:{t.get('reference')}")
        parent_img = parent["versions"][-1]["media"] if parent and parent["versions"] else None
        if t.get("method") == "reference_edit" and str(f.get("instruction") or "").strip():
            if not parent_img or not Path(parent_img).is_file():
                raise ReviewError(f"parent image of {f['anchor']} ({t.get('reference')}) is not rendered yet")
            jobs.append({"anchor": f["anchor"], "variant": "A-instruction", "prompt": f["instruction"].strip(),
                         "args": ["--method", "reference_edit", "--reference", str(parent_img), *common]})
        jobs.append({"anchor": f["anchor"], "variant": "B-fresh", "prompt": t["positive_prompt"],
                     "args": ["--method", "independent_t2i", *common]})
    for j in jobs:
        j["prompt_file"] = str(out_dir / f"{j['anchor']}.{j['variant']}.txt")
        j["label"] = f"fix-{j['anchor']}-{j['variant']}"[:60]
    return jobs


def run_tests(jobs: list[dict], *, runner=None, python: str | None = None, runs_root: str = "outputs/runs") -> list[dict]:
    """Run the jobs one at a time (each refuses a busy queue); stop at the first failure."""
    run = runner or (lambda args: subprocess.run(args, shell=False, check=False).returncode)
    exe = python or sys.executable
    results = []
    for j in jobs:
        Path(j["prompt_file"]).parent.mkdir(parents=True, exist_ok=True)
        Path(j["prompt_file"]).write_text(j["prompt"], encoding="utf-8")
        code = run([exe, "-m", "morph_studio.cli", "anchor", "--prompt-file", j["prompt_file"], *j["args"],
                    "--label", j["label"], "--runs-root", runs_root, "--confirm-gpu"])
        results.append({"anchor": j["anchor"], "variant": j["variant"], "exit": code})
        if code != 0:
            break
    return results


def main_summary(jobs: list[dict]) -> str:
    return json.dumps([{k: j[k] for k in ("anchor", "variant", "label")} for j in jobs], indent=2)
