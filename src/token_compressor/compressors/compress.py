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
