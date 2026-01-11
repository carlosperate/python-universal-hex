"""Pytest configuration and shared fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def hex_files_dir() -> Path:
    """Return the path to the hex-files test fixtures directory."""
    return Path(__file__).parent / "hex-files"


@pytest.fixture
def load_hex_file(hex_files_dir: Path):
    """Factory fixture to load hex files by name."""

    def _load(filename: str) -> str:
        filepath = hex_files_dir / filename
        # Read as binary first to preserve exact line endings for comparison
        return filepath.read_text(encoding="ascii")

    return _load
