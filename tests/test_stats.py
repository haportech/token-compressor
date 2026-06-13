"""Tests for LogStats — JSONL stats logging with env opt-out."""
import json
import os
import tempfile
from pathlib import Path

import pytest

from token_compressor.stats import LogStats


class TestLogStats:
    """Verify LogStats writes valid JSONL and respects env var opt-out."""

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        """Use a temp file per test, clean env."""
        self.tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.stats_path = Path(self.tmp.name)
        self.tmp.close()
        monkeypatch.setenv("TOKEN_COMPRESSOR_STATS_PATH", str(self.stats_path))
        monkeypatch.setenv("TOKEN_COMPRESSOR_STATS", "1")
        # Reset the singleton state
        LogStats._instance = None
        yield
        if self.stats_path.exists():
            self.stats_path.unlink()

    @property
    def stats(self) -> LogStats:
        return LogStats()

    def read_lines(self) -> list[dict]:
        if not self.stats_path.exists():
            return []
        return [json.loads(line) for line in self.stats_path.read_text().splitlines() if line.strip()]

    def test_record_writes_valid_jsonl_line(self):
        self.stats.record(
            input_tokens=1000,
            output_tokens=200,
            strategy="auto",
            source="test build log",
        )
        lines = self.read_lines()
        assert len(lines) == 1
        entry = lines[0]
        assert entry["input_tokens"] == 1000
        assert entry["output_tokens"] == 200
        assert entry["saved_tokens"] == 800
        assert entry["savings_pct"] == 80.0
        assert entry["strategy"] == "auto"
        assert entry["source"] == "test build log"
        assert "timestamp" in entry

    def test_multiple_records_append(self):
        for i in range(3):
            self.stats.record(input_tokens=100, output_tokens=10, strategy="truncate", source=f"event {i}")
        lines = self.read_lines()
        assert len(lines) == 3

    def test_savings_pct_rounding(self):
        """Percent should be rounded to 1 decimal place."""
        self.stats.record(input_tokens=3, output_tokens=1, strategy="auto", source="test")
        entry = self.read_lines()[0]
        assert entry["savings_pct"] == 66.7

    def test_source_truncated_to_80_chars(self):
        long_source = "a" * 200
        self.stats.record(input_tokens=100, output_tokens=10, strategy="auto", source=long_source)
        entry = self.read_lines()[0]
        assert len(entry["source"]) == 80
        assert entry["source"] == "a" * 80

    def test_env_var_opt_out_disables_writes(self, monkeypatch):
        monkeypatch.setenv("TOKEN_COMPRESSOR_STATS", "0")
        # Re-init singleton so it picks up the env
        LogStats._instance = None
        stats = LogStats()
        stats.record(input_tokens=100, output_tokens=10, strategy="auto", source="should not write")
        # File may exist from fixture, but should be empty
        content = self.stats_path.read_text().strip()
        assert content == "", f"Expected empty file, got: {content}"

    def test_valid_timestamp_iso_format(self):
        self.stats.record(input_tokens=1, output_tokens=0, strategy="json", source="ts test")
        entry = self.read_lines()[0]
        # Basic ISO 8601 check: YYYY-MM-DDTHH:MM:SS
        ts = entry["timestamp"]
        assert len(ts) >= 19
        assert ts[10] == "T"

    def test_negative_savings_when_output_exceeds_input(self):
        """When output is larger than input, saved_tokens should be negative."""
        self.stats.record(input_tokens=50, output_tokens=100, strategy="auto", source="expansion test")
        entry = self.read_lines()[0]
        assert entry["saved_tokens"] == -50
        assert entry["savings_pct"] == -100.0

    def test_zero_input_does_not_crash(self):
        self.stats.record(input_tokens=0, output_tokens=0, strategy="auto", source="zero input")
        entry = self.read_lines()[0]
        assert entry["savings_pct"] == 0.0
        assert entry["saved_tokens"] == 0
