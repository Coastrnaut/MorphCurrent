import httpx
import pytest

from morph_studio.comfy_client import ComfyClient, ComfyError, validate_local_url


def test_non_loopback_disallowed():
    for url in (
        "http://192.168.1.10:8188",
        "https://example.com:8188",
        "http://127.0.0.1",
        "file:///tmp/comfy",
        "http://127.0.0.1:8188/other",
    ):
        with pytest.raises(ValueError):
            validate_local_url(url)
    assert validate_local_url("http://127.0.0.1:8188") == "http://127.0.0.1:8188"


def test_submit_and_history_mocked():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/system_stats":
            return httpx.Response(200, json={"devices": []})
        if request.url.path == "/prompt":
            return httpx.Response(200, json={"prompt_id": "p1"})
        if request.url.path == "/history/p1":
            return httpx.Response(200, json={"p1": {
                "status": {"completed": True, "status_str": "success"}, "outputs": {}
            }})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    fake_http = httpx.Client(base_url="http://127.0.0.1:8188", transport=transport)
    with fake_http, ComfyClient(http_client=fake_http) as client:
        assert client.health() == {"devices": []}
        prompt_id = client.submit({"1": {"class_type": "Test", "inputs": {}}})
        assert prompt_id == "p1"
        assert client.await_result(prompt_id, timeout=1)["status"]["completed"]


def test_bad_workflow_rejected_before_request():
    with ComfyClient() as client:
        with pytest.raises(ValueError):
            client.submit({"1": {"inputs": {}}})


def test_prompt_validation_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": "missing model"})
    fake_http = httpx.Client(base_url="http://127.0.0.1:8188",
                             transport=httpx.MockTransport(handler))
    with fake_http, ComfyClient(http_client=fake_http) as client:
        with pytest.raises(ComfyError):
            client.submit({"1": {"class_type": "Test", "inputs": {}}})
