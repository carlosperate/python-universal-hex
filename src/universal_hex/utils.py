"""Utility functions for hex string and byte conversions."""

from __future__ import annotations


def hex_to_bytes(hex_str: str) -> bytes:
    """Convert a hexadecimal string to bytes.

    :param hex_str: A string of hexadecimal characters (e.g., "48656C6C6F").
    :returns: The decoded bytes.
    :raises ValueError: If the string contains non-hex characters or has odd length.
    """
    if len(hex_str) % 2 != 0:
        raise ValueError("Hex string length is not divisible by 2")
    try:
        return bytes.fromhex(hex_str)
    except ValueError as e:
        raise ValueError("String contains non-hex characters") from e


# Precomputed lookup table for fast byte to hex conversion
_BYTE_TO_HEX = tuple(f"{i:02X}" for i in range(256))


def byte_to_hex(value: int) -> str:
    """Convert a single byte value to a two-character uppercase hex string.

    Internal function optimized for speed. No validation performed.

    :param value: An integer in the range 0-255.
    :returns: A two-character uppercase hex string.
    """
    return _BYTE_TO_HEX[value]


def bytes_to_hex(data: bytes) -> str:
    """Convert bytes to a hexadecimal string.

    :param data: The bytes to convert.
    :returns: An uppercase hexadecimal string representation.
    """
    return data.hex().upper()


def concat_bytes(*arrays: bytes) -> bytes:
    """Concatenate multiple byte arrays into one.

    :param arrays: Variable number of bytes objects to concatenate.
    :returns: A single bytes object containing all input bytes.
    """
    return b"".join(arrays)
