"""ffprobe inspection of rendered clips (native Windows binary, argument arrays only)."""
from __future__ import annotations

import json
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path


class ImageInvalid(ValueError):
    """Downloaded or supplied anchor bytes are not a complete PNG/JPEG image."""


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def inspect_image(path: str | Path) -> dict:
    """Structural PNG/JPEG check (stdlib only): format, width, height.

    PNG: every chunk's length bound and CRC32, IHDR first, IEND last.
    JPEG: SOI, a SOFn segment with dimensions, EOI at the end.
    Detects truncated or corrupted files; it does not judge image content.
    """
    data = Path(path).read_bytes()
    if data.startswith(_PNG_SIGNATURE):
        return _inspect_png(data)
    if data.startswith(b"\xff\xd8"):
        return _inspect_jpeg(data)
    raise ImageInvalid(f"{Path(path).name}: not a PNG or JPEG file")


def _inspect_png(data: bytes) -> dict:
    import struct
    import zlib
    pos, chunks, size = 8, [], None
    while pos < len(data):
        if pos + 12 > len(data):
            raise ImageInvalid("PNG truncated inside a chunk header")
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        end = pos + 12 + length
        if end > len(data):
            raise ImageInvalid(f"PNG chunk {kind!r} truncated")
        body = data[pos + 8:pos + 8 + length]
        (crc,) = struct.unpack(">I", data[pos + 8 + length:end])
        if zlib.crc32(kind + body) & 0xFFFFFFFF != crc:
            raise ImageInvalid(f"PNG chunk {kind!r} CRC mismatch")
        if kind == b"IHDR":
            size = struct.unpack(">II", body[:8])
        chunks.append(kind)
        pos = end
        if kind == b"IEND":
            break
    if not chunks or chunks[0] != b"IHDR" or chunks[-1] != b"IEND" or size is None:
        raise ImageInvalid("PNG must start with IHDR and end with IEND")
    if b"IDAT" not in chunks:
        raise ImageInvalid("PNG has no image data")
    return {"format": "png", "width": size[0], "height": size[1]}


def _inspect_jpeg(data: bytes) -> dict:
    import struct
    if not data.rstrip(b"\x00").endswith(b"\xff\xd9"):
        raise ImageInvalid("JPEG truncated (no EOI marker)")
    pos = 2
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            raise ImageInvalid("JPEG segment marker expected")
        marker = data[pos + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        (length,) = struct.unpack(">H", data[pos + 2:pos + 4])
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            if pos + 9 > len(data):
                raise ImageInvalid("JPEG SOF truncated")
            height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            if not width or not height:
                raise ImageInvalid("JPEG has zero dimension")
            return {"format": "jpeg", "width": width, "height": height}
        if marker == 0xDA:
            break
        pos += 2 + length
    raise ImageInvalid("JPEG has no SOF segment before scan data")


def contact_sheet(images: list[Path], output: Path, *, height: int = 240,
                  ffmpeg: str | None = None, timeout: float = 120) -> Path:
    """Side-by-side PNG of ``images`` scaled to one height (review aid; never overwrites)."""
    executable = ffmpeg or shutil.which("ffmpeg")
    if not executable:
        raise ProbeUnavailable("ffmpeg not found on PATH")
    if len(images) < 2:
        raise ValueError("contact sheet needs at least two images")
    if output.exists():
        raise FileExistsError(output)
    args = [executable, "-hide_banner", "-nostdin", "-v", "error", "-n"]
    for image in images:
        args += ["-i", str(image)]
    chains = [f"[{i}:v]scale=-2:{height},format=rgb24[s{i}]" for i in range(len(images))]
    graph = ";".join(chains) + ";" + "".join(f"[s{i}]" for i in range(len(images))) \
        + f"hstack=inputs={len(images)}[out]"
    args += ["-filter_complex", graph, "-map", "[out]", "-frames:v", "1", str(output)]
    output.parent.mkdir(parents=True, exist_ok=True)
    done = subprocess.run(args, capture_output=True, text=True, errors="replace",
                          timeout=timeout, shell=False, check=False)
    if done.returncode != 0:
        raise RuntimeError(f"ffmpeg contact sheet failed: {done.stderr.strip()[:500]}")
    return output


class ProbeUnavailable(RuntimeError):
    """ffprobe is not on PATH; verification must be reported as skipped, not passed."""


def probe_video(path: str | Path, *, ffprobe: str | None = None, timeout: float = 120) -> dict:
    """Return width, height, decoded frame count, fps and codec of the first video stream."""
    executable = ffprobe or shutil.which("ffprobe")
    if not executable:
        raise ProbeUnavailable("ffprobe not found on PATH")
    args = [executable, "-v", "error", "-select_streams", "v:0", "-count_frames",
            "-show_entries", "stream=width,height,r_frame_rate,avg_frame_rate,nb_read_frames,codec_name",
            "-show_entries", "format=duration", "-of", "json", str(path)]
    completed = subprocess.run(args, capture_output=True, text=True, errors="replace",
                               timeout=timeout, shell=False, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"ffprobe failed ({completed.returncode}): {completed.stderr.strip()[:500]}")
    payload = json.loads(completed.stdout or "{}")
    streams = payload.get("streams") or []
    if not streams:
        raise RuntimeError(f"no video stream in {path}")
    stream = streams[0]
    rate = stream.get("r_frame_rate") or stream.get("avg_frame_rate") or "0/1"
    frames = stream.get("nb_read_frames")
    duration = (payload.get("format") or {}).get("duration")
    return {
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "frame_count": int(frames) if frames not in (None, "N/A") else None,
        "fps": float(Fraction(rate)) if rate != "0/0" else None,
        "codec": stream.get("codec_name"),
        "duration_s": float(duration) if duration not in (None, "N/A") else None,
    }
