from pathlib import Path

import pytest
from click.testing import CliRunner

from universal_hex import BoardId, IndividualHex
from universal_hex import cli as cli_module
from universal_hex.cli import cli


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_help_lists_commands(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "join" in result.output
    assert "separate" in result.output


def test_join_requires_at_least_one_input(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["join"])
    assert result.exit_code == 2
    assert "Provide at least one input" in result.output


@pytest.mark.parametrize("option", ["--v1", "--v2"])
def test_join_non_repeatable_options_fail(
    runner: CliRunner, tmp_path: Path, option: str
) -> None:
    file_path = tmp_path / "file.hex"
    file_path.write_text(":00000001FF\n", encoding="utf-8")

    result = runner.invoke(
        cli, ["join", option, str(file_path), option, str(file_path)]
    )
    assert result.exit_code == 2
    assert "may be provided only once" in result.output


def test_join_rejects_non_hex_extension(runner: CliRunner, tmp_path: Path) -> None:
    file_path = tmp_path / "file.txt"
    file_path.write_text(":00000001FF\n", encoding="utf-8")

    result = runner.invoke(cli, ["join", "--v1", str(file_path)])
    assert result.exit_code == 2
    assert "File must have a .hex extension" in result.output


def test_join_rejects_out_of_range_board_id(runner: CliRunner, tmp_path: Path) -> None:
    file_path = tmp_path / "file.hex"
    file_path.write_text(":00000001FF\n", encoding="utf-8")

    result = runner.invoke(cli, ["join", "-b", "70000", str(file_path)])
    assert result.exit_code == 2
    assert "Invalid value for '-b" in result.output


def test_join_mixes_option_inputs(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test join collects V1, V2, and board-file options."""
    v1_path = tmp_path / "v1.hex"
    custom_path = tmp_path / "custom.hex"
    v2_path = tmp_path / "v2.hex"

    v1_path.write_text("v1", encoding="utf-8")
    custom_path.write_text("custom", encoding="utf-8")
    v2_path.write_text("v2", encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_create_uhex(hexes: list[IndividualHex]) -> str:
        captured["hexes"] = hexes
        return "combined"

    monkeypatch.setattr(cli_module, "create_uhex", fake_create_uhex)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        cli,
        [
            "join",
            "--v1",
            str(v1_path),
            "-b",
            "1001",
            str(custom_path),
            "--v2",
            str(v2_path),
        ],
    )

    assert result.exit_code == 0
    assert "Universal Hex written to:" in result.output

    hexes = captured["hexes"]
    assert isinstance(hexes, list)
    # Click doesn't preserve interleaved order; ordering is: V1, V2, board-files
    assert [h.board_id for h in hexes] == [BoardId.V1, BoardId.V2, 1001]
    assert [h.hex for h in hexes] == ["v1", "v2", "custom"]


def test_separate_writes_files_and_outputs_paths(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_path = tmp_path / "input.hex"
    input_path.write_text("content", encoding="utf-8")

    outputs = [
        IndividualHex(hex="v1-data\n", board_id=BoardId.V1),
        IndividualHex(hex="custom\n", board_id=0x1234),
    ]

    def fake_separate_uhex(data: str) -> list[IndividualHex]:
        assert data == "content"
        return outputs

    monkeypatch.setattr(cli_module, "separate_uhex", fake_separate_uhex)

    result = runner.invoke(cli, ["separate", str(input_path)])
    assert result.exit_code == 0

    out_v1 = tmp_path / "input-board-0x9900.hex"
    out_custom = tmp_path / "input-board-0x1234.hex"

    assert out_v1.read_text(encoding="utf-8") == "v1-data\n"
    assert out_custom.read_text(encoding="utf-8") == "custom\n"

    assert str(out_v1) in result.output
    assert str(out_custom) in result.output


def test_separate_requires_hex_extension(runner: CliRunner, tmp_path: Path) -> None:
    input_path = tmp_path / "input.bin"
    input_path.write_text("content", encoding="utf-8")

    result = runner.invoke(cli, ["separate", str(input_path)])
    assert result.exit_code == 2
    assert "File must have a .hex extension" in result.output


def test_join_rejects_v1_with_matching_board_id(
    runner: CliRunner, tmp_path: Path
) -> None:
    """Test --v1 cannot be used with -b using BoardId.V1 (0x9900)."""
    file_path = tmp_path / "file.hex"
    file_path.write_text(":00000001FF\n", encoding="utf-8")

    result = runner.invoke(
        cli, ["join", "--v1", str(file_path), "-b", "39168", str(file_path)]
    )
    assert result.exit_code == 2
    assert "Board ID for V1 and --v1 provided together" in result.output


def test_join_rejects_v2_with_matching_board_id(
    runner: CliRunner, tmp_path: Path
) -> None:
    """Test --v2 cannot be used with -b using BoardId.V2 (0x9903)."""
    file_path = tmp_path / "file.hex"
    file_path.write_text(":00000001FF\n", encoding="utf-8")

    result = runner.invoke(
        cli, ["join", "--v2", str(file_path), "-b", "39171", str(file_path)]
    )
    assert result.exit_code == 2
    assert "Board ID for V2 and --v2 provided together" in result.output


def test_join_rejects_duplicate_board_ids(runner: CliRunner, tmp_path: Path) -> None:
    """Test that the same board ID cannot be provided twice via -b."""
    file_path = tmp_path / "file.hex"
    file_path.write_text(":00000001FF\n", encoding="utf-8")

    result = runner.invoke(
        cli,
        ["join", "-b", "1234", str(file_path), "-b", "1234", str(file_path)],
    )
    assert result.exit_code == 2
    assert "Board ID may be provided only once" in result.output


def test_join_accepts_hex_board_id(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test -b accepts hexadecimal board IDs like 0x1234."""
    file_path = tmp_path / "file.hex"
    file_path.write_text("hex-content", encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_create_uhex(hexes: list[IndividualHex]) -> str:
        captured["hexes"] = hexes
        return "combined"

    monkeypatch.setattr(cli_module, "create_uhex", fake_create_uhex)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(cli, ["join", "-b", "0x1234", str(file_path)])
    assert result.exit_code == 0

    hexes = captured["hexes"]
    assert isinstance(hexes, list)
    assert len(hexes) == 1
    assert hexes[0].board_id == 0x1234  # 4660 in decimal


def test_join_rejects_hex_board_id_out_of_range(
    runner: CliRunner, tmp_path: Path
) -> None:
    """Test -b rejects hex board IDs outside 0-65535 range."""
    file_path = tmp_path / "file.hex"
    file_path.write_text(":00000001FF\n", encoding="utf-8")

    result = runner.invoke(cli, ["join", "-b", "0x10000", str(file_path)])
    assert result.exit_code == 2
    assert "not in the range 0 to 65535" in result.output


def test_join_rejects_invalid_board_id_string(
    runner: CliRunner, tmp_path: Path
) -> None:
    """Test -b rejects non-numeric board ID strings."""
    file_path = tmp_path / "file.hex"
    file_path.write_text(":00000001FF\n", encoding="utf-8")

    result = runner.invoke(cli, ["join", "-b", "notanumber", str(file_path)])
    assert result.exit_code == 2
    assert "is not a valid integer" in result.output
