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
    # Content before the truncation notice should end at a sentence boundary
    content = result.split("\n\n[truncated")[0]
    assert content.endswith(".") and "Second" not in content


def test_truncate_includes_truncation_notice():
    text = "word " * 5000
    result = smart_truncate(text, target_tokens=100)
    assert "[truncated" in result.lower()
