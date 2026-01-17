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

---

## Phase 2: MIDI Part Configuration (MidiPartTrack)

### Overview

Implement `MidiPartTrack` class for configuring MIDI track settings at the Part level. This is analogous to `PartTrack` for audio tracks (machine type, sample slots) but for MIDI (channel, program, default note/velocity/length).

### Settings to Implement

| Property | Field | Offset | Type | Default | Description |
|----------|-------|--------|------|---------|-------------|
| `channel` | `chan` | TBD | int | 0 | MIDI channel (0-15) |
| `bank` | `bank` | TBD | int | 128 | Bank select (128 = off) |
| `program` | `prog` | TBD | int | 128 | Program change (128 = off) |
| `default_note` | `note` | TBD | int | 48 | Base note (48 = C3) |
| `default_velocity` | `vel` | TBD | int | 100 | Base velocity (0-127) |
| `default_length` | `len` | TBD | int | 6 | Base note length |

### Note Length Values

The `default_length` field uses value `6` as the default. Based on device observation, this appears to display as "1/16" in the UI (SRC page, dial C).

**TODO: Full value mapping needs device verification.**

The exact mapping between byte values (0-127?) and musical durations (1/128, 1/64, 1/32, 1/16, 1/8, etc.) is not documented in the ot-tools-io library. For now, implement with raw integer values and default of 6.

### Implementation Tasks

#### 1. Add MidiPartTrack class

Location: `octapy/api/part.py`

```python
class MidiPartTrack:
    """
    MIDI configuration for a track within a Part.

    Provides access to MIDI channel, program, and default note parameters.
    """

    def __init__(self, part: "Part", track_num: int):
        self._part = part
        self._track_num = track_num

    @property
    def channel(self) -> int:
        """MIDI channel (0-15)."""
        # TODO: implement offset calculation
        pass

    @channel.setter
    def channel(self, value: int):
        pass

    @property
    def default_length(self) -> int:
        """Default note length. Value 6 = 1/16 (believed)."""
        pass

    @default_length.setter
    def default_length(self, value: int):
        pass

    # ... similar for other properties
```

#### 2. Add midi_track() method to Part

Location: `octapy/api/part.py`

```python
class Part:
    def __init__(self, ...):
        ...
        self._midi_tracks: Dict[int, MidiPartTrack] = {}

    def midi_track(self, track_num: int) -> MidiPartTrack:
        """
        Get MIDI configuration for a track (1-8).

        Args:
            track_num: Track number (1-8)

        Returns:
            MidiPartTrack instance
        """
        if track_num not in self._midi_tracks:
            self._midi_tracks[track_num] = MidiPartTrack(self, track_num)
        return self._midi_tracks[track_num]
```

#### 3. Add low-level offsets

Location: `octapy/_io/bank.py`

```python
class MidiPartOffset:
    """Offsets for MIDI track data within a Part."""
    # TODO: Determine from ot-tools-io or reverse engineering
    MIDI_TRACK_PARAMS_VALUES = ...
    MIDI_TRACK_PARAMS_SETUP = ...
```

#### 4. Add tests

Location: `tests/test_parts.py`

```python
class TestMidiPartTrack:
    def test_channel_default(self):
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.channel == 0

    def test_default_length_default(self):
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.default_length == 6  # 1/16

    def test_channel_roundtrip(self, temp_dir):
        project = Project.from_template("TEST")
        project.bank(1).part(1).midi_track(1).channel = 5
        project.to_zip(temp_dir / "TEST.zip")

        loaded = Project.from_zip(temp_dir / "TEST.zip")
        assert loaded.bank(1).part(1).midi_track(1).channel == 5
```

### API Usage

```python
from octapy import Project

project = Project.from_template("MY PROJECT")
part = project.bank(1).part(1)

# Configure MIDI track 1
midi_track = part.midi_track(1)
midi_track.channel = 5           # MIDI channel 6 (0-indexed)
midi_track.program = 32          # Program 33
midi_track.default_note = 60     # Middle C
midi_track.default_velocity = 100
midi_track.default_length = 6    # 1/16 (believed default)

project.to_zip("MY PROJECT.zip")
```

### Files to Modify

| File | Changes |
|------|---------|
| `octapy/_io/bank.py` | Add `MidiPartOffset` constants |
| `octapy/api/part.py` | Add `MidiPartTrack` class, `Part.midi_track()` method |
| `tests/test_parts.py` | Add roundtrip tests for MIDI part configuration |

### Verification

1. Create project with MIDI track configured
2. Copy to Octatrack
3. Press MIDI button, select track, verify channel/program in SRC page
4. Verify default note/velocity/length values

### Deferred

- CC number assignments (Phase 4)
- Arp setup and sequences (Phase 5)

---

## Future Phases

- **Phase 3**: MIDI pattern sequencing (MidiPatternTrack, MidiStep)
- **Phase 4**: MIDI CC assignments and control
- **Phase 5**: Arp sequences and advanced MIDI features
