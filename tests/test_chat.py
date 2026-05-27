"""Tests for chat completions (non-streaming)."""

import json
import pytest
import httpx
from tests.conftest import MockTransport, _json_response, make_chat_response
from cocapn import Cocapn, ChatResponse, TokenCount


def _chat_client(api_key, response_body=None):
    """Create a Cocapn client with mocked chat response."""
    body = response_body or make_chat_response()

    def handler(request):
        assert request.method == "POST"
        assert "/v1/chat/completions" in str(request.url)
        return _json_response(200, body)

    transport = MockTransport(handler)
    client = Cocapn(api_key=api_key)
    client._client = httpx.Client(transport=transport)
    client._transport = transport
    return client


class TestChatBasic:
    def test_simple_chat(self, api_key):
        client = _chat_client(api_key)
        resp = client.chat("Hello!")
        assert isinstance(resp, ChatResponse)
        assert resp.text == "Hello!"
        assert resp.cost == 0.0042
        assert resp.model == "deepseek-chat"
        assert resp.provider == "deepseek"
        client.close()

    def test_token_counts(self, api_key):
        client = _chat_client(api_key)
        resp = client.chat("Hello!")
        assert isinstance(resp.tokens, TokenCount)
        assert resp.tokens.in_ == 15
        assert resp.tokens.out == 847
        assert resp.tokens.total == 862
        assert resp.tokens.in_ + resp.tokens.out == resp.tokens.total
        client.close()

    def test_repr(self, api_key):
        client = _chat_client(api_key)
        resp = client.chat("Hello!")
        r = repr(resp)
        assert "ChatResponse" in r
        assert "deepseek-chat" in r
        client.close()

    def test_token_count_repr(self):
        tc = TokenCount(in_=10, out=20)
        assert repr(tc) == "TokenCount(in=10, out=20)"

    def test_custom_model(self, api_key):
        body = make_chat_response(model="gpt-4o", provider="openai", cost=0.01)
        client = _chat_client(api_key, body)
        resp = client.chat("Hello!", model="gpt-4o")
        assert resp.model == "gpt-4o"
        assert resp.provider == "openai"
        client.close()

    def test_system_prompt_sent(self, api_key):
        captured = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return _json_response(200, make_chat_response())

        transport = MockTransport(handler)
        client = Cocapn(api_key=api_key)
        client._client = httpx.Client(transport=transport)
        client._transport = transport

        resp = client.chat("Hello!", system="You are a pirate.")
        msgs = captured["body"]["messages"]
        assert msgs[0]["role"] == "system"
        assert msgs[0]["content"] == "You are a pirate."
        assert msgs[-1]["role"] == "user"
        client.close()

    def test_history_sent(self, api_key):
        captured = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return _json_response(200, make_chat_response())

        transport = MockTransport(handler)
        client = Cocapn(api_key=api_key)
        client._client = httpx.Client(transport=transport)
        client._transport = transport

        history = [
            {"role": "user", "content": "My name is Casey"},
            {"role": "assistant", "content": "Hello Casey!"},
        ]
        resp = client.chat("What's my name?", history=history)
        msgs = captured["body"]["messages"]
        # user message should be last, history before it
        assert len(msgs) == 3
        assert msgs[0]["content"] == "My name is Casey"
        assert msgs[2]["role"] == "user"
        assert msgs[2]["content"] == "What's my name?"
        client.close()

    def test_temperature_sent(self, api_key):
        captured = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return _json_response(200, make_chat_response())

        transport = MockTransport(handler)
        client = Cocapn(api_key=api_key)
        client._client = httpx.Client(transport=transport)
        client._transport = transport

        client.chat("Hello!", temperature=0.7)
        assert captured["body"]["temperature"] == 0.7
        client.close()

    def test_no_temperature_when_none(self, api_key):
        captured = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return _json_response(200, make_chat_response())

        transport = MockTransport(handler)
        client = Cocapn(api_key=api_key)
        client._client = httpx.Client(transport=transport)
        client._transport = transport

        client.chat("Hello!")
        assert "temperature" not in captured["body"]
        client.close()

    def test_max_tokens_default(self, api_key):
        captured = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return _json_response(200, make_chat_response())

        transport = MockTransport(handler)
        client = Cocapn(api_key=api_key)
        client._client = httpx.Client(transport=transport)
        client._transport = transport

        client.chat("Hello!")
        assert captured["body"]["max_tokens"] == 4096
        client.close()

    def test_raw_response_preserved(self, api_key):
        body = make_chat_response()
        client = _chat_client(api_key, body)
        resp = client.chat("Hello!")
        assert resp.raw is not None
        assert resp.raw["id"] == "chatcmpl-test123"
        client.close()

    def test_system_and_history_combined(self, api_key):
        captured = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return _json_response(200, make_chat_response())

        transport = MockTransport(handler)
        client = Cocapn(api_key=api_key)
        client._client = httpx.Client(transport=transport)
        client._transport = transport

        history = [{"role": "user", "content": "hi"}]
        client.chat("follow-up", system="Be brief.", history=history)
        msgs = captured["body"]["messages"]
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"
        assert msgs[1]["content"] == "hi"
        assert msgs[2]["role"] == "user"
        assert msgs[2]["content"] == "follow-up"
        client.close()


class TestChatErrors:
    def test_http_error_raised(self, api_key):
        def handler(request):
            return _json_response(401, {"error": {"message": "Invalid API key"}})

        transport = MockTransport(handler)
        client = Cocapn(api_key=api_key)
        client._client = httpx.Client(transport=transport)

        with pytest.raises(httpx.HTTPStatusError):
            client.chat("Hello!")
        client.close()

    def test_server_error_raised(self, api_key):
        def handler(request):
            return _json_response(500, {"error": {"message": "Internal server error"}})

        transport = MockTransport(handler)
        client = Cocapn(api_key=api_key)
        client._client = httpx.Client(transport=transport)

        with pytest.raises(httpx.HTTPStatusError):
            client.chat("Hello!")
        client.close()
