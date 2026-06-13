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
