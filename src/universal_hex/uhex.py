"""Universal Hex creation and separation."""

from __future__ import annotations

from enum import IntEnum
from typing import NamedTuple, TypedDict

from . import ihex


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


def _is_uhex_records(records: list[str]) -> bool:
    """Check if records belong to a Universal Hex.

    :param records: List of hex record strings.
    :returns: True if records form a Universal Hex.
    """
    if len(records) < 3:
        return False
    return (
        ihex.get_record_type(records[0]) == ihex.RecordType.ExtendedLinearAddress
        and ihex.get_record_type(records[1]) == ihex.RecordType.BlockStart
        and ihex.get_record_type(records[-1]) == ihex.RecordType.EndOfFile
    )


def _is_makecode_v1_records(records: list[str]) -> bool:
    """Check if records belong to a MakeCode V1 Intel Hex file.

    :param records: List of hex record strings.
    :returns: True if records are from MakeCode V1.
    """
    eof_record = ihex.eof_record()
    try:
        i = records.index(eof_record)
    except ValueError:
        return False

    if i == len(records) - 1:
        # MakeCode v0: metadata in RAM before EoF
        while i > 0:
            i -= 1
            if records[i] == ihex.ext_lin_address_record(0x20000000):
                return True
        return False

    # Check records after EoF
    ram_ext_addr = ihex.ext_lin_address_record(0x20000000)
    i += 1
    while i < len(records):
        record = records[i]
        # OtherData records used for MakeCode project metadata (v2 and v3)
        if ihex.get_record_type(record) == ihex.RecordType.OtherData:
            return True
        # In MakeCode v1 metadata went to RAM memory space 0x2000_0000
        if record == ram_ext_addr:
            return True
        i += 1

    return False


def _ihex_to_uhex_blocks(hex_str: str, board_id: int) -> str:
    """Convert Intel Hex to Universal Hex 512-byte blocks format.

    Note: This format is for future use. Sections format is recommended.

    :param hex_str: Intel Hex file contents.
    :param board_id: Target board ID.
    :returns: Universal Hex formatted string with 512-byte blocks.
    :raises ValueError: If the input is invalid.
    """
    # Use Data records for V1 boards, CustomData for others
    replace_data_record = board_id not in V1_BOARD_IDS

    # Generate constant records
    start_record = ihex.block_start_record(board_id)
    current_ext_addr = ihex.ext_lin_address_record(0)

    # Pre-calculate known record lengths (including \n)
    ext_addr_record_len = len(current_ext_addr) + 1
    start_record_len = len(start_record) + 1
    end_record_base_len = len(ihex.block_end_record(0)) + 1
    pad_record_base_len = len(ihex.padded_data_record(0)) + 1

    hex_records = ihex.split_ihex_into_records(hex_str)
    if not hex_records:
        return ""

    if _is_uhex_records(hex_records):
        raise ValueError(f"Board ID {board_id} Hex is already a Universal Hex.")

    record_padding_capacity = ihex.find_data_field_length(hex_str)

    # Each loop iteration corresponds to a 512-bytes block
    ih = 0
    block_lines: list[str] = []

    while ih < len(hex_records):
        block_len = 0

        # Check for extended address record at block start
        first_record_type = ihex.get_record_type(hex_records[ih])
        if first_record_type == ihex.RecordType.ExtendedLinearAddress:
            current_ext_addr = hex_records[ih]
            ih += 1
        elif first_record_type == ihex.RecordType.ExtendedSegmentAddress:
            current_ext_addr = ihex.convert_ext_seg_to_lin_address(hex_records[ih])
            ih += 1

        block_lines.append(current_ext_addr)
        block_len += ext_addr_record_len
        block_lines.append(start_record)
        block_len += start_record_len
        block_len += end_record_base_len  # Reserve space for block end

        end_of_file = False
        while ih < len(hex_records):
            if block_len + len(hex_records[ih]) + 1 > BLOCK_SIZE:
                break
            record = hex_records[ih]
            ih += 1
            record_type = ihex.get_record_type(record)

            if replace_data_record and record_type == ihex.RecordType.Data:
                record = ihex.convert_record_to(record, ihex.RecordType.CustomData)
            elif record_type == ihex.RecordType.ExtendedLinearAddress:
                current_ext_addr = record
            elif record_type == ihex.RecordType.ExtendedSegmentAddress:
                record = ihex.convert_ext_seg_to_lin_address(record)
                current_ext_addr = record
            elif record_type == ihex.RecordType.EndOfFile:
                end_of_file = True
                break

            block_lines.append(record)
            block_len += len(record) + 1

        if end_of_file:
            # Error if EoF not at the end
            if ih != len(hex_records):
                if _is_makecode_v1_records(hex_records):
                    raise ValueError(
                        f"Board ID {board_id} Hex is from MakeCode, import this hex "
                        "into the MakeCode editor to create a Universal Hex."
                    )
                else:
                    raise ValueError(
                        f"EoF record found at record {ih} of {len(hex_records)} "
                        f"in Board ID {board_id} hex"
                    )
            # EoF goes after Block End Record
            block_lines.append(ihex.block_end_record(0))
            block_lines.append(ihex.eof_record())
        else:
            # Add padding records
            while BLOCK_SIZE - block_len > record_padding_capacity * 2:
                pad_bytes = min(
                    (BLOCK_SIZE - block_len - pad_record_base_len) // 2,
                    record_padding_capacity,
                )
                record = ihex.padded_data_record(pad_bytes)
                block_lines.append(record)
                block_len += len(record) + 1
            block_lines.append(ihex.block_end_record((BLOCK_SIZE - block_len) // 2))

    block_lines.append("")  # Ensure trailing newline
    return "\n".join(block_lines)


def _ihex_to_uhex_sections(hex_str: str, board_id: int) -> str:
    """Convert Intel Hex to Universal Hex 512-byte aligned sections format.

    This is the recommended format for Universal Hex files.

    :param hex_str: Intel Hex file contents.
    :param board_id: Target board ID.
    :returns: Universal Hex formatted string with 512-byte aligned sections.
    :raises ValueError: If the input is invalid.
    """
    section_lines: list[str] = []
    section_len = 0

    def add_record_length(record: str) -> None:
        nonlocal section_len
        section_len += len(record) + 1  # +1 for \n

    def add_record(record: str) -> None:
        section_lines.append(record)
        add_record_length(record)

    hex_records = ihex.split_ihex_into_records(hex_str)
    if not hex_records:
        return ""

    if _is_uhex_records(hex_records):
        raise ValueError(f"Board ID {board_id} Hex is already a Universal Hex.")

    # Check first record type
    ih = 0
    first_record_type = ihex.get_record_type(hex_records[0])
    if first_record_type == ihex.RecordType.ExtendedLinearAddress:
        add_record(hex_records[0])
        ih = 1
    elif first_record_type == ihex.RecordType.ExtendedSegmentAddress:
        add_record(ihex.convert_ext_seg_to_lin_address(hex_records[0]))
        ih = 1
    else:
        add_record(ihex.ext_lin_address_record(0))

    # Add Block Start record
    add_record(ihex.block_start_record(board_id))

    # Process remaining records
    replace_data_record = board_id not in V1_BOARD_IDS
    end_of_file = False

    while ih < len(hex_records):
        record = hex_records[ih]
        ih += 1
        record_type = ihex.get_record_type(record)

        if record_type == ihex.RecordType.Data:
            if replace_data_record:
                add_record(ihex.convert_record_to(record, ihex.RecordType.CustomData))
            else:
                add_record(record)
        elif record_type == ihex.RecordType.ExtendedSegmentAddress:
            add_record(ihex.convert_ext_seg_to_lin_address(record))
        elif record_type == ihex.RecordType.ExtendedLinearAddress:
            add_record(record)
        elif record_type == ihex.RecordType.EndOfFile:
            end_of_file = True
            break

    # Check for mid-file EoF
    if ih != len(hex_records):
        if _is_makecode_v1_records(hex_records):
            raise ValueError(
                f"Board ID {board_id} Hex is from MakeCode, import this hex "
                "into the MakeCode editor to create a Universal Hex."
            )
        else:
            raise ValueError(
                f"EoF record found at record {ih} of {len(hex_records)} "
                f"in Board ID {board_id} hex "
            )

    # Add Block End record length for padding calculation
    add_record_length(ihex.block_end_record(0))

    # Calculate padding needed for 512-byte alignment
    record_no_data_len = len(ihex.padded_data_record(0)) + 1
    record_data_max_bytes = ihex.find_data_field_length(hex_str)
    padding_capacity_chars = record_data_max_bytes * 2

    chars_needed = (BLOCK_SIZE - (section_len % BLOCK_SIZE)) % BLOCK_SIZE
    while chars_needed > padding_capacity_chars:
        byte_len = (chars_needed - record_no_data_len) >> 1  # Integer div by 2
        record = ihex.padded_data_record(min(byte_len, record_data_max_bytes))
        add_record(record)
        chars_needed = (BLOCK_SIZE - (section_len % BLOCK_SIZE)) % BLOCK_SIZE

    section_lines.append(ihex.block_end_record(chars_needed >> 1))
    if end_of_file:
        section_lines.append(ihex.eof_record())
    section_lines.append("")  # Ensure trailing newline

    return "\n".join(section_lines)


def create_uhex(hexes: list[IndividualHex], blocks: bool = False) -> str:
    """Create a Universal Hex from multiple Intel Hex files.

    :param hexes: List of IndividualHex tuples, each containing hex content
        and board ID.
    :param blocks: If True, use "blocks" format instead of "sections".
        The "sections" format (default) is recommended.
    :returns: A Universal Hex file string containing all input hex files.
    :raises ValueError: If input is invalid or already Universal Hex.
    """
    if not hexes:
        return ""

    ihex_to_custom_format = _ihex_to_uhex_blocks if blocks else _ihex_to_uhex_sections
    eof_nl_record = ihex.eof_record() + "\n"

    custom_hexes: list[str] = []

    # Process all but the last hex, removing EoF if present
    for i in range(len(hexes) - 1):
        custom_hex = ihex_to_custom_format(hexes[i].hex, hexes[i].board_id)
        if custom_hex.endswith(eof_nl_record):
            custom_hex = custom_hex[: -len(eof_nl_record)]
        custom_hexes.append(custom_hex)

    # Process the last hex with guaranteed EoF
    last_custom_hex = ihex_to_custom_format(hexes[-1].hex, hexes[-1].board_id)
    custom_hexes.append(last_custom_hex)
    if not last_custom_hex.endswith(eof_nl_record):
        custom_hexes.append(eof_nl_record)

    return "".join(custom_hexes)


def separate_uhex(uhex: str) -> list[IndividualHex]:
    """Separate a Universal Hex into individual Intel Hex files.

    :param uhex: A Universal Hex file string.
    :returns: List of IndividualHex tuples, one per board.
    :raises ValueError: If input is not a valid Universal Hex.
    """
    records = ihex.split_ihex_into_records(uhex)
    if not records:
        raise ValueError("Empty Universal Hex.")

    if not _is_uhex_records(records):
        raise ValueError("Universal Hex format invalid.")

    # Record types to pass through unchanged
    pass_through_types = {
        ihex.RecordType.Data,
        ihex.RecordType.EndOfFile,
        ihex.RecordType.ExtendedSegmentAddress,
        ihex.RecordType.StartSegmentAddress,
    }

    class _HexEntry(TypedDict):
        board_id: int
        last_ext_addr: str
        hex: list[str]

    # Dictionary to hold hexes by board ID
    hexes: dict[int, _HexEntry] = {}
    current_board_id = 0

    for i, record in enumerate(records):
        record_type = ihex.get_record_type(record)

        if record_type in pass_through_types:
            hexes[current_board_id]["hex"].append(record)
        elif record_type == ihex.RecordType.CustomData:
            hexes[current_board_id]["hex"].append(
                ihex.convert_record_to(record, ihex.RecordType.Data)
            )
        elif record_type == ihex.RecordType.ExtendedLinearAddress:
            # Check if next record is BlockStart
            if i + 1 < len(records):
                next_record = records[i + 1]
                if ihex.get_record_type(next_record) == ihex.RecordType.BlockStart:
                    # Process Block Start record (first 2 bytes = board ID)
                    block_start_data = ihex.get_record_data(next_record)
                    if len(block_start_data) != 4:
                        raise ValueError(f"Block Start record invalid: {next_record}")
                    current_board_id = (block_start_data[0] << 8) + block_start_data[1]
                    if current_board_id not in hexes:
                        hexes[current_board_id] = {
                            "board_id": current_board_id,
                            "last_ext_addr": record,
                            "hex": [record],
                        }
                    continue  # Skip, will process next record normally

            # Only add if different from last ext addr
            if hexes[current_board_id]["last_ext_addr"] != record:
                hexes[current_board_id]["last_ext_addr"] = record
                hexes[current_board_id]["hex"].append(record)

    # Build return list
    result: list[IndividualHex] = []
    eof = ihex.eof_record()
    for board_id in hexes:
        hex_list = hexes[board_id]["hex"]
        # Ensure all hexes end with EoF record
        if hex_list[-1] != eof:
            hex_list.append(eof)
        result.append(
            IndividualHex(
                hex="\n".join(hex_list) + "\n",
                board_id=hexes[board_id]["board_id"],
            )
        )

    return result


def is_uhex(hex_str: str) -> bool:
    """Check if a hex string is a Universal Hex file.

    Very simple test only checking for the opening Extended Linear Address and
    Block Start records. Manually iterates string for performance (~20x faster
    than parsing records).

    :param hex_str: A hex file string.
    :returns: True if the string is a Universal Hex file.
    """
    # Check the beginning of Extended Linear Address record
    ela_record_beginning = ":02000004"
    if not hex_str.startswith(ela_record_beginning):
        return False

    # Find index of next record (handle unknown line endings)
    i = len(ela_record_beginning)
    max_search = ihex.MAX_RECORD_STR_LEN + 3
    while i < len(hex_str) and hex_str[i] != ":" and i < max_search:
        i += 1

    if i >= len(hex_str):
        return False

    # Check the beginning of Block Start record
    block_start_beginning = ":0400000A"
    return hex_str[i : i + len(block_start_beginning)] == block_start_beginning


def _is_makecode_v1(hex_str: str) -> bool:
    """Check if a hex string is a MakeCode V1 Intel Hex file.

    :param hex_str: A hex file string.
    :returns: True if the string is a MakeCode V1 hex file.
    """
    return _is_makecode_v1_records(ihex.split_ihex_into_records(hex_str))
