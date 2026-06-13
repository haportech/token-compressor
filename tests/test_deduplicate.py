"""Tests for deduplication compressor."""
from token_compressor.compressors.deduplicate import deduplicate


def test_dedup_identical_lines():
    text = "error: timeout\nerror: timeout\nerror: timeout\n"
    result = deduplicate(text)
    # Collapsed to one annotation line; trailing empty line retained
    assert "error: timeout  [repeated 3×]" in result
    assert result.count("error: timeout") == 1


def test_dedup_unique_lines_unchanged():
    text = "line one\nline two\nline three"
    result = deduplicate(text)
    assert result == text


def test_dedup_reports_savings():
    text = "repeated\n" * 100
    result = deduplicate(text)
    assert "repeated" in result
    assert "100" in result  # all 100 lines collapsed
