"""Test configuration — disable stats logging for all tests."""
import os


def pytest_configure(config):
    os.environ.setdefault("TOKEN_COMPRESSOR_STATS", "0")
