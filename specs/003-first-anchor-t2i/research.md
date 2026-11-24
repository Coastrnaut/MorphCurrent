# Research — F03

- **Image integrity without Pillow** — Decision: PNG: 8-byte signature, walk every chunk verifying length bounds and CRC32 (`zlib.crc32`), require IHDR first and IEND last; JPEG: SOI, parse segments to SOF0–SOF15 (excluding DHT/JPG/DAC markers C4/C8/CC) for dimensions, require EOI at end. Rationale: detects truncation/corruption of ComfyUI `SaveImage` PNG output; no new dependency. Alternative: Pillow (new dependency) or ffmpeg decode (heavier) — rejected for now.
- **Shared executor** — Decision: generalise `bridge` functions (already generic over `job.record` and `plan.graph`). Alternative: copy into `anchors.py` — rejected (two crash-recovery implementations to keep correct).
- **Expected dimensions** — taken from bound `width`/`height` values when the profile binds them; otherwise measured only (edit graphs may rescale via `FluxKontextImageScale`).
- **History output shape** — `SaveImage` in ComfyUI reports `outputs[node]["images"] = [{filename, subfolder, type: "output"}]`; existing `extract_outputs` already reads it.
