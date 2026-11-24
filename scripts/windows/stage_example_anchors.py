"""Stage only reviewed example FLF2V anchors into ComfyUI Portable input.

Usage from Windows Command Prompt:
    python scripts\windows\stage_example_anchors.py --install-root C:\AI\ComfyUI_windows_portable --dry-run
    python scripts\windows\stage_example_anchors.py --install-root C:\AI\ComfyUI_windows_portable

No external downloads, shell execution, model installs or GPU inference.
Existing different files require --overwrite.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

ANCHORS = ("01_glass_orchid.jpg", "02_metallic_butterfly.jpg")


def _same_contents(a: Path, b: Path) -> bool:
    if a.stat().st_size != b.stat().st_size:
        return False
    return hashlib.sha256(a.read_bytes()).digest() == hashlib.sha256(b.read_bytes()).digest()


def stage(install_root: Path, *, dry_run: bool = False, overwrite: bool = False) -> list[str]:
    repo_root = Path(__file__).resolve().parents[2]
    source = repo_root / "assets" / "anchors"
    root = install_root.expanduser().resolve()
    comfy = root / "ComfyUI"
    if not (comfy / "main.py").is_file():
        raise FileNotFoundError(
            f"ComfyUI Portable main.py was not found at {comfy / 'main.py'}; "
            "pass the actual extraction root"
        )
    destination = comfy / "input"
    actions: list[tuple[Path, Path, bool]] = []
    # Full preflight: do not partially stage a set if one destination conflicts.
    for name in ANCHORS:
        src = source / name
        dst = destination / name
        if not src.is_file():
            raise FileNotFoundError(f"Reviewed sample image missing: {src}")
        same = dst.is_file() and _same_contents(src, dst)
        if dst.exists() and not same and not overwrite:
            raise FileExistsError(
                f"Different file exists at {dst}; inspect first or explicitly use --overwrite"
            )
        actions.append((src, dst, same))
    result = []
    if not dry_run:
        destination.mkdir(parents=True, exist_ok=True)
    for src, dst, same in actions:
        if same:
            status = "unchanged"
        elif dry_run:
            status = "would copy"
        else:
            shutil.copy2(src, dst)
            status = "copied"
        result.append(f"{status}: {dst}")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage reviewed first/last-frame sample images")
    parser.add_argument("--install-root", type=Path, required=True, help="ComfyUI Portable extraction root")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true", help="Explicitly replace conflicting sample filenames")
    args = parser.parse_args(argv)
    try:
        for line in stage(args.install_root, dry_run=args.dry_run, overwrite=args.overwrite):
            print(line)
        return 0
    except (OSError, ValueError) as exc:
        print(f"Cannot stage anchors: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
