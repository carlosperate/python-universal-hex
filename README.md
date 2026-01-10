# Python Universal Hex Library

A Python library to create and process micro:bit Universal Hex files.

Universal Hex is a superset of the Intel Hex format that can contain data for multiple micro:bit board versions (V1 and V2) in a single file.

## Installation

```bash
pip install universal-hex
```

## Usage

### Creating a Universal Hex

```python
from universal_hex import create_uhex, IndividualHex, BoardId

# Load your V1 and V2 hex files
v1_hex = open("program_v1.hex").read()
v2_hex = open("program_v2.hex").read()

# Create a Universal Hex
uhex = create_uhex([
    IndividualHex(hex=v1_hex, board_id=BoardId.V1),
    IndividualHex(hex=v2_hex, board_id=BoardId.V2),
])

# Save the result (always use \n line endings)
with open("program_universal.hex", "w", newline="\n") as f:
    f.write(uhex)
```

### Separating a Universal Hex

```python
from universal_hex import separate_uhex

# Load a Universal Hex file
uhex = open("program_universal.hex").read()

# Separate into individual Intel Hex files
ihexes = separate_uhex(uhex)

for ihex in ihexes:
    print(f"Board ID: 0x{ihex.board_id:04X}")
    # ihex.hex contains the Intel Hex content for this board
```

### Checking if a file is a Universal Hex

```python
from universal_hex import is_uhex

hex_content = open("some_file.hex").read()

if is_uhex(hex_content):
    print("This is a Universal Hex file")
else:
    print("This is a standard Intel Hex file")
```

## Development

```bash
# Install with dev dependencies
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=universal_hex
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- This project has been ported (AI assisted) from the original
  [microbit-universal-hex](https://github.com/microbit-foundation/microbit-universal-hex)
  TypeScript library.
