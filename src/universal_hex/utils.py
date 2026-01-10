"""Utility functions for hex string and byte conversions."""

from __future__ import annotations


def hex_to_bytes(hex_str: str) -> bytes:
    """Convert a hexadecimal string to bytes.
    
    Args:
        hex_str: A string of hexadecimal characters (e.g., "48656C6C6F").
        
    Returns:
        The decoded bytes.
        
    Raises:
        ValueError: If the string contains non-hex characters or has odd length.
    """
    raise NotImplementedError()


def byte_to_hex(value: int, prefix: str = "") -> str:
    """Convert a single byte value to a hexadecimal string.
    
    Args:
        value: An integer in the range 0-255.
        prefix: Optional prefix to add (e.g., "0x").
        
    Returns:
        A two-character uppercase hex string, optionally prefixed.
        
    Raises:
        ValueError: If value is not in range 0-255 or is not an integer.
    """
    raise NotImplementedError()


def bytes_to_hex(data: bytes) -> str:
    """Convert bytes to a hexadecimal string.
    
    Args:
        data: The bytes to convert.
        
    Returns:
        An uppercase hexadecimal string representation.
    """
    raise NotImplementedError()


def concat_bytes(*arrays: bytes) -> bytes:
    """Concatenate multiple byte arrays into one.
    
    Args:
        *arrays: Variable number of bytes objects to concatenate.
        
    Returns:
        A single bytes object containing all input bytes.
    """
    raise NotImplementedError()
