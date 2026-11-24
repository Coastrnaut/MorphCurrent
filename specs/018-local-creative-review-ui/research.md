# Research: F18 local review experience

## R1 Display surface (the ledger requires a design review)
- **Decision**: a strictly-loopback page served by the stdlib HTTP server and viewed in the local browser.
- **Rationale**: review means watching H.264 MP4 clips and PNGs; browsers play them natively, with seeking. Tk, the only stdlib GUI, cannot play video without new packages.
- **Alternatives**: Tk + launching an external player (clunky, no in-place view); Qt/PySide6 (large new dependency, LGPL packaging); FastAPI/Flask (new dependencies for no gain).

## R2 Threat model and controls
| Threat | Control |
|---|---|
| Remote network access | bind only 127.0.0.1 / ::1 / localhost; refuse others at startup |
| DNS rebinding | reject requests whose Host is not a loopback name |
| CSRF from other sites | per-process random form token (constant-time compare) + Origin must be loopback when present |
| Path traversal / arbitrary file read | media served only via opaque token from an allowlist built from the run's own manifest and job records, resolved inside the runs root |
| Markup/script injection via storyboard text | `html.escape` everything; CSP `default-src 'self'`; no scripts; `nosniff`; `X-Frame-Options: DENY` |
| Involuntary rendering | handler imports no ComfyUI client or render code |
| Oversized posts | 10 kB form limit; note ≤ 500 chars |

## R3 Video seeking
- **Decision**: single-range `Range: bytes=` responses (206/416); browsers need them to scrub MP4 reliably.

## R4 Locating media
- **Decision**: resolve job dirs as `runs_root / basename(job_dir)` (manifests store cwd-relative paths such as `outputs\runs\<id>`); media path from `job.json` (`image.local_path`, or the `video` output's `local_path`).

## R5 Concurrency with the CLI
- **Decision**: reuse `qa.record_review` (temp file + `os.replace`); last write wins; pages re-read on every request.
