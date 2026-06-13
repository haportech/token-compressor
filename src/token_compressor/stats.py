"""Singleton stats logger for token compression events.

Writes JSONL to ~/.hermes/token-compressor-stats.jsonl.
Opt-out via TOKEN_COMPRESSOR_STATS=0.
Override path via TOKEN_COMPRESSOR_STATS_PATH.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def _stats_path() -> Path:
    """Resolve the stats file path."""
    env_path = os.environ.get("TOKEN_COMPRESSOR_STATS_PATH")
    if env_path:
        return Path(env_path)
    return Path.home() / ".hermes" / "token-compressor-stats.jsonl"


class LogStats:
    """Singleton that writes compression events to a JSONL file."""

    _instance: "LogStats | None" = None

    def __new__(cls) -> "LogStats":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._enabled = os.environ.get("TOKEN_COMPRESSOR_STATS", "1") != "0"
            cls._instance._path = _stats_path()
        return cls._instance

    def record(
        self,
        *,
        input_tokens: int,
        output_tokens: int,
        strategy: str,
        source: str,
    ) -> None:
        """Record one compression event as a JSONL line.

        Args:
            input_tokens: Token count of the original text
            output_tokens: Token count of the compressed text
            strategy: Compression strategy used
            source: Brief description (truncated to 80 chars)
        """
        if not self._enabled:
            return

        if input_tokens > 0:
            pct = round((input_tokens - output_tokens) / input_tokens * 100, 1)
        else:
            pct = 0.0

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "saved_tokens": input_tokens - output_tokens,
            "savings_pct": pct,
            "strategy": strategy,
            "source": source[:80],
        }

        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# Module-level convenience instance
log_stats = LogStats()
