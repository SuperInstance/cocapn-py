"""Cocapn SDK for Python — one API key, any AI model, see what it costs."""

import os
import json
import httpx

__version__ = "1.0.0"

DEFAULT_BASE = "https://cocapn.ai"


class Cocapn:
    """Cocapn AI client.

    >>> cocapn = Cocapn(api_key="cocapn_your_key")
    >>> response = cocapn.chat("Hello!", model="deepseek-chat")
    >>> print(response.text)
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.environ.get("COCAPN_API_KEY")
        if not self.api_key:
            raise ValueError("API key required. Pass api_key= or set COCAPN_API_KEY env var.")
        self.base_url = (base_url or os.environ.get("COCAPN_BASE_URL") or DEFAULT_BASE).rstrip("/")
        self._client = httpx.Client(timeout=120)

    def chat(
        self,
        message: str,
        *,
        model: str = "deepseek-chat",
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float | None = None,
        history: list[dict] | None = None,
    ) -> "ChatResponse":
        """Send a chat message and get a response.

        Returns ChatResponse with .text, .cost, .tokens, .model, .provider
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})

        body = {"model": model, "messages": messages, "max_tokens": max_tokens}
        if temperature is not None:
            body["temperature"] = temperature

        data = self._post("/v1/chat/completions", body)
        choice = data["choices"][0]
        usage = data.get("usage", {})

        return ChatResponse(
            text=choice["message"]["content"],
            cost=float(data.get("cocapn_cost", 0)),
            tokens=TokenCount(
                in_=usage.get("prompt_tokens", 0),
                out=usage.get("completion_tokens", 0),
            ),
            model=data.get("model", model),
            provider=data.get("cocapn_provider", model.split("-")[0]),
            raw=data,
        )

    def chat_stream(
        self,
        message: str,
        *,
        model: str = "deepseek-chat",
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float | None = None,
        history: list[dict] | None = None,
    ):
        """Stream a chat response. Yields text chunks."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})

        body = {"model": model, "messages": messages, "max_tokens": max_tokens, "stream": True}
        if temperature is not None:
            body["temperature"] = temperature

        with self._client.stream("POST", f"{self.base_url}/v1/chat/completions",
                                  json=body, headers=self._headers()) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        chunk = json.loads(line[6:])
                        delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content")
                        if delta:
                            yield delta
                    except json.JSONDecodeError:
                        continue

    def models(self) -> list["Model"]:
        """List available models."""
        data = self._get("/v1/models")
        return [
            Model(
                id=m["id"],
                provider=m["owned_by"],
                cost_in=m.get("cocapn_cost_in", 0),
                cost_out=m.get("cocapn_cost_out", 0),
            )
            for m in data["data"]
        ]

    def usage(self, period: str = "day") -> "UsageStats":
        """Get usage stats. Period: 'day', 'week', or 'month'."""
        return self._get(f"/v1/usage?period={period}")

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ─── Internal ───

    def _headers(self):
        return {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

    def _post(self, path, body):
        resp = self._client.post(f"{self.base_url}{path}", json=body, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def _get(self, path):
        resp = self._client.get(f"{self.base_url}{path}", headers=self._headers())
        resp.raise_for_status()
        return resp.json()


class TokenCount:
    __slots__ = ("in_", "out")

    def __init__(self, in_: int, out: int):
        self.in_ = in_
        self.out = out

    def __repr__(self):
        return f"TokenCount(in={self.in_}, out={self.out})"

    @property
    def total(self):
        return self.in_ + self.out


class ChatResponse:
    __slots__ = ("text", "cost", "tokens", "model", "provider", "raw")

    def __init__(self, text: str, cost: float, tokens: TokenCount, model: str, provider: str, raw: dict = None):
        self.text = text
        self.cost = cost
        self.tokens = tokens
        self.model = model
        self.provider = provider
        self.raw = raw

    def __repr__(self):
        return f"ChatResponse(model={self.model!r}, cost=${self.cost:.6f}, tokens={self.tokens})"


class Model:
    __slots__ = ("id", "provider", "cost_in", "cost_out")

    def __init__(self, id: str, provider: str, cost_in: float, cost_out: float):
        self.id = id
        self.provider = provider
        self.cost_in = cost_in
        self.cost_out = cost_out

    def __repr__(self):
        return f"Model({self.id!r}, cost_in=${self.cost_in}, cost_out=${self.cost_out})"


# Module-level convenience
_default = None


def chat(message: str, **kwargs) -> ChatResponse:
    """Quick chat with default client."""
    global _default
    if _default is None:
        _default = Cocapn()
    return _default.chat(message, **kwargs)


__all__ = ["Cocapn", "ChatResponse", "TokenCount", "Model", "chat"]
