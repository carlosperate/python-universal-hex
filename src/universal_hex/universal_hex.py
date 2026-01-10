"""Universal Hex creation and separation."""

from __future__ import annotations

from enum import IntEnum
from typing import List, NamedTuple


class BoardId(IntEnum):
    """micro:bit board identifiers for Universal Hex."""
    V1 = 0x9900
    V2 = 0x9903


class IndividualHex(NamedTuple):
    """An individual Intel Hex file with its board ID."""
    hex: str
    board_id: int


# Board IDs that use standard Data records (0x00) instead of CustomData (0x0D)
V1_BOARD_IDS = (0x9900, 0x9901)

# USB block size for alignment
BLOCK_SIZE = 512


def _ihex_to_uhex_blocks(hex_str: str, board_id: int) -> str:
    """Convert Intel Hex to Universal Hex 512-byte blocks format.
    
    Note: This format is for future use. Sections format is recommended.
    
    Args:
        hex_str: Intel Hex file contents.
        board_id: Target board ID.
        
    Returns:
        Universal Hex formatted string with 512-byte blocks.
    """
    raise NotImplementedError()


def _ihex_to_uhex_sections(hex_str: str, board_id: int) -> str:
    """Convert Intel Hex to Universal Hex 512-byte aligned sections format.
    
    This is the recommended format for Universal Hex files.
    
    Args:
        hex_str: Intel Hex file contents.
        board_id: Target board ID.
        
    Returns:
        Universal Hex formatted string with 512-byte aligned sections.
    """
    raise NotImplementedError()


def create_uhex(hexes: List[IndividualHex]) -> str:
    """Create a Universal Hex from multiple Intel Hex files.
    
    Args:
        hexes: List of IndividualHex tuples, each containing hex content
               and board ID. Must contain at least 2 entries.
               
    Returns:
        A Universal Hex file string containing all input hex files.
        
    Raises:
        ValueError: If input is invalid or already Universal Hex.
    """
    raise NotImplementedError()


def separate_uhex(uhex: str) -> List[IndividualHex]:
    """Separate a Universal Hex into individual Intel Hex files.
    
    Args:
        uhex: A Universal Hex file string.
        
    Returns:
        List of IndividualHex tuples, one per board.
        
    Raises:
        ValueError: If input is not a valid Universal Hex.
    """
    raise NotImplementedError()


def is_uhex(hex_str: str) -> bool:
    """Check if a hex string is a Universal Hex file.
    
    Args:
        hex_str: A hex file string.
        
    Returns:
        True if the string is a Universal Hex file.
    """
    raise NotImplementedError()


def _is_makecode_v1(hex_str: str) -> bool:
    """Check if a hex string is a MakeCode V1 Intel Hex file.
    
    Args:
        hex_str: A hex file string.
        
    Returns:
        True if the string is a MakeCode V1 hex file.
    """
    raise NotImplementedError()
