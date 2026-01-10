"""
Tests for utilities.
"""

import pytest

from universal_hex.utils import (
    hex_to_bytes,
    byte_to_hex,
    bytes_to_hex,
    concat_bytes,
)


class TestHexToBytes:
    """Test hex_to_bytes()."""

    def test_converts_hexadecimal_string_to_bytes(self):
        assert hex_to_bytes("0102030A11FF80") == bytes([1, 2, 3, 10, 17, 255, 128])

    def test_converts_empty_string_to_empty_bytes(self):
        assert hex_to_bytes("") == b""

    def test_throws_error_on_non_hex_string(self):
        with pytest.raises(ValueError, match="non-hex characters"):
            hex_to_bytes("carlos")

    def test_throws_error_when_string_has_odd_length(self):
        with pytest.raises(ValueError, match="not divisible by 2"):
            hex_to_bytes("123")


class TestBytesToHex:
    """Test bytes_to_hex()."""

    def test_converts_bytes_to_hexadecimal_string(self):
        result = bytes_to_hex(bytes([1, 2, 3, 10, 17, 255, 128]))
        assert result == "0102030A11FF80"

    def test_converts_empty_bytes_to_empty_string(self):
        assert bytes_to_hex(b"") == ""


class TestRoundTrip:
    """Loop back between bytes_to_hex() and hex_to_bytes()."""

    def test_converts_bytes_to_hex_and_back(self):
        initial_bytes = bytes([66, 8, 90, 110, 217, 255, 128, 0])
        result = hex_to_bytes(bytes_to_hex(initial_bytes))
        assert result == initial_bytes

    def test_converts_hex_to_bytes_and_back(self):
        initial_str = "28B1304601F018FF304608F034FB234F"
        result = bytes_to_hex(hex_to_bytes(initial_str))
        assert result == initial_str


class TestByteToHex:
    """Test byte_to_hex().

    Note: byte_to_hex is an internal function optimized for speed.
    No validation is performed; callers must ensure valid input (0-255).
    """

    def test_converts_byte_to_hexadecimal_string(self):
        assert byte_to_hex(10) == "0A"
        assert byte_to_hex(0) == "00"
        assert byte_to_hex(255) == "FF"

    def test_converts_all_byte_values(self):
        """Verify lookup table covers full byte range."""
        for i in range(256):
            assert byte_to_hex(i) == f"{i:02X}"


class TestConcatBytes:
    """Test concat_bytes()."""

    def test_concatenates_bytes_of_different_sizes(self):
        result = concat_bytes(
            bytes([1, 2]),
            bytes([3, 4, 5, 6, 7]),
            bytes([8]),
            bytes([9, 10]),
        )
        assert result == bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    def test_concatenates_empty_input_to_empty_bytes(self):
        assert concat_bytes() == b""
