# octapy

Python library for reading, writing, and modifying Elektron Octatrack binary files.

## Installation

```bash
pip install -e .
```

## API Overview

### High-Level API (`octapy.api`)

The high-level API mirrors the Octatrack's UI hierarchy:

```
Project
└── Bank (1-16)
    ├── Pattern (1-16)
    │   ├── AudioPatternTrack (1-8) — audio sequence data
    │   │   └── AudioStep (1-64) — triggers, p-locks, conditions
    │   └── MidiPatternTrack (1-8) — MIDI sequence data
    │       └── MidiStep (1-64) — note, velocity, CC p-locks
    └── Part (1-4)
        ├── AudioPartTrack (1-8) — machine-specific sound settings
        └── MidiPartTrack (1-8) — MIDI channel, note, arp settings
```

**Project** is the main entry point. Load from directory, zip, or create from template.

**Bank** contains 16 patterns and 4 parts. Each pattern references one of the 4 parts for its sound settings.

**Pattern → PatternTrack → Step** is the sequencer path. AudioPatternTrack/MidiPatternTrack hold trigger data; AudioStep/MidiStep provide per-step access to triggers, p-locks, and trig conditions.

**Part → PartTrack** is the sound design path. AudioPartTrack subclasses configure machine-specific parameters; MidiPartTrack handles MIDI channel and note settings.

### Module Structure

```
octapy/api/
├── project.py          # Project entry point
├── bank.py             # Bank container
├── sample_pool.py      # SamplePool for loading samples
├── slot_manager.py     # Sample slot management
├── enums.py            # MachineType, TrigCondition, NoteLength, etc.
├── utils.py            # Quantization utilities
├── part/               # Part and PartTrack classes
│   ├── base.py         # BasePartTrack (ABC)
│   ├── audio.py        # AudioPartTrack (LFO, AMP pages)
│   ├── sampler.py      # SamplerPartTrack (Flex/Static base)
│   ├── flex.py         # FlexPartTrack
│   ├── static.py       # StaticPartTrack
│   ├── thru.py         # ThruPartTrack (input routing)
│   ├── neighbor.py     # NeighborPartTrack
│   ├── pickup.py       # PickupPartTrack
│   ├── midi.py         # MidiPartTrack
│   └── part.py         # Part container
├── pattern/            # Pattern and PatternTrack classes
│   ├── base.py         # BasePatternTrack (ABC)
│   ├── audio.py        # AudioPatternTrack
│   ├── midi.py         # MidiPatternTrack
│   └── pattern.py      # Pattern container
└── step/               # Step classes
    ├── base.py         # BaseStep + trig mask utilities
    ├── audio.py        # AudioStep (volume, pitch, sample lock)
    └── midi.py         # MidiStep (note, velocity, CC)
```

### Machine Types

AudioPartTrack returns machine-specific subclasses based on the track's machine type:

| Machine | Class | Description |
|---------|-------|-------------|
| FLEX | `FlexPartTrack` | RAM-based sample playback |
| STATIC | `StaticPartTrack` | Streaming sample playback |
| THRU | `ThruPartTrack` | Live input routing |
| NEIGHBOR | `NeighborPartTrack` | Adjacent track routing |
| PICKUP | `PickupPartTrack` | Live looper |

### Enums

- `MachineType` — FLEX, STATIC, THRU, NEIGHBOR, PICKUP
- `TrigCondition` — FILL, PRE, NEI, probability (1-99%), loop patterns (T1_R2, etc.)
- `NoteLength` — THIRTY_SECOND, SIXTEENTH, EIGHTH, QUARTER, HALF
- `FX1Type`, `FX2Type` — Effect types for FX slots
- `ThruInput` — Input routing for Thru machines

See `demos/` for usage examples.

### Low-Level File API (`octapy._io`)

The `_io` module provides direct buffer access to Octatrack binary formats, based on [ot-tools-io](https://gitlab.com/ot-tools/ot-tools-io/), an open-source Rust library by Mike Robeson (dijksterhuis).

- `BankFile` — patterns, parts, triggers, p-locks
- `MarkersFile` — sample markers, trim points, slices
- `ProjectFile` — project settings, sample slot assignments (INI format)

Each class wraps a `bytearray` buffer with typed accessors and offset enums.

## Supported Files

| File | Format | Contents |
|------|--------|----------|
| `bank01.work` - `bank16.work` | Binary | Patterns, parts, machine settings |
| `markers.work` | Binary | Sample markers, trim points, slices |
| `project.work` | Text (INI) | Project settings, sample slots |

## Project Structure

```
octapy/
├── api/           # High-level API
│   ├── part/      # Part and PartTrack classes (per-machine modules)
│   ├── pattern/   # Pattern and PatternTrack classes
│   └── step/      # Step classes (audio/MIDI)
├── _io/           # Low-level file I/O (BankFile, MarkersFile, ProjectFile)
└── templates/     # Embedded template files for new projects
demos/             # Usage examples (hello_flex, etc.)
tests/             # Test suite
tools/             # CLI utilities (copy_project, list_projects, etc.)
```

## References

- [ot-tools-io](https://gitlab.com/ot-tools/ot-tools-io/) — Original Rust implementation
- [Elektronauts thread](https://www.elektronauts.com/t/ot-tools-io-open-source-rust-library-for-reading-writing-modifying-octatrack-files/232508) — Community discussion
- [Rust API docs](https://docs.rs/ot-tools-io/latest/ot_tools_io/index.html) — Reference documentation

## License

MIT
