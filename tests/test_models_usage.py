"""Tests for models listing and usage stats."""

import pytest
import httpx
from tests.conftest import MockTransport, _json_response, make_models_response
from cocapn import Cocapn, Model


class TestModels:
    def _models_client(self, api_key, models_body=None):
        body = models_body or make_models_response()

        def handler(request):
            assert request.method == "GET"
            assert "/v1/models" in str(request.url)
            return _json_response(200, body)

        transport = MockTransport(handler)
        client = Cocapn(api_key=api_key)
        client._client = httpx.Client(transport=transport)
        client._transport = transport
        return client

    def test_list_models(self, api_key):
        client = self._models_client(api_key)
        models = client.models()
        assert len(models) == 3
        assert models[0].id == "deepseek-chat"
        assert models[1].id == "gpt-4o"
        assert models[2].id == "claude-3-5-sonnet"
        client.close()

    def test_model_attributes(self, api_key):
        client = self._models_client(api_key)
        models = client.models()
        ds = models[0]
        assert ds.provider == "deepseek"
        assert ds.cost_in == 0.14
        assert ds.cost_out == 0.28
        client.close()

    def test_model_repr(self, api_key):
        client = self._models_client(api_key)
        models = client.models()
        r = repr(models[0])
        assert "Model" in r
        assert "deepseek-chat" in r
        client.close()

    def test_empty_models(self, api_key):
        client = self._models_client(api_key, make_models_response([]))
        models = client.models()
        assert models == []
        client.close()


class TestUsage:
    def _usage_client(self, api_key, usage_body=None):
        body = usage_body or {"totalCost": 1.23, "requests": 42}

        def handler(request):
            assert request.method == "GET"
            assert "/v1/usage" in str(request.url)
            return _json_response(200, body)

        transport = MockTransport(handler)
        client = Cocapn(api_key=api_key)
        client._client = httpx.Client(transport=transport)
        client._transport = transport
        return client

    def test_usage_day(self, api_key):
        client = self._usage_client(api_key)
        stats = client.usage("day")
        assert stats["totalCost"] == 1.23
        assert stats["requests"] == 42
        client.close()

    def test_usage_period_in_url(self, api_key):
        captured = {}

        def handler(request):
            captured["url"] = str(request.url)
            return _json_response(200, {"totalCost": 0})

        transport = MockTransport(handler)
        client = Cocapn(api_key=api_key)
        client._client = httpx.Client(transport=transport)
        client._transport = transport

        client.usage("week")
        assert "period=week" in captured["url"]
        client.close()
