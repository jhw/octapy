# octapy

Python library for reading, writing, and modifying Elektron Octatrack binary files.

This is a Pythonic port of [ot-tools-io](https://gitlab.com/ot-tools/ot-tools-io/), an open-source Rust library by Mike Robeson (dijksterhuis).

## About ot-tools-io

- **Forum thread**: [Elektronauts announcement](https://www.elektronauts.com/t/ot-tools-io-open-source-rust-library-for-reading-writing-modifying-octatrack-files/232508) - Community discussion and project announcement
- **Source code**: [GitLab repository](https://gitlab.com/ot-tools/ot-tools-io/) - The original Rust implementation
- **API docs**: [docs.rs documentation](https://docs.rs/ot-tools-io/latest/ot_tools_io/index.html) - Rust API reference

## Installation

```bash
pip install -e .
```

Or for development:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Creating a project with Flex machines

```python
from octapy import BankFile, MarkersFile, ProjectFile, MachineType

# Load a bank file from a template
bank = BankFile.from_file("path/to/bank01.work")

# Set up a Flex machine on track 1
bank.set_machine_type(track=1, machine_type=MachineType.FLEX)
bank.set_flex_slot(track=1, slot=1)

# Set trigger pattern (steps 1, 5, 9, 13 for a kick drum)
bank.set_trigs(pattern=1, track=1, steps=[1, 5, 9, 13])

# Save the bank
bank.to_file("path/to/bank01.work")

# Set up markers (sample lengths)
markers = MarkersFile.from_file("path/to/markers.work")
markers.set_sample_length(slot=1, length=44100)  # 1 second at 44.1kHz
markers.to_file("path/to/markers.work")

# Create project.work with sample slot assignments
project = ProjectFile()
project.tempo = 120.0
project.add_sample_slot(slot_number=1, path="../AUDIO/kick.wav", slot_type="FLEX")
project.add_recorder_slots()
project.to_file("path/to/project.work")
```

### Reading pattern data

```python
from octapy import BankFile

bank = BankFile.from_file("bank01.work")

# Get trigger steps for track 1 in pattern 1
steps = bank.get_trigs(pattern=1, track=1)
print(f"Active steps: {steps}")

# Get machine type
machine = bank.get_machine_type(track=1)
print(f"Machine type: {machine}")
```

## Supported File Types

| File | Format | Description |
|------|--------|-------------|
| `bank01.work` - `bank16.work` | Binary | Patterns, parts, machine settings |
| `markers.work` | Binary | Sample playback markers, trim points, slices |
| `project.work` | Text (INI) | Project settings, sample slot assignments |

## Architecture

octapy uses a buffer-based serialization approach (inspired by [pym8](https://github.com/jhw/pym8)):

- Each file type has a corresponding class (`BankFile`, `MarkersFile`, `ProjectFile`)
- Binary data is stored in `_data: bytearray` buffers
- Typed property accessors provide safe read/write access
- Offset enums define byte positions within structures

## Project Structure

```
octapy/
├── api/
│   ├── __init__.py    # Base classes, enums, utilities
│   ├── banks.py       # BankFile (patterns, parts, machines)
│   ├── patterns.py    # Pattern, AudioTrack (triggers)
│   ├── parts.py       # Part (track settings, slots)
│   └── markers.py     # MarkersFile, SlotMarkers
├── projects.py        # ProjectFile (text-based INI)
└── __init__.py        # Public API exports
demos/
└── hello_flex.py      # Example: create project with Flex machines
tools/
├── copy_project.py    # Copy project to Octatrack
├── list_projects.py   # List projects on device
└── ...
```

## License

MIT

## Credits

- **ot-tools-io**: Mike Robeson (dijksterhuis) - Original Rust implementation
- **pym8**: Serialization pattern inspiration
