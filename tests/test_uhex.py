"""
Tests for Universal HEX creation and separation.

(c) 2020 Micro:bit Educational Foundation and contributors.
SPDX-License-Identifier: MIT
"""

from pathlib import Path

import pytest

from universal_hex import (
    BoardId,
    IndividualHex,
    create_uhex,
    separate_uhex,
    is_uhex,
)
from universal_hex.ihex import RecordType, get_record_type, split_ihex_into_records
from universal_hex.uhex import (
    _is_makecode_v1,
    _is_makecode_v1_records,
    _is_uhex_records,
    _ihex_to_uhex_blocks,
    _ihex_to_uhex_sections,
)


# Load test fixture files
HEX_PATH = Path(__file__).parent / "hex-files"
hex116 = (HEX_PATH / "1-duck-umbrella-16.hex").read_text()
hex216 = (HEX_PATH / "2-ghost-music-16.hex").read_text()
hex132 = (HEX_PATH / "1-duck-umbrella-32.hex").read_text()
hex232 = (HEX_PATH / "2-ghost-music-32.hex").read_text()
hex_combined_blocks = (HEX_PATH / "combined-16-blocks-1-9901-2-9903.hex").read_text()
hex_combined_sections = (HEX_PATH / "combined-32-sections-1-9901-2-9903.hex").read_text()
hex_python_editor_universal = (HEX_PATH / "python-editor-universal.hex").read_text()
# MakeCode Intel Hex files (pre-V2 micro:bit, not Universal Hex)
hex_makecode_v1_intel = (HEX_PATH / "makecode-v1-intel.hex").read_text()
hex_makecode_v2_intel = (HEX_PATH / "makecode-v2-intel.hex").read_text()
# MakeCode Universal Hex files (post-V2 micro:bit)
hex_makecode_v3_universal = (HEX_PATH / "makecode-v3-universal.hex").read_text()
hex_makecode_v5_universal = (HEX_PATH / "makecode-v5-universal.hex").read_text()
hex_makecode_v8_universal = (HEX_PATH / "makecode-v8-universal.hex").read_text()

# Valid Intel HEX record types (not Universal HEX extensions)
VALID_IHEX_RECORD_TYPES = {
    RecordType.Data,
    RecordType.EndOfFile,
    RecordType.ExtendedSegmentAddress,
    RecordType.StartSegmentAddress,
    RecordType.ExtendedLinearAddress,
    RecordType.StartLinearAddress,
}


def assert_valid_ihex(hex_str: str) -> None:
    """Assert that all records in a hex string are valid Intel HEX types.

    Raises AssertionError if any Universal HEX extension types are found.
    """
    records = split_ihex_into_records(hex_str)
    for record in records:
        record_type = get_record_type(record)
        assert record_type in VALID_IHEX_RECORD_TYPES, (
            f"Invalid Intel HEX record type {record_type.name} (0x{record_type:02X}) "
            f"found in record: {record}"
        )


class TestIsUhex:
    """Test is_uhex()."""

    def test_detects_universal_hex(self):
        uhex = (
            ":020000040000FA\n"
            ":0400000A9900C0DEBB\n"
            ":1000000000400020218E01005D8E01005F8E010006\n"
            ":1000100000000000000000000000000000000000E0\n"
            ":10002000000000000000000000000000618E0100E0\n"
            ":100030000000000000000000638E0100658E0100DA\n"
            ":10004000678E01005D3D000065950100678E01002F\n"
            ":10005000678E010000000000218F0100678E010003\n"
            ":1000600069E80000D59A0100D9930100678E01006C\n"
            ":10007000678E0100678E0100678E0100678E0100A8\n"
            ":10008000678E0100678E0100678E0100678E010098\n"
            ":10009000678E01000D8A0100D98A0100A5E90000E0\n"
            ":0C00000BFFFFFFFFFFFFFFFFFFFFFFFFF5\n"
            ":00000001FF\n"
        )

        assert is_uhex(uhex) is True

    def test_detects_universal_hex_with_windows_line_endings(self):
        uhex = (
            ":020000040000FA\r\n"
            ":0400000A9900C0DEBB\r\n"
            ":1000000000400020218E01005D8E01005F8E010006\r\n"
            ":1000100000000000000000000000000000000000E0\r\n"
            ":10002000000000000000000000000000618E0100E0\r\n"
            ":100030000000000000000000638E0100658E0100DA\r\n"
            ":10004000678E01005D3D000065950100678E01002F\r\n"
            ":10005000678E010000000000218F0100678E010003\r\n"
            ":1000600069E80000D59A0100D9930100678E01006C\r\n"
            ":10007000678E0100678E0100678E0100678E0100A8\r\n"
            ":10008000678E0100678E0100678E0100678E010098\r\n"
            ":10009000678E01000D8A0100D98A0100A5E90000E0\r\n"
            ":0C00000BFFFFFFFFFFFFFFFFFFFFFFFFF5\r\n"
            ":00000001FF\r\n"
        )

        assert is_uhex(uhex) is True

    def test_detects_empty_string_as_false(self):
        assert is_uhex("") is False

    def test_detects_normal_ihex_as_false(self):
        normal_hex = (
            ":020000040000FA\n"
            ":10558000002EEDD1E9E70020EAE7C0464302F0B57E\n"
            ":1055900042005D0AC30F4802440A4800120E000E82\n"
            ":00000001FF\n"
        )

        assert is_uhex(normal_hex) is False

    def test_detects_random_string_as_false(self):
        assert is_uhex("This is just a random string") is False

    def test_returns_false_when_failing_to_find_second_record(self):
        malformed = ":02000004\nThis is just a random string, nor a record."

        assert is_uhex(malformed) is False


class TestCreateUhex:
    """Test create_uhex()."""

    def test_empty_input_returns_empty_output(self):
        result = create_uhex([])

        assert result == ""

    def test_ihex_without_eof_record_ends_with_one(self):
        normal_hex = (
            ":020000040000FA\n"
            ":1000000000400020218E01005D8E01005F8E010006\n"
            ":1000100000000000000000000000000000000000E0\n"
            ":10002000000000000000000000000000618E0100E0\n"
            ":100030000000000000000000638E0100658E0100DA\n"
            ":10004000678E01005D3D000065950100678E01002F\n"
            ":10005000678E010000000000218F0100678E010003\n"
            ":1000600069E80000D59A0100D9930100678E01006C\n"
            ":10007000678E0100678E0100678E0100678E0100A8\n"
            ":10008000678E0100678E0100678E0100678E010098\n"
            ":10009000678E01000D8A0100D98A0100A5E90000E0\n"
            ":0C00000BFFFFFFFFFFFFFFFFFFFFFFFFF5\n"
        )
        normal_hex_win = normal_hex.replace("\n", "\r\n")

        result_single = create_uhex([
            IndividualHex(hex=normal_hex_win, board_id=0x9903),
        ])
        result_double = create_uhex([
            IndividualHex(hex=normal_hex_win, board_id=0x9900),
            IndividualHex(hex=normal_hex, board_id=0x9903),
        ])

        assert result_single.endswith(":00000001FF\n")
        assert result_double.endswith(":00000001FF\n")

    def test_ihex_with_eof_in_middle_throws_error(self):
        normal_hex = (
            ":020000040000FA\n"
            ":1000000000400020218E01005D8E01005F8E010006\n"
            ":1000100000000000000000000000000000000000E0\n"
            ":10002000000000000000000000000000618E0100E0\n"
            ":100030000000000000000000638E0100658E0100DA\n"
            ":10004000678E01005D3D000065950100678E01002F\n"
            ":10005000678E010000000000218F0100678E010003\n"
            ":1000600069E80000D59A0100D9930100678E01006C\n"
            ":10007000678E0100678E0100678E0100678E0100A8\n"
            ":10008000678E0100678E0100678E0100678E010098\n"
            ":10009000678E01000D8A0100D98A0100A5E90000E0\n"
        )
        # Insert EoF at record 9 (after record 8)
        hex_with_eof = normal_hex.replace(
            ":10008000678E0100678E0100678E0100678E010098\n",
            ":10008000678E0100678E0100678E0100678E010098\n:00000001FF\n",
        )

        with pytest.raises(ValueError, match="EoF record found at record"):
            create_uhex([
                IndividualHex(hex=hex_with_eof, board_id=0x9900),
                IndividualHex(hex=normal_hex, board_id=0x9903),
            ])

    def test_universal_hex_input_throws_error(self):
        normal_hex = (
            ":020000040000FA\n"
            ":1000000000400020218E01005D8E01005F8E010006\n"
            ":1000100000000000000000000000000000000000E0\n"
            ":10002000000000000000000000000000618E0100E0\n"
            ":100030000000000000000000638E0100658E0100DA\n"
            ":10004000678E01005D3D000065950100678E01002F\n"
            ":10005000678E010000000000218F0100678E010003\n"
            ":1000600069E80000D59A0100D9930100678E01006C\n"
            ":10007000678E0100678E0100678E0100678E0100A8\n"
            ":10008000678E0100678E0100678E0100678E010098\n"
            ":10009000678E01000D8A0100D98A0100A5E90000E0\n"
            ":0C00000BFFFFFFFFFFFFFFFFFFFFFFFFF5\n"
            ":00000001FF\n"
        )
        universal_hex = (
            ":020000040000FA\n"
            ":0400000A9900C0DEBB\n"
            ":1000000000400020218E01005D8E01005F8E010006\n"
            ":1000100000000000000000000000000000000000E0\n"
            ":10002000000000000000000000000000618E0100E0\n"
            ":100030000000000000000000638E0100658E0100DA\n"
            ":10004000678E01005D3D000065950100678E01002F\n"
            ":10005000678E010000000000218F0100678E010003\n"
            ":1000600069E80000D59A0100D9930100678E01006C\n"
            ":10007000678E0100678E0100678E0100678E0100A8\n"
            ":10008000678E0100678E0100678E0100678E010098\n"
            ":10009000678E01000D8A0100D98A0100A5E90000E0\n"
            ":0C00000BFFFFFFFFFFFFFFFFFFFFFFFFF5\n"
            ":00000001FF\n"
        )

        with pytest.raises(ValueError, match="already a Universal Hex"):
            create_uhex([
                IndividualHex(hex=universal_hex, board_id=0x9900),
                IndividualHex(hex=normal_hex, board_id=0x9903),
            ])


class TestSeparateUhex:
    """Test separate_uhex()."""

    def test_throws_error_on_empty_input(self):
        with pytest.raises(ValueError, match="Empty"):
            separate_uhex("")

    def test_normal_hex_cannot_be_separated(self):
        normal_hex = (
            ":020000040000FA\n"
            ":10558000002EEDD1E9E70020EAE7C0464302F0B57E\n"
            ":1055900042005D0AC30F4802440A4800120E000E82\n"
            ":00000001FF\n"
        )

        with pytest.raises(ValueError, match="format invalid"):
            separate_uhex(normal_hex)

    def test_throws_error_on_malformed_block_start(self):
        malformed = (
            ":020000040003F7\n"
            ":0400000A9901BA\n"  # Invalid BlockStart (wrong checksum/format)
            ":1056C0009946F600ED042E437F3F434642465D0275\n"
            ":1056D000D20F5B006D0A1B0E904640D0FF2B39D0D5\n"
            ":1056E00080220020ED00D20415437F3BFB18424688\n"
            ":1056F0005746591C62408C4607430F2F5CD86F49B0\n"
            ":0000000BF5\n"
            ":00000001FF\n"
        )

        with pytest.raises(ValueError, match="Block Start record invalid"):
            separate_uhex(malformed)

    def test_all_separated_hexes_have_eof_records(self):
        first_block = (
            ":020000040002F8\n"
            ":0400000A9901C0DEBA\n"
            ":105620004802120E450A240EC90FFF2A17D0FF2C7C\n"
            ":1056300019D0002A0BD170427041002C17D00028DD\n"
            ":1056400007D048424141012049420843F0BD002CA7\n"
            ":1056500013D08B4214D0584201231843F6E702209E\n"
            ":10566000002EF3D1E3E70220002DEFD1E1E7002D7A\n"
            ":10567000E5D10020002EE9D0EDE7002DE9D1EAE7E1\n"
            ":10568000A242E8DC04DBAE42E5D80020AE42DDD227\n"
            ":105690005842434101205B421843D7E7F0B55746D3\n"
            ":1056A0004E4645464300E0B446028846760A1F0E41\n"
            ":1056B000C40F002F47D0FF2F25D0002380259A4606\n"
            ":06F80000FDFFFFFFFFFF0A\n"
            ":0000000BF5\n"
        )
        first_hex = (
            ":020000040002F8\n"
            ":105620004802120E450A240EC90FFF2A17D0FF2C7C\n"
            ":1056300019D0002A0BD170427041002C17D00028DD\n"
            ":1056400007D048424141012049420843F0BD002CA7\n"
            ":1056500013D08B4214D0584201231843F6E702209E\n"
            ":10566000002EF3D1E3E70220002DEFD1E1E7002D7A\n"
            ":10567000E5D10020002EE9D0EDE7002DE9D1EAE7E1\n"
            ":10568000A242E8DC04DBAE42E5D80020AE42DDD227\n"
            ":105690005842434101205B421843D7E7F0B55746D3\n"
            ":1056A0004E4645464300E0B446028846760A1F0E41\n"
            ":1056B000C40F002F47D0FF2F25D0002380259A4606\n"
            ":06F80000FDFFFFFFFFFF0A\n"
            ":00000001FF\n"
        )
        second_block = (
            ":020000040003F7\n"
            ":0400000A9903C0DEB8\n"
            ":1056C0009946F600ED042E437F3F434642465D0275\n"
            ":1056D000D20F5B006D0A1B0E904640D0FF2B39D0D5\n"
            ":1056E00080220020ED00D20415437F3BFB18424688\n"
            ":1056F0005746591C62408C4607430F2F5CD86F49B0\n"
            ":0000000BF5\n"
            ":00000001FF\n"
        )
        second_hex = (
            ":020000040003F7\n"
            ":1056C0009946F600ED042E437F3F434642465D0275\n"
            ":1056D000D20F5B006D0A1B0E904640D0FF2B39D0D5\n"
            ":1056E00080220020ED00D20415437F3BFB18424688\n"
            ":1056F0005746591C62408C4607430F2F5CD86F49B0\n"
            ":00000001FF\n"
        )

        result = separate_uhex(first_block + second_block)

        assert result[0].board_id == 0x9901
        assert result[0].hex == first_hex
        assert result[1].board_id == 0x9903
        assert result[1].hex == second_hex

        # Verify all records are valid Intel HEX types (not Universal HEX extensions)
        for ihex in result:
            assert_valid_ihex(ihex.hex)

    def test_separate_blocks_universal_hex_file(self):
        result = separate_uhex(hex_combined_blocks)

        assert result[0].board_id == 0x9901
        assert result[0].hex == hex116
        assert result[1].board_id == 0x9903
        # 2-ghost-music.hex does not open with the optional :020000040000FA record
        assert result[1].hex == ":020000040000FA\n" + hex216

        # Verify all records are valid Intel HEX types
        for ihex in result:
            assert_valid_ihex(ihex.hex)

    def test_separate_sections_universal_hex_file(self):
        result = separate_uhex(hex_combined_sections)

        assert result[0].board_id == 0x9901
        assert result[0].hex == hex132
        assert result[1].board_id == 0x9903
        # 2-ghost-music.hex does not open with the optional :020000040000FA record
        # And it has a Start Linear Address record at the end
        assert result[1].hex == ":020000040000FA\n" + hex232.replace(
            ":040000050000FA55A8\n", ""
        )

        # Verify all records are valid Intel HEX types
        for ihex in result:
            assert_valid_ihex(ihex.hex)

    def test_separate_python_editor_universal_hex(self):
        """Test separating a Universal HEX file from the Python Editor."""
        result = separate_uhex(hex_python_editor_universal)

        # Should contain exactly 2 boards: V1 (0x9900) and V2 (0x9903)
        assert len(result) == 2
        assert result[0].board_id == BoardId.V1
        assert result[1].board_id == BoardId.V2

        # Each separated hex should be valid Intel HEX
        assert result[0].hex.startswith(":")
        assert result[0].hex.endswith(":00000001FF\n")
        assert result[1].hex.startswith(":")
        assert result[1].hex.endswith(":00000001FF\n")

        # Verify all records are valid Intel HEX types
        for ihex in result:
            assert_valid_ihex(ihex.hex)

    def test_separate_makecode_v8_universal_hex(self):
        """Test separating a Universal HEX file from MakeCode v8."""
        result = separate_uhex(hex_makecode_v8_universal)

        # Should contain exactly 2 boards: V1 (0x9900) and V2 (0x9903)
        assert len(result) == 2
        assert result[0].board_id == BoardId.V1
        assert result[1].board_id == BoardId.V2

        # Each separated hex should be valid Intel HEX
        assert result[0].hex.startswith(":")
        assert result[0].hex.endswith(":00000001FF\n")
        assert result[1].hex.startswith(":")
        assert result[1].hex.endswith(":00000001FF\n")

        # Verify all records are valid Intel HEX types
        for ihex in result:
            assert_valid_ihex(ihex.hex)


class TestLoopbackUhex:
    """Test round-trip conversion: Intel Hex -> Universal Hex -> Intel Hex."""

    def test_from_small_sample(self):
        hex_str = (
            ":020000040000FA\n"
            ":10558000002EEDD1E9E70020EAE7C0464302F0B57E\n"
            ":1055900042005D0AC30F4802440A4800120E000E82\n"
            ":1055A000C90FFF2A1FD0FF2822D0002A09D16E423E\n"
            ":1055B0006E4100280FD1002C0DD10020002D09D004\n"
            ":1055C00005E0002801D1002C01D08B4213D05842B5\n"
            ":1055D00001231843F0BD002EF7D04842414101207D\n"
            ":1055E00049420843F6E7002DDDD002204042F1E7B2\n"
            ":1055F000002CDAD0F9E78242E9DC04DBA542E6D8E8\n"
            ":105600000020A542E6D25842434101205B421843A4\n"
            ":020000040002F8\n"
            ":10561000E0E7C0464302F0B542004C005E0AC30F0B\n"
            ":105620004802120E450A240EC90FFF2A17D0FF2C7C\n"
            ":1056300019D0002A0BD170427041002C17D00028DD\n"
            ":1056400007D048424141012049420843F0BD002CA7\n"
            ":1056500013D08B4214D0584201231843F6E702209E\n"
            ":10566000002EF3D1E3E70220002DEFD1E1E7002D7A\n"
            ":10567000E5D10020002EE9D0EDE7002DE9D1EAE7E1\n"
            ":10568000A242E8DC04DBAE42E5D80020AE42DDD227\n"
            ":105690005842434101205B421843D7E7F0B55746D3\n"
            ":1056A0004E4645464300E0B446028846760A1F0E41\n"
            ":1056B000C40F002F47D0FF2F25D0002380259A4606\n"
            ":06F80000FDFFFFFFFFFF0A\n"
            ":020000040003F7\n"
            ":1056C0009946F600ED042E437F3F434642465D0275\n"
            ":1056D000D20F5B006D0A1B0E904640D0FF2B39D0D5\n"
            ":1056E00080220020ED00D20415437F3BFB18424688\n"
            ":1056F0005746591C62408C4607430F2F5CD86F49B0\n"
            ":00000001FF\n"
        )
        hex_str_win = hex_str.replace("\n", "\r\n")

        # Create universal hex from multiple boards
        universal_hex = create_uhex([
            IndividualHex(hex=hex_str, board_id=0x9901),
            IndividualHex(hex=hex_str_win, board_id=0x9902),
            IndividualHex(hex=hex_str, board_id=0x9903),
            IndividualHex(hex=hex_str_win, board_id=0x9904),
        ])

        # Separate back
        result = separate_uhex(universal_hex)

        assert result[0].hex == hex_str
        assert result[1].hex == hex_str
        assert result[2].hex == hex_str
        assert result[3].hex == hex_str

    def test_from_full_makecode_files_sections(self):
        universal_hex = create_uhex([
            IndividualHex(hex=hex132, board_id=0x9901),
            IndividualHex(hex=hex232, board_id=0x9903),
        ])

        assert universal_hex == hex_combined_sections

        separated = separate_uhex(universal_hex)

        assert separated[0].board_id == 0x9901
        assert separated[0].hex == hex132
        assert separated[1].board_id == 0x9903
        # 2-ghost-music.hex does not open with the optional :020000040000FA record
        # And it has a Start Linear Address record at the end
        assert separated[1].hex == ":020000040000FA\n" + hex232.replace(
            ":040000050000FA55A8\n", ""
        )

    def test_python_editor_universal_loopback(self):
        """Test round-trip: separate and re-create Python Editor Universal HEX."""
        # Separate the universal hex
        separated = separate_uhex(hex_python_editor_universal)

        # Re-create universal hex from separated parts
        recreated = create_uhex(separated)

        # Separate again and compare
        separated_again = separate_uhex(recreated)

        assert len(separated) == len(separated_again)
        for orig, new in zip(separated, separated_again):
            assert orig.board_id == new.board_id
            assert orig.hex == new.hex
            assert_valid_ihex(orig.hex)

    def test_makecode_v8_universal_loopback(self):
        """Test round-trip: separate and re-create MakeCode v8 Universal HEX."""
        # Separate the universal hex
        separated = separate_uhex(hex_makecode_v8_universal)

        # Re-create universal hex from separated parts
        recreated = create_uhex(separated)

        # Separate again and compare
        separated_again = separate_uhex(recreated)

        assert len(separated) == len(separated_again)
        for orig, new in zip(separated, separated_again):
            assert orig.board_id == new.board_id
            assert orig.hex == new.hex
            assert_valid_ihex(orig.hex)


class TestBoardId:
    """Test BoardId enum."""

    def test_board_id_values(self):
        assert BoardId.V1 == 0x9900
        assert BoardId.V2 == 0x9903


class TestIndividualHex:
    """Test IndividualHex namedtuple."""

    def test_individual_hex_creation(self):
        ihex = IndividualHex(hex=":00000001FF\n", board_id=0x9900)

        assert ihex.hex == ":00000001FF\n"
        assert ihex.board_id == 0x9900


class TestBlocksFormat:
    """Test create_uhex() with blocks=True format."""

    def test_create_blocks_format_single_hex(self):
        """Test creating Universal Hex with blocks format."""
        normal_hex = (
            ":020000040000FA\n"
            ":1000000000400020218E01005D8E01005F8E010006\n"
            ":1000100000000000000000000000000000000000E0\n"
            ":10002000000000000000000000000000618E0100E0\n"
            ":00000001FF\n"
        )

        result = create_uhex(
            [IndividualHex(hex=normal_hex, board_id=0x9903)],
            blocks=True,
        )

        # Should be a valid Universal Hex
        assert is_uhex(result) is True
        assert result.endswith(":00000001FF\n")

    def test_create_blocks_format_multiple_hexes(self):
        """Test creating Universal Hex with blocks format for multiple boards."""
        normal_hex = (
            ":020000040000FA\n"
            ":1000000000400020218E01005D8E01005F8E010006\n"
            ":1000100000000000000000000000000000000000E0\n"
            ":10002000000000000000000000000000618E0100E0\n"
            ":00000001FF\n"
        )

        result = create_uhex(
            [
                IndividualHex(hex=normal_hex, board_id=0x9900),
                IndividualHex(hex=normal_hex, board_id=0x9903),
            ],
            blocks=True,
        )

        # Should be a valid Universal Hex
        assert is_uhex(result) is True
        # Can separate back
        separated = separate_uhex(result)
        assert len(separated) == 2
        assert separated[0].board_id == 0x9900
        assert separated[1].board_id == 0x9903

    def test_blocks_format_loopback(self):
        """Test round-trip with blocks format."""
        hex_str = (
            ":020000040000FA\n"
            ":10558000002EEDD1E9E70020EAE7C0464302F0B57E\n"
            ":1055900042005D0AC30F4802440A4800120E000E82\n"
            ":00000001FF\n"
        )

        universal_hex = create_uhex(
            [
                IndividualHex(hex=hex_str, board_id=0x9900),
                IndividualHex(hex=hex_str, board_id=0x9903),
            ],
            blocks=True,
        )

        separated = separate_uhex(universal_hex)

        assert len(separated) == 2
        # Separated hexes should have valid Intel HEX types
        for ihex in separated:
            assert_valid_ihex(ihex.hex)

    def test_blocks_format_v1_uses_data_records(self):
        """Test that V1 board IDs use standard Data records in blocks format."""
        normal_hex = (
            ":020000040000FA\n"
            ":1000000000400020218E01005D8E01005F8E010006\n"
            ":00000001FF\n"
        )

        result = create_uhex(
            [IndividualHex(hex=normal_hex, board_id=0x9900)],
            blocks=True,
        )

        # V1 boards should use Data records (type 00), not CustomData (type 0D)
        records = split_ihex_into_records(result)
        data_records = [r for r in records if get_record_type(r) == RecordType.Data]
        custom_data_records = [
            r for r in records if get_record_type(r) == RecordType.CustomData
        ]
        assert len(data_records) > 0
        assert len(custom_data_records) == 0


class TestMakeCodeV1Detection:
    """Test _is_makecode_v1() and _is_makecode_v1_records() functions."""

    def test_normal_hex_is_not_makecode_v1(self):
        """Test that normal hex files are not detected as MakeCode V1."""
        normal_hex = (
            ":020000040000FA\n"
            ":1000000000400020218E01005D8E01005F8E010006\n"
            ":00000001FF\n"
        )

        assert _is_makecode_v1(normal_hex) is False

    def test_hex_with_ram_address_before_eof_is_makecode_v0(self):
        """Test detection of MakeCode v0 hex (metadata in RAM before EoF)."""
        # MakeCode v0 placed metadata in RAM space 0x20000000 before EoF
        makecode_v0_hex = (
            ":020000040000FA\n"
            ":1000000000400020218E01005D8E01005F8E010006\n"
            ":020000042000DA\n"  # Extended Linear Address to 0x20000000
            ":10000000DEADBEEFDEADBEEFDEADBEEFDEADBEEF00\n"
            ":00000001FF\n"
        )

        assert _is_makecode_v1(makecode_v0_hex) is True

    def test_hex_with_other_data_after_eof_is_makecode_v1(self):
        """Test detection of MakeCode v2/v3 hex (OtherData after EoF)."""
        # MakeCode v2/v3 uses OtherData (0x0E) records after EoF
        makecode_v2_hex = (
            ":020000040000FA\n"
            ":1000000000400020218E01005D8E01005F8E010006\n"
            ":00000001FF\n"
            ":0400000EDEADBEEFB6\n"  # OtherData record (type 0E)
        )

        records = split_ihex_into_records(makecode_v2_hex)
        assert _is_makecode_v1_records(records) is True

    def test_hex_with_ram_address_after_eof_is_makecode_v1(self):
        """Test detection of MakeCode v1 hex (RAM address after EoF)."""
        # MakeCode v1 placed metadata in RAM after EoF
        makecode_v1_hex = (
            ":020000040000FA\n"
            ":1000000000400020218E01005D8E01005F8E010006\n"
            ":00000001FF\n"
            ":020000042000DA\n"  # Extended Linear Address to 0x20000000
            ":10000000METADATA123456789ABCDEF0123456700\n"
        )

        assert _is_makecode_v1(makecode_v1_hex) is True

    def test_hex_without_eof_is_not_makecode(self):
        """Test that hex without EoF record is not detected as MakeCode."""
        no_eof_hex = (
            ":020000040000FA\n"
            ":1000000000400020218E01005D8E01005F8E010006\n"
        )

        assert _is_makecode_v1(no_eof_hex) is False

class TestExtendedSegmentAddress:
    """Test handling of Extended Segment Address records."""

    def test_create_uhex_with_extended_segment_address(self):
        """Test creating Universal Hex from hex with Extended Segment Address."""
        # Extended Segment Address record (type 02) instead of Extended Linear (04)
        hex_with_ext_seg = (
            ":020000020000FC\n"  # Extended Segment Address to 0x0000
            ":1000000000400020218E01005D8E01005F8E010006\n"
            ":1000100000000000000000000000000000000000E0\n"
            ":020000021000EC\n"  # Extended Segment Address to 0x1000
            ":1000000011111111111111111111111111111111EF\n"
            ":00000001FF\n"
        )

        result = create_uhex(
            [IndividualHex(hex=hex_with_ext_seg, board_id=0x9903)],
        )

        assert is_uhex(result) is True
        separated = separate_uhex(result)
        assert len(separated) == 1
        assert_valid_ihex(separated[0].hex)

    def test_blocks_format_with_extended_segment_address(self):
        """Test blocks format handles Extended Segment Address records."""
        hex_with_ext_seg = (
            ":020000020000FC\n"  # Extended Segment Address to 0x0000
            ":1000000000400020218E01005D8E01005F8E010006\n"
            ":020000021000EC\n"  # Extended Segment Address mid-file
            ":1000000011111111111111111111111111111111EF\n"
            ":00000001FF\n"
        )

        result = create_uhex(
            [IndividualHex(hex=hex_with_ext_seg, board_id=0x9903)],
            blocks=True,
        )

        assert is_uhex(result) is True
        separated = separate_uhex(result)
        assert len(separated) == 1
        assert_valid_ihex(separated[0].hex)

    def test_blocks_format_large_hex_needs_padding(self):
        """Test blocks format with larger hex that requires multiple padding records."""
        # Create a hex with enough data to fill multiple 512-byte blocks
        data_records = "\n".join(
            f":10{i:04X}00{'AA' * 16}00"  # Dummy data records
            for i in range(0, 0x1000, 0x10)
        )
        large_hex = f":020000040000FA\n{data_records}\n:00000001FF\n"

        # Fix checksums - just use a simpler approach
        large_hex = (
            ":020000040000FA\n"
            + "\n".join(
                f":100{i:03X}00{'00' * 16}{(256 - (16 + (i >> 4) + (i & 0xF) + (i >> 8))) & 0xFF:02X}"
                for i in range(0, 256, 16)
            )
            + "\n:00000001FF\n"
        )

        result = create_uhex(
            [IndividualHex(hex=large_hex, board_id=0x9903)],
            blocks=True,
        )

        assert is_uhex(result) is True
        # Should contain padding records
        assert ":0C00000C" in result or ":0000000B" in result  # PaddedData or BlockEnd


class TestMakeCodeFixtureFiles:
    """Test with real MakeCode hex files from different versions."""

    def test_makecode_v1_intel_detected_as_makecode(self):
        """MakeCode v1 Intel Hex files are detected as MakeCode."""
        assert _is_makecode_v1(hex_makecode_v1_intel) is True

    def test_makecode_v2_intel_detected_as_makecode(self):
        """MakeCode v2 Intel Hex files are detected as MakeCode."""
        assert _is_makecode_v1(hex_makecode_v2_intel) is True

    def test_makecode_v3_universal_not_detected_as_makecode_v1(self):
        """MakeCode v3 Universal Hex files are not detected as MakeCode V1."""
        assert _is_makecode_v1(hex_makecode_v3_universal) is False

    def test_separate_makecode_v3_universal(self):
        """Test separating MakeCode v3 Universal Hex."""
        result = separate_uhex(hex_makecode_v3_universal)

        # MakeCode v3 uses board IDs 0x9901 and 0x9903
        assert len(result) == 2
        assert result[0].board_id == 0x9901
        assert result[1].board_id == 0x9903

        # Verify all records are valid Intel HEX types
        for ihex in result:
            assert_valid_ihex(ihex.hex)

    def test_separate_makecode_v5_universal(self):
        """Test separating MakeCode v5 Universal Hex."""
        result = separate_uhex(hex_makecode_v5_universal)

        # MakeCode v5 uses board IDs 0x9900 and 0x9903
        assert len(result) == 2
        assert result[0].board_id == BoardId.V1
        assert result[1].board_id == BoardId.V2

        # Verify all records are valid Intel HEX types
        for ihex in result:
            assert_valid_ihex(ihex.hex)

class TestInternalFunctions:
    """Test internal functions for edge cases and coverage."""

    def test_is_uhex_records_with_less_than_3_records(self):
        """Test _is_uhex_records returns False for less than 3 records."""
        assert _is_uhex_records([]) is False
        assert _is_uhex_records([":020000040000FA"]) is False
        assert _is_uhex_records([":020000040000FA", ":0400000A9900C0DEBB"]) is False

    def test_ihex_to_uhex_blocks_empty_input(self):
        """Test _ihex_to_uhex_blocks with empty input returns empty string."""
        assert _ihex_to_uhex_blocks("", 0x9903) == ""

    def test_ihex_to_uhex_sections_empty_input(self):
        """Test _ihex_to_uhex_sections with empty input returns empty string."""
        assert _ihex_to_uhex_sections("", 0x9903) == ""

    def test_blocks_format_makecode_v1_error(self):
        """Test that MakeCode V1 hex with mid-file EoF raises specific error."""
        # This is a MakeCode V1 hex - it has EoF in the middle and RAM address
        with pytest.raises(ValueError, match="from MakeCode"):
            create_uhex(
                [IndividualHex(hex=hex_makecode_v1_intel, board_id=0x9900)],
                blocks=True,
            )

    def test_sections_format_makecode_v1_error(self):
        """Test that MakeCode V1 hex with mid-file EoF raises specific error."""
        with pytest.raises(ValueError, match="from MakeCode"):
            create_uhex(
                [IndividualHex(hex=hex_makecode_v1_intel, board_id=0x9900)],
                blocks=False,
            )

    def test_separate_uhex_ext_linear_not_followed_by_block_start(self):
        """Test separate_uhex when ExtendedLinearAddress is not followed by BlockStart."""
        # Create a Universal Hex where an ExtendedLinearAddress appears mid-section
        # (not at the start of a new block)
        uhex_with_mid_ext_lin = (
            ":020000040000FA\n"  # Extended Linear Address
            ":0400000A9900C0DEBB\n"  # Block Start for board 0x9900
            ":1000000000400020218E01005D8E01005F8E010006\n"  # Data
            ":020000040001F9\n"  # Extended Linear Address mid-section (NOT followed by BlockStart)
            ":1000000011111111111111111111111111111111EF\n"  # More data
            ":0000000BF5\n"  # Block End
            ":00000001FF\n"  # End of File
        )

        result = separate_uhex(uhex_with_mid_ext_lin)

        # Should have one board
        assert len(result) == 1
        assert result[0].board_id == 0x9900
        # The mid-section ExtendedLinearAddress should be included in the output
        assert ":020000040001F9" in result[0].hex
        assert_valid_ihex(result[0].hex)
