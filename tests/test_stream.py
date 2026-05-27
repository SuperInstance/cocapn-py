"""Tests for streaming chat completions."""

import json
import pytest
import httpx
from tests.conftest import MockTransport


def _stream_body(chunks: list[str]) -> bytes:
    """Build SSE response bytes from a list of content chunks."""
    lines = []
    for chunk in chunks:
        data = {
            "id": "chatcmpl-stream",
            "choices": [{"delta": {"content": chunk}, "index": 0}],
        }
        lines.append(f"data: {json.dumps(data)}")
    lines.append("data: [DONE]")
    return "\n".join(lines).encode()


class _StreamTransport(httpx.BaseTransport):
    """Mock transport that returns an SSE stream."""

    def __init__(self, body: bytes, status_code: int = 200):
        self.body = body
        self.status_code = status_code
        self.last_request = None

    def handle_request(self, request):
        self.last_request = request
        return httpx.Response(
            status_code=self.status_code,
            headers={"content-type": "text/event-stream"},
            content=self.body,
        )


class TestChatStream:
    def test_basic_stream(self, api_key):
        from cocapn import Cocapn

        content = ["Hello", " ", "world", "!"]
        transport = _StreamTransport(_stream_body(content))
        client = Cocapn(api_key=api_key)
        client._client = httpx.Client(transport=transport)
        client._transport = transport

        collected = list(client.chat_stream("Hi"))
        assert collected == ["Hello", " ", "world", "!"]
        client.close()

    def test_stream_empty(self, api_key):
        from cocapn import Cocapn

        transport = _StreamTransport(_stream_body([]))
        client = Cocapn(api_key=api_key)
        client._client = httpx.Client(transport=transport)

        collected = list(client.chat_stream("Hi"))
        assert collected == []
        client.close()

    def test_stream_with_system_and_history(self, api_key):
        from cocapn import Cocapn

        transport = _StreamTransport(_stream_body(["ok"]))
        client = Cocapn(api_key=api_key)
        client._client = httpx.Client(transport=transport)
        client._transport = transport

        list(client.chat_stream("Hi", system="Be brief.", history=[{"role": "user", "content": "hey"}]))

        req_body = json.loads(transport.last_request.content)
        assert req_body["messages"][0]["role"] == "system"
        assert req_body["stream"] is True
        client.close()

    def test_stream_sse_done_ignored(self, api_key):
        from cocapn import Cocapn

        # Include some malformed lines mixed in
        sse = (
            "data: {\"id\":\"x\",\"choices\":[{\"delta\":{\"content\":\"hi\"},\"index\":0}]}\n"
            "data: [DONE]\n"
            "data: not json\n"
        ).encode()
        transport = _StreamTransport(sse)
        client = Cocapn(api_key=api_key)
        client._client = httpx.Client(transport=transport)

        collected = list(client.chat_stream("Hi"))
        assert collected == ["hi"]
        client.close()

    def test_stream_sse_no_content_delta_skipped(self, api_key):
        from cocapn import Cocapn

        sse = (
            "data: {\"id\":\"x\",\"choices\":[{\"delta\":{\"role\":\"assistant\"},\"index\":0}]}\n"
            "data: {\"id\":\"x\",\"choices\":[{\"delta\":{\"content\":\"yo\"},\"index\":0}]}\n"
            "data: [DONE]\n"
        ).encode()
        transport = _StreamTransport(sse)
        client = Cocapn(api_key=api_key)
        client._client = httpx.Client(transport=transport)

        collected = list(client.chat_stream("Hi"))
        assert collected == ["yo"]
        client.close()
