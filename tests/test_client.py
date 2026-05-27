"""Tests for Cocapn client initialization, configuration, and auth."""

import os
import pytest
from cocapn import Cocapn


class TestInit:
    def test_explicit_api_key(self, api_key):
        client = Cocapn(api_key=api_key)
        assert client.api_key == api_key
        client.close()

    def test_env_var_api_key(self, api_key, monkeypatch):
        monkeypatch.setenv("COCAPN_API_KEY", api_key)
        client = Cocapn()
        assert client.api_key == api_key
        client.close()

    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("COCAPN_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key required"):
            Cocapn()

    def test_default_base_url(self, api_key):
        client = Cocapn(api_key=api_key)
        assert client.base_url == "https://cocapn.ai"
        client.close()

    def test_custom_base_url(self, api_key):
        client = Cocapn(api_key=api_key, base_url="https://custom.example.com/")
        assert client.base_url == "https://custom.example.com"  # trailing slash stripped
        client.close()

    def test_env_var_base_url(self, api_key, monkeypatch):
        monkeypatch.setenv("COCAPN_BASE_URL", "https://env.example.com")
        client = Cocapn(api_key=api_key)
        assert client.base_url == "https://env.example.com"
        client.close()

    def test_context_manager(self, api_key):
        with Cocapn(api_key=api_key) as client:
            assert client.api_key == api_key

    def test_headers(self, api_key):
        client = Cocapn(api_key=api_key)
        headers = client._headers()
        assert headers["Authorization"] == f"Bearer {api_key}"
        assert headers["Content-Type"] == "application/json"
        client.close()
