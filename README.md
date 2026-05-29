# cocapn-py — Python SDK

**One API key, any AI model, see what it costs. Python edition.**

## What This Gives You

- **One API key** — route to DeepSeek, GPT-4o, Claude, Gemini, and more through a single endpoint
- **Cost transparency** — every response includes exact cost, token counts, and provider
- **Streaming** — `chat_stream()` yields text chunks as they arrive
- **Model catalog** — list available models with per-token pricing
- **Usage stats** — query your spend by day, week, or month
- **Type-hinted** — full type annotations, dataclass responses

## Quick Start

```bash
pip install cocapn
```

```python
from cocapn import Cocapn

client = Cocapn()  # uses COCAPN_API_KEY env var

response = client.chat(
    "Explain transformers in one paragraph",
    model="deepseek-chat",
    system="You are a concise teacher."
)

print(response.text)      # "Transformers are..."
print(response.cost)      # 0.000042
print(response.tokens)    # TokenCount(in_=15, out=47)
print(response.provider)  # "deepseek"
```

### Streaming

```python
for chunk in client.chat_stream("Tell me a story", model="gpt-4o"):
    print(chunk, end="", flush=True)
```

### List Models

```python
for m in client.models():
    print(f"{m.id:30s} ${m.cost_in}/in  ${m.cost_out}/out")
```

### Usage Stats

```python
usage = client.usage("week")
```

## API Reference

### `Cocapn(api_key=None, base_url=None)`
| Param | Default | Description |
|-------|---------|-------------|
| `api_key` | `COCAPN_API_KEY` env | Your Cocapn API key |
| `base_url` | `https://cocapn.ai` | API base URL |

### `chat(message, *, model="deepseek-chat", system=None, max_tokens=4096, temperature=None, history=None) → ChatResponse`
Returns `ChatResponse(text, cost, tokens: TokenCount, model, provider, raw)`.

### `chat_stream(message, ...) → Iterator[str]`
Yields text chunks.

### `models() → list[ModelInfo]`
### `usage(period="day") → UsageReport`

## How It Fits
- [OpenConstruct Documentation](https://github.com/SuperInstance/openconstruct-docs) — ecosystem-wide docs and guides

The Python counterpart to [cocapn-sdk](https://github.com/SuperInstance/cocapn-sdk) (Node.js). Both talk to the same [API gateway](https://github.com/SuperInstance/api-gateway-1).

- **[cocapn](https://github.com/SuperInstance/cocapn)** — Core agent infrastructure (uses this SDK)
- **[cocapn-explain](https://github.com/SuperInstance/cocapn-explain)** — Agent explainability
- **[cocapn-health-rs](https://github.com/SuperInstance/cocapn-health-rs)** — Fleet health monitoring

## Testing

```bash
pip install pytest pytest-asyncio
pytest tests/
```

## Installation

```bash
pip install cocapn
```

Requires Python 3.9+. Uses `httpx` for HTTP. MIT license.
