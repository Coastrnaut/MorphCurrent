"""Production acceptance tools (F20): run comparison, source/licence audit, run backup/restore,
acceptance matrix. Offline and read-only except the archive/restore targets you name; nothing here
tags releases or uploads. Only ``replay`` may render, and only with explicit GPU consent.
"""
from __future__ import annotations

import json
import os
import re
import secrets as _random
import shutil
import subprocess
import zipfile
from pathlib import Path, PurePosixPath
from typing import Callable

from .cache import sha256_file

UNRESOLVED = re.compile(r"pending|partial|planned|not evidenced|not implemented|blocked", re.I)
MEDIA_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".webm", ".mov", ".wav", ".flac", ".mp3",
             ".opus", ".ogg"}
WEIGHT_EXT = {".safetensors", ".ckpt", ".gguf", ".pt", ".pth", ".bin", ".onnx"}
SECRET_NAME = re.compile(r"(^|/)\.env|\.pem$|\.key$|credentials|secret|token", re.I)
EQUIVALENT_MAD = 1.0
SUMS = "SHA256SUMS.json"


class ReleaseError(ValueError):
    pass


# --- run layout ---------------------------------------------------------------------------------

def _load_manifest(run_dir: Path) -> dict:
    try:
        return json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ReleaseError(f"cannot read {run_dir / 'manifest.json'}: {exc}") from exc


def _job_dir(runs_root: Path, job_dir: str | None) -> Path | None:
    return runs_root / Path(job_dir.replace("\\", "/")).name if job_dir else None


def _job_output(job: Path) -> Path | None:
    try:
        record = json.loads((job / "job.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    local = (record.get("image") or {}).get("local_path") or next(
        (o.get("local_path") for o in record.get("outputs", []) if o.get("kind") == "video"), None)
    return job / Path(local.replace("\\", "/")) if local else None


def _stage_files(run_dir: Path) -> dict[str, dict]:
    """Stage → {state, recorded sha, file}. Job dirs live in the run's parent (the runs root)."""
    manifest = _load_manifest(run_dir)
    runs_root = run_dir.parent
    out: dict[str, dict] = {}
    for task in manifest.get("order") or list(manifest.get("stages", {})):
        stage = manifest.get("stages", {}).get(task, {})
        entry = {"state": stage.get("state"), "recorded": stage.get("image_sha256") or stage.get("video_sha256"),
                 "file": None}
        if task == "final:movie":
            final = (manifest.get("final") or {}).get("output")
            if final:
                entry["file"] = run_dir / "final" / Path(final.replace("\\", "/")).name
        else:
            job = _job_dir(runs_root, stage.get("job_dir"))
            entry["file"] = _job_output(job) if job else None
            entry["job"] = job
        out[task] = entry
    return out


# --- US1: comparison ----------------------------------------------------------------------------

def _frames(a: Path, b: Path) -> dict:
    from .qa import decode_gray_frames
    fa, fb = decode_gray_frames(a), decode_gray_frames(b)
    diffs = [sum(abs(x - y) for x, y in zip(p, q)) / max(1, len(p)) for p, q in zip(fa, fb)]
    worst = round(max(diffs), 3) if diffs else None
    return {"count_a": len(fa), "count_b": len(fb), "max_mean_abs_diff": worst,
            "visually_equivalent": bool(fa) and len(fa) == len(fb) and worst is not None and worst <= EQUIVALENT_MAD}


def compare_runs(a: str | Path, b: str | Path, frames: bool = False) -> dict:
    """Stage-by-stage content comparison of two run directories (bytes re-hashed on disk)."""
    ra, rb = Path(a), Path(b)
    sa, sb = _stage_files(ra), _stage_files(rb)
    same_plan = _load_manifest(ra).get("plan_sha256") == _load_manifest(rb).get("plan_sha256")
    order = list(sa) + [t for t in sb if t not in sa]
    rows = []
    for task in order:
        ea, eb = sa.get(task), sb.get(task)
        row: dict = {"task": task}
        if ea is None or eb is None:
            row["status"] = "missing_a" if ea is None else "missing_b"
        elif ea["state"] != "verified" or eb["state"] != "verified":
            row["status"] = "not_verified"
        else:
            fa = ea["file"] if ea["file"] and ea["file"].is_file() else None
            fb = eb["file"] if eb["file"] and eb["file"].is_file() else None
            if fa is None or fb is None:
                row["status"] = "missing_a" if fa is None else "missing_b"
            else:
                row["sha_a"], row["sha_b"] = sha256_file(fa), sha256_file(fb)
                row["status"] = "identical" if row["sha_a"] == row["sha_b"] else "different"
                if row["status"] == "different" and frames and fa.suffix.lower() == ".mp4":
                    try:
                        row["frames"] = _frames(fa, fb)
                    except Exception as exc:  # decoding problems are reported, not fatal
                        row["frames"] = {"error": str(exc)[:200]}
        rows.append(row)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    if all(r["status"] == "identical" for r in rows) and same_plan:
        verdict = "reproduced"
    elif any(r["status"] in ("different", "missing_a", "missing_b") for r in rows) or not same_plan:
        verdict = "differs"
    else:
        verdict = "incomplete"
    return {"a": str(ra), "b": str(rb), "same_plan": same_plan, "verdict": verdict, "counts": counts,
            "stages": rows}


def replay(storyboard: str | Path, reference: str | Path, runs_root: str | Path,
           client_factory: Callable, *, confirm_gpu: bool = False, frames: bool = False, **render_kw) -> dict:
    """Render into a fresh, empty runs root (GPU only with consent), then compare to ``reference``."""
    from .render import dry_run, run_render
    root = Path(runs_root)
    if root.exists() and any(root.iterdir()):
        raise ReleaseError(f"{root} is not empty; replay needs a fresh, empty runs root")
    if not confirm_gpu:  # validate only: write nothing, so the fresh root stays usable for the real replay
        report = dry_run(storyboard, render_kw.get("profiles"), render_kw.get("repo_root", "."))
        return {"render": {"status": "validated" if report["status"] == "ready" else "blocked",
                           "blocked": report["blocked"], "gpu_jobs": report["gpu_jobs"]}}
    result = run_render(storyboard, client_factory, runs_root=root, confirm_gpu=confirm_gpu, **render_kw)
    out = {"render": result}
    if result.get("status") in ("complete", "awaiting_review") and confirm_gpu:
        out["comparison"] = compare_runs(reference, result["run_dir"], frames=frames)
    return out


# --- US2: audit ---------------------------------------------------------------------------------

def _tracked_files(root: Path) -> tuple[list[str], str | None]:
    try:
        done = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, timeout=30,
                              shell=False, check=False)
        if done.returncode == 0:
            return [p for p in done.stdout.decode("utf-8", "replace").split("\0") if p], None
    except (OSError, subprocess.SubprocessError):
        pass
    skip = {".git", ".venv", "outputs", "library", ".local", "__pycache__"}
    files = [p.relative_to(root).as_posix() for p in root.rglob("*")
             if p.is_file() and not skip.intersection(p.relative_to(root).parts)]
    return files, "git unavailable: audited the working tree instead of tracked files"


def _model_hashes(models_md: Path) -> list[dict]:
    rows = []
    if not models_md.is_file():
        return rows
    for line in models_md.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|[^|]*\|\s*`([^`]+)`\s*\|\s*`([^`]+\.(?:safetensors|pth))`\s*\|\s*`([0-9a-f]{64})`\s*\|", line)
        if m:
            rows.append({"folder": m.group(1), "file": m.group(2), "sha256": m.group(3)})
    return rows


def audit_repo(root: str | Path = ".") -> dict:
    """Read-only release audit. Never hashes model weights."""
    from .workflow_adapter import graph_sha256, load_api_workflow
    base = Path(root)
    checks: list[dict] = []

    def add(check: str, status: str, detail: str) -> None:
        checks.append({"check": check, "status": status, "detail": detail})

    for prof in sorted((base / "configs" / "profiles").glob("*.binding.json")):
        name = prof.relative_to(base).as_posix()
        try:
            data = json.loads(prof.read_text(encoding="utf-8"))
            workflow = base / data["workflow"]
            pinned = data["workflow_sha256"]
        except (OSError, ValueError, KeyError) as exc:
            add(f"profile {name}", "error", f"unreadable profile: {exc}")
            continue
        if not workflow.is_file():
            add(f"profile {name}", "warning" if prof.name.startswith("test_") else "error",
                f"workflow {data['workflow']} not found")
            continue
        actual = graph_sha256(load_api_workflow(workflow))
        add(f"profile {name}", "ok" if actual == pinned else "error",
            f"{data['workflow']} pinned" if actual == pinned else
            f"{data['workflow']} hash {actual[:12]} != pinned {pinned[:12]} in {name}")

    files, note = _tracked_files(base)
    if note:
        add("tracked files", "warning", note)
    for rel in files:
        path = PurePosixPath(rel)
        suffix = path.suffix.lower()
        if suffix in WEIGHT_EXT:
            add("forbidden file", "error", f"model weight tracked: {rel}")
        elif path.parts and path.parts[0] in ("outputs", "library"):
            add("forbidden file", "error", f"generated/private file tracked: {rel}")
        elif path.name == "manifest.json" and any(p.startswith("run-") for p in path.parts[:-1]):
            add("forbidden file", "error", f"run record tracked: {rel}")
        elif SECRET_NAME.search(rel) and suffix not in (".py", ".md"):
            add("forbidden file", "error", f"secret-like file tracked: {rel}")
        elif suffix in MEDIA_EXT:
            prov = base / path.with_suffix(".json")
            try:
                meta = json.loads(prov.read_text(encoding="utf-8"))
                ok = bool(meta.get("license")) and any(meta.get(k) for k in ("source", "work", "url"))
            except (OSError, ValueError):
                ok = False
            add("media licence", "ok" if ok else "error",
                f"{rel} has licence provenance" if ok else
                f"{rel} lacks licence provenance (same-stem .json with license and source)")
    models = _model_hashes(base / "docs" / "MODELS.md")
    add("recorded model hashes", "ok" if models else "warning",
        f"{len(models)} model SHA-256 values recorded in docs/MODELS.md (not re-hashed)")
    return {"checks": checks, "models": models,
            "errors": [c["detail"] for c in checks if c["status"] == "error"],
            "warnings": [c["detail"] for c in checks if c["status"] == "warning"]}


# --- US3: backup / restore ----------------------------------------------------------------------

def backup_run(run_dir: str | Path, out: str | Path, allow_missing_jobs: bool = False) -> dict:
    run, archive = Path(run_dir), Path(out)
    if archive.exists():
        raise ReleaseError(f"{archive} exists; choose another archive path")
    stages = _stage_files(run)
    jobs = sorted({s["job"] for s in stages.values() if s.get("job")}, key=str)
    missing = [str(j.name) for j in jobs if not (j / "job.json").is_file()]
    if missing and not allow_missing_jobs:
        raise ReleaseError(f"job folders missing for this run: {', '.join(missing)} (use allow_missing_jobs)")
    members: list[tuple[Path, str]] = [(f, f"run/{run.name}/{f.relative_to(run).as_posix()}")
                                       for f in sorted(run.rglob("*")) if f.is_file()]
    for job in jobs:
        if job.name in missing:
            continue
        members += [(f, f"jobs/{job.name}/{f.relative_to(job).as_posix()}") for f in sorted(job.rglob("*"))
                    if f.is_file()]
    sums = {name: sha256_file(path) for path, name in members}
    tmp = archive.with_name(archive.name + ".part")
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path, name in members:
            z.write(path, name)
        z.writestr(SUMS, json.dumps(sums, indent=1, sort_keys=True))
    os.replace(tmp, archive)
    return {"archive": str(archive), "files": len(members), "bytes": archive.stat().st_size,
            "missing_jobs": missing}


def _safe_member(name: str) -> bool:
    p = PurePosixPath(name)
    return not (p.is_absolute() or ".." in p.parts or ":" in name or name.startswith("\\"))


def restore_run(archive: str | Path, runs_root: str | Path) -> Path:
    """Verify every checksum, then place the run and its jobs under ``runs_root``; never overwrite."""
    import hashlib
    dest = Path(runs_root)
    with zipfile.ZipFile(archive) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        for name in names:
            if not _safe_member(name):
                raise ReleaseError(f"unsafe archive member path: {name}")
        if SUMS not in names:
            raise ReleaseError(f"{archive} has no {SUMS}")
        sums = json.loads(z.read(SUMS))
        if set(sums) != set(names) - {SUMS}:
            raise ReleaseError("archive members do not match the checksum list")
        for name in sums:
            if hashlib.sha256(z.read(name)).hexdigest() != sums[name]:
                raise ReleaseError(f"checksum mismatch for {name}; nothing restored")
        tops = {"/".join(PurePosixPath(n).parts[1:2]) for n in sums}
        for top in tops:
            if (dest / top).exists():
                raise ReleaseError(f"{dest / top} exists; restore never overwrites")
        staging = dest.parent / f".{dest.name}.restore-{_random.token_hex(4)}"
        try:
            for name in sums:
                parts = PurePosixPath(name).parts
                target = staging.joinpath(*parts[1:])
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read(name))
            dest.mkdir(parents=True, exist_ok=True)
            moved: list[str] = []
            try:
                for top in sorted(tops):
                    os.replace(staging / top, dest / top)
                    moved.append(top)
            except OSError:
                for top in moved:  # roll back so a failed restore leaves nothing behind
                    shutil.rmtree(dest / top, ignore_errors=True)
                raise
        finally:
            shutil.rmtree(staging, ignore_errors=True)
    run_names = {PurePosixPath(n).parts[1] for n in sums if n.startswith("run/")}
    if len(run_names) != 1:
        raise ReleaseError("archive must contain exactly one run")
    return dest / run_names.pop()


# --- US4: acceptance matrix ---------------------------------------------------------------------

def acceptance_matrix(ledger: str | Path, all_features: bool = False) -> dict:
    rows: dict[str, dict] = {}
    for line in Path(ledger).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*\*{0,2}(F\d\d)\*{0,2}\s*\|", line)
        if not m or m.group(1) in rows:
            continue
        status = re.search(r"\*\*([^*]+)\*\*", line[m.end():])
        text = line[m.end():]
        rows[m.group(1)] = {"feature": m.group(1), "status": status.group(1).strip() if status else "UNKNOWN",
                            "evidenced": not UNRESOLVED.search(text),
                            "gate": (UNRESOLVED.search(text).group(0) if UNRESOLVED.search(text) else None)}
    limit = 40 if all_features else 20
    ordered = [rows[f"F{i:02d}"] for i in range(1, limit + 1) if f"F{i:02d}" in rows]
    unresolved = sum(not r["evidenced"] for r in ordered)
    return {"rows": ordered, "evidenced": len(ordered) - unresolved, "unresolved": unresolved,
            "release_ready": unresolved == 0 and len(ordered) == limit,
            "note": "Release tagging requires owner approval even when release_ready is true."}
