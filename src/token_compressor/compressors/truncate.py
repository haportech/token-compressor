"""Smart truncation — cuts to target token count at sentence boundaries."""
import re
from ..token_counter import count_tokens


def smart_truncate(text: str, target_tokens: int = 4000) -> str:
    """
    Truncate text to approximately target_tokens while preserving
    sentence boundaries. Adds a truncation notice with stats.
    """
    total = count_tokens(text)
    if total <= target_tokens:
        return text

    sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
    result = ""
    for sentence in sentences:
        candidate = result + " " + sentence if result else sentence
        if count_tokens(candidate) > target_tokens:
            break
        result = candidate

    truncated_count = count_tokens(result)
    saved = total - truncated_count
    pct = round(saved / total * 100)
    notice = (
        f"\n\n[truncated: {truncated_count}/{total} tokens kept, "
        f"{saved} tokens ({pct}%) saved]"
    )
    return result + notice
