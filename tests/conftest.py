"""Shared test fixtures and mock httpx transport for Cocapn SDK tests."""

import json
import pytest
import httpx


class MockTransport(httpx.BaseTransport):
    """Captures requests and returns pre-configured responses."""

    def __init__(self, handler):
        self.handler = handler
        self.last_request = None

    def handle_request(self, request):
        self.last_request = request
        return self.handler(request)


def _json_response(status_code: int = 200, body: dict | None = None) -> httpx.Response:
    """Build an httpx.Response with JSON body."""
    return httpx.Response(
        status_code=status_code,
        headers={"content-type": "application/json"},
        json=body or {},
    )


def make_chat_response(
    text: str = "Hello!",
    model: str = "deepseek-chat",
    cost: float = 0.0042,
    prompt_tokens: int = 15,
    completion_tokens: int = 847,
    provider: str = "deepseek",
) -> dict:
    """Build a realistic /v1/chat/completions response body."""
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "model": model,
        "cocapn_cost": cost,
        "cocapn_provider": provider,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


def make_models_response(models: list[dict] | None = None) -> dict:
    """Build a realistic /v1/models response body."""
    if models is None:
        models = [
            {"id": "deepseek-chat", "owned_by": "deepseek", "cocapn_cost_in": 0.14, "cocapn_cost_out": 0.28},
            {"id": "gpt-4o", "owned_by": "openai", "cocapn_cost_in": 2.50, "cocapn_cost_out": 10.0},
            {"id": "claude-3-5-sonnet", "owned_by": "anthropic", "cocapn_cost_in": 3.0, "cocapn_cost_out": 15.0},
        ]
    return {"object": "list", "data": models}


@pytest.fixture
def api_key():
    return "cocapn_test_key_abc123"


@pytest.fixture
def mock_transport_factory():
    """Returns a factory that creates a Cocapn client with a mock transport."""

    def _factory(api_key: str, handler):
        from cocapn import Cocapn

        transport = MockTransport(handler)
        client = Cocapn(api_key=api_key)
        client._client = httpx.Client(transport=transport)
        client._transport = transport  # keep reference for assertions
        return client

    return _factory
