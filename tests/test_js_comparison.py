"""
Comparison tests between Python and JavaScript Universal Hex implementations.

These tests verify that the Python port produces identical results to the
original TypeScript/JavaScript library.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from universal_hex import BoardId, IndividualHex, create_uhex, is_uhex, separate_uhex

from .universalhex_js.universalhex_js import (
    IndividualHexJS,
)
from .universalhex_js.universalhex_js import (
    create_universal_hex as js_create_uhex,
)
from .universalhex_js.universalhex_js import (
    is_universal_hex as js_is_uhex,
)
from .universalhex_js.universalhex_js import (
    separate_universal_hex as js_separate_uhex,
)

HEX_FILES_DIR = Path(__file__).parent / "hex-files"


class TestIsUniversalHexComparison:
    """Compare is_uhex() with JavaScript isUniversalHex()."""

    @pytest.mark.parametrize(
        "hex_file",
        [
            "1-duck-umbrella-16.hex",
            "1-duck-umbrella-32.hex",
            "2-ghost-music-16.hex",
            "2-ghost-music-32.hex",
        ],
    )
    def test_intel_hex_not_universal(self, hex_file: str) -> None:
        """Intel Hex files should not be detected as Universal Hex."""
        hex_str = (HEX_FILES_DIR / hex_file).read_text(encoding="ascii")

        py_result = is_uhex(hex_str)
        js_result = js_is_uhex(hex_str)

        assert py_result == js_result
        assert py_result is False

    @pytest.mark.parametrize(
        "hex_file",
        [
            "makecode-v3-universal.hex",
            "makecode-v5-universal.hex",
            "makecode-v8-universal.hex",
            "python-editor-universal.hex",
            "combined-16-blocks-1-9901-2-9903.hex",
            "combined-32-sections-1-9901-2-9903.hex",
        ],
    )
    def test_universal_hex_detected(self, hex_file: str) -> None:
        """Universal Hex files should be detected correctly."""
        hex_str = (HEX_FILES_DIR / hex_file).read_text(encoding="ascii")

        py_result = is_uhex(hex_str)
        js_result = js_is_uhex(hex_str)

        assert py_result == js_result
        assert py_result is True


class TestCreateUniversalHexComparison:
    """Compare create_uhex() with JavaScript createUniversalHex()."""

    def test_create_from_two_intel_hex_files_sections(self) -> None:
        """Creating Universal Hex from two Intel Hex files should match JS output."""
        v1_hex = (HEX_FILES_DIR / "1-duck-umbrella-16.hex").read_text(encoding="ascii")
        v2_hex = (HEX_FILES_DIR / "2-ghost-music-16.hex").read_text(encoding="ascii")

        py_result = create_uhex(
            [
                IndividualHex(hex=v1_hex, board_id=BoardId.V1),
                IndividualHex(hex=v2_hex, board_id=BoardId.V2),
            ]
        )
        js_result = js_create_uhex(
            [
                IndividualHexJS(hex=v1_hex, board_id=BoardId.V1),
                IndividualHexJS(hex=v2_hex, board_id=BoardId.V2),
            ]
        )

        assert py_result == js_result

    @pytest.mark.skip(reason="use_blocks not yet implemented in Python")
    def test_create_from_two_intel_hex_files_blocks(self) -> None:
        """Creating Universal Hex with blocks format should match JS output."""
        v1_hex = (HEX_FILES_DIR / "1-duck-umbrella-16.hex").read_text(encoding="ascii")
        v2_hex = (HEX_FILES_DIR / "2-ghost-music-16.hex").read_text(encoding="ascii")

        py_result = create_uhex(
            [
                IndividualHex(hex=v1_hex, board_id=BoardId.V1),
                IndividualHex(hex=v2_hex, board_id=BoardId.V2),
            ],
            use_blocks=True,  # type: ignore[call-arg]
        )
        js_result = js_create_uhex(
            [
                IndividualHexJS(hex=v1_hex, board_id=BoardId.V1),
                IndividualHexJS(hex=v2_hex, board_id=BoardId.V2),
            ],
            use_blocks=True,
        )

        assert py_result == js_result

    def test_create_with_32_byte_records(self) -> None:
        """Creating Universal Hex from 32-byte record files should match JS output."""
        v1_hex = (HEX_FILES_DIR / "1-duck-umbrella-32.hex").read_text(encoding="ascii")
        v2_hex = (HEX_FILES_DIR / "2-ghost-music-32.hex").read_text(encoding="ascii")

        py_result = create_uhex(
            [
                IndividualHex(hex=v1_hex, board_id=BoardId.V1),
                IndividualHex(hex=v2_hex, board_id=BoardId.V2),
            ]
        )
        js_result = js_create_uhex(
            [
                IndividualHexJS(hex=v1_hex, board_id=BoardId.V1),
                IndividualHexJS(hex=v2_hex, board_id=BoardId.V2),
            ]
        )

        assert py_result == js_result

    def test_create_with_custom_board_ids(self) -> None:
        """Creating Universal Hex with custom board IDs should match JS output."""
        v1_hex = (HEX_FILES_DIR / "1-duck-umbrella-16.hex").read_text(encoding="ascii")
        v2_hex = (HEX_FILES_DIR / "2-ghost-music-16.hex").read_text(encoding="ascii")

        # Use non-standard board IDs
        py_result = create_uhex(
            [
                IndividualHex(hex=v1_hex, board_id=0x9901),  # V1.5
                IndividualHex(hex=v2_hex, board_id=0x9903),  # V2
            ]
        )
        js_result = js_create_uhex(
            [
                IndividualHexJS(hex=v1_hex, board_id=0x9901),
                IndividualHexJS(hex=v2_hex, board_id=0x9903),
            ]
        )

        assert py_result == js_result

    def test_create_reversed_order(self) -> None:
        """Order of input hexes should affect output identically in both."""
        v1_hex = (HEX_FILES_DIR / "1-duck-umbrella-16.hex").read_text(encoding="ascii")
        v2_hex = (HEX_FILES_DIR / "2-ghost-music-16.hex").read_text(encoding="ascii")

        # V2 first, then V1
        py_result = create_uhex(
            [
                IndividualHex(hex=v2_hex, board_id=BoardId.V2),
                IndividualHex(hex=v1_hex, board_id=BoardId.V1),
            ]
        )
        js_result = js_create_uhex(
            [
                IndividualHexJS(hex=v2_hex, board_id=BoardId.V2),
                IndividualHexJS(hex=v1_hex, board_id=BoardId.V1),
            ]
        )

        assert py_result == js_result


class TestSeparateUniversalHexComparison:
    """Compare separate_uhex() with JavaScript separateUniversalHex()."""

    @pytest.mark.parametrize(
        "hex_file",
        [
            "makecode-v3-universal.hex",
            "makecode-v5-universal.hex",
            "makecode-v8-universal.hex",
            "python-editor-universal.hex",
            "combined-16-blocks-1-9901-2-9903.hex",
            "combined-32-sections-1-9901-2-9903.hex",
        ],
    )
    def test_separate_universal_hex(self, hex_file: str) -> None:
        """Separating Universal Hex should produce identical results."""
        uhex_str = (HEX_FILES_DIR / hex_file).read_text(encoding="ascii")

        py_result = separate_uhex(uhex_str)
        js_result = js_separate_uhex(uhex_str)

        # Compare number of separated hexes
        assert len(py_result) == len(js_result)

        # Sort both by board_id for consistent comparison
        py_sorted = sorted(py_result, key=lambda x: x.board_id)
        js_sorted = sorted(js_result, key=lambda x: x.board_id)

        for py_hex, js_hex in zip(py_sorted, js_sorted):
            assert py_hex.board_id == js_hex.board_id
            assert py_hex.hex == js_hex.hex


class TestRoundTripComparison:
    """Test that create -> separate -> create produces consistent results."""

    def test_roundtrip_sections_format(self) -> None:
        """Round-trip through create and separate should be consistent."""
        v1_hex = (HEX_FILES_DIR / "1-duck-umbrella-16.hex").read_text(encoding="ascii")
        v2_hex = (HEX_FILES_DIR / "2-ghost-music-16.hex").read_text(encoding="ascii")

        # Create Universal Hex with Python
        py_uhex = create_uhex(
            [
                IndividualHex(hex=v1_hex, board_id=BoardId.V1),
                IndividualHex(hex=v2_hex, board_id=BoardId.V2),
            ]
        )

        # Create Universal Hex with JavaScript
        js_uhex = js_create_uhex(
            [
                IndividualHexJS(hex=v1_hex, board_id=BoardId.V1),
                IndividualHexJS(hex=v2_hex, board_id=BoardId.V2),
            ]
        )

        # Both should produce identical Universal Hex
        assert py_uhex == js_uhex

        # Separate the Python-created Universal Hex with both implementations
        py_separated_by_py = separate_uhex(py_uhex)
        py_separated_by_js = js_separate_uhex(py_uhex)

        # Results should be identical
        assert len(py_separated_by_py) == len(py_separated_by_js)

        py_sorted = sorted(py_separated_by_py, key=lambda x: x.board_id)
        js_sorted = sorted(py_separated_by_js, key=lambda x: x.board_id)

        for py_hex, js_hex in zip(py_sorted, js_sorted):
            assert py_hex.board_id == js_hex.board_id
            assert py_hex.hex == js_hex.hex

    @pytest.mark.skip(reason="use_blocks not yet implemented in Python")
    def test_roundtrip_blocks_format(self) -> None:
        """Round-trip with blocks format should be consistent."""
        v1_hex = (HEX_FILES_DIR / "1-duck-umbrella-16.hex").read_text(encoding="ascii")
        v2_hex = (HEX_FILES_DIR / "2-ghost-music-16.hex").read_text(encoding="ascii")

        # Create Universal Hex with Python using blocks format
        py_uhex = create_uhex(
            [
                IndividualHex(hex=v1_hex, board_id=BoardId.V1),
                IndividualHex(hex=v2_hex, board_id=BoardId.V2),
            ],
            use_blocks=True,  # type: ignore[call-arg]
        )

        # Create Universal Hex with JavaScript using blocks format
        js_uhex = js_create_uhex(
            [
                IndividualHexJS(hex=v1_hex, board_id=BoardId.V1),
                IndividualHexJS(hex=v2_hex, board_id=BoardId.V2),
            ],
            use_blocks=True,
        )

        # Both should produce identical Universal Hex
        assert py_uhex == js_uhex
