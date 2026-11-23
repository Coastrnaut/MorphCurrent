"""Localhost-only ComfyUI REST client with optional WebSocket progress."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import httpx


class ComfyError(RuntimeError):
    """ComfyUI transport, validation or execution error."""


def validate_local_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
        "127.0.0.1", "localhost", "::1"
    } or parsed.username or parsed.password:
        raise ValueError("ComfyUI URL must be local loopback HTTP(S), without credentials")
    if not parsed.port:
        raise ValueError("ComfyUI URL must specify a port")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("ComfyUI base URL must not contain a path/query")
    return url.rstrip("/")


class ComfyClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8188",
                 timeout: float = 30, http_client: httpx.Client | None = None):
        self.base_url = validate_local_url(base_url)
        self.client_id = str(uuid.uuid4())
        self._owns_client = http_client is None
        self.http = http_client or httpx.Client(base_url=self.base_url, timeout=timeout)

    def __enter__(self) -> "ComfyClient":
        return self

    def __exit__(self, *exc: object) -> None:
        if self._owns_client:
            self.http.close()

    def _json(self, method: str, endpoint: str, **kwargs: object) -> dict:
        try:
            response = self.http.request(method, endpoint, **kwargs)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ComfyError(f"unexpected {endpoint} response")
            return payload
        except (httpx.HTTPError, ValueError) as exc:
            raise ComfyError(f"{method} {endpoint}: {exc}") from exc

    def health(self) -> dict:
        return self._json("GET", "/system_stats")

    def object_info(self) -> dict:
        return self._json("GET", "/object_info")

    def submit(self, api_workflow: dict) -> str:
        if not isinstance(api_workflow, dict) or not api_workflow:
            raise ValueError("nonempty API-format workflow required")
        for node_id, node in api_workflow.items():
            if not isinstance(node, dict) or "class_type" not in node or "inputs" not in node:
                raise ValueError(f"node {node_id} is not in ComfyUI API format")
        result = self._json("POST", "/prompt", json={
            "prompt": api_workflow, "client_id": self.client_id
        })
        if "error" in result:
            raise ComfyError(f"ComfyUI rejected prompt: {result}")
        if not result.get("prompt_id"):
            raise ComfyError(f"missing prompt_id: {result}")
        return str(result["prompt_id"])

    def history(self, prompt_id: str) -> dict | None:
        payload = self._json("GET", f"/history/{prompt_id}")
        return payload.get(prompt_id)

    def await_result(self, prompt_id: str, timeout: float = 3600,
                     poll_seconds: float = 2) -> dict:
        """Recoverable polling: WS is advisory; history is the source of truth."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            item = self.history(prompt_id)
            if item is not None:
                status = item.get("status", {})
                if status.get("status_str") == "error":
                    raise ComfyError(f"ComfyUI execution failed: {status}")
                if status.get("completed") is True or status.get("status_str") == "success":
                    return item
            time.sleep(poll_seconds)
        raise TimeoutError(f"ComfyUI prompt {prompt_id} did not finish in {timeout}s")

    def progress_events(self, timeout: float = 60):
        """Optional generator of raw WS messages; reconnect/recovery is caller's job."""
        from websockets.sync.client import connect
        parsed = urlparse(self.base_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        url = f"{scheme}://{parsed.netloc}/ws?clientId={self.client_id}"
        with connect(url, open_timeout=timeout, close_timeout=5) as websocket:
            for raw in websocket:
                if isinstance(raw, str):
                    yield json.loads(raw)

    def upload_image(self, image_path: str | Path, *, overwrite: bool = False) -> dict:
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        with path.open("rb") as stream:
            return self._json("POST", "/upload/image", files={
                "image": (path.name, stream, "application/octet-stream")
            }, data={"type": "input", "overwrite": str(overwrite).lower()})

    def download_output(self, filename: str, destination: str | Path,
                        *, subfolder: str = "", folder_type: str = "output") -> Path:
        if not filename or filename in {".", ".."} or "/" in filename or "\\" in filename:
            raise ValueError("output filename must be a basename")
        if folder_type not in {"output", "temp"}:
            raise ValueError("only ComfyUI output/temp artifacts can be downloaded")
        try:
            response = self.http.get("/view", params={
                "filename": filename, "subfolder": subfolder, "type": folder_type
            })
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ComfyError(f"download failed: {exc}") from exc
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(response.content)
        return target
