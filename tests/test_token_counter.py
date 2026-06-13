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
