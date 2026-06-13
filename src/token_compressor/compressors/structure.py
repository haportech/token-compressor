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
            for value in data.values():
                _strip_recursive(value, strip_keys)
        elif isinstance(data, list):
            for item in data:
                _strip_recursive(item, strip_keys)

    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def _strip_recursive(obj, strip_keys: list[str]):
    """Recursively strip keys from nested dicts/lists."""
    if isinstance(obj, dict):
        for key in strip_keys:
            obj.pop(key, None)
        for value in obj.values():
            _strip_recursive(value, strip_keys)
    elif isinstance(obj, list):
        for item in obj:
            _strip_recursive(item, strip_keys)
