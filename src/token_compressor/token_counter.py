"""Token counting using tiktoken."""
import tiktoken

_ENCODER = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens in text using cl100k_base encoding."""
    if not text:
        return 0
    return len(_ENCODER.encode(text))
