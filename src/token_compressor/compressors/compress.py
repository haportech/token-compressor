"""Unified compress function with strategy dispatch."""
from .truncate import smart_truncate
from .deduplicate import deduplicate
from .structure import compress_json
from ..token_counter import count_tokens
from ..stats import log_stats


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

    input_tok = count_tokens(text)

    if strategy == "truncate":
        result = smart_truncate(text, target_tokens)
    elif strategy == "deduplicate":
        result = deduplicate(text)
    elif strategy == "json":
        result = compress_json(text, strip_keys=strip_keys)
    elif strategy == "auto":
        deduped = deduplicate(text)
        if count_tokens(deduped) > target_tokens:
            result = smart_truncate(deduped, target_tokens)
        else:
            result = deduped
    else:
        result = text  # unknown strategy → passthrough

    output_tok = count_tokens(result)
    source = text[:80]
    log_stats.record(
        input_tokens=input_tok,
        output_tokens=output_tok,
        strategy=strategy,
        source=source,
    )
    return result
