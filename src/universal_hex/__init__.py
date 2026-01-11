"""
universal_hex - Create and process micro:bit Universal Hex files.

Universal Hex is a superset of the Intel Hex format that can contain
data for multiple micro:bit board versions (V1 and V2) in a single file.
"""

from __future__ import annotations

from .uhex import (
    BoardId,
    IndividualHex,
    create_uhex,
    is_uhex,
    separate_uhex,
)

__version__ = "0.1.0"

__all__ = [
    "BoardId",
    "IndividualHex",
    "create_uhex",
    "separate_uhex",
    "is_uhex",
]
