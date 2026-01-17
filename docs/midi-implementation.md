# MIDI Implementation Plan

This document outlines the phased implementation of MIDI support in octapy.

## Phase 1: Global MIDI Settings

### Overview

Implement project-level MIDI settings for clock, transport, and program change. These are stored in `project.work` (INI text format) and control how the Octatrack syncs with external MIDI gear.

### Current State

The low-level `ProjectSettings` dataclass already defines these fields:

```python
@dataclass
class ProjectSettings:
    midi_clock_send: int = 0
    midi_clock_receive: int = 0
    midi_transport_send: int = 0
    midi_transport_receive: int = 0
    midi_program_change_send: int = 0
    midi_program_change_send_ch: int = -1
    midi_program_change_receive: int = 0
    midi_program_change_receive_ch: int = -1
```

**What works:**
- Fields are written to `project.work` on save

**What's missing:**
- Fields are not parsed on load (use defaults)
- No high-level API on Project class
- Types are int, should expose as bool where appropriate

### Settings to Implement

| Setting | File Field | Type | Default | Description |
|---------|------------|------|---------|-------------|
| `midi_clock_send` | `MIDI_CLOCK_SEND` | bool | False | Send MIDI clock to external gear |
| `midi_clock_receive` | `MIDI_CLOCK_RECEIVE` | bool | False | Sync to incoming MIDI clock |
| `midi_transport_send` | `MIDI_TRANSPORT_SEND` | bool | False | Send start/stop/continue |
| `midi_transport_receive` | `MIDI_TRANSPORT_RECEIVE` | bool | False | Respond to start/stop/continue |
| `midi_program_change_send` | `MIDI_PROGRAM_CHANGE_SEND` | bool | False | Send program changes on pattern switch |
| `midi_program_change_send_ch` | `MIDI_PROGRAM_CHANGE_SEND_CH` | int | -1 | Channel for send (-1 = disabled) |
| `midi_program_change_receive` | `MIDI_PROGRAM_CHANGE_RECEIVE` | bool | False | Switch patterns on program change |
| `midi_program_change_receive_ch` | `MIDI_PROGRAM_CHANGE_RECEIVE_CH` | int | -1 | Channel for receive (-1 = disabled) |

### Implementation Tasks

#### 1. Add parsing in `ProjectFile._parse_content()`

Location: `octapy/_io/project.py`

```python
# In SETTINGS section parsing
midi_clock_send = re.search(r'MIDI_CLOCK_SEND=(\d+)', settings_content)
if midi_clock_send:
    self.settings.midi_clock_send = int(midi_clock_send.group(1))

midi_clock_receive = re.search(r'MIDI_CLOCK_RECEIVE=(\d+)', settings_content)
if midi_clock_receive:
    self.settings.midi_clock_receive = int(midi_clock_receive.group(1))

# ... repeat for other fields
```

#### 2. Add high-level properties on Project class

Location: `octapy/api/project.py`

```python
@property
def midi_clock_send(self) -> bool:
    """Enable/disable sending MIDI clock to external gear."""
    return bool(self._project_file.settings.midi_clock_send)

@midi_clock_send.setter
def midi_clock_send(self, value: bool):
    self._project_file.settings.midi_clock_send = int(value)

@property
def midi_clock_receive(self) -> bool:
    """Enable/disable syncing to incoming MIDI clock."""
    return bool(self._project_file.settings.midi_clock_receive)

@midi_clock_receive.setter
def midi_clock_receive(self, value: bool):
    self._project_file.settings.midi_clock_receive = int(value)

# ... similar for transport and program change
```

#### 3. Add tests

Location: `tests/test_project.py`

```python
class TestMidiSettings:
    def test_midi_clock_send_default_false(self):
        project = Project.from_template("TEST")
        assert project.midi_clock_send is False

    def test_midi_clock_send_roundtrip(self, temp_dir):
        project = Project.from_template("TEST")
        project.midi_clock_send = True
        project.to_directory(temp_dir / "TEST")

        loaded = Project.from_directory(temp_dir / "TEST")
        assert loaded.midi_clock_send is True

    # ... similar for other settings
```

#### 4. Export from package

Location: `octapy/__init__.py`

No changes needed — settings accessed via `project.midi_clock_send` etc.

### API Usage

```python
from octapy import Project

project = Project.from_template("MY PROJECT")

# Configure MIDI sync
project.midi_clock_send = True
project.midi_transport_send = True

# Configure program change
project.midi_program_change_send = True
project.midi_program_change_send_ch = 10  # Channel 10

project.to_zip("MY PROJECT.zip")
```

### Files to Modify

| File | Changes |
|------|---------|
| `octapy/_io/project.py` | Add parsing for 8 MIDI settings |
| `octapy/api/project.py` | Add 8 properties (4 bool, 4 int/bool pairs) |
| `tests/test_project.py` | Add roundtrip tests for each setting |

### Verification

1. Create project with settings enabled
2. Copy to Octatrack
3. Verify settings appear correctly in PROJECT > MIDI > SYNC menu

### Future Phases

- **Phase 2**: MIDI track channel/program configuration (MidiPartTrack)
- **Phase 3**: MIDI pattern sequencing (MidiPatternTrack, MidiStep)
- **Phase 4**: MIDI CC assignments and control
- **Phase 5**: Arp sequences and advanced MIDI features
