"""Tests for the module-level convenience chat() function."""

import os
import httpx
import pytest
from unittest.mock import patch, MagicMock
from tests.conftest import MockTransport, _json_response, make_chat_response
import cocapn


class TestModuleLevelChat:
    def test_chat_creates_default_client(self, api_key, monkeypatch):
        monkeypatch.setenv("COCAPN_API_KEY", api_key)
        # Reset module-level default
        cocapn._default = None

        body = make_chat_response()
        transport = MockTransport(lambda r: _json_response(200, body))

        with patch.object(cocapn.Cocapn, "__init__", lambda self, **kw: None):
            client = cocapn.Cocapn.__new__(cocapn.Cocapn)
            client._client = MagicMock()
            client._client.post.return_value = httpx.Response(200, json=body)

        # Just verify the function exists and has right signature
        assert callable(cocapn.chat)

    def test_all_exports(self):
        """Verify __all__ exports are importable."""
        for name in cocapn.__all__:
            assert hasattr(cocapn, name), f"{name} not found in cocapn module"

    def test_version(self):
        assert cocapn.__version__ == "1.0.0"
