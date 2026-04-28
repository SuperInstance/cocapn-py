# cocapn — Python SDK

One API key, any AI model, see what it costs.

## Install

```bash
pip install cocapn
```

## Quick Start

```python
from cocapn import Cocapn

client = Cocapn(api_key="cocapn_your_key")

response = client.chat("Explain quantum computing", model="deepseek-chat")
print(response.text)      # "Quantum computing uses..."
print(response.cost)      # 0.0042
print(response.tokens)    # TokenCount(in=15, out=847)
print(response.tokens.total)  # 862
```

## Streaming

```python
for chunk in client.chat_stream("Tell me a story", model="claude-3-5-sonnet"):
    print(chunk, end="", flush=True)
```

## System Prompts

```python
response = client.chat(
    "Summarize this article",
    model="gpt-4o",
    system="You write concise summaries.",
)
```

## Conversation History

```python
history = [
    {"role": "user", "content": "My name is Casey"},
    {"role": "assistant", "content": "Hello Casey!"},
]
response = client.chat("What's my name?", history=history)
# "Your name is Casey."
```

## Models

```python
for model in client.models():
    print(f"{model.id}: ${model.cost_in}/${model.cost_out} per 1M tokens")
```

## Usage

```python
usage = client.usage("week")
print(f"Total cost: ${usage['totalCost']}")
print(f"Requests: {usage['requests']}")
```

## Environment Variables

```bash
export COCAPN_API_KEY="cocapn_your_key"
export COCAPN_BASE_URL="https://cocapn.ai"  # optional
```

## Context Manager

```python
with Cocapn() as client:
    response = client.chat("Hello!")
```

## Quick One-Liner

```python
from cocapn import chat
response = chat("Hello!", model="deepseek-chat")
```
