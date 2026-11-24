"""Portable project packages: export, safe inspection, format migrations and sandboxed import (F28).

A package is one zip holding a storyboard's project files at their repository-relative paths (storyboard,
style packs, binding profiles, workflow exports, model catalogue), a ``project.json`` description (plan
checksum, profile identities, model/licence report - models are never bundled), optional run provenance with
local paths redacted, optional owner-authorized media, and ``SHA256SUMS.json`` over every other member.
``inspect_package`` checks a package without extracting it; ``import_project`` restores it into a new folder
and reports whether the storyboard re-plans to the recorded plan. No inference, no network, no downloads.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import secrets
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from . import __version__
from .cache import sha256_file

FORMAT = 1
KIND = "morphcurrent_project"
DESCRIPTION = "project.json"
SUMS = "SHA256SUMS.json"
REDACTED = "<redacted-local-path>"
WEIGHT_EXT = {".safetensors", ".pth", ".pt", ".ckpt", ".bin", ".gguf", ".onnx"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv"}
AUDIO_EXT = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"}
MEDIA_EXT = IMAGE_EXT | VIDEO_EXT | AUDIO_EXT
MAX_MEMBERS = 10_000
MAX_NON_MEDIA = 2 * 1024 ** 3
MAX_TOTAL = 64 * 1024 ** 3
MAX_RATIO = 200
RATIO_MIN_BYTES = 1024 ** 2
RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
_ABS = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\|//|/(?:home|Users|tmp|var|mnt|root)/)")
_CHUNK = 1024 * 1024


class PackageError(ValueError):
    pass


# ---------------------------------------------------------------------------------------- helpers

def _unsafe_name(name: str) -> bool:
    """True for member names that could escape a destination or hit special Windows names."""
    if not name or name.startswith("/") or "\\" in name or ":" in name:
        return True
    for part in PurePosixPath(name).parts:
        if part in ("..", ".") or part.endswith((" ", ".")):
            return True
        if part.split(".")[0].upper() in RESERVED:
            return True
    return False


def _is_abs(text: str) -> bool:
    return bool(_ABS.match(text))


def absolute_paths(data) -> list[str]:
    """Every string inside JSON-like ``data`` that looks like an absolute local path."""
    found = []
    if isinstance(data, str):
        if _is_abs(data):
            found.append(data)
    elif isinstance(data, dict):
        for value in data.values():
            found += absolute_paths(value)
    elif isinstance(data, list):
        for value in data:
            found += absolute_paths(value)
    return found


def redact(data, roots: list[Path]):
    """Replace absolute paths: inside a root -> relative POSIX name (first matching root), else REDACTED."""
    prefixes = [str(Path(r).resolve()).replace("\\", "/").rstrip("/").lower() + "/" for r in roots]
    count = 0

    def walk(value):
        nonlocal count
        if isinstance(value, str) and _is_abs(value):
            count += 1
            norm = value.replace("\\", "/")
            for prefix in prefixes:
                if norm.lower().startswith(prefix):
                    return norm[len(prefix):]
            return REDACTED
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        if isinstance(value, list):
            return [walk(v) for v in value]
        return value

    return walk(data), count


def _kind(path: Path) -> str:
    suffix = path.suffix.lower()
    return "image" if suffix in IMAGE_EXT else "video" if suffix in VIDEO_EXT else "audio"


def _json_bytes(data) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


# ----------------------------------------------------------------------------------------- export

def _style_chain(pack_id: str | None, styles_dir: Path) -> list:
    from .styles import load_pack
    chain, seen = [], set()
    while pack_id and pack_id not in seen:
        seen.add(pack_id)
        pack = load_pack(pack_id, styles_dir)
        chain.append(pack)
        pack_id = pack.extends
    return chain


def export_project(storyboard: str | Path, out: str | Path, *, repo_root: str | Path = ".",
                   run_dir: str | Path | None = None, profiles: dict[str, str] | None = None,
                   include_media: bool = False, include_audio: bool = False) -> dict:
    from .dag import compile_plan
    from .registry import build_entry
    from .release import _stage_files
    from .schema import load_storyboard

    root, out = Path(repo_root).resolve(), Path(out)
    if out.exists():
        raise FileExistsError(f"{out} exists; refusing to overwrite")
    if include_audio and not include_media:
        raise PackageError("music needs media authorization too (--include-media --include-audio)")
    sb_path = Path(storyboard).resolve()
    try:
        sb_rel = sb_path.relative_to(root).as_posix()
    except ValueError as exc:
        raise PackageError(f"storyboard {sb_path} must be inside the repository root {root}") from exc
    raw = sb_path.read_bytes()
    sb = load_storyboard(sb_path)
    plan = compile_plan(sb, profiles=profiles, repo_root=root, storyboard_bytes=raw)

    members: dict[str, bytes | Path] = {sb_rel: sb_path}
    desc: dict = {"format": FORMAT, "kind": KIND,
                  "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                  "morphcurrent_version": __version__,
                  "storyboard": {"name": sb.name, "path": sb_rel, "sha256": hashlib.sha256(raw).hexdigest()},
                  "plan_sha256": plan["plan_sha256"], "profile_overrides": profiles or None,
                  "anchors": [a.id for a in sb.anchors], "stage_ids": list(plan["order"]),
                  "profiles": [], "style_packs": [], "models": []}

    models: dict[str, dict] = {}
    for capability, req in sorted(plan["requirements"].items()):
        entry = build_entry(root / req["profile"], repo_root=root)
        members[req["profile"]] = root / req["profile"]
        if entry["workflow"] and (root / entry["workflow"]).is_file():
            members[entry["workflow"]] = root / entry["workflow"]
        desc["profiles"].append({"capability": capability, "path": req["profile"], "profile": entry["profile"],
                                 "workflow": entry["workflow"], "workflow_sha256": entry["workflow_sha256"],
                                 "status": entry["status"]})
        for m in entry["models"]:
            models.setdefault(f"{m['folder']}/{m['file']}", {k: m[k] for k in ("folder", "file", "role", "licence",
                                                                               "sha256")} | {"bundled": False})
    desc["models"] = [models[k] for k in sorted(models)]
    catalogue = root / "configs" / "model_catalogue.json"
    if catalogue.is_file():
        members["configs/model_catalogue.json"] = catalogue

    media: list[tuple[Path, str]] = []  # (source, member name if included)
    for pack in _style_chain(sb.style.pack, root / "configs" / "styles"):
        rel = f"configs/styles/{pack.id}.yaml"
        members[rel] = root / rel
        desc["style_packs"].append({"id": pack.id, "version": pack.version, "path": rel,
                                    "sha256": sha256_file(root / rel)})
        for asset in pack.reference_assets:
            media.append((root / "library" / asset.path, f"media/library/{PurePosixPath(asset.path).as_posix()}"))

    redactions = 0
    missing: list[dict] = []  # verified stages whose output file is no longer on disk
    if run_dir:
        run = Path(run_dir).resolve()
        for name in ("manifest.json", "plan.json", "review.json"):
            if (run / name).is_file():
                data, n = redact(json.loads((run / name).read_text(encoding="utf-8")), [root, run])
                redactions += n
                members[f"run/{run.name}/{name}"] = _json_bytes(data)
        manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        stages, seen, stage_files = {}, set(), _stage_files(run)
        for task, info in stage_files.items():
            file = info.get("file")
            present = bool(file and Path(file).is_file())
            stages[task] = {"state": info.get("state"),
                            "output_sha256": info.get("recorded") or (sha256_file(file) if present else None)}
            if present and task != "final:movie":
                media.append((Path(file), f"media/jobs/{Path(file).parent.parent.name}/{Path(file).name}"))
                seen.add(Path(file).resolve())
            elif not present and task != "final:movie" and info.get("state") == "verified":
                job = info.get("job")
                missing.append({"path": f"media/jobs/{job.name if job else 'unknown'}/{task.replace(':', '_').replace('>', '')}",
                                "sha256": "not found", "recorded_sha256": stages[task]["output_sha256"],
                                "kind": "image" if task.startswith("anchor:") else "video", "included": False})
        final = (stage_files.get("final:movie") or {}).get("file")
        for f in sorted(run.rglob("*")):
            if f.is_file() and f.suffix.lower() in MEDIA_EXT | WEIGHT_EXT and f.resolve() not in seen:
                media.append((f, f"media/run/{run.name}/{f.relative_to(run).as_posix()}"))
        desc["run"] = {"name": run.name, "plan_sha256": manifest.get("plan_sha256"),
                       "plan_matches_storyboard": manifest.get("plan_sha256") == plan["plan_sha256"],
                       "stages": stages,
                       "final": {"sha256": sha256_file(final) if final and Path(final).is_file() else None},
                       "redactions": redactions}

    audio_file = None
    if sb.audio.file:
        candidate = Path(sb.audio.file)
        audio_file = candidate if candidate.is_absolute() else root / candidate
    files = []
    for source, member in media:
        weights = source.suffix.lower() in WEIGHT_EXT
        if include_media and weights and source.is_file():
            raise PackageError(f"{source.name} is model weights; packages never bundle model weights")
        exists = source.is_file()
        files.append({"path": member, "sha256": sha256_file(source) if exists else "not found",
                      "kind": "weights" if weights else _kind(source), "included": include_media and exists})
        if include_media and exists:
            members[member] = source
    if audio_file is not None:
        exists = audio_file.is_file()
        member = f"media/audio/{audio_file.name}"
        files.append({"path": member, "sha256": sha256_file(audio_file) if exists else "not found",
                      "kind": "audio", "included": include_audio and exists})
        if include_audio and exists:
            members[member] = audio_file
    files += missing
    desc["media"] = {"included": include_media, "audio_included": include_audio and audio_file is not None,
                     "files": files}

    for name, source in members.items():
        if Path(name).suffix.lower() in WEIGHT_EXT:
            raise PackageError(f"{name} is model weights; packages never bundle model weights")
    members[DESCRIPTION] = _json_bytes(desc)
    payload = {n: (s if isinstance(s, bytes) else Path(s).read_bytes()) for n, s in sorted(members.items())}
    sums = {n: hashlib.sha256(b).hexdigest() for n, b in payload.items()}
    out.parent.mkdir(parents=True, exist_ok=True)
    part = out.with_name(out.name + ".part")
    try:
        with zipfile.ZipFile(part, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for name, data in payload.items():
                z.writestr(name, data)
            z.writestr(SUMS, json.dumps(sums, indent=1, sort_keys=True))
        os.replace(part, out)
    finally:
        part.unlink(missing_ok=True)
    return {"out": str(out), "members": len(payload) + 1, "bytes": out.stat().st_size,
            "plan_sha256": plan["plan_sha256"], "media_included": include_media,
            "excluded": sum(not f["included"] for f in files), "redactions": redactions}


# ------------------------------------------------------------------------------------- migrations

def _from_run_backup(d: dict) -> dict:
    """Format 0 (F20 ``run-backup`` archive) -> format 1 description."""
    m = d["run_manifest"]
    order = m.get("order") or list(m.get("stages", {}))
    storyboard = m.get("storyboard") or ""
    stages = {t: {"state": s.get("state"), "output_sha256": s.get("image_sha256") or s.get("video_sha256")}
              for t, s in m.get("stages", {}).items()}
    return {"format": 1, "kind": KIND, "migrated_from": 0,
            "storyboard": {"name": PurePosixPath(storyboard.replace("\\", "/")).stem or None,
                           "path": None, "sha256": m.get("storyboard_sha256")},
            "plan_sha256": m.get("plan_sha256"), "profiles": [], "style_packs": [], "models": [],
            "anchors": [t.split(":", 1)[1] for t in order if t.startswith("anchor:")], "stage_ids": list(order),
            "run": {"name": d["run_name"], "plan_sha256": m.get("plan_sha256"), "stages": stages},
            "media": {"included": None, "files": []}}


MIGRATIONS = {0: _from_run_backup}


def migrate(desc: dict, from_format: int) -> dict:
    """Upgrade a description step by step; the input is never modified and a failing step is named."""
    current, version = copy.deepcopy(desc), from_format
    while version < FORMAT:
        step = MIGRATIONS.get(version)
        if step is None:
            raise PackageError(f"no migration from format {version}")
        try:
            current = step(copy.deepcopy(current))
        except Exception as exc:  # noqa: BLE001 - any failure aborts the whole migration
            raise PackageError(f"migration step {version}->{version + 1} failed: {exc}") from exc
        version += 1
    return current


# ------------------------------------------------------------------------------------- inspection

def _verify(z: zipfile.ZipFile, info: zipfile.ZipInfo) -> str:
    digest, read = hashlib.sha256(), 0
    with z.open(info) as stream:
        while chunk := stream.read(_CHUNK):
            read += len(chunk)
            if read > info.file_size:
                raise PackageError(f"{info.filename} expands beyond its declared size")
            digest.update(chunk)
    return digest.hexdigest()


def _inspect(path: str | Path) -> tuple[dict, dict | None]:
    report: dict = {"package": str(path), "ok": False, "format": None, "kind": None, "problems": [],
                    "summary": {}}
    problems = report["problems"]
    try:
        z = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as exc:
        problems.append(f"not a valid zip file: {exc}")
        return report, None
    desc = None
    with z:
        infos = [i for i in z.infolist() if not i.is_dir()]
        names = [i.filename for i in infos]
        if len(infos) > MAX_MEMBERS:
            problems.append(f"too many members: {len(infos)} > {MAX_MEMBERS}")
            return report, None
        for name in names:
            if _unsafe_name(name):
                problems.append(f"unsafe member name: {name!r}")
        if len(set(names)) != len(names):
            problems.append("duplicate member names: " + ", ".join(sorted({n for n in names if names.count(n) > 1})))
        lowered: dict[str, str] = {}
        for name in set(names):
            if name.lower() in lowered:
                problems.append(f"member names differ only by case: {lowered[name.lower()]}, {name}")
            lowered[name.lower()] = name
        non_media = sum(i.file_size for i in infos if PurePosixPath(i.filename).suffix.lower() not in MEDIA_EXT)
        total = sum(i.file_size for i in infos)
        if non_media > MAX_NON_MEDIA:
            problems.append(f"would expand to {non_media} bytes of non-media files (limit {MAX_NON_MEDIA})")
        if total > MAX_TOTAL:
            problems.append(f"would expand to {total} bytes in total (limit {MAX_TOTAL})")
        for i in infos:
            if i.file_size > RATIO_MIN_BYTES and i.file_size / max(i.compress_size, 1) > MAX_RATIO:
                problems.append(f"{i.filename}: compression ratio above {MAX_RATIO}:1 (possible archive bomb)")
        if problems:
            return report, None
        if SUMS not in names:
            problems.append(f"no checksum list ({SUMS})")
            return report, None
        try:
            sums = json.loads(z.read(SUMS))
        except ValueError:
            problems.append("checksum list is not valid JSON")
            return report, None
        if set(sums) != set(names) - {SUMS}:
            problems.append("members do not match the checksum list")
            return report, None
        for info in infos:
            if info.filename == SUMS:
                continue
            try:
                if _verify(z, info) != sums[info.filename]:
                    problems.append(f"checksum mismatch: {info.filename}")
            except (PackageError, zipfile.BadZipFile, OSError) as exc:
                problems.append(f"cannot read {info.filename}: {exc}")
        if problems:
            return report, None
        if DESCRIPTION in names:
            try:
                desc = json.loads(z.read(DESCRIPTION))
            except ValueError:
                problems.append(f"{DESCRIPTION} is not valid JSON")
                return report, None
            fmt = desc.get("format")
        elif any(n.startswith("run/") and n.endswith("/manifest.json") for n in names):
            member = next(n for n in names if n.startswith("run/") and n.endswith("/manifest.json"))
            desc = {"format": 0, "run_name": PurePosixPath(member).parts[1],
                    "run_manifest": json.loads(z.read(member))}
            fmt = 0
        else:
            problems.append(f"no {DESCRIPTION}; not a MorphCurrent package")
            return report, None
        media_included = any(PurePosixPath(n).suffix.lower() in MEDIA_EXT for n in names)
    if not isinstance(fmt, int) or fmt < 0:
        problems.append(f"unknown package format {fmt!r}")
        return report, None
    if fmt > FORMAT:
        problems.append(f"package format {fmt} is from a newer MorphCurrent (this one reads up to {FORMAT})")
        return report, None
    if fmt < FORMAT:
        try:
            desc = migrate(desc, fmt)
        except PackageError as exc:
            problems.append(str(exc))
            return report, None
        report["migrated_from"] = fmt
    if desc.get("kind") != KIND:
        problems.append(f"{DESCRIPTION} kind is {desc.get('kind')!r}, expected {KIND!r}")
    for label, key in (("anchor", "anchors"), ("stage", "stage_ids")):
        ids = desc.get(key) or []
        dups = sorted({i for i in ids if ids.count(i) > 1})
        if dups:
            problems.append(f"duplicate {label} ids: {', '.join(map(str, dups))}")
    for found in absolute_paths(desc):
        problems.append(f"absolute local path in {DESCRIPTION}: {found}")
    report.update(format=desc.get("format"), kind=desc.get("kind"),
                  summary={"members": len(names), "expanded_bytes": total, "media_included": media_included,
                           "storyboard": (desc.get("storyboard") or {}).get("name"),
                           "plan_sha256": desc.get("plan_sha256"), "run": (desc.get("run") or {}).get("name"),
                           "models_bundled": False})
    report["ok"] = not problems
    return report, desc


def inspect_package(path: str | Path) -> dict:
    """Verify a package without writing anything; ``ok`` is False with reasons when unsafe or corrupt."""
    return _inspect(path)[0]


# ----------------------------------------------------------------------------------------- import

def import_project(path: str | Path, dest: str | Path, *, models_root: str | Path | None = None) -> dict:
    """Restore a verified package into a new (or empty) folder, then report replay readiness."""
    report, desc = _inspect(path)
    if not report["ok"]:
        raise PackageError("package failed inspection: " + "; ".join(report["problems"]))
    dest = Path(dest)
    if dest.is_file():
        raise PackageError(f"destination {dest} is a file")
    if dest.exists() and any(dest.iterdir()):
        raise PackageError(f"destination {dest} is not empty; import never overwrites")
    dest.parent.mkdir(parents=True, exist_ok=True)
    staging = dest.parent / f".{dest.name}.import-{secrets.token_hex(4)}"
    try:
        staging.mkdir()
        base = staging.resolve()
        with zipfile.ZipFile(path) as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                target = (staging / info.filename).resolve()
                if base not in target.parents:
                    raise PackageError(f"member {info.filename!r} would write outside the destination")
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst, _CHUNK)
        recreate = dest.exists()
        if recreate:
            dest.rmdir()
        try:
            os.replace(staging, dest)
        except OSError:
            if recreate:
                dest.mkdir(exist_ok=True)  # leave the owner's empty folder as it was
            raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return readiness(dest, desc, models_root=models_root, migrated_from=report.get("migrated_from"))


def readiness(dest: Path, desc: dict, *, models_root: str | Path | None = None,
              migrated_from: int | None = None) -> dict:
    """Re-plan from the restored files and list workflow statuses and missing models (no inference)."""
    from .dag import compile_plan
    from .registry import build_registry
    from .schema import load_storyboard
    recompiled = None
    sb_rel = (desc.get("storyboard") or {}).get("path")
    if sb_rel and (dest / sb_rel).is_file():
        raw = (dest / sb_rel).read_bytes()
        recompiled = compile_plan(load_storyboard(dest / sb_rel), profiles=desc.get("profile_overrides"),
                                  repo_root=dest, storyboard_bytes=raw)["plan_sha256"]
    entries = build_registry(dest / "configs" / "profiles", repo_root=dest, models_root=models_root) \
        if (dest / "configs" / "profiles").is_dir() else []
    missing = sorted({f"{m['folder']}/{m['file']}" for e in entries for m in e["models"] if m["present"] is False})
    return {"dest": str(dest), "restored_files": sum(1 for f in dest.rglob("*") if f.is_file()),
            "migrated_from": migrated_from, "plan_sha256_recorded": desc.get("plan_sha256"),
            "plan_sha256_recompiled": recompiled,
            "plan_matches": (recompiled == desc.get("plan_sha256")) if recompiled else None,
            "profiles": [{"path": e["path"], "status": e["status"]} for e in entries],
            "missing_models": missing,
            "note": "Missing models need owner approval to download; nothing was downloaded and no inference ran."}
