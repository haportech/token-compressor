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
