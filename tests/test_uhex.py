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


# Load test fixture files
HEX_PATH = Path(__file__).parent / "hex-files"
hex116 = (HEX_PATH / "1-duck-umbrella-16.hex").read_text()
hex216 = (HEX_PATH / "2-ghost-music-16.hex").read_text()
hex132 = (HEX_PATH / "1-duck-umbrella-32.hex").read_text()
hex232 = (HEX_PATH / "2-ghost-music-32.hex").read_text()
hex_combined_blocks = (HEX_PATH / "combined-16-blocks-1-9901-2-9903.hex").read_text()
hex_combined_sections = (HEX_PATH / "combined-32-sections-1-9901-2-9903.hex").read_text()
hex_python_editor_universal = (HEX_PATH / "python-editor-universal.hex").read_text()
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
