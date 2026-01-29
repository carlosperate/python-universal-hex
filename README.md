# Python Universal Hex Library

A Python library to create and process micro:bit Universal Hex files.

Universal Hex is a superset of the Intel Hex format that can contain data for
multiple micro:bit board versions (V1 and V2) in a single file.

## Installation

To get easy access to the Universal Hex command line interface we recommend
using [uv](https://docs.astral.sh/uv/):

```bash
uv tool install universal-hex
```

It can also be pip installed as a normal Python package and used as a library.

```bash
pip install universal-hex
```

## Command Line Interface

A CLI is provided via the `uhex` entry point.

The `separate` command takes a Universal Hex file and created

```bash
# Separate a single Universal Hex into board-specific files
uhex separate file.hex
```

The `join` command takes multiple Intel Hex files to combine them into a
Universal Hex:

```bash
# Join Intel Hex files for micro:bit V1 and V2 boards
uhex join --v1 one.hex --v2 two.hex

# Join using custom board IDs (repeat -b as needed)
uhex join -b 12345 board_a.hex -b 42 board_b.hex

# Mix V1/V2 with custom board IDs
uhex join --v1 one.hex -b 12345 other.hex --v2 two.hex
```

- `separate` writes one output per board next to the input file using the
    pattern `<input-stem>-board-<BOARD_ID>.hex` (e.g. `firmware-board-9900.hex`).
- `join` reads all provided hex files and writes the Universal Hex to stdout.
- Validation happens during CLI parsing: files must exist, must not be
    directories, must end with `.hex`, and board IDs must be within 0–65535.

## Library Usage

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
# Clone
git clone https://github.com/carlosperate/python-universal-hex.git
cd python-universal-hex

# Install with dev dependencies
uv sync

# Run all checkers and tests
uv run make.py check
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- This project has been ported (AI assisted) from the original
  [microbit-universal-hex](https://github.com/microbit-foundation/microbit-universal-hex)
  TypeScript library.
