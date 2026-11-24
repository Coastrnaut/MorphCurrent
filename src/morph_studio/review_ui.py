"""Strictly-loopback local review UI (F18). Stdlib only; never renders or contacts ComfyUI.

Pages: ``/`` runs index, ``/run/<run>`` stages/previews/QA/reviews, ``/plan?i=<n>`` read-only plan.
``POST /run/<run>/review`` writes the same ``review.json`` entry as ``morphcurrent review``.
Media is served only by opaque token from an allowlist derived from the run manifest.
Security design review: specs/018-local-creative-review-ui/plan.md.
"""
from __future__ import annotations

import hashlib
import html
import json
import mimetypes
import re
import secrets
import socket
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .qa import load_reviews, record_review
from .run_manifest import RunManifest

LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}
RUN_NAME = re.compile(r"^run-[0-9a-f]{8,64}$")
DECISIONS = ("approved", "rejected", "pending")
CSP = "default-src 'self'; img-src 'self'; media-src 'self'; style-src 'unsafe-inline'; form-action 'self'"
STYLE = """body{font:15px/1.45 system-ui,sans-serif;margin:16px auto;max-width:1100px;padding:0 16px;
color:#1d1d1f;background:#fafafa}h1,h2{font-weight:600}table{border-collapse:collapse;width:100%}
td,th{border-bottom:1px solid #ddd;padding:6px;text-align:left;vertical-align:top}
.flag{color:#a40000;font-weight:600}.ok{color:#0a6b2d}img,video{max-width:100%;height:auto;background:#000}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
button{font:inherit;padding:4px 10px;margin-right:4px}button:focus,a:focus,input:focus{outline:3px solid #0050c8}
.note{color:#555}code{background:#eee;padding:1px 4px}"""


class UiError(ValueError):
    pass


def e(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _token(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:24]


def _job_dir(runs_root: Path, job_dir: str | None) -> Path | None:
    if not job_dir:
        return None
    return runs_root / Path(job_dir.replace("\\", "/")).name  # job dirs always live in the runs root


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _job_media(job_dir: Path | None) -> Path | None:
    if job_dir is None or not (job_dir / "job.json").is_file():
        return None
    try:
        record = json.loads((job_dir / "job.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    local = (record.get("image") or {}).get("local_path")
    if not local:
        local = next((o.get("local_path") for o in record.get("outputs", []) if o.get("kind") == "video"), None)
    return job_dir / Path(local.replace("\\", "/")) if local else None


def run_view(runs_root: str | Path, run_name: str) -> dict:
    """Everything the run page shows, plus the media allowlist (token -> path)."""
    root = Path(runs_root)
    if not RUN_NAME.match(run_name) or not (root / run_name / "manifest.json").is_file():
        raise UiError(f"no such run: {run_name}")
    manifest = RunManifest.load(root / run_name)
    data = manifest.data
    reviews = load_reviews(manifest.dir / "review.json")
    media: dict[str, Path] = {}

    def allow(path: Path | None) -> str | None:
        if path is None or not path.is_file() or not _inside(root, path):
            return None
        token = _token(path)
        media[token] = path.resolve()
        return token

    stages = []
    for task_id in data.get("order", list(data.get("stages", {}))):
        stage = data["stages"].get(task_id, {})
        kind = task_id.split(":", 1)[0]
        path = _job_media(_job_dir(root, stage.get("job_dir"))) if kind in ("anchor", "bridge") else None
        stages.append({"task": task_id, "kind": kind, "state": stage.get("state", "pending"),
                       "qa": stage.get("qa"), "qa_flags": stage.get("qa_flags") or [],
                       "reason": stage.get("reason"),
                       "media": allow(path), "media_missing": kind in ("anchor", "bridge")
                       and stage.get("state") == "verified" and allow(path) is None,
                       "review": reviews.get(task_id)})
    sheet = data.get("contact_sheet")
    final = (data.get("final") or {}).get("output")
    final_file = None
    if final:  # manifests store cwd-relative paths; the movie always lives in <run>/final/
        name = Path(final.replace("\\", "/")).name
        final_file = manifest.dir / "final" / name
    return {"run": run_name, "status": data.get("status"), "storyboard": data.get("storyboard"),
            "plan_sha256": data.get("plan_sha256"), "stages": stages,
            "contact_sheet": allow(manifest.dir / "anchors_contact_sheet.png") if sheet else None,
            "final": allow(final_file), "final_path": final,
            "budget_note": "GPU actions are not available here: re-run the render command from the CLI.",
            "media": media}


def list_runs(runs_root: str | Path) -> list[dict]:
    root = Path(runs_root)
    rows = []
    if root.is_dir():
        for d in sorted(root.iterdir()):
            if RUN_NAME.match(d.name) and (d / "manifest.json").is_file():
                try:
                    m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                rows.append({"run": d.name, "storyboard": m.get("storyboard"), "status": m.get("status"),
                             "created_at": m.get("created_at")})
    return rows


def _page(title: str, body: str) -> str:
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'><title>{e(title)}</title>"
            f"<style>{STYLE}</style></head><body><nav><a href='/'>Runs</a></nav>{body}</body></html>")


def render_index(runs: list[dict], storyboards: list[str]) -> str:
    rows = "".join(f"<tr><td><a href='/run/{e(r['run'])}'>{e(r['run'])}</a></td><td>{e(r['storyboard'])}</td>"
                   f"<td>{e(r['status'])}</td><td>{e(r['created_at'])}</td></tr>" for r in runs)
    plans = "".join(f"<li><a href='/plan?i={i}'>{e(s)}</a></li>" for i, s in enumerate(storyboards))
    return _page("MorphCurrent review", "<h1>MorphCurrent local review</h1>"
                 "<p class=note>Loopback only. Nothing here renders or contacts ComfyUI.</p>"
                 f"<h2>Runs</h2><table><tr><th>Run</th><th>Storyboard</th><th>Status</th><th>Created</th></tr>"
                 f"{rows or '<tr><td colspan=4>No runs yet.</td></tr>'}</table>"
                 + (f"<h2>Storyboard plans</h2><ul>{plans}</ul>" if plans else ""))


def render_run_page(view: dict, csrf: str, message: str = "") -> str:
    run = view["run"]
    parts = [f"<h1>Run {e(run)}</h1>",
             f"<p>Storyboard <code>{e(view['storyboard'])}</code> · status <strong>{e(view['status'])}</strong>"
             f" · plan <code>{e((view['plan_sha256'] or '')[:12])}</code></p>",
             f"<p class=note>{e(view['budget_note'])}</p>"]
    if message:
        parts.append(f"<p role=status><strong>{e(message)}</strong></p>")
    if view["contact_sheet"]:
        parts.append(f"<h2>Anchors contact sheet</h2><img src='/media/{e(run)}/{view['contact_sheet']}' "
                     "alt='Anchor contact sheet'>")
    anchors = [s for s in view["stages"] if s["kind"] == "anchor"]
    if anchors:
        cells = "".join(
            f"<figure><figcaption>{e(s['task'])} — {e(s['state'])}</figcaption>"
            + (f"<img src='/media/{e(run)}/{s['media']}' alt='{e(s['task'])}'>" if s["media"]
               else f"<p class=flag>{'media missing' if s['media_missing'] else 'not generated'}</p>")
            + "</figure>" for s in anchors)
        parts.append(f"<h2>Anchors</h2><div class=grid>{cells}</div>")
    for s in (x for x in view["stages"] if x["kind"] == "bridge"):
        flags = ", ".join(map(str, s["qa_flags"]))
        review = s["review"] or {}
        buttons = "".join(f"<button type=submit name=decision value={d}>{d.capitalize()}</button>"
                          for d in DECISIONS)
        parts.append(
            f"<section aria-label='{e(s['task'])}'><h2>{e(s['task'])}</h2>"
            f"<p>State {e(s['state'])} · QA "
            + (f"<span class=flag>{e(flags)}</span>" if flags else f"<span class=ok>{e(s['qa'] or 'not run')}</span>")
            + f" · review <strong>{e(review.get('decision', 'none'))}</strong> {e(review.get('note', ''))}</p>"
            + (f"<video controls preload=metadata src='/media/{e(run)}/{s['media']}' "
               f"aria-label='{e(s['task'])} clip'></video>" if s["media"]
               else f"<p class=flag>{'clip missing' if s['media_missing'] else 'not generated'}</p>")
            + f"<form method=post action='/run/{e(run)}/review'>"
            f"<input type=hidden name=csrf value='{e(csrf)}'><input type=hidden name=task value='{e(s['task'])}'>"
            f"<label>Note <input name=note maxlength=500 size=40></label> {buttons}</form></section>")
    if view["final"]:
        parts.append(f"<h2>Final movie</h2><video controls preload=metadata src='/media/{e(run)}/{view['final']}'"
                     " aria-label='Final movie'></video>")
    elif view["final_path"]:
        parts.append("<h2>Final movie</h2><p class=flag>final movie missing on disk</p>")
    blocked = [s for s in view["stages"] if s["reason"]]
    if blocked:
        parts.append("<h2>Blocked</h2><ul>" + "".join(f"<li>{e(s['task'])}: {e(s['reason'])}</li>"
                                                     for s in blocked) + "</ul>")
    return _page(f"Run {run}", "".join(parts))


def plan_summary(storyboard_path: str | Path, repo_root: str | Path = ".") -> dict:
    from .dag import compile_plan
    from .longform import chapter_index
    from .perf import estimate, load_history
    from .schema import load_storyboard
    sb = load_storyboard(storyboard_path)
    plan = compile_plan(sb, repo_root=repo_root)
    history_file = Path(repo_root) / "configs" / "perf_history.json"
    est = estimate(plan, load_history(history_file)) if history_file.is_file() else {}
    return {"storyboard": sb, "plan": plan, "index": chapter_index(sb, plan), "estimate": est}


def render_plan_page(summary: dict) -> str:
    sb, plan, index, est = summary["storyboard"], summary["plan"], summary["index"], summary["estimate"]
    times = {a["anchor"]: a for a in index["anchors"]}
    anchors = "".join(
        f"<tr><td>{e(a.id)}</td><td>{e(a.chapter)}</td><td>{e(times[a.id]['time_s'])} s</td>"
        f"<td>{e(a.generation)}{(' ← ' + e(a.reference)) if a.reference else ''}</td>"
        f"<td>{e(plan['tasks']['anchor:' + a.id]['positive_prompt'])}</td>"
        f"<td>{e(plan['tasks']['anchor:' + a.id].get('negative_prompt'))}</td></tr>" for a in sb.anchors)
    bridges = "".join(
        f"<tr><td>{e(t['id'])}</td><td>{e(t['frames'])}</td><td>{e(t['anchor_span_seconds'])} s</td>"
        f"<td>{e(t['candidates'])}</td><td>{e(t['positive_prompt'])}</td></tr>"
        for t in (plan["tasks"][k] for k in plan["order"]) if t["kind"] == "bridge")
    profiles = "".join(f"<li>{e(cap)}: <code>{e(req['profile'])}</code> "
                       + ("<span class=ok>present</span>" if req["exists"] else "<span class=flag>missing</span>")
                       + "</li>" for cap, req in plan["requirements"].items())
    total = est.get("total_gpu_s")
    return _page(f"Plan {sb.name}", f"<h1>Plan: {e(sb.name)}</h1>"
                 f"<p>{len(sb.anchors)} anchors · {len(sb.transitions)} bridges · {e(index['duration_s'])} s · "
                 f"plan <code>{e(plan['plan_sha256'][:12])}</code> · estimated GPU "
                 f"{e(round(total) if total else 'NO DATA')} s ({e(est.get('label', 'NO DATA'))})</p>"
                 "<p class=note>Read-only. Edit the storyboard YAML, then run <code>morphcurrent render "
                 "--dry-run</code>; rendering needs the CLI and <code>--confirm-gpu</code>.</p>"
                 f"<h2>Profiles</h2><ul>{profiles}</ul>"
                 "<h2>Anchors</h2><table><tr><th>Id</th><th>Chapter</th><th>Time</th><th>Method</th>"
                 f"<th>Prompt</th><th>Negative</th></tr>{anchors}</table>"
                 "<h2>Transitions</h2><table><tr><th>Bridge</th><th>Frames</th><th>Span</th>"
                 f"<th>Candidates</th><th>Prompt</th></tr>{bridges}</table>")


def apply_review(runs_root: str | Path, run_name: str, task: str, decision: str, note: str = "") -> dict:
    """Validated UI review: same file and entry format as ``morphcurrent review``."""
    view = run_view(runs_root, run_name)
    bridges = {s["task"] for s in view["stages"] if s["kind"] == "bridge"}
    if task not in bridges:
        raise UiError(f"{task!r} is not a bridge of {run_name}")
    if decision not in DECISIONS:
        raise UiError("decision must be approved, rejected or pending")
    return record_review(Path(runs_root) / run_name / "review.json", task, decision, note[:500])


def make_handler(runs_root: str | Path, storyboards: list[str] | None = None, repo_root: str | Path = ".",
                 csrf: str | None = None):
    root = Path(runs_root)
    boards = list(storyboards or [])
    token = csrf or secrets.token_urlsafe(24)

    class Handler(BaseHTTPRequestHandler):
        server_version = "MorphCurrentReview"
        sys_version = ""
        csrf_token = token

        def log_message(self, fmt: str, *args: object) -> None:  # quiet; no request logging to disk
            pass

        def _host_ok(self) -> bool:
            host = (self.headers.get("Host") or "").strip()
            name = host[1:host.index("]")] if host.startswith("[") and "]" in host else host.rsplit(":", 1)[0]
            return name in LOOPBACK_HOSTS

        def _send(self, status: int, body: bytes, ctype: str = "text/html; charset=utf-8",
                  extra: dict | None = None) -> None:
            self.send_response(status)
            for k, v in {"Content-Type": ctype, "Content-Length": str(len(body)),
                         "Content-Security-Policy": CSP, "X-Content-Type-Options": "nosniff",
                         "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer",
                         "Cache-Control": "no-store", **(extra or {})}.items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _error(self, status: int, text: str) -> None:
            self._send(status, _page("Error", f"<h1>{status}</h1><p>{e(text)}</p>").encode("utf-8"))

        def do_HEAD(self) -> None:
            self.do_GET()

        def do_GET(self) -> None:
            if not self._host_ok():
                return self._error(HTTPStatus.FORBIDDEN, "non-loopback Host header refused")
            url = urlsplit(self.path)
            parts = [p for p in url.path.split("/") if p]
            try:
                if not parts:
                    return self._send(200, render_index(list_runs(root), boards).encode("utf-8"))
                if parts[0] == "run" and len(parts) == 2:
                    msg = parse_qs(url.query).get("msg", [""])[0][:200]
                    return self._send(200, render_run_page(run_view(root, parts[1]), self.csrf_token, msg).encode("utf-8"))
                if parts[0] == "plan" and len(parts) == 1:
                    i = parse_qs(url.query).get("i", [""])[0]
                    if not i.isdigit() or int(i) >= len(boards):
                        raise UiError("no such storyboard")
                    return self._send(200, render_plan_page(plan_summary(boards[int(i)], repo_root)).encode("utf-8"))
                if parts[0] == "media" and len(parts) == 3:
                    return self._media(parts[1], parts[2])
            except UiError as exc:
                return self._error(HTTPStatus.NOT_FOUND, str(exc))
            except (ValueError, OSError) as exc:
                return self._error(HTTPStatus.UNPROCESSABLE_ENTITY, str(exc))
            return self._error(HTTPStatus.NOT_FOUND, "not found")

        def _media(self, run: str, media_token: str) -> None:
            path = run_view(root, run)["media"].get(media_token)
            if path is None:
                return self._error(HTTPStatus.NOT_FOUND, "media not available")
            size = path.stat().st_size
            ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            start, end, status = 0, size - 1, 200
            match = re.match(r"^bytes=(\d*)-(\d*)$", self.headers.get("Range", ""))
            if match and size:
                if match.group(1):
                    start = int(match.group(1))
                    end = int(match.group(2)) if match.group(2) else size - 1
                else:
                    start = max(0, size - int(match.group(2) or 0))
                end = min(end, size - 1)
                if start > end:
                    return self._send(416, b"", "text/plain", {"Content-Range": f"bytes */{size}"})
                status = 206
            with path.open("rb") as stream:
                stream.seek(start)
                body = stream.read(end - start + 1)
            extra = {"Accept-Ranges": "bytes", "Cache-Control": "private, max-age=60"}
            if status == 206:
                extra["Content-Range"] = f"bytes {start}-{end}/{size}"
            self._send(status, body, ctype, extra)

        def do_POST(self) -> None:
            if not self._host_ok():
                return self._error(HTTPStatus.FORBIDDEN, "non-loopback Host header refused")
            origin = self.headers.get("Origin")
            if origin and urlsplit(origin).hostname not in LOOPBACK_HOSTS:
                return self._error(HTTPStatus.FORBIDDEN, "cross-origin request refused")
            parts = [p for p in urlsplit(self.path).path.split("/") if p]
            if len(parts) != 3 or parts[0] != "run" or parts[2] != "review":
                return self._error(HTTPStatus.NOT_FOUND, "not found")
            length = int(self.headers.get("Content-Length") or 0)
            if length > 10_000:
                if length <= 1_000_000:  # drain so the client can read the reply (Windows aborts otherwise)
                    self.rfile.read(length)
                self.close_connection = True
                return self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "form too large")
            form = {k: v[0] for k, v in parse_qs(self.rfile.read(length).decode("utf-8", "replace")).items()}
            if not secrets.compare_digest(form.get("csrf", ""), self.csrf_token):
                return self._error(HTTPStatus.FORBIDDEN, "missing or invalid form token")
            try:
                apply_review(root, parts[1], form.get("task", ""), form.get("decision", ""), form.get("note", ""))
            except UiError as exc:
                return self._error(HTTPStatus.BAD_REQUEST, str(exc))
            from urllib.parse import quote
            msg = quote(f"Recorded {form.get('decision')} for {form.get('task')}. Re-run the same render "
                        "command to continue.")
            self._send(303, b"", "text/plain", {"Location": f"/run/{parts[1]}?msg={msg}"})

    return Handler


def make_server(runs_root: str | Path, *, host: str = "127.0.0.1", port: int = 8765,
                storyboards: list[str] | None = None, repo_root: str | Path = ".") -> ThreadingHTTPServer:
    if host not in LOOPBACK_HOSTS:
        raise UiError(f"review-ui binds only to loopback ({', '.join(sorted(LOOPBACK_HOSTS))}), not {host!r}")
    cls = _Server6 if host == "::1" else _Server
    return cls((host, port), make_handler(runs_root, storyboards, repo_root))


def default_storyboards(repo_root: str | Path = ".") -> list[str]:
    """Plan view list: every storyboard in configs/sequences (FR-009)."""
    folder = Path(repo_root) / "configs" / "sequences"
    return [str(p) for p in sorted(folder.glob("*.yaml"))] if folder.is_dir() else []


class _Server(ThreadingHTTPServer):
    daemon_threads = True


class _Server6(_Server):
    address_family = socket.AF_INET6
