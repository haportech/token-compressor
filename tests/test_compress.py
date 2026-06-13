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
