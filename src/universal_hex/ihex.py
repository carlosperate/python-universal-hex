"""Intel HEX record creation and parsing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from .utils import byte_to_hex, bytes_to_hex, concat_bytes, hex_to_bytes

# Maximum data bytes per record (DAPLink doesn't support more than 32)
RECORD_DATA_MAX_BYTES = 32

# Record string constants
START_CODE = ":"
START_CODE_LEN = 1
BYTE_COUNT_LEN = 2
ADDRESS_LEN = 4
RECORD_TYPE_LEN = 2
CHECKSUM_LEN = 2

# Minimum record: :LLAAAATT CC (no data)
MIN_RECORD_STR_LEN = (
    START_CODE_LEN + BYTE_COUNT_LEN + ADDRESS_LEN + RECORD_TYPE_LEN + CHECKSUM_LEN
)
# Maximum record: minimum + 32 bytes of data (64 hex chars)
MAX_RECORD_STR_LEN = MIN_RECORD_STR_LEN + RECORD_DATA_MAX_BYTES * 2

# Field positions in record string (after colon)
BYTE_COUNT_INDEX = START_CODE_LEN
ADDRESS_INDEX = BYTE_COUNT_INDEX + BYTE_COUNT_LEN
RECORD_TYPE_INDEX = ADDRESS_INDEX + ADDRESS_LEN
DATA_INDEX = RECORD_TYPE_INDEX + RECORD_TYPE_LEN


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


def _is_record_type_valid(record_type: int) -> bool:
    """Check if a record type value is valid.

    :param record_type: The record type value to check.
    :returns: True if valid, False otherwise.
    """
    return (
        RecordType.Data <= record_type <= RecordType.StartLinearAddress
        or RecordType.BlockStart <= record_type <= RecordType.OtherData
    )


def _calc_checksum(data_bytes: bytes) -> int:
    """Calculate Intel HEX checksum (LSB of two's complement of sum).

    :param data_bytes: Bytes to calculate checksum for.
    :returns: Checksum byte (0-255).
    """
    return (-sum(data_bytes)) & 0xFF


def create_record(
    record_type: RecordType,
    address: int,
    data: bytes,
) -> str:
    """Create an Intel HEX record string.

    :param record_type: The record type.
    :param address: 16-bit address (0x0000-0xFFFF).
    :param data: Data bytes (max 32 bytes).
    :returns: A complete Intel HEX record string (without newline).
    :raises ValueError: If address is out of range or data is too large.
    """
    if address < 0 or address > 0xFFFF:
        raise ValueError(f"Record ({record_type}) address out of range: {address}")

    byte_count = len(data)
    if byte_count > RECORD_DATA_MAX_BYTES:
        raise ValueError(
            f"Record ({record_type}) data has too many bytes ({byte_count})."
        )

    if not _is_record_type_valid(record_type):
        raise ValueError(f"Record type '{record_type}' is not valid.")

    # Build record content: byte_count, address_hi, address_lo, record_type, data
    record_content = concat_bytes(
        bytes([byte_count, (address >> 8) & 0xFF, address & 0xFF, record_type]),
        data,
    )
    record_content_str = bytes_to_hex(record_content)
    checksum_str = byte_to_hex(_calc_checksum(record_content))

    return f"{START_CODE}{record_content_str}{checksum_str}"


def _validate_record(record: str) -> None:
    """Validate basic record format.

    :param record: Intel HEX record string.
    :raises ValueError: If the record is invalid.
    """
    # Strip trailing whitespace/newlines for length check
    record_stripped = record.rstrip()

    if len(record_stripped) < MIN_RECORD_STR_LEN:
        raise ValueError(f"Record length too small: {record}")

    if len(record_stripped) > MAX_RECORD_STR_LEN:
        raise ValueError(f"Record length is too large: {record}")

    if not record.startswith(":"):
        raise ValueError(f'Record does not start with a ":": {record}')


def get_record_type(record: str) -> RecordType:
    """Extract the record type from a record string.

    :param record: An Intel HEX record string.
    :returns: The RecordType enum value.
    :raises ValueError: If the record type is invalid.
    """
    _validate_record(record)

    record_type_str = record[RECORD_TYPE_INDEX : RECORD_TYPE_INDEX + RECORD_TYPE_LEN]
    record_type = int(record_type_str, 16)

    if not _is_record_type_valid(record_type):
        raise ValueError(
            f"Record type '{record_type_str}' from record '{record}' is not valid."
        )

    return RecordType(record_type)


def get_record_data(record: str) -> bytes:
    """Extract the data field from a record string.

    :param record: An Intel HEX record string.
    :returns: The data bytes from the record.
    :raises ValueError: If the record cannot be parsed.
    """
    try:
        # Data is everything after header, before last 2 chars (checksum)
        data_hex = record[DATA_INDEX:-CHECKSUM_LEN]
        if not data_hex:
            return b""
        return hex_to_bytes(data_hex)
    except ValueError as e:
        raise ValueError(f'Could not parse Intel Hex record "{record}": {e}') from e


def parse_record(record: str) -> Record:
    """Parse an Intel HEX record string into a Record object.

    :param record: An Intel HEX record string.
    :returns: A Record object with all parsed fields.
    :raises ValueError: If the record is invalid.
    """
    _validate_record(record)

    try:
        # Parse everything after the colon
        record_bytes = hex_to_bytes(record[1:])
    except ValueError as e:
        raise ValueError(f'Could not parse Intel Hex record "{record}": {e}') from e

    byte_count = record_bytes[0]
    address = (record_bytes[1] << 8) | record_bytes[2]
    record_type = record_bytes[3]
    data = record_bytes[4 : 4 + byte_count]
    checksum = record_bytes[4 + byte_count]

    # Verify length matches byte count
    expected_length = 4 + byte_count + 1  # header + data + checksum
    if len(record_bytes) > expected_length:
        raise ValueError(
            f'Parsed record "{record}" is larger than indicated by the byte count.'
            f"\n\tExpected: {expected_length}; Length: {len(record_bytes)}."
        )

    return Record(
        byte_count=byte_count,
        address=address,
        record_type=RecordType(record_type),
        data=data,
        checksum=checksum,
    )


def eof_record() -> str:
    """Return the End Of File record.

    :returns: The string ":00000001FF".
    """
    return ":00000001FF"


def ext_lin_address_record(address: int) -> str:
    """Create an Extended Linear Address record.

    :param address: 32-bit address; upper 16 bits are used.
    :returns: An Extended Linear Address record string.
    :raises ValueError: If address is out of range.
    """
    if address < 0 or address > 0xFFFFFFFF:
        raise ValueError(
            f"Address '{address}' for Extended Linear Address record is out of range."
        )

    # Use upper 16 bits of the 32-bit address
    data = bytes([(address >> 24) & 0xFF, (address >> 16) & 0xFF])
    return create_record(RecordType.ExtendedLinearAddress, 0, data)


def block_start_record(board_id: int) -> str:
    """Create a Universal Hex Block Start record.

    :param board_id: The board ID (e.g., 0x9900 for V1, 0x9903 for V2).
    :returns: A Block Start record string.
    :raises ValueError: If board_id is out of range.
    """
    if board_id < 0 or board_id > 0xFFFF:
        raise ValueError("Board ID out of range when creating Block Start record.")

    data = bytes([(board_id >> 8) & 0xFF, board_id & 0xFF, 0xC0, 0xDE])
    return create_record(RecordType.BlockStart, 0, data)


def block_end_record(padding_length: int = 0) -> str:
    """Create a Universal Hex Block End record.

    :param padding_length: Number of padding bytes to include (default 0).
    :returns: A Block End record string.
    :raises ValueError: If padding_length is invalid.
    """
    if padding_length < 0:
        raise ValueError("Padding length cannot be negative.")

    # Cache common cases for performance
    if padding_length == 0x04:
        return ":0400000BFFFFFFFFF5"
    if padding_length == 0x0C:
        return ":0C00000BFFFFFFFFFFFFFFFFFFFFFFFFF5"

    data = bytes([0xFF] * padding_length)
    return create_record(RecordType.BlockEnd, 0, data)


def padded_data_record(padding_length: int) -> str:
    """Create a Universal Hex Padded Data record.

    :param padding_length: Number of 0xFF padding bytes.
    :returns: A Padded Data record string.
    :raises ValueError: If padding_length is invalid.
    """
    if padding_length < 0:
        raise ValueError("Padding length cannot be negative.")

    data = bytes([0xFF] * padding_length)
    return create_record(RecordType.PaddedData, 0, data)


def convert_record_to(record: str, new_type: RecordType) -> str:
    """Convert a record to a different type, updating checksum.

    :param record: An Intel HEX record string.
    :param new_type: The new record type.
    :returns: The record with updated type and checksum.
    """
    parsed = parse_record(record)

    # Rebuild record content with new type
    record_content = concat_bytes(
        bytes(
            [
                len(parsed.data),
                (parsed.address >> 8) & 0xFF,
                parsed.address & 0xFF,
                new_type,
            ]
        ),
        parsed.data,
    )
    record_content_str = bytes_to_hex(record_content)
    checksum_str = byte_to_hex(_calc_checksum(record_content))

    return f"{START_CODE}{record_content_str}{checksum_str}"


def convert_ext_seg_to_lin_address(record: str) -> str:
    """Convert Extended Segment Address to Extended Linear Address.

    :param record: An Extended Segment Address record.
    :returns: An equivalent Extended Linear Address record.
    :raises ValueError: If the record is not a valid Extended Segment Address.
    """
    segment_address = get_record_data(record)

    # Must be exactly 2 bytes, high nibble of first byte must be 0,
    # second byte must be 0
    if (
        len(segment_address) != 2
        or (segment_address[0] & 0x0F) != 0  # Only multiples of 0x1000
        or segment_address[1] != 0
    ):
        raise ValueError(f"Invalid Extended Segment Address record {record}")

    start_address = segment_address[0] << 12
    return ext_lin_address_record(start_address)


def split_ihex_into_records(hex_str: str) -> list[str]:
    """Split an Intel HEX file string into individual records.

    Handles various line endings (\\n, \\r\\n, \\r).

    :param hex_str: The Intel HEX file contents.
    :returns: A list of record strings (without line endings).
    """
    # Normalize line endings: replace \r with nothing, split on \n
    # This handles \r\n (becomes \n), \r (becomes nothing), and \n
    output = hex_str.replace("\r", "").split("\n")

    # Filter out empty strings
    return [line for line in output if line]


def find_data_field_length(hex_str: str) -> int:
    """Find the maximum data field length used in a hex file.

    :param hex_str: The Intel HEX file contents.
    :returns: The maximum data field length (16 or 32).
    :raises ValueError: If records have data larger than 32 bytes.
    """
    records = split_ihex_into_records(hex_str)

    max_data_bytes = 16
    max_data_bytes_count = 0

    for record in records:
        # Data length = (record_length - min_record_length) / 2
        data_bytes_length = (len(record) - MIN_RECORD_STR_LEN) // 2

        if data_bytes_length > max_data_bytes:
            max_data_bytes = data_bytes_length
            max_data_bytes_count = 0
        elif data_bytes_length == max_data_bytes:
            max_data_bytes_count += 1

        # Stop early if we've found enough records at max size
        if max_data_bytes_count > 12:
            break

    if max_data_bytes > RECORD_DATA_MAX_BYTES:
        raise ValueError(f"Intel Hex record data size is too large: {max_data_bytes}")

    return max_data_bytes
