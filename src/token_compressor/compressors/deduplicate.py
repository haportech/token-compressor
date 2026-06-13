"""Deduplication — collapse repeated lines with count annotations."""
from collections import OrderedDict


def deduplicate(text: str) -> str:
    """
    Collapse consecutive duplicate lines, replacing runs with
    a single line + count annotation. Non-consecutive duplicates
    are left as-is (semantically they may differ).
    """
    lines = text.split("\n")
    if len(lines) <= 1:
        return text

    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        count = 1
        while i + count < len(lines) and lines[i + count] == line:
            count += 1
        if count == 1:
            result.append(line)
        else:
            result.append(f"{line}  [repeated {count}×]")
        i += count

    return "\n".join(result)
