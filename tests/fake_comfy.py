"""Stateful fake ComfyUI for image (SaveImage) and video (SaveVideo) stages; no GPU.

Mirrors the observed ComfyUI 0.46 REST behaviour used by MorphCurrent: uploads
extend ``LoadImage`` choices, client-chosen ``prompt_id`` is honoured, ``/history``
appears after a poll, outputs are served by ``/view``.
"""
from __future__ import annotations

import json
import struct
import zlib

import httpx

from image_graphs import installed_object_info
from morph_studio.comfy_client import ComfyClient

VIDEO_BYTES = b"\x00\x00\x00\x18ftypmp42fake-video"


def make_png(width: int, height: int, rgb: tuple[int, int, int] = (40, 60, 200)) -> bytes:
    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    row = b"\x00" + bytes(rgb) * width
    raw = zlib.compress(row * height)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", raw) + chunk(b"IEND", b""))


class FakeComfy:
    def __init__(self, object_info: dict | None = None):
        self.object_info = object_info or installed_object_info()
        self.uploads: dict[str, bytes] = {}
        self.prompts: dict[str, dict] = {}
        self.pending: list[str] = []
        self.running: list[str] = []
        self.history: dict[str, dict] = {}
        self.files: dict[str, bytes] = {}
        self.calls: list[str] = []
        self.fail_execution = False
        self.drop_next_prompt_response = False
        self.images_per_save = 1
        self.image_override: bytes | None = None  # serve these bytes for every image
        self.default_size = (832, 480)
        self.seed_colour = True  # vary pixels by seed so different seeds give different bytes

    @property
    def prompt_posts(self) -> int:
        return sum(1 for c in self.calls if c == "POST /prompt")

    def client(self) -> ComfyClient:
        http = httpx.Client(base_url="http://127.0.0.1:8188", transport=httpx.MockTransport(self.handler))
        return ComfyClient(http_client=http)

    def _choices(self) -> list:
        return self.object_info["LoadImage"]["input"]["required"]["image"][0]

    def handler(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        self.calls.append(f"{request.method} {path}")
        if path == "/system_stats":
            return httpx.Response(200, json={"system": {"comfyui_version": "0.46.0", "argv": []},
                                             "devices": [{"name": "cuda:0 fake", "vram_total": 1, "vram_free": 1}]})
        if path == "/object_info":
            return httpx.Response(200, json=self.object_info)
        if path == "/upload/image":
            body = request.read()
            name = body.split(b'filename="', 1)[1].split(b'"', 1)[0].decode()
            self.uploads[name] = body
            if name not in self._choices():
                self._choices().append(name)
            return httpx.Response(200, json={"name": name, "subfolder": "", "type": "input"})
        if path == "/queue" and request.method == "GET":
            return httpx.Response(200, json={
                "queue_running": [[0, p, {}, {}, []] for p in self.running],
                "queue_pending": [[1, p, {}, {}, []] for p in self.pending]})
        if path == "/prompt":
            body = json.loads(request.read())
            pid = body["prompt_id"]
            self.prompts[pid] = body["prompt"]
            self.pending.append(pid)
            if self.drop_next_prompt_response:
                self.drop_next_prompt_response = False
                raise httpx.ReadError("connection reset", request=request)
            return httpx.Response(200, json={"prompt_id": pid, "number": 1, "node_errors": {}})
        if path.startswith("/history/"):
            pid = path.rsplit("/", 1)[1]
            if pid in self.pending or pid in self.running:
                self._finish(pid)
            return httpx.Response(200, json={pid: self.history[pid]} if pid in self.history else {})
        if path == "/view":
            key = f"{request.url.params.get('subfolder')}/{request.url.params.get('filename')}"
            return httpx.Response(200, content=self.files.get(key, VIDEO_BYTES))
        return httpx.Response(404)

    def _size(self, graph: dict) -> tuple[int, int]:
        for node in graph.values():
            inputs = node["inputs"]
            if isinstance(inputs.get("width"), int) and isinstance(inputs.get("height"), int):
                return inputs["width"], inputs["height"]
        return self.default_size

    def _finish(self, pid: str) -> None:
        for queue in (self.pending, self.running):
            if pid in queue:
                queue.remove(pid)
        graph = self.prompts[pid]
        if self.fail_execution:
            self.history[pid] = {"status": {"status_str": "error", "completed": False, "messages": []},
                                 "outputs": {}}
            return
        outputs = {}
        seed = next((n["inputs"].get("seed", n["inputs"].get("noise_seed")) for n in graph.values()
                     if isinstance(n["inputs"].get("seed", n["inputs"].get("noise_seed")), int)), 0)
        for node_id, node in graph.items():
            prefix = node["inputs"].get("filename_prefix", "ComfyUI")
            subfolder, _, stem = prefix.rpartition("/")
            if node["class_type"] in ("SaveImage", "SaveImageAdvanced"):
                items = []
                for i in range(self.images_per_save):
                    name = f"{stem}_{i + 1:05d}_.png"
                    colour = (seed % 251, 60, 200) if self.seed_colour else (40, 60, 200)
                    self.files[f"{subfolder}/{name}"] = self.image_override or make_png(*self._size(graph), colour)
                    items.append({"filename": name, "subfolder": subfolder, "type": "output"})
                outputs[node_id] = {"images": items}
            elif node["class_type"] == "SaveVideo":
                name = f"{stem}_00001_.mp4"
                self.files[f"{subfolder}/{name}"] = VIDEO_BYTES
                outputs[node_id] = {"images": [{"filename": name, "subfolder": subfolder,
                                                "type": "output"}], "animated": [True]}
        self.history[pid] = {"status": {"status_str": "success", "completed": True, "messages": [
            ["execution_start", {"timestamp": 1_000}], ["execution_success", {"timestamp": 5_000}]]},
            "outputs": outputs}
