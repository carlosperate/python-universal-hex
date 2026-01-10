"""Intel HEX record creation and parsing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import List


# Maximum record string length (including colon, excluding newline)
MAX_RECORD_STR_LENGTH = 75


class RecordType(IntEnum):
    """Intel HEX and Universal HEX record types."""
    Data = 0x00
    EndOfFile = 0x01
    ExtendedSegmentAddress = 0x02
    StartSegmentAddress = 0x03
    ExtendedLinearAddress = 0x04
    StartLinearAddress = 0x05
    # Universal Hex extensions
    BlockStart = 0x0A
    BlockEnd = 0x0B
    PaddedData = 0x0C
    CustomData = 0x0D
    OtherData = 0x0E


@dataclass
class Record:
    """Parsed Intel HEX record."""
    byte_count: int
    address: int
    record_type: RecordType
    data: bytes
    checksum: int


def create_record(
    record_type: RecordType,
    address: int,
    data: bytes,
) -> str:
    """Create an Intel HEX record string.
    
    Args:
        record_type: The record type.
        address: 16-bit address (0x0000-0xFFFF).
        data: Data bytes (max 32 bytes).
        
    Returns:
        A complete Intel HEX record string (without newline).
        
    Raises:
        ValueError: If address is out of range or data is too large.
    """
    raise NotImplementedError()


def get_record_type(record: str) -> RecordType:
    """Extract the record type from a record string.
    
    Args:
        record: An Intel HEX record string.
        
    Returns:
        The RecordType enum value.
        
    Raises:
        ValueError: If the record type is invalid.
    """
    raise NotImplementedError()


def get_record_data(record: str) -> bytes:
    """Extract the data field from a record string.
    
    Args:
        record: An Intel HEX record string.
        
    Returns:
        The data bytes from the record.
        
    Raises:
        ValueError: If the record cannot be parsed.
    """
    raise NotImplementedError()


def parse_record(record: str) -> Record:
    """Parse an Intel HEX record string into a Record object.
    
    Args:
        record: An Intel HEX record string.
        
    Returns:
        A Record object with all parsed fields.
        
    Raises:
        ValueError: If the record is invalid.
    """
    raise NotImplementedError()


def eof_record() -> str:
    """Return the End Of File record.
    
    Returns:
        The string ":00000001FF".
    """
    raise NotImplementedError()


def ext_lin_address_record(address: int) -> str:
    """Create an Extended Linear Address record.
    
    Args:
        address: 32-bit address; upper 16 bits are used.
        
    Returns:
        An Extended Linear Address record string.
        
    Raises:
        ValueError: If address is out of range.
    """
    raise NotImplementedError()


def block_start_record(board_id: int) -> str:
    """Create a Universal Hex Block Start record.
    
    Args:
        board_id: The board ID (e.g., 0x9900 for V1, 0x9903 for V2).
        
    Returns:
        A Block Start record string.
        
    Raises:
        ValueError: If board_id is out of range.
    """
    raise NotImplementedError()


def block_end_record(padding_length: int = 0) -> str:
    """Create a Universal Hex Block End record.
    
    Args:
        padding_length: Number of padding bytes to include.
        
    Returns:
        A Block End record string.
        
    Raises:
        ValueError: If padding_length is invalid.
    """
    raise NotImplementedError()


def padded_data_record(padding_length: int) -> str:
    """Create a Universal Hex Padded Data record.
    
    Args:
        padding_length: Number of 0xFF padding bytes.
        
    Returns:
        A Padded Data record string.
        
    Raises:
        ValueError: If padding_length is invalid.
    """
    raise NotImplementedError()


def convert_record_to(record: str, new_type: RecordType) -> str:
    """Convert a record to a different type, updating checksum.
    
    Args:
        record: An Intel HEX record string.
        new_type: The new record type.
        
    Returns:
        The record with updated type and checksum.
    """
    raise NotImplementedError()


def convert_ext_seg_to_lin_address(record: str) -> str:
    """Convert Extended Segment Address to Extended Linear Address.
    
    Args:
        record: An Extended Segment Address record.
        
    Returns:
        An equivalent Extended Linear Address record.
        
    Raises:
        ValueError: If the record is not a valid Extended Segment Address.
    """
    raise NotImplementedError()


def split_intel_hex_into_records(hex_str: str) -> List[str]:
    """Split an Intel HEX file string into individual records.
    
    Handles various line endings (\\n, \\r\\n, \\r).
    
    Args:
        hex_str: The Intel HEX file contents.
        
    Returns:
        A list of record strings (without line endings).
    """
    raise NotImplementedError()


def find_data_field_length(hex_str: str) -> int:
    """Find the maximum data field length used in a hex file.
    
    Args:
        hex_str: The Intel HEX file contents.
        
    Returns:
        The maximum data field length (16 or 32).
        
    Raises:
        ValueError: If records have data larger than 32 bytes.
    """
    raise NotImplementedError()
