"""
Tests for Intel HEX record creation and parsing.

(c) 2020 Micro:bit Educational Foundation and contributors.
SPDX-License-Identifier: MIT
"""

import pytest

from universal_hex.ihex import (
    RecordType,
    block_end_record,
    block_start_record,
    convert_ext_seg_to_lin_address,
    convert_record_to,
    create_record,
    eof_record,
    ext_lin_address_record,
    find_data_field_length,
    get_record_data,
    get_record_type,
    padded_data_record,
    parse_record,
    split_ihex_into_records,
)


class TestCreateRecordStandard:
    """Test create_record() for standard records."""

    def test_creates_standard_data_records(self):
        a = [0x64, 0x27, 0x00, 0x20, 0x03, 0x4B, 0x19, 0x60]
        b = [0x43, 0x68, 0x03, 0x49, 0x9B, 0x00, 0x5A, 0x50]
        # Examples taken from a random micro:bit hex file
        assert (
            create_record(RecordType.Data, 0x4290, bytes(a + b))
            == ":1042900064270020034B1960436803499B005A5070"
        )

        a = [0x12, 0xF0, 0xD0, 0xFB, 0x07, 0xEE, 0x90, 0x0A, 0xF5, 0xEE, 0xC0]
        b = [0x7A, 0xF1, 0xEE, 0x10, 0xFA, 0x44, 0xBF, 0x9F, 0xED, 0x08, 0x7A]
        c = [0x77, 0xEE, 0x87, 0x7A, 0xFD, 0xEE, 0xE7, 0x7A, 0x17, 0xEE]
        assert create_record(RecordType.Data, 0x07E0, bytes(a + b + c)) == (
            ":2007E00012F0D0FB07EE900AF5EEC07AF1EE10FA44BF9FED087A77EE877AFDEEE77A17EECF"
        )

        assert (
            create_record(RecordType.Data, 0xF870, bytes([0x00, 0x00, 0x00, 0x00]))
            == ":04F870000000000094"
        )

        data = bytes([0x0C, 0x1A, 0xFF, 0x7F, 0x01, 0x00, 0x00, 0x00])
        assert create_record(RecordType.Data, 0xE7D4, data) == (
            ":08E7D4000C1AFF7F0100000098"
        )

    def test_creates_end_of_file_record(self):
        assert create_record(RecordType.EndOfFile, 0, b"") == ":00000001FF"

    def test_throws_error_when_data_too_large(self):
        data = list(range(1, 17)) * 2  # 32 bytes - should not throw
        create_record(RecordType.Data, 0, bytes(data))

        data.append(33)  # 33 bytes - should throw
        with pytest.raises(ValueError, match="data has too many bytes"):
            create_record(RecordType.Data, 0, bytes(data))

    def test_throws_error_when_address_too_large(self):
        with pytest.raises(ValueError, match="address out of range"):
            create_record(RecordType.Data, 0x10000, b"")

    def test_throws_error_when_address_negative(self):
        with pytest.raises(ValueError, match="address out of range"):
            create_record(RecordType.Data, -1, b"")

    def test_throws_error_when_record_type_invalid(self):
        with pytest.raises(ValueError, match="is not valid"):
            create_record(0xFF, 0, b"")  # type: ignore[arg-type]


class TestCreateRecordCustom:
    """Test create_record() for custom records."""

    def test_creates_custom_block_start_record(self):
        assert (
            create_record(RecordType.BlockStart, 0, bytes([0x99, 0x01, 0xC0, 0xDE]))
            == ":0400000A9901C0DEBA"
        )


class TestGetRecordTypeStandard:
    """Test get_record_type() for standard records."""

    def test_detects_eof_record(self):
        assert get_record_type(":00000001FF") == RecordType.EndOfFile
        assert get_record_type(":00000001FF\n") == RecordType.EndOfFile
        assert get_record_type(":00000001FF\r\n") == RecordType.EndOfFile
        assert get_record_type(":00000001FF\n\r") == RecordType.EndOfFile


class TestGetRecordTypeCustom:
    """Test get_record_type() for custom records."""

    def test_detects_block_start_record(self):
        assert get_record_type(":0400000A9901C0DEBA") == RecordType.BlockStart

    def test_detects_block_end_record(self):
        record = ":0C00000BFFFFFFFFFFFFFFFFFFFFFFFFF5"
        assert get_record_type(record) == RecordType.BlockEnd
        assert get_record_type(":0000000BF5") == RecordType.BlockEnd

    def test_detects_padded_data_record(self):
        record = ":1000000CFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF4"
        assert get_record_type(record) == RecordType.PaddedData

    def test_detects_custom_data_record(self):
        record = ":102AA00D34000F2D03653A35000C2D03653A3600C1"
        assert get_record_type(record) == RecordType.CustomData

    def test_detects_other_data_record(self):
        record = ":1002800EE4EA519366D2B52AA5EE1DBDD0414C5578"
        assert get_record_type(record) == RecordType.OtherData

    def test_throws_error_with_invalid_record_type(self):
        with pytest.raises(ValueError, match="is not valid"):
            get_record_type(":0000000FF5")


class TestGetRecordData:
    """Test get_record_data()."""

    def test_empty_data_field(self):
        assert get_record_data(":00000001FF") == b""

    def test_get_data_from_block_start_record(self):
        assert get_record_data(":0400000A9903C0DEB8") == bytes([0x99, 0x03, 0xC0, 0xDE])

    def test_get_data_from_half_padding_record(self):
        record = ":1080B00DFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC3"
        assert get_record_data(record) == bytes([0xFF] * 16)

    def test_get_data_from_full_padding_record(self):
        record = (  # noqa: E501
            ":1080B00DFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC3"
        )
        assert get_record_data(record) == bytes([0xFF] * 32)

    def test_empty_bytes_when_record_too_short(self):
        assert get_record_data(":00000001") == b""

    def test_throws_error_with_invalid_record(self):
        with pytest.raises(ValueError, match="Could not parse"):
            get_record_data(":0000000F_THIS_IS_NOT_A_HEX_F5")


class TestParseRecordStandard:
    """Test parse_record() for standard records."""

    def test_parses_data_record_32_bytes(self):
        result = parse_record(
            ":201C400010F0D2FF3246CDE900013B463046394610F0EEFC02460B46DDE9000110F09AFE2C"
        )

        assert result.byte_count == 0x20
        assert result.address == 0x1C40
        assert result.record_type == RecordType.Data
        a = [0x10, 0xF0, 0xD2, 0xFF, 0x32, 0x46, 0xCD, 0xE9, 0x00, 0x01]
        b = [0x3B, 0x46, 0x30, 0x46, 0x39, 0x46, 0x10, 0xF0, 0xEE, 0xFC]
        c = [0x02, 0x46, 0x0B, 0x46, 0xDD, 0xE9, 0x00, 0x01, 0x10, 0xF0]
        d = [0x9A, 0xFE]
        assert result.data == bytes(a + b + c + d)
        assert result.checksum == 0x2C

    def test_parses_data_record_16_bytes(self):
        result = parse_record(":10FFF0009B6D9847A06810F039FF0621A06810F0AB")

        assert result.byte_count == 0x10
        assert result.address == 0xFFF0
        assert result.record_type == RecordType.Data
        a = [0x9B, 0x6D, 0x98, 0x47, 0xA0, 0x68, 0x10, 0xF0]
        b = [0x39, 0xFF, 0x06, 0x21, 0xA0, 0x68, 0x10, 0xF0]
        assert result.data == bytes(a + b)
        assert result.checksum == 0xAB

    def test_parses_data_record_8_bytes(self):
        result = parse_record(":08AEE0007C53FF7F010000001C")

        assert result.byte_count == 0x08
        assert result.address == 0xAEE0
        assert result.record_type == RecordType.Data
        assert result.data == bytes([0x7C, 0x53, 0xFF, 0x7F, 0x01, 0x00, 0x00, 0x00])
        assert result.checksum == 0x1C

    def test_parses_data_record_4_bytes(self):
        result = parse_record(":04F870000000000094")

        assert result.byte_count == 0x04
        assert result.address == 0xF870
        assert result.record_type == RecordType.Data
        assert result.data == bytes([0x00, 0x00, 0x00, 0x00])
        assert result.checksum == 0x94

    def test_throws_error_when_no_colon(self):
        with pytest.raises(ValueError, match='does not start with a ":"'):
            parse_record("04F870000000000094")

    def test_throws_error_when_not_even_hex_chars(self):
        with pytest.raises(ValueError, match="not divisible by 2"):
            parse_record(":04F87000000000094")

    def test_throws_error_when_byte_count_mismatch(self):
        with pytest.raises(ValueError, match="byte count"):
            parse_record(":04F87000000000009400")

    def test_throws_error_with_invalid_record(self):
        with pytest.raises(ValueError, match="Could not parse"):
            parse_record(":0000000F_THIS_IS_NOT_A_HEX_F5")

    def test_throws_error_when_record_too_small(self):
        with pytest.raises(ValueError, match="Record length too small"):
            parse_record(":000000")

    def test_throws_error_when_record_too_large(self):
        with pytest.raises(ValueError, match="Record length is too large"):
            parse_record(
                ":2000600031F8000039F8000041F800008FFA00008FFA00008FFA00008FFA00008FFA0000FF40"
            )


class TestEndOfFileRecord:
    """Test eof_record()."""

    def test_creates_standard_eof_record(self):
        assert eof_record() == ":00000001FF"


class TestExtLinAddressRecord:
    """Test ext_lin_address_record()."""

    def test_creates_extended_linear_address_records(self):
        assert ext_lin_address_record(0x00000) == ":020000040000FA"
        assert ext_lin_address_record(0x04321) == ":020000040000FA"
        assert ext_lin_address_record(0x10000) == ":020000040001F9"
        assert ext_lin_address_record(0x20000) == ":020000040002F8"
        assert ext_lin_address_record(0x30000) == ":020000040003F7"
        assert ext_lin_address_record(0x31234) == ":020000040003F7"
        assert ext_lin_address_record(0x40000) == ":020000040004F6"
        assert ext_lin_address_record(0x48264) == ":020000040004F6"
        assert ext_lin_address_record(0x50000) == ":020000040005F5"
        assert ext_lin_address_record(0x55555) == ":020000040005F5"
        assert ext_lin_address_record(0x60000) == ":020000040006F4"
        assert ext_lin_address_record(0x61230) == ":020000040006F4"
        assert ext_lin_address_record(0x70000) == ":020000040007F3"
        assert ext_lin_address_record(0x72946) == ":020000040007F3"

    def test_throws_error_when_address_out_of_range(self):
        with pytest.raises(ValueError, match="Address record is out of range"):
            ext_lin_address_record(0x100000000)


class TestBlockStartRecord:
    """Test block_start_record()."""

    def test_creates_custom_block_start_record(self):
        assert block_start_record(0x9901) == ":0400000A9901C0DEBA"
        assert block_start_record(0x9903) == ":0400000A9903C0DEB8"

    def test_throws_error_when_board_id_too_large(self):
        with pytest.raises(ValueError, match="Board ID out of range"):
            block_start_record(0x10000)

    def test_throws_error_when_board_id_negative(self):
        with pytest.raises(ValueError, match="Board ID out of range"):
            block_start_record(-1)


class TestBlockEndRecord:
    """Test block_end_record()."""

    def test_creates_custom_block_end_record(self):
        assert block_end_record(0) == ":0000000BF5"
        assert block_end_record(1) == ":0100000BFFF5"
        assert block_end_record(0x9) == ":0900000BFFFFFFFFFFFFFFFFFFF5"
        assert block_end_record(0x10) == ":1000000BFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5"
        assert block_end_record(0x20) == (
            ":2000000BFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5"
        )

    def test_throws_error_when_padding_negative(self):
        with pytest.raises(ValueError):
            block_end_record(-1)

    def test_throws_error_when_padding_too_large(self):
        block_end_record(32)  # should not throw

        with pytest.raises(ValueError, match="has too many bytes"):
            block_end_record(33)


class TestPaddedDataRecord:
    """Test padded_data_record()."""

    def test_creates_custom_padded_data_record(self):
        assert padded_data_record(0) == ":0000000CF4"
        assert padded_data_record(1) == ":0100000CFFF4"
        assert padded_data_record(0x9) == ":0900000CFFFFFFFFFFFFFFFFFFF4"
        assert padded_data_record(0x10) == ":1000000CFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF4"
        assert padded_data_record(0x20) == (
            ":2000000CFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF4"
        )

    def test_throws_error_when_padding_negative(self):
        with pytest.raises(ValueError):
            padded_data_record(-1)

    def test_throws_error_when_padding_too_large(self):
        padded_data_record(32)  # should not throw

        with pytest.raises(ValueError, match="has too many bytes"):
            padded_data_record(33)


class TestConvertRecordTo:
    """Test convert_record_to()."""

    def test_converts_data_record_to_custom_data_record(self):
        assert (
            convert_record_to(
                ":105D3000E060E3802046FFF765FF0123A1881A4653",
                RecordType.CustomData,
            )
            == ":105D300DE060E3802046FFF765FF0123A1881A4646"
        )

        assert (
            convert_record_to(
                ":10B04000D90B08BD40420F0070B5044616460D46A8",
                RecordType.CustomData,
            )
            == ":10B0400DD90B08BD40420F0070B5044616460D469B"
        )


class TestConvertExtSegToLinAddress:
    """Test convert_ext_seg_to_lin_address()."""

    def test_converts_valid_extended_segment_address_records(self):
        assert convert_ext_seg_to_lin_address(":020000020000FC") == ":020000040000FA"
        assert convert_ext_seg_to_lin_address(":020000021000EC") == ":020000040001F9"
        assert convert_ext_seg_to_lin_address(":020000022000DC") == ":020000040002F8"
        assert convert_ext_seg_to_lin_address(":020000023000CC") == ":020000040003F7"
        assert convert_ext_seg_to_lin_address(":020000024000BC") == ":020000040004F6"
        assert convert_ext_seg_to_lin_address(":0200000270008C") == ":020000040007F3"

    def test_throws_error_with_invalid_extended_segment_address(self):
        with pytest.raises(ValueError, match="Invalid Extended Segment Address record"):
            convert_ext_seg_to_lin_address(":0200000270018C")

        with pytest.raises(ValueError, match="Invalid Extended Segment Address record"):
            convert_ext_seg_to_lin_address(":0300000271008C")

        with pytest.raises(ValueError, match="Invalid Extended Segment Address record"):
            convert_ext_seg_to_lin_address(":030000027000FF8C")


class TestSplitIhexIntoRecords:
    """Test split_ihex_into_records()."""

    def test_normal_hex_file_string(self):
        hex_str = (
            ":020000040000FA\n"
            ":1001000D084748204D490968095808474C204B4974\n"
            ":1001100D096809580847502048490968095808478F\n"
            ":020000040003F7\n"
            ":1001200D5420464909680958084758204349096829\n"
            ":00000001FF\n"
        )
        assert split_ihex_into_records(hex_str) == [
            ":020000040000FA",
            ":1001000D084748204D490968095808474C204B4974",
            ":1001100D096809580847502048490968095808478F",
            ":020000040003F7",
            ":1001200D5420464909680958084758204349096829",
            ":00000001FF",
        ]

    def test_newlines_with_carriage_returns(self):
        hex_str = (
            ":020000040000FA\r\n"
            ":1001000D084748204D490968095808474C204B4974\r\n"
            ":1001100D096809580847502048490968095808478F\r\n"
            ":020000040003F7\r\n"
            ":1001200D5420464909680958084758204349096829\r\n"
            ":00000001FF\r\n"
        )
        assert split_ihex_into_records(hex_str) == [
            ":020000040000FA",
            ":1001000D084748204D490968095808474C204B4974",
            ":1001100D096809580847502048490968095808478F",
            ":020000040003F7",
            ":1001200D5420464909680958084758204349096829",
            ":00000001FF",
        ]

    def test_no_newline_at_last_record(self):
        hex_str_unix = (
            ":020000040000FA\n"
            ":1001000D084748204D490968095808474C204B4974\n"
            ":1001100D096809580847502048490968095808478F\n"
            ":020000040003F7\n"
            ":1001200D5420464909680958084758204349096829\n"
            ":00000001FF"
        )
        hex_str_win = hex_str_unix.replace("\n", "\r\n")
        expected = [
            ":020000040000FA",
            ":1001000D084748204D490968095808474C204B4974",
            ":1001100D096809580847502048490968095808478F",
            ":020000040003F7",
            ":1001200D5420464909680958084758204349096829",
            ":00000001FF",
        ]

        assert split_ihex_into_records(hex_str_unix) == expected
        assert split_ihex_into_records(hex_str_win) == expected

    def test_mixed_carriage_returns_and_newlines(self):
        hex_str = (
            ":020000040000FA\r\n"
            ":1001000D084748204D490968095808474C204B4974\r\n"
            ":1001100D096809580847502048490968095808478F\n"
            ":020000040003F7\r\n"
            ":1001200D5420464909680958084758204349096829\n"
            ":00000001FF\n"
        )
        assert split_ihex_into_records(hex_str) == [
            ":020000040000FA",
            ":1001000D084748204D490968095808474C204B4974",
            ":1001100D096809580847502048490968095808478F",
            ":020000040003F7",
            ":1001200D5420464909680958084758204349096829",
            ":00000001FF",
        ]

    def test_empty_lines_removed_from_output(self):
        hex_str = (
            ":1001000D084748204D490968095808474C204B4974\n"
            "\n"
            ":1001100D096809580847502048490968095808478F\n"
            ":00000001FF\n"
            "\n"
        )
        assert split_ihex_into_records(hex_str) == [
            ":1001000D084748204D490968095808474C204B4974",
            ":1001100D096809580847502048490968095808478F",
            ":00000001FF",
        ]

    def test_single_record_without_newlines(self):
        assert split_ihex_into_records(
            ":1001000D084748204D490968095808474C204B4974"
        ) == [":1001000D084748204D490968095808474C204B4974"]

    def test_empty_input_returns_empty_list(self):
        assert split_ihex_into_records("") == []


class TestFindDataFieldLength:
    """Test find_data_field_length()."""

    def test_standard_16_byte_record_hex(self):
        hex_str = (
            ":020000040000FA\n"
            ":10000000C0070000D1060000D1000000B1060000CA\n"
            ":1000100000000000000000000000000000000000E0\n"
            ":100020000000000000000000000000005107000078\n"
            ":100030000000000000000000DB000000E500000000\n"
            ":10004000EF000000F9000000030100000D010000B6\n"
            ":1000500017010000210100002B0100003501000004\n"
            ":100160000968095808477020344909680958084740\n"
            ":100170007420324909680958084778202F490968CE\n"
            ":10018000095808477C202D490968095808478020EC\n"
            ":100190002A490968095808478420284909680958E4\n"
            ":020000040001F9\n"
            ":10000000058209E003984179027909021143490404\n"
            ":10001000490C0171090A417103AA04A90898FFF764\n"
            ":1000200068FF0028EED0822C02D020460BB0F0BD35\n"
            ":100030000020FBE730B50446406B002597B0002850\n"
            ":00000001FF\n"
        )

        assert find_data_field_length(hex_str) == 16

    def test_finds_mixed_records_with_32_byte_records(self):
        hex_str = (
            ":020000040000FA\n"
            ":10000000C0070000D1060000D1000000B1060000CA\n"
            ":1000100000000000000000000000000000000000E0\n"
            ":100020000000000000000000000000005107000078\n"
            ":100030000000000000000000DB000000E500000000\n"
            ":10004000EF000000F9000000030100000D010000B6\n"
            ":1000500017010000210100002B0100003501000004\n"
            ":2000600031F8000039F8000041F800008FFA00008FFA00008FFA00008FFA00008FFA000040\n"
            ":200080008FFA00008FFA00008FFA0000410101008FFA00008FFA00008FFA00008FFA00005E\n"
            ":2000A0008FFA00008FFA000049F8000051F800008FFA00008FFA0000000000000000000092\n"
            ":2000C0008FFA00008FFA00008FFA0000350101008FFA00008FFA00008FFA000000000000B3\n"
            ":2000E000000000000000000000000000000000000000000000000000000000000000000000\n"
            ":200100000000000000000000000000000000000000000000000000000000000000000000DF\n"
            ":200120000000000000000000000000000000000000000000000000000000000000000000BF\n"
            ":2001400000000000000000000000000000000000000000000000000000000000000000009F\n"
            ":100160000968095808477020344909680958084740\n"
            ":100170007420324909680958084778202F490968CE\n"
            ":10018000095808477C202D490968095808478020EC\n"
            ":100190002A490968095808478420284909680958E4\n"
            ":1001A0000847882025490968095808478C202349B1\n"
            ":1001B00009680958084790202049096809580847E4\n"
            ":1001C00094201E4909680958084798201B49096866\n"
            ":1001D000095808479C201949096809580847A02070\n"
            ":020000040001F9\n"
            ":10000000058209E003984179027909021143490404\n"
            ":10001000490C0171090A417103AA04A90898FFF764\n"
            ":1000200068FF0028EED0822C02D020460BB0F0BD35\n"
            ":100030000020FBE730B50446406B002597B0002850\n"
            ":200040000098C3F83415C3F83825D3F80012E26141F02001C3F800127A1906EB82025268EB\n"
            ":2000600052B14FF404722948C3F8042303B0F0BD00293AD1002C3ED1D3F81021D3F8441186\n"
            ":20008000D3F82441002AF3D03D4421481F4F214B002206EB8506944208BF3846B2619142E0\n"
            ":2000A00018BF1846E2E70368A261C3F810E1D3F8100101900198C3F844E1D3F844010090A2\n"
            ":2000C0000120E160C4F81CE0009CC3F83415C3F838251860C0E733B103680F484FF40472D0\n"
            ":00000001FF\n"
        )

        assert find_data_field_length(hex_str) == 32

    def test_throws_error_when_data_larger_than_32_bytes(self):
        hex_str = (
            ":020000040000FA\n"
            ":10000000C0070000D1060000D1000000B1060000CA\n"
            ":2000600031F8000039F8000041F800008FFA00008FFA00008FFA00008FFA00008FFA000040\n"
            ":300080008FFA00008FFA00008FFA0000410101008FFA00008FFA00008FFA00008FFA0000C0070000D1060000D1000000B106000028\n"
            ":00000001FF\n"
        )

        with pytest.raises(ValueError, match="data size is too large"):
            find_data_field_length(hex_str)
