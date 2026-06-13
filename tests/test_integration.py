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
    result = compress(text, strategy="json", strip_keys=["debug_info"])
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
