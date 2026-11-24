"""Versioned style packs with inheritance, overrides and private asset references (F21).

A style pack (``configs/styles/<id>.yaml``) captures a reusable visual language:
description, palette, lighting, lens, composition, materials, negative terms, an
advisory size and optional reference assets kept in a local, gitignored library.
Packs resolve parent-first; scalar fields override, ``negative`` merges without
duplicates, ``palette`` replaces. Style text is *appended* to artist prompts — prompts
are never rewritten — and the resolved pack's SHA-256 joins the plan identity.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .cache import sha256_file

DEFAULT_DIR = Path("configs/styles")
DEFAULT_LIBRARY = Path("library")
TEXT_FIELDS = ("lighting", "lens", "composition", "materials")


class StyleError(ValueError):
    pass


class ReferenceAsset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    license: str = Field(min_length=1)
    note: str | None = None


class StyleFields(BaseModel):
    """Fields a pack defines and an anchor may override."""
    model_config = ConfigDict(extra="forbid")
    description: str | None = None
    palette: list[str] | None = None
    lighting: str | None = None
    lens: str | None = None
    composition: str | None = None
    materials: str | None = None
    negative: list[str] | None = None


class StylePack(StyleFields):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,62}$")
    version: int = Field(ge=1)
    extends: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9-]{0,62}$")
    size: list[int] | None = Field(default=None, min_length=2, max_length=2)
    reference_assets: list[ReferenceAsset] = Field(default_factory=list)


def load_pack(pack_id: str, styles_dir: str | Path = DEFAULT_DIR) -> StylePack:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", pack_id or ""):
        raise StyleError(f"invalid style pack id {pack_id!r} (lower-case slug expected)")
    path = Path(styles_dir) / f"{pack_id}.yaml"
    if not path.is_file():
        raise StyleError(f"style pack {pack_id!r} not found in {styles_dir}")
    pack = StylePack.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    if pack.id != pack_id:
        raise StyleError(f"{path.name} declares id {pack.id!r}")
    return pack


def _merge(base: dict, top: dict) -> dict:
    out = dict(base)
    for key, value in top.items():
        if value is None:
            continue
        if key == "negative":
            merged = list(out.get("negative") or [])
            for term in value:
                if term.strip().lower() not in [m.strip().lower() for m in merged]:
                    merged.append(term)
            out["negative"] = merged
        else:
            out[key] = value
    return out


def resolve_pack(pack_id: str, styles_dir: str | Path = DEFAULT_DIR) -> dict:
    """Parent-first resolution; returns the flattened pack with its lineage and SHA-256."""
    chain, seen, current = [], set(), pack_id
    while current:
        if current in seen:
            raise StyleError(f"style pack inheritance cycle: {' -> '.join([*chain_ids(chain), current])}")
        seen.add(current)
        pack = load_pack(current, styles_dir)
        chain.append(pack)
        current = pack.extends
    resolved: dict = {}
    for pack in reversed(chain):
        fields = pack.model_dump(include=set(StyleFields.model_fields))
        resolved = _merge(resolved, fields)
        if pack.reference_assets:
            resolved["reference_assets"] = [a.model_dump() for a in pack.reference_assets]
        if pack.size:
            resolved["size"] = pack.size
    resolved["lineage"] = [f"{p.id}@v{p.version}" for p in reversed(chain)]
    resolved["sha256"] = pack_sha256(resolved)
    return resolved


def chain_ids(chain: list[StylePack]) -> list[str]:
    return [p.id for p in chain]


def pack_sha256(resolved: dict) -> str:
    body = {k: v for k, v in resolved.items() if k != "sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def apply_override(resolved: dict, override: dict | None) -> dict:
    if not override:
        return resolved
    fields = StyleFields.model_validate(override).model_dump()
    out = _merge(resolved, fields)
    out["sha256"] = pack_sha256(out)
    return out


def style_text(resolved: dict) -> str:
    """Deterministic style clause appended after the artist's prompt."""
    parts = []
    if resolved.get("description"):
        parts.append(" ".join(resolved["description"].split()).rstrip(".") + ".")
    details = []
    if resolved.get("palette"):
        details.append("palette: " + ", ".join(resolved["palette"]))
    for key in TEXT_FIELDS:
        if resolved.get(key):
            details.append(f"{key}: {' '.join(resolved[key].split())}")
    if details:
        parts.append("; ".join(details)[:1].upper() + "; ".join(details)[1:] + ".")
    return " ".join(parts)


def negative_text(resolved: dict, anchor_negative: str | None) -> str | None:
    terms = [t.strip() for t in (anchor_negative or "").split(",") if t.strip()]
    for term in resolved.get("negative") or []:
        if term.lower() not in [t.lower() for t in terms]:
            terms.append(term)
    return ", ".join(terms) or None


def _safe_relative(path: str) -> bool:
    for flavour in (PurePosixPath(path), PureWindowsPath(path)):
        if flavour.is_absolute() or flavour.drive or ".." in flavour.parts:
            return False
    return True


def check_assets(resolved: dict, library: str | Path = DEFAULT_LIBRARY) -> list[dict]:
    """Read-only status of each reference asset: ok / missing / changed / unsafe."""
    root = Path(library)
    out = []
    for asset in resolved.get("reference_assets") or []:
        entry = {"path": asset["path"], "license": asset["license"]}
        if not _safe_relative(asset["path"]):
            entry["status"] = "unsafe path (must be relative to the library, no '..')"
        else:
            target = root / asset["path"]
            if not target.is_file():
                entry["status"] = "missing"
            elif sha256_file(target) != asset["sha256"]:
                entry["status"] = "changed (sha256 mismatch)"
            else:
                entry["status"] = "ok"
        out.append(entry)
    return out


def list_packs(styles_dir: str | Path = DEFAULT_DIR) -> list[dict]:
    out = []
    for path in sorted(Path(styles_dir).glob("*.yaml")):
        try:
            pack = StylePack.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
            out.append({"id": pack.id, "version": pack.version, "extends": pack.extends,
                        "description": (pack.description or "")[:80]})
        except Exception as exc:  # report broken files instead of hiding them
            out.append({"file": path.name, "error": str(exc)[:200]})
    return out
