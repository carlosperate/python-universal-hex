"""Command-line interface for universal-hex."""

from __future__ import annotations

from pathlib import Path

import click

from . import __version__
from .uhex import BoardId, IndividualHex, create_uhex, separate_uhex


class BoardIdType(click.ParamType):
    """Click type that accepts decimal or hexadecimal board IDs (0-65535)."""

    name = "BOARD_ID"

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> int:
        try:
            board_id = int(value, 0)  # base 0 auto-detects hex (0x) or decimal
        except ValueError:
            self.fail(f"{value!r} is not a valid integer.", param, ctx)
        if not 0 <= board_id <= 65535:
            self.fail(f"{board_id} is not in the range 0 to 65535.", param, ctx)
        return board_id


def _validate_hex_path(path: Path, param_name: str) -> None:
    """Ensure the provided path points to a .hex file."""
    if path.suffix.lower() != ".hex":
        raise click.BadParameter(
            "File must have a .hex extension.",
            param_hint=param_name,
        )


@click.group()
@click.version_option(version=__version__, prog_name="uhex")
def cli() -> None:
    """Create or separate micro:bit Universal Hex files."""
    pass


@cli.command()
@click.option(
    "--v1",
    "v1_files",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    multiple=True,
    help="Intel Hex file for micro:bit V1 (only once).",
)
@click.option(
    "--v2",
    "v2_files",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    multiple=True,
    help="Intel Hex file for micro:bit V2 (only once).",
)
@click.option(
    "-b",
    "--board-file",
    "board_files",
    nargs=2,
    type=(
        BoardIdType(),
        click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    ),
    multiple=True,
    help="Board ID (decimal or hex) and Intel Hex file (repeatable).",
)
@click.option(
    "-o",
    "--output",
    "output_file",
    type=click.Path(path_type=Path),
    default="universal.hex",
    help="Output file path for the Universal Hex (default: universal.hex).",
)
def join(
    v1_files: tuple[Path, ...],
    v2_files: tuple[Path, ...],
    board_files: tuple[tuple[int, Path], ...],
    output_file: Path,
) -> None:
    """Join Intel Hex files into a Universal Hex."""
    # Validate option combinations
    if len(v1_files) > 1:
        raise click.UsageError("--v1 may be provided only once.")
    if len(v2_files) > 1:
        raise click.UsageError("--v2 may be provided only once.")
    if len(board_files):
        board_ids = [board_id for board_id, _ in board_files]
        if len(board_ids) != len(set(board_ids)):
            raise click.UsageError(
                "Board ID may be provided only once per --board-file."
            )
        if len(v1_files) and BoardId.V1 in board_ids:
            raise click.UsageError("Board ID for V1 and --v1 provided together.")
        if len(v2_files) and BoardId.V2 in board_ids:
            raise click.UsageError("Board ID for V2 and --v2 provided together.")
    if not v1_files and not v2_files and not board_files:
        raise click.UsageError(
            "Provide at least one input via --v1, --v2, or --board-file."
        )

    # Validate .hex extensions
    for path in v1_files:
        _validate_hex_path(path, "--v1")
    for path in v2_files:
        _validate_hex_path(path, "--v2")
    for _, path in board_files:
        _validate_hex_path(path, "--board-file")

    # Build list preserving CLI order is tricky with multiple options.
    # Click doesn't preserve interleaved order, so we collect separately.
    # For predictable ordering: V1 first, then V2, then board-files.
    hexes: list[IndividualHex] = []
    for path in v1_files:
        content = path.read_text(encoding="ascii")
        hexes.append(IndividualHex(hex=content, board_id=BoardId.V1))
    for path in v2_files:
        content = path.read_text(encoding="ascii")
        hexes.append(IndividualHex(hex=content, board_id=BoardId.V2))
    for board_id, path in board_files:
        content = path.read_text(encoding="ascii")
        hexes.append(IndividualHex(hex=content, board_id=board_id))

    universal_hex = create_uhex(hexes)
    uhex_file = output_file
    with uhex_file.open("w", encoding="ascii", newline="\n") as handle:
        handle.write(universal_hex)
    click.echo(f"Universal Hex written to: {uhex_file}")


@cli.command()
@click.argument(
    "file",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
)
def separate(file: Path) -> None:
    """Separate a Universal Hex into individual Intel Hex files."""
    _validate_hex_path(file, "FILE")
    content = file.read_text(encoding="ascii")

    hexes = separate_uhex(content)
    if not hexes:
        click.echo("No individual hex files found in the Universal Hex.", err=True)
        return

    output_paths: list[Path] = []
    for entry in hexes:
        out_path = file.with_name(f"{file.stem}-board-0x{entry.board_id:04X}.hex")
        with out_path.open("w", encoding="ascii", newline="\n") as handle:
            handle.write(entry.hex)
        output_paths.append(out_path)

    click.echo("Separated Intel Hex files written to:")
    for out_path in output_paths:
        click.echo(str(out_path))


if __name__ == "__main__":
    cli()
