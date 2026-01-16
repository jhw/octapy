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
    │   └── PatternTrack (1-8) — sequence data
    │       └── Step (1-64) — triggers, p-locks, conditions
    └── Part (1-4)
        └── PartTrack (1-8) — sound/machine settings
```

**Project** is the main entry point. Load from directory, zip, or create from template.

**Bank** contains 16 patterns and 4 parts. Each pattern references one of the 4 parts for its sound settings.

**Pattern → PatternTrack → Step** is the sequencer path. PatternTrack holds trigger data; Step provides per-step access to triggers, p-locks (volume, pitch, sample lock), and trig conditions (FILL, probability, loop patterns).

**Part → PartTrack** is the sound design path. PartTrack configures machine type, sample slots, and effects for each track.

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
├── api/           # High-level API (Project, Bank, Pattern, Part, Step)
├── _io/           # Low-level file I/O (BankFile, MarkersFile, ProjectFile)
└── templates/     # Embedded template files for new projects
demos/             # Usage examples
tools/             # CLI utilities (copy_project, list_projects, etc.)
```

## References

- [ot-tools-io](https://gitlab.com/ot-tools/ot-tools-io/) — Original Rust implementation
- [Elektronauts thread](https://www.elektronauts.com/t/ot-tools-io-open-source-rust-library-for-reading-writing-modifying-octatrack-files/232508) — Community discussion
- [Rust API docs](https://docs.rs/ot-tools-io/latest/ot_tools_io/index.html) — Reference documentation

## License

MIT
