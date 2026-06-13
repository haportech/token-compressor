# Token Compressor MCP Server — Implementation Plan

> **For Hermes:** Use claude-code skill to delegate to Claude Code (configured with DeepSeek v4 Flash).

**Goal:** Build an MCP server that provides token-aware text compression tools for Hermes — slash API costs by stripping noise from tool outputs before they hit the LLM context.

**Architecture:** Python MCP server using `mcp` SDK. Three compression strategies: smart truncation (boundary-aware), deduplication (pattern collapse), structure extraction (keep what matters). One MCP tool `compress` with strategy selection. Token counting via tiktoken.

**Tech Stack:** Python 3.12+, mcp SDK, tiktoken, pytest

---

### Task 1: Project scaffold and dependencies

**Objective:** Create the project skeleton with pyproject.toml and install all dependencies.

**Files:**
- Create: `/Users/jack/token-compressor/pyproject.toml`
- Create: `/Users/jack/token-compressor/src/token_compressor/__init__.py`
- Create: `/Users/jack/token-compressor/src/token_compressor/server.py` (stub)

**Step 1: Write pyproject.toml**

```toml
[project]
name = "token-compressor"
version = "0.1.0"
description = "MCP server for token-aware text compression"
requires-python = ">=3.12"
dependencies = [
    "mcp>=1.0.0",
    "tiktoken>=0.7.0",
]

[project.scripts]
token-compressor = "token_compressor.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Step 2: Create directory structure**

```
mkdir -p src/token_compressor/compressors tests
```

**Step 3: Create __init__.py stub**

```python
"""Token Compressor — MCP server for compressing text before LLM context."""
```

**Step 4: Install dependencies**

```bash
cd /Users/jack/token-compressor && python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
```

Wait, let's keep deps simple:
```bash
cd /Users/jack/token-compressor && python3 -m venv .venv && source .venv/bin/activate && pip install mcp tiktoken pytest
```

**Step 5: Verify imports**

```bash
cd /Users/jack/token-compressor && .venv/bin/python3 -c "import mcp; import tiktoken; print('OK')"
```
Expected: `OK`

---

### Task 2: Token counter utility

**Objective:** Create a utility that counts tokens in text using tiktoken (cl100k_base for GPT/DeepSeek compatibility).

**Files:**
- Create: `/Users/jack/token-compressor/src/token_compressor/token_counter.py`
- Create: `/Users/jack/token-compressor/tests/test_token_counter.py`

**Step 1: Write failing test**

```python
"""Tests for token_counter."""
from token_compressor.token_counter import count_tokens


def test_count_tokens_empty():
    assert count_tokens("") == 0


def test_count_tokens_simple():
    tokens = count_tokens("Hello world")
    assert tokens == 2


def test_count_tokens_multiline():
    text = "Line one\nLine two\nLine three"
    tokens = count_tokens(text)
    assert tokens > 3
    assert isinstance(tokens, int)
```

**Step 2: Run test — verify failure**

```bash
cd /Users/jack/token-compressor && .venv/bin/python3 -m pytest tests/test_token_counter.py -v
```
Expected: FAIL — ModuleNotFoundError

**Step 3: Write implementation**

```python
"""Token counting using tiktoken."""
import tiktoken

_ENCODER = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens in text using cl100k_base encoding."""
    if not text:
        return 0
    return len(_ENCODER.encode(text))
```

**Step 4: Run test — verify pass**

```bash
cd /Users/jack/token-compressor && .venv/bin/python3 -m pytest tests/test_token_counter.py -v
```
Expected: 3 passed

**Step 5: Commit**

---

### Task 3: Smart truncation compressor

**Objective:** Truncate text to target token count while preserving sentence/paragraph boundaries.

**Files:**
- Create: `/Users/jack/token-compressor/src/token_compressor/compressors/__init__.py`
- Create: `/Users/jack/token-compressor/src/token_compressor/compressors/truncate.py`
- Create: `/Users/jack/token-compressor/tests/test_truncate.py`

**Step 1: Write failing test**

```python
"""Tests for smart truncation compressor."""
from token_compressor.compressors.truncate import smart_truncate


def test_truncate_noop_when_under_limit():
    text = "Short text under limit."
    result = smart_truncate(text, target_tokens=100)
    assert result == text


def test_truncate_reduces_long_text():
    text = "word " * 5000  # ~5000 tokens
    result = smart_truncate(text, target_tokens=100)
    from token_compressor.token_counter import count_tokens
    assert count_tokens(result) <= 110  # small margin


def test_truncate_preserves_boundaries():
    text = "First sentence. Second sentence. Third sentence. Fourth sentence."
    result = smart_truncate(text, target_tokens=5)
    # Should end at a sentence boundary, not mid-word
    assert result.endswith(".") or result.endswith("!") or result.endswith("?")


def test_truncate_includes_truncation_notice():
    text = "word " * 5000
    result = smart_truncate(text, target_tokens=100)
    assert "[truncated" in result.lower()
```

**Step 2: Run test — verify failure**

**Step 3: Write implementation**

```python
"""Smart truncation — cuts to target token count at sentence boundaries."""
import re
from ..token_counter import count_tokens


def smart_truncate(text: str, target_tokens: int = 4000) -> str:
    """
    Truncate text to approximately target_tokens while preserving
    sentence boundaries. Adds a truncation notice with stats.
    """
    total = count_tokens(text)
    if total <= target_tokens:
        return text

    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = ""
    for sentence in sentences:
        candidate = result + " " + sentence if result else sentence
        if count_tokens(candidate) > target_tokens:
            break
        result = candidate

    truncated_count = count_tokens(result)
    saved = total - truncated_count
    pct = round(saved / total * 100)
    notice = (
        f"\n\n[truncated: {truncated_count}/{total} tokens kept, "
        f"{saved} tokens ({pct}%) saved]"
    )
    return result + notice
```

**Step 4: Run test — verify pass**

**Step 5: Commit**

---

### Task 4: Deduplication compressor

**Objective:** Collapse repeated lines/patterns in logs and structured output.

**Files:**
- Create: `/Users/jack/token-compressor/src/token_compressor/compressors/deduplicate.py`
- Create: `/Users/jack/token-compressor/tests/test_deduplicate.py`

**Step 1: Write failing test**

```python
"""Tests for deduplication compressor."""
from token_compressor.compressors.deduplicate import deduplicate


def test_dedup_identical_lines():
    text = "error: timeout\nerror: timeout\nerror: timeout\n"
    result = deduplicate(text)
    assert result.count("error: timeout") == 2  # first occurrence + count line


def test_dedup_unique_lines_unchanged():
    text = "line one\nline two\nline three"
    result = deduplicate(text)
    assert result == text


def test_dedup_reports_savings():
    text = "repeated\n" * 100
    result = deduplicate(text)
    assert "repeated" in result
    assert "99" in result  # 99 duplicates collapsed
```

**Step 2: Run test — verify failure**

**Step 3: Write implementation**

```python
"""Deduplication — collapse repeated lines with count annotations."""
from collections import OrderedDict


def deduplicate(text: str) -> str:
    """
    Collapse consecutive duplicate lines, replacing runs with
    a single line + count annotation. Non-consecutive duplicates
    are left as-is (semantically they may differ).
    """
    lines = text.split("\n")
    if len(lines) <= 1:
        return text

    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        count = 1
        while i + count < len(lines) and lines[i + count] == line:
            count += 1
        if count == 1:
            result.append(line)
        else:
            result.append(f"{line}  [repeated {count}×]")
        i += count

    return "\n".join(result)
```

**Step 4: Run test — verify pass**

**Step 5: Commit**

---

### Task 5: Structure-aware compression

**Objective:** For JSON output, strip whitespace and optionally remove specified keys.

**Files:**
- Create: `/Users/jack/token-compressor/src/token_compressor/compressors/structure.py`
- Create: `/Users/jack/token-compressor/tests/test_structure.py`

**Step 1: Write failing test**

```python
"""Tests for structure-aware compression."""
import json
from token_compressor.compressors.structure import compress_json


def test_compress_json_minifies():
    data = {"key": "value", "nested": {"a": 1, "b": 2}}
    pretty = json.dumps(data, indent=2)
    result = compress_json(pretty)
    # Should be minified (no pretty whitespace)
    assert "\n" not in result
    parsed = json.loads(result)
    assert parsed == data


def test_compress_json_strips_keys():
    data = {"keep": "important", "debug": "verbose", "trace": "noisy"}
    text = json.dumps(data)
    result = compress_json(text, strip_keys=["debug", "trace"])
    parsed = json.loads(result)
    assert "keep" in parsed
    assert "debug" not in parsed
    assert "trace" not in parsed


def test_compress_json_non_json_passthrough():
    result = compress_json("not json at all")
    assert result == "not json at all"
```

**Step 2: Run test — verify failure**

**Step 3: Write implementation**

```python
"""Structure-aware compression for JSON output."""
import json


def compress_json(text: str, strip_keys: list[str] | None = None) -> str:
    """
    Compress JSON text: minify whitespace, optionally remove keys.
    Returns original text if not valid JSON.
    """
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return text

    if strip_keys:
        if isinstance(data, dict):
            for key in strip_keys:
                data.pop(key, None)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    for key in strip_keys:
                        item.pop(key, None)

    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)
```

**Step 4: Run test — verify pass**

**Step 5: Commit**

---

### Task 6: Unified compressor with strategy dispatch

**Objective:** Single `compress` function that dispatches to the right strategy.

**Files:**
- Create: `/Users/jack/token-compressor/src/token_compressor/compressors/compress.py`
- Create: `/Users/jack/token-compressor/tests/test_compress.py`

**Step 1: Write failing test**

```python
"""Tests for unified compress function."""
from token_compressor.compressors.compress import compress


def test_compress_truncate_strategy():
    text = "long " * 10000
    result = compress(text, strategy="truncate", target_tokens=50)
    assert "[truncated" in result.lower()


def test_compress_deduplicate_strategy():
    text = "dup\n" * 50
    result = compress(text, strategy="deduplicate")
    assert "repeated 50×" in result


def test_compress_json_strategy():
    result = compress('{"a": 1, "b": 2}', strategy="json", strip_keys=["b"])
    import json
    assert json.loads(result) == {"a": 1}


def test_compress_auto_detects():
    # Long repetitive text → should use dedup+truncate
    text = "repeated line\n" * 2000
    result = compress(text, strategy="auto", target_tokens=100)
    # Should be shorter than original
    from token_compressor.token_counter import count_tokens
    assert count_tokens(result) < count_tokens(text)


def test_compress_empty():
    assert compress("") == ""
```

**Step 2: Run test — verify failure**

**Step 3: Write implementation**

```python
"""Unified compress function with strategy dispatch."""
from .truncate import smart_truncate
from .deduplicate import deduplicate
from .structure import compress_json
from ..token_counter import count_tokens


def compress(
    text: str,
    strategy: str = "auto",
    target_tokens: int = 4000,
    strip_keys: list[str] | None = None,
) -> str:
    """
    Compress text using the specified strategy.

    Strategies:
        truncate   — smart boundary-aware truncation
        deduplicate — collapse repeated lines
        json       — minify JSON, optionally strip keys
        auto       — apply dedup then truncate (best for general use)

    Args:
        text: The text to compress
        strategy: Compression strategy (default: auto)
        target_tokens: Target token count for truncate/auto (default: 4000)
        strip_keys: Keys to remove for json strategy
    """
    if not text:
        return text

    if strategy == "truncate":
        return smart_truncate(text, target_tokens)

    if strategy == "deduplicate":
        return deduplicate(text)

    if strategy == "json":
        return compress_json(text, strip_keys=strip_keys)

    if strategy == "auto":
        # Dedup first (cheap), then truncate if still over target
        deduped = deduplicate(text)
        if count_tokens(deduped) > target_tokens:
            return smart_truncate(deduped, target_tokens)
        return deduped

    return text  # unknown strategy → passthrough
```

**Step 4: Run test — verify pass**

**Step 5: Commit**

---

### Task 7: MCP server

**Objective:** Wire up the MCP server exposing `compress` and `count_tokens` tools.

**Files:**
- Modify: `/Users/jack/token-compressor/src/token_compressor/server.py`
- Create: `/Users/jack/token-compressor/tests/test_server.py`

**Step 1: Write failing test**

```python
"""Tests for MCP server tools (call functions directly, not via stdio)."""
from token_compressor.server import handle_compress, handle_count_tokens


def test_handle_compress():
    result = handle_compress(
        text="repeated\n" * 100,
        strategy="deduplicate",
        target_tokens=4000,
    )
    assert "repeated" in result


def test_handle_count_tokens():
    result = handle_count_tokens(text="hello world")
    assert result["tokens"] == 2
    assert result["chars"] == 11


def test_handle_compress_empty():
    result = handle_compress(text="", strategy="auto")
    assert result == ""
```

**Step 2: Run test — verify failure**

**Step 3: Write implementation**

```python
"""MCP server for Token Compressor."""
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .compressors.compress import compress
from .token_counter import count_tokens

server = Server("token-compressor")


def handle_compress(
    text: str,
    strategy: str = "auto",
    target_tokens: int = 4000,
    strip_keys: str = "",
) -> str:
    """Handle compress tool call (non-async for testing)."""
    keys = [k.strip() for k in strip_keys.split(",") if k.strip()] if strip_keys else None
    return compress(text, strategy=strategy, target_tokens=target_tokens, strip_keys=keys)


def handle_count_tokens(text: str) -> dict:
    """Handle count_tokens tool call."""
    return {
        "tokens": count_tokens(text),
        "chars": len(text),
    }


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="compress",
            description=(
                "Compress text to reduce token usage. Strategies: auto (dedup+truncate), "
                "truncate (boundary-aware cut), deduplicate (collapse repeats), "
                "json (minify+strip keys). Default: auto at 4000 tokens."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to compress"},
                    "strategy": {
                        "type": "string",
                        "enum": ["auto", "truncate", "deduplicate", "json"],
                        "default": "auto",
                    },
                    "target_tokens": {
                        "type": "integer",
                        "default": 4000,
                        "description": "Target token count for truncate/auto",
                    },
                    "strip_keys": {
                        "type": "string",
                        "default": "",
                        "description": "Comma-separated keys to strip (json strategy)",
                    },
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="count_tokens",
            description="Count tokens in text using cl100k_base encoding.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to count tokens for"},
                },
                "required": ["text"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "compress":
        result = compress(
            text=arguments["text"],
            strategy=arguments.get("strategy", "auto"),
            target_tokens=arguments.get("target_tokens", 4000),
            strip_keys=(
                [k.strip() for k in arguments.get("strip_keys", "").split(",") if k.strip()]
                if arguments.get("strip_keys")
                else None
            ),
        )
        return [TextContent(type="text", text=result)]

    if name == "count_tokens":
        result = handle_count_tokens(arguments["text"])
        return [TextContent(type="text", text=str(result))]

    raise ValueError(f"Unknown tool: {name}")


def main():
    """Entry point for `token-compressor` CLI."""
    asyncio.run(stdio_server(server))


if __name__ == "__main__":
    main()
```

**Step 4: Run test — verify pass**

**Step 5: Commit**

---

### Task 8: Integration test — end to end

**Objective:** Verify the full pipeline works: compress real-world outputs and confirm token savings.

**Files:**
- Create: `/Users/jack/token-compressor/tests/test_integration.py`

**Step 1: Write test**

```python
"""Integration tests with real-world text patterns."""
from token_compressor.compressors.compress import compress
from token_compressor.token_counter import count_tokens


def test_log_file_compression():
    """Simulate compressing a noisy build log."""
    log = (
        "[2026-06-13 10:00:01] INFO Starting build\n"
        + "[2026-06-13 10:00:01] DEBUG Loading config\n"
        + "error: missing dependency\n"
        + "error: missing dependency\n"
        + "error: missing dependency\n"
        + "[2026-06-13 10:00:02] INFO Build failed\n"
    ) * 100

    original_tokens = count_tokens(log)
    result = compress(log, strategy="auto", target_tokens=200)
    compressed_tokens = count_tokens(result)

    assert compressed_tokens <= 250  # near target
    assert compressed_tokens < original_tokens
    assert "missing dependency" in result  # error preserved


def test_json_api_response_compression():
    """Simulate compressing a large JSON API response."""
    import json
    data = {
        "results": [{"id": i, "name": f"item-{i}", "debug_info": "x" * 500} for i in range(100)],
        "metadata": {"count": 100, "page": 1},
    }
    text = json.dumps(data, indent=2)

    original_tokens = count_tokens(text)
    result = compress(text, strategy="json")
    compressed_tokens = count_tokens(result)

    assert compressed_tokens < original_tokens * 0.5  # at least 50% savings
    assert "\n" not in result  # minified


def test_no_crash_on_special_chars():
    """Should not crash on binary-looking strings."""
    text = "\x00\x01\x02" + "hello" * 1000 + "\xff\xfe"
    result = compress(text, strategy="auto", target_tokens=100)
    assert len(result) > 0


def test_count_tokens_accuracy():
    assert count_tokens("Hello world") == 2
    assert count_tokens("") == 0
    assert count_tokens("token") == 1
```

**Step 2: Run test — verify pass**

---

### Task 9: CLAUDE.md and MCP config for Claude Code

**Objective:** Create project context so Claude Code understands this project when working on it.

**Files:**
- Create: `/Users/jack/token-compressor/CLAUDE.md`
- Create: `/Users/jack/token-compressor/.claude/settings.json`

**Step 1: Write CLAUDE.md**

```markdown
# Token Compressor

MCP server that compresses text to save LLM tokens. Three strategies: smart
truncation, deduplication, JSON minification.

## Architecture
- `src/token_compressor/server.py` — MCP server entry point
- `src/token_compressor/compressors/` — compression strategies
- `src/token_compressor/token_counter.py` — tiktoken wrapper (cl100k_base)

## Commands
- Run tests: `.venv/bin/python3 -m pytest tests/ -v`
- Run server: `.venv/bin/python3 -m token_compressor.server`

## Code Standards
- Type hints on all public functions
- pytest for testing
- No external API calls (fully local compression)
```

**Step 2: Write .claude/settings.json**

```json
{
  "permissions": {
    "allow": [
      "Bash(python3 *)",
      "Bash(pytest *)",
      "Bash(pip *)",
      "Bash(git *)",
      "Read",
      "Write",
      "Edit"
    ]
  }
}
```

**Step 3: Commit everything**

---

### Task 10: Hermes MCP registration

**Objective:** Tell Hermes about this MCP server so it can use the tools.

**Files:**
- Create: `/Users/jack/.hermes/mcp-servers/token-compressor.json`

```json
{
  "mcpServers": {
    "token-compressor": {
      "command": "/Users/jack/token-compressor/.venv/bin/python3",
      "args": ["-m", "token_compressor.server"]
    }
  }
}
```

Update Hermes config to include this server. Check `~/.hermes/config.yaml` for `mcp:` section.

---

## Execution Strategy

Use Claude Code in print mode (`-p`) to implement each task. Prefer batch: 2-3 tasks per Claude Code invocation.

```bash
cd /Users/jack/token-compressor
claude -p "Implement tasks 1-3 from .hermes/plans/2026-06-13_token-compressor-mcp.md: project scaffold, token counter, smart truncation. Run tests after each task." --allowedTools "Read,Write,Edit,Bash" --max-turns 20
```
