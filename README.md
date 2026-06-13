# Token Compressor MCP Server

MCP server that compresses text before it enters an LLM's context window. 99% savings on noisy build logs. Fully local — no API calls, no network.

## How It Works

```text
Before: 6,600 tokens of dev server logs (99% repeated noise)
After:   21 tokens — just the unique lines
```

## Tools

| Tool | What It Does |
|------|-------------|
| `compress` | Squeeze text down with 4 strategies |
| `count_tokens` | Count tokens via cl100k encoding |

## Strategies

| Strategy | Best For | Example |
|----------|----------|---------|
| `auto` | General use | Dedup then truncate. 99% savings on logs. |
| `deduplicate` | Repeated output | Collapse "error: timeout × 300" → one line |
| `truncate` | Long prose | Cut at sentence/newline boundaries to target |
| `json` | API responses | Minify + strip verbose keys recursively |

## Install

```bash
git clone https://github.com/haportech/token-compressor.git
cd token-compressor
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Hermes Integration

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  token-compressor:
    command: "/path/to/token-compressor/.venv/bin/python3"
    args: ["-m", "token_compressor.server"]
    timeout: 30
```

Restart Hermes. Tools appear as `mcp_token_compressor_compress` and `mcp_token_compressor_count_tokens`.

## Usage (Python)

```python
from token_compressor.compressors.compress import compress
from token_compressor.token_counter import count_tokens

# 99% savings on noisy logs
log = ("error: timeout\n" * 1000) + "deploy successful\n"
print(count_tokens(log))     # ~2000
compressed = compress(log, strategy="auto", target_tokens=50)
print(count_tokens(compressed))  # ~20

# Minify + strip debug noise from API responses
result = compress(json_text, strategy="json", strip_keys=["debug_info", "stack_trace"])
```

## Dev

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## Architecture

```
src/token_compressor/
├── server.py          # MCP server (stdio transport)
├── token_counter.py   # tiktoken wrapper (cl100k_base)
└── compressors/
    ├── compress.py    # Strategy dispatch
    ├── truncate.py    # Smart boundary-aware cut
    ├── deduplicate.py # Collapse repeated lines
    └── structure.py   # JSON minify + recursive key strip
```

Built by [Jarvise](https://github.com/haportech) — Vientiane, Laos.
