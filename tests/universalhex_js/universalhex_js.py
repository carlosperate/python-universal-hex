"""
Python wrapper for the original microbit-universal-hex JavaScript library.

This module uses py_mini_racer to execute the JavaScript library and compare
its outputs with the Python port for testing purposes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, NamedTuple

from py_mini_racer import MiniRacer

_ctx_mr: MiniRacer | None = None


class IndividualHexJS(NamedTuple):
    """An individual Intel Hex file with its board ID (from JS library)."""

    hex: str
    board_id: int


def _get_ctx() -> MiniRacer:
    """Get or create the MiniRacer context with the JS library loaded."""
    global _ctx_mr
    if _ctx_mr is None:
        js_file = Path(__file__).parent / "microbit-universal-hex.js"
        if not js_file.exists():
            raise FileNotFoundError(
                f"JavaScript bundle not found at {js_file}. "
                "Run the build steps in tests/universalhex_js/README.md"
            )
        universal_hex_js = js_file.read_text(encoding="utf-8")
        _ctx_mr = MiniRacer()
        _ctx_mr.eval(universal_hex_js)
    return _ctx_mr


def create_universal_hex(
    hexes: list[IndividualHexJS], *, use_blocks: bool = False
) -> str:
    """
    Create a Universal Hex from multiple Intel Hex strings using the JS library.

    :param hexes: List of IndividualHexJS with hex string and board_id.
    :param use_blocks: If True, use 512-byte blocks format instead of sections.
    :return: Universal Hex string.
    """
    ctx_mr = _get_ctx()

    hex_array_js = "["
    for ih in hexes:
        hex_array_js += f"{{ hex: `{ih.hex}`, boardId: {ih.board_id} }}, "
    hex_array_js += "]"

    use_blocks_js = "true" if use_blocks else "false"
    result: Any = ctx_mr.eval(
        f"universalHex.createUniversalHex({hex_array_js}, {use_blocks_js})"
    )
    return str(result)


def separate_universal_hex(universal_hex_str: str) -> list[IndividualHexJS]:
    """
    Separate a Universal Hex into its individual Intel Hexes using the JS library.

    :param universal_hex_str: Universal Hex string to separate.
    :return: List of IndividualHexJS tuples with hex and board_id.
    """
    ctx_mr = _get_ctx()

    result: Any = ctx_mr.eval(
        f"universalHex.separateUniversalHex(`{universal_hex_str}`)"
    )

    # Convert the result to Python objects
    hexes: list[IndividualHexJS] = []
    for item in result:
        hexes.append(
            IndividualHexJS(hex=str(item["hex"]), board_id=int(item["boardId"]))
        )
    return hexes


def is_universal_hex(hex_str: str) -> bool:
    """
    Check if the provided hex string is a Universal Hex using the JS library.

    :param hex_str: Hex string to check.
    :return: True if the hex is a Universal Hex.
    """
    ctx_mr = _get_ctx()
    result: Any = ctx_mr.eval(f"universalHex.isUniversalHex(`{hex_str}`)")
    return bool(result)


def is_makecode_for_v1_hex(hex_str: str) -> bool:
    """
    Check if the hex string is a MakeCode for V1 Intel Hex using the JS library.

    :param hex_str: Hex string to check.
    :return: True if the hex is a MakeCode V1 hex.
    """
    ctx_mr = _get_ctx()
    result: Any = ctx_mr.eval(f"universalHex.isMakeCodeForV1Hex(`{hex_str}`)")
    return bool(result)


def main() -> None:
    """Simple test/demo of the JS library wrapper."""
    from pathlib import Path

    hex_files_dir = Path(__file__).parent.parent / "hex-files"

    # Test with some hex files
    v1_hex = (hex_files_dir / "1-duck-umbrella-16.hex").read_text(encoding="ascii")
    v2_hex = (hex_files_dir / "2-ghost-music-16.hex").read_text(encoding="ascii")

    print("Testing is_universal_hex...")
    print(f"  V1 hex is Universal Hex: {is_universal_hex(v1_hex)}")

    # Load a Universal Hex
    uhex = (hex_files_dir / "makecode-v3-universal.hex").read_text(encoding="ascii")
    print(f"  Universal Hex is Universal Hex: {is_universal_hex(uhex)}")

    print("\nTesting create_universal_hex...")
    combined = create_universal_hex(
        [
            IndividualHexJS(hex=v1_hex, board_id=0x9900),  # V1 board ID
            IndividualHexJS(hex=v2_hex, board_id=0x9903),  # V2 board ID
        ]
    )
    print(f"  Created Universal Hex with {len(combined)} characters")
    print(f"  Result is Universal Hex: {is_universal_hex(combined)}")

    print("\nTesting separate_universal_hex...")
    separated = separate_universal_hex(uhex)
    print(f"  Separated into {len(separated)} hex files:")
    for ih in separated:
        print(f"    Board ID: 0x{ih.board_id:04X}, hex length: {len(ih.hex)}")


if __name__ == "__main__":
    main()
